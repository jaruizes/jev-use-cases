import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface Rate {
  provider: string;
  model: string;
  inputUsdPerMillion: number;
  outputUsdPerMillion: number;
  source: string;
  updatedAt: string;
}

@Component({
  standalone: true,
  imports: [FormsModule],
  templateUrl: './pricing.page.html',
})
export class PricingPage {
  private http = inject(HttpClient);
  prices = signal<Rate[]>([]);
  loading = signal(true);
  saving = signal('');
  error = signal('');
  success = signal('');

  constructor() { this.reload(); }

  reload(): void {
    this.http.get<Rate[]>('/api/pricing').subscribe({
      next: rates => { this.prices.set(rates); this.loading.set(false); },
      error: () => { this.loading.set(false); this.error.set('Could not load pricing configuration.'); },
    });
  }

  save(rate: Rate): void {
    if (this.saving()) return;
    if (![rate.inputUsdPerMillion, rate.outputUsdPerMillion].every(value =>
      Number.isFinite(value) && value >= 0 && value <= 100000)) {
      this.error.set('Enter finite, non-negative rates (max 100,000 USD / MTok).');
      return;
    }
    this.saving.set(rate.provider);
    this.error.set('');
    this.success.set('');
    this.http.put<Rate>('/api/pricing/' + encodeURIComponent(rate.provider), {
      inputUsdPerMillion: rate.inputUsdPerMillion,
      outputUsdPerMillion: rate.outputUsdPerMillion,
    }).subscribe({
      next: saved => {
        this.prices.update(items => items.map(item => item.provider === saved.provider ? saved : item));
        this.saving.set('');
        this.success.set(saved.provider.toUpperCase() + ' pricing saved. New executions will use this rate.');
      },
      error: () => { this.saving.set(''); this.error.set('Could not save pricing. Check the backend logs.'); },
    });
  }
}
