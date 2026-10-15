import { DecimalPipe, JsonPipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Execution } from '../../../core/models';

interface CostComparison {
  provider: string;
  cost: number;
  percent: number;
}

@Component({
  selector: 'app-provider-results',
  standalone: true,
  imports: [DecimalPipe, JsonPipe],
  templateUrl: './provider-results.component.html',
})
export class ProviderResultsComponent {
  @Input({ required: true }) execution!: Execution;

  formatMoney(value: number | null | undefined): string {
    return value == null ? 'N/A' : '$' + value.toFixed(8);
  }

  costMessage(status?: string): string {
    switch (status) {
      case 'rate_not_configured':
        return 'Jev rate not configured';
      case 'unknown_model':
        return 'No price for this model version';
      case 'missing_usage':
        return 'Usage not available';
      case 'invalid_rate':
        return 'Invalid pricing configuration';
      default:
        return 'Cost unavailable';
    }
  }

  comparison(): CostComparison[] | null {
    const eligible = this.execution.results.filter(
      result => result.status === 'success' &&
        result.estimatedCostUsd != null
    );

    if (eligible.length < 2) {
      return null;
    }

    const maximum = Math.max(...eligible.map(result => result.estimatedCostUsd!));

    return eligible.map(result => ({
      provider: result.provider,
      cost: result.estimatedCostUsd!,
      percent: maximum > 0 ? (result.estimatedCostUsd! / maximum) * 100 : 0,
    }));
  }

  isLongText(value: string | number | undefined): boolean {
    return typeof value === 'string' && value.length > 120;
  }
}
