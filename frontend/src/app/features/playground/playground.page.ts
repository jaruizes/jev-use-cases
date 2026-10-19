import { Component, DestroyRef, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';
import { UseCase, ProviderId, Execution } from '../../core/models';
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
  providers = signal<ProviderId[]>(['jev', 'haiku', 'sonnet', 'laya']);
  loading = signal(false);
  error = signal('');
  result = signal<Execution | null>(null);
  input = '';
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
    this.providers.set(useCase.kind === 'generation' ? ['haiku', 'sonnet'] : ['jev', 'haiku', 'sonnet', 'laya']);
    this.result.set(null);
    this.error.set('');
  }

  changeCase(id: string): void {
    void this.router.navigate(['/playground', id]);
  }

  toggle(provider: ProviderId): void {
    this.providers.update(items =>
      items.includes(provider) ? items.filter(item => item !== provider) : [...items, provider]
    );
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
    this.executionApi.executePlayground(useCase.id, this.input, this.providers()).subscribe({
      next: execution => {
        this.result.set(execution);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Execution failed. Check backend availability and logs.');
        this.loading.set(false);
      },
    });
  }
}
