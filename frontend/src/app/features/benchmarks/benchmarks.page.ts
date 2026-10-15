import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
@Component({standalone:true,imports:[RouterLink],template:`<div class="eyebrow">NEXT PHASE · BENCHMARKS</div><h1>Measure at scale.<br><em>Decide with evidence.</em></h1><div class="panel"><h2>Benchmark runner — not yet implemented</h2><p>The Playground is operational. Repeatable dataset runs, reviewed ground truth, p50/p95, provider pricing and CSV exports require the next implementation milestone. We intentionally do not show synthetic benchmark results.</p><a class="button" routerLink="/playground/model-routing">Open Playground ↗</a></div>`})
export class BenchmarksPage {}
