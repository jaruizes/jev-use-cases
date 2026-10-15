import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { UseCasesApiService } from '../../services/use-cases-api.service';
import { UseCase } from '../../core/models';
@Component({standalone: true, imports:[RouterLink],
template:`<section class="hero"><div class="eyebrow">THE DECISION INTELLIGENCE LAB</div><h1>Right model.<br><em>Right decision.</em></h1><p>Explore where Jev excels at structured decisions, where deterministic rules are enough, and when only a generative LLM can solve the problem.</p><a class="button" routerLink="/playground/model-routing">Launch Playground <span>↗</span></a></section><div class="section-head"><div><span class="eyebrow">EXPLORE THE LAB</span><h2>Four experiments. One clear answer.</h2></div><span class="muted">INTERACTIVE USE CASES</span></div><div class="case-grid">@for(c of cases(); track c.id; let i=$index){<a class="case-card" [routerLink]="['/playground',c.id]"><div class="card-top"><span class="case-number">0{{i+1}}</span><span class="tag">{{c.kind.toUpperCase()}}</span></div><h3>{{c.name}}</h3><p>{{c.description}}</p><span class="explore">Explore experiment ↗</span></a>}</div><section class="principle"><span class="eyebrow">THE CORE PRINCIPLE</span><div class="principles"><div><strong>01 — RULES</strong><p>Exact conditions, predictable output.</p></div><div><strong>02 — JEV</strong><p>Contextual, bounded decisions.</p></div><div><strong>03 — LLM</strong><p>Open-ended reasoning and generation.</p></div></div></section>`})
export class DashboardPage { private api=inject(UseCasesApiService); cases=signal<UseCase[]>([]);
constructor(){this.api.list().subscribe({next:x=>this.cases.set(x)});}
}
