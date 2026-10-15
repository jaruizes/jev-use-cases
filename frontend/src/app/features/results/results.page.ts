import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ExecutionsApiService } from '../../services/executions-api.service';
import { Execution } from '../../core/models';
import { ProviderResultsComponent } from '../playground/components/provider-results.component';
@Component({standalone:true,imports:[DatePipe,ProviderResultsComponent],template:`<div class="eyebrow">EXPERIMENT HISTORY</div><h1>Previous <em>runs.</em></h1><p class="muted">Recent executions in backend memory. Restarting the API clears this list until persistence is implemented.</p><div class="history">@for(e of records();track e.id){<button class="history-row" (click)="select(e)"><span><strong>{{e.useCaseId}}</strong><small>{{e.timestamp | date:'medium'}}</small></span><span>{{e.results.length}} providers →</span></button>}@empty{<div class="panel">No executions yet. Run a Playground experiment first.</div>}</div>@if(active()){<app-provider-results [execution]="active()!" />}`})
export class ResultsPage {private api=inject(ExecutionsApiService); records=signal<Execution[]>([]);active=signal<Execution|null>(null);constructor(){this.api.list().subscribe({next:x=>this.records.set(x)});}select(e:Execution){this.active.set(e);}}
