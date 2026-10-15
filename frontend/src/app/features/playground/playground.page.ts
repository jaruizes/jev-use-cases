import { Component, DestroyRef, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';
import { UseCase, ProviderId, Execution, Scenario, QualitySummary } from '../../core/models';
import { UseCasesApiService } from '../../services/use-cases-api.service';
import { ExecutionsApiService } from '../../services/executions-api.service';
import { ProviderResultsComponent } from './components/provider-results.component';

@Component({
  standalone: true,
  imports: [FormsModule, ProviderResultsComponent],
  templateUrl: './playground.page.html',
})
export class PlaygroundPage {
  private catalog = inject(UseCasesApiService);
  private executionApi = inject(ExecutionsApiService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroy = inject(DestroyRef);

  cases = signal<UseCase[]>([]);
  selected = signal<UseCase | null>(null);
  providers = signal<ProviderId[]>(['jev', 'haiku', 'sonnet']);
  loading = signal(false);
  error = signal('');
  result = signal<Execution | null>(null);
  input = '';
  selectedScenarioId = '';
  quality = signal<QualitySummary | null>(null);
  runningAll = signal(false);
  batchProgress = signal(0);

  constructor() {
    this.catalog.list()
      .pipe(
        switchMap(cases => {
          this.cases.set(cases);
          return this.route.paramMap;
        }),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe({
        next: params => this.select(params.get('id') || 'model-routing'),
        error: () => this.error.set('Unable to load the API catalog. Verify the backend is running.'),
      });
  }

  select(id: string): void {
    const useCase = this.cases().find(item => item.id === id) || this.cases()[0];
    if (!useCase) return;
    this.selected.set(useCase);
    this.input = useCase.example;
    this.selectedScenarioId = '';
    this.quality.set(null);
    this.refreshQuality(useCase.id);
    this.providers.set(useCase.kind === 'generation' ? ['haiku', 'sonnet'] : ['jev', 'haiku', 'sonnet']);
    this.result.set(null);
    this.error.set('');
  }

  changeCase(id: string): void {
    void this.router.navigate(['/playground', id]);
  }

  useScenario(id: string): void {
    const chosen = this.selected()?.scenarios.find(s => s.id === id);
    if (!chosen) return;
    this.selectedScenarioId = id;
    this.input = chosen.input;
    this.result.set(null);
  }

  editInput(text: string): void {
    this.input = text;
    if (this.selected()?.scenarios.find(s => s.id === this.selectedScenarioId)?.input !== text) {
      this.selectedScenarioId = '';
    }
  }

  refreshQuality(useCaseId: string): void {
    this.executionApi.quality(useCaseId).subscribe({next: value => {
      if (this.selected()?.id === useCaseId) this.quality.set(value);
    }});
  }

  async runAllScenarios(): Promise<void> {
    const useCase = this.selected();
    if (!useCase || this.loading() || !this.providers().length) return;
    const providers = [...this.providers()];
    this.loading.set(true);
    this.runningAll.set(true);
    this.batchProgress.set(0);
    this.error.set('');
    try {
      for (const [index, scenario] of useCase.scenarios.entries()) {
        const execution = await import('rxjs').then(({firstValueFrom}) =>
          firstValueFrom(this.executionApi.execute(useCase.id, scenario.input, providers, scenario.id)));
        this.batchProgress.set(index + 1);
        this.selectedScenarioId = scenario.id;
        this.input = scenario.input;
        this.result.set(execution);
        this.refreshQuality(useCase.id);
      }
    } catch {
      this.error.set('A scenario failed. Inspect backend logs and retry.');
    } finally {
      this.loading.set(false);
      this.runningAll.set(false);
      this.refreshQuality(useCase.id);
    }
  }

  toggle(provider: ProviderId): void {
    this.providers.update(items =>
      items.includes(provider) ? items.filter(item => item !== provider) : [...items, provider]
    );
  }

  expectedLabel(useCase: UseCase): string {
    const scenario = useCase.scenarios.find(s => s.id === this.selectedScenarioId);
    return scenario?.expected == null ? 'Qualitative review (no automatic accuracy)' : String(scenario.expected);
  }

  choiceEntries(useCase: UseCase): { key: string; value: string }[] {
    return Object.entries(useCase.criteria as Record<string, string>)
      .map(([key, value]) => ({ key, value }));
  }

  scoreEntries(useCase: UseCase): string[] {
    return useCase.criteria as string[];
  }

  execute(): void {
    const useCase = this.selected();
    if (!useCase || !this.input.trim() || !this.providers().length || this.loading()) return;
    this.loading.set(true);
    this.result.set(null);
    this.error.set('');
    this.executionApi.execute(useCase.id, this.input, this.providers(), this.selectedScenarioId || undefined).subscribe({
      next: execution => {
        this.result.set(execution);
        this.refreshQuality(useCase.id);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Execution failed. Check backend availability and logs.');
        this.loading.set(false);
      },
    });
  }
}
