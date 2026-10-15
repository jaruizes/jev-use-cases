import { Component, DestroyRef, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { switchMap } from 'rxjs';
import { UseCase, ProviderId, Execution } from '../../core/models';
import { UseCasesApiService } from '../../services/use-cases-api.service';
import { ExecutionsApiService } from '../../services/executions-api.service';
import { ProviderResultsComponent } from './components/provider-results.component';
@Component({standalone:true,imports:[FormsModule,RouterLink,ProviderResultsComponent],
template:`<div class="eyebrow">LIVE EXPERIMENT · PLAYGROUND</div><div class="section-head"><div><h1>Compare decisions,<br><em>not assumptions.</em></h1><p class="muted">Run identical inputs through real providers and inspect their outputs.</p></div></div>@if(error()){<div class="alert">{{error()}}</div>}@if(selected();as current){<div class="work-layout"><div class="panel"><label class="field-label" for="case">01 / EXPERIMENT</label><select id="case" [ngModel]="current.id" (ngModelChange)="changeCase($event)">@for(c of cases();track c.id){<option [value]="c.id">{{c.name}}</option>}</select><p class="muted">{{current.description}}</p><label class="field-label" for="input">02 / INPUT CONTEXT</label><textarea id="input" [(ngModel)]="input" rows="9"></textarea><button class="secondary" (click)="input=current.example">↺ Reset to example</button><label class="field-label">03 / COMPARE PROVIDERS</label><div class="provider-list">@for(p of current.providers;track p){<label class="check"><input type="checkbox" [checked]="providers().includes(p)" (change)="toggle(p)"><span>{{p.toUpperCase()}}</span></label>}</div><button class="button run" [disabled]="loading() || !input.trim() || providers().length===0" (click)="execute()">{{loading()?'Running providers…':'▶ Run comparison'}}</button><p class="note">Calls use your own configured API keys. Jev and Claude may incur charges. No demo results are fabricated.</p></div><div class="panel info"><span class="eyebrow">EXPERIMENT DESIGN</span><h2>{{current.name}}</h2><p>{{current.prompt}}</p><h3>Decision contract</h3><div class="criteria">@if(current.kind==='choice'){@for(item of choiceEntries(current);track item.key){<div><strong>{{item.key}}</strong><span>{{item.value}}</span></div>}}@else if(current.kind==='score'){@for(item of scoreEntries(current);track $index){<div><strong>{{$index}}</strong><span>{{item}}</span></div>}}@else if(current.kind==='noul'){<div><strong>0…1</strong><span>Degree of support for the stated proposition</span></div>}@else{<div><strong>Markdown</strong><span>Open-ended architecture proposal with alternatives and trade-offs. Jev is not a generative LLM.</span></div>}}</div><div class="tip">This is a proof of concept. Evaluator accuracy requires an independently reviewed dataset.</div></div></div>@if(result()){<app-provider-results [execution]="result()!" />}}@else{<p>Loading use cases…</p>}`})
export class PlaygroundPage {
  private catalog=inject(UseCasesApiService); private executionApi=inject(ExecutionsApiService); private route=inject(ActivatedRoute); private destroy=inject(DestroyRef);
  cases=signal<UseCase[]>([]); selected=signal<UseCase|null>(null); providers=signal<ProviderId[]>(['jev','haiku','sonnet']); loading=signal(false); error=signal(''); result=signal<Execution|null>(null); input='';
  constructor(){
    this.catalog.list().pipe(switchMap(c=>{this.cases.set(c);return this.route.paramMap;}),takeUntilDestroyed(this.destroy)).subscribe({next:p=>this.select(p.get('id')||'model-routing'),error:()=>this.error.set('Unable to load the API catalog. Verify the backend is running.')});
  }
  select(id:string){const c=this.cases().find(x=>x.id===id)||this.cases()[0];if(!c)return;this.selected.set(c);this.input=c.example;this.providers.set(c.kind==='generation'?['haiku','sonnet']:['jev','haiku','sonnet']);this.result.set(null);this.error.set('');}
  changeCase(id:string){location.assign('/playground/'+encodeURIComponent(id));}
  toggle(p:ProviderId){this.providers.update(arr=>arr.includes(p)?arr.filter(x=>x!==p):[...arr,p]);}
  choiceEntries(c:UseCase){return Object.entries(c.criteria as Record<string,string>).map(([key,value])=>({key,value}));}
  scoreEntries(c:UseCase){return c.criteria as string[];}
  execute(){const c=this.selected();if(!c)return;this.loading.set(true);this.result.set(null);this.error.set('');this.executionApi.execute(c.id,this.input,this.providers()).subscribe({next:r=>{this.result.set(r);this.loading.set(false);},error:()=>{this.error.set('Execution failed. Check backend availability and logs.');this.loading.set(false);}});}
}
