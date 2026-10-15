import { Component, Input } from '@angular/core';
import { DecimalPipe, JsonPipe } from '@angular/common';
import { Execution } from '../../../core/models';

@Component({
  selector: 'app-provider-results',
  standalone: true,
  imports: [DecimalPipe, JsonPipe],
  templateUrl: './provider-results.component.html',
})
export class ProviderResultsComponent {
  @Input({ required: true }) execution!: Execution;

  formatMoney(value: number | null | undefined): string {
    return value === null || value === undefined ? 'N/A' : ' string | number | undefined): boolean {
    return typeof value === 'string' && value.length > 120;
  }
}
 + value.toFixed(8);
  }

  costMessage(status?: string): string {
    if (status === 'rate_not_configured') return 'Jev rate not configured';
    if (status === 'unknown_model') return 'No price for this model version';
    if (status === 'missing_usage') return 'Usage not available';
    return 'Cost unavailable';
  }

  comparison(): {provider: string; cost: number; percent: number}[] | null {
    const eligible = this.execution.results.filter(
      r => r.status === 'success' && r.estimatedCostUsd !== null &&
           r.estimatedCostUsd !== undefined
    );
    if (eligible.length < 2) return null;
    const max = Math.max(...eligible.map(r => r.estimatedCostUsd!));
    return eligible.map(r => ({
      provider: r.provider, cost: r.estimatedCostUsd!,
      percent: max > 0 ? r.estimatedCostUsd! / max * 100 : 0,
    }));
  }

  isLongText(value: string | number | undefined): boolean {
    return typeof value === 'string' && value.length > 120;
  }
}
