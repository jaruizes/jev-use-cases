import { Component, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { UseCase, ProviderId, Execution, ProviderResult, Scenario } from '../../core/models';
import { UseCasesApiService } from '../../services/use-cases-api.service';
import { ExecutionsApiService } from '../../services/executions-api.service';

interface Row {
  provider: ProviderId;
  attempts: number;
  successes: number;
  errors: number;
  correct: number;
  evaluated: number;
  accuracy: number | null;
  avgLatency: number | null;
  minLatency: number | null;
  maxLatency: number | null;
  totalCost: number | null;
  avgCost: number | null;
}
interface Detail {
  scenario: Scenario;
  values: {provider: ProviderId; correct: number; evaluated: number; failed: number;
    responses: string[]; avgLatency: number | null; avgCost: number | null;}[];
}

@Component({
  standalone: true,
  imports: [FormsModule, DecimalPipe],
  templateUrl: './test-scenarios.page.html',
})
export class TestScenariosPage {
  private catalog = inject(UseCasesApiService);
  private executions = inject(ExecutionsApiService);

  cases = signal<UseCase[]>([]);
  selectedId = 'incident-prioritization';
  iterations = 3;
  providers = signal<ProviderId[]>(['jev', 'haiku', 'sonnet']);
  running = signal(false);
  completed = signal(false);
  progress = signal(0);
  error = signal('');
  runs = signal<Execution[]>([]);
  cancelled = false;

  constructor() {
    this.catalog.list().subscribe({
      next: cases => this.cases.set(cases),
      error: () => this.error.set('Cannot load use cases from the API.'),
    });
  }

  get selected(): UseCase | undefined {
    return this.cases().find(c => c.id === this.selectedId);
  }

  get total(): number {
    return (this.selected?.scenarios.length ?? 0) * this.iterations;
  }

  changeCase(id: string): void {
    this.selectedId = id;
    if (this.selected?.kind === 'generation') this.providers.set(['haiku','sonnet']);
    else this.providers.set(['jev','haiku','sonnet']);
    this.clearResults();
  }

  toggle(provider: ProviderId): void {
    this.providers.update(items =>
      items.includes(provider) ? items.filter(i => i !== provider) : [...items, provider]);
    this.clearResults();
  }

  clearResults(): void {
    if (this.running()) return;
    this.runs.set([]);
    this.completed.set(false);
    this.progress.set(0);
  }

  async start(): Promise<void> {
    const c = this.selected;
    const n = Number(this.iterations);
    if (!c || this.running() || this.providers().length === 0 ||
        !Number.isInteger(n) || n < 1 || n > 20) {
      this.error.set('Select providers and between 1 and 20 iterations.');
      return;
    }
    this.error.set('');
    this.cancelled = false;
    this.running.set(true);
    this.completed.set(false);
    this.progress.set(0);
    this.runs.set([]);
    const ids = [...this.providers()];
    try {
      for (let iteration = 0; iteration < n; iteration++) {
        for (const scenario of c.scenarios) {
          if (this.cancelled) break;
          const execution = await firstValueFrom(
            this.executions.execute(c.id, scenario.input, ids, scenario.id));
          this.runs.update(previous => [...previous, execution]);
          this.progress.update(value => value + 1);
        }
        if (this.cancelled) break;
      }
      this.completed.set(true);
    } catch {
      this.error.set('The batch stopped due to an API error. Completed results are still shown.');
      this.completed.set(true);
    } finally {
      this.running.set(false);
    }
  }

  stop(): void {
    this.cancelled = true; // Cannot interrupt a request already in flight.
  }

  resultsFor(provider: ProviderId): ProviderResult[] {
    return this.runs().flatMap(run => run.results.filter(result => result.provider === provider));
  }

  rows(): Row[] {
    return this.providers().map(provider => {
      const all = this.resultsFor(provider);
      const successes = all.filter(r => r.status === 'success');
      const evaluated = successes.filter(r => r.correct != null);
      const costs = successes.filter(r => r.estimatedCostUsd != null);
      const latencies = successes.map(r => r.latencyMs);
      const totalCost = costs.length === successes.length && successes.length > 0 ?
        costs.reduce((sum, r) => sum + r.estimatedCostUsd!, 0) : null;
      return {
        provider, attempts: all.length, successes: successes.length,
        errors: all.length - successes.length,
        correct: evaluated.filter(r => r.correct === true).length,
        evaluated: evaluated.length,
        accuracy: evaluated.length ?
          100 * evaluated.filter(r => r.correct === true).length / evaluated.length : null,
        avgLatency: latencies.length ? latencies.reduce((a,b)=>a+b,0)/latencies.length : null,
        minLatency: latencies.length ? Math.min(...latencies) : null,
        maxLatency: latencies.length ? Math.max(...latencies) : null,
        totalCost,
        avgCost: totalCost == null ? null : totalCost / successes.length,
      };
    });
  }

  details(): Detail[] {
    return (this.selected?.scenarios ?? []).map(scenario => ({
      scenario,
      values: this.providers().map(provider => {
        const results = this.runs()
          .filter(run => run.scenarioId === scenario.id)
          .flatMap(run => run.results.filter(r => r.provider === provider));
        const successes = results.filter(r => r.status === 'success');
        const evaluated = successes.filter(r => r.correct != null);
        const priced = successes.filter(r => r.estimatedCostUsd != null);
        return {
          provider,
          correct: evaluated.filter(r => r.correct === true).length,
          evaluated: evaluated.length,
          failed: results.length - successes.length,
          responses: successes.map(r => typeof r.value === 'object' && r.value != null ? JSON.stringify(r.value) : String(r.value ?? '—')),
          avgLatency: successes.length ?
            successes.reduce((sum,r)=>sum+r.latencyMs,0)/successes.length : null,
          avgCost: priced.length === successes.length && successes.length > 0 ?
            priced.reduce((sum,r)=>sum+r.estimatedCostUsd!,0)/successes.length : null,
        };
      }),
    }));
  }

  ratio(metric: 'cost' | 'latency', other: ProviderId): string {
    const rows = this.rows();
    const jev = rows.find(row => row.provider === 'jev');
    const competitor = rows.find(row => row.provider === other);
    if (!jev || !competitor) return 'N/A';
    const base = metric === 'cost' ? jev.avgCost : jev.avgLatency;
    const value = metric === 'cost' ? competitor.avgCost : competitor.avgLatency;
    return base != null && value != null && base > 0 ?
      (value/base).toFixed(1) + '×' : 'N/A';
  }

  money(value: number | null): string {
    return value == null ? 'N/A' : '$' + value.toFixed(8);
  }
}
