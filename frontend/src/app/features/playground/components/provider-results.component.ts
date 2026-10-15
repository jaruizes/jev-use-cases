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

  isLongText(value: string | number | undefined): boolean {
    return typeof value === 'string' && value.length > 120;
  }
}
