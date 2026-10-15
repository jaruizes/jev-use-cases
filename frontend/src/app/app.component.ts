import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
@Component({
  standalone: true, selector: 'app-root', imports: [RouterLink, RouterLinkActive, RouterOutlet],
  template: `<div class="shell"><aside class="sidebar"><a class="brand" routerLink="/"><span class="mark">J</span><span>Jev Decision Lab<small>AI DECISION ENGINEERING</small></span></a><nav><a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{exact:true}">◫ &nbsp; Overview</a><a routerLink="/playground/model-routing" routerLinkActive="active">◇ &nbsp; Playground</a><a routerLink="/test-scenarios" routerLinkActive="active">▤ &nbsp; Test Scenarios</a><a routerLink="/results" routerLinkActive="active">◷ &nbsp; History</a></nav><div class="side-footer">Structured decisions vs.<br>generative intelligence<br><small>Proof of concept · v0.1</small></div></aside><main class="main"><header class="topbar"><span>EXPERIMENT WORKSPACE</span><span class="pill">● &nbsp; Local Lab</span></header><div class="content"><router-outlet /></div></main></div>`
})
export class AppComponent {}
