import { Routes } from '@angular/router';
export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/dashboard/dashboard.page').then(m => m.DashboardPage) },
  { path: 'playground/:id', loadComponent: () => import('./features/playground/playground.page').then(m => m.PlaygroundPage) },
  { path: 'results', loadComponent: () => import('./features/results/results.page').then(m => m.ResultsPage) },
  { path: 'benchmarks', loadComponent: () => import('./features/benchmarks/benchmarks.page').then(m => m.BenchmarksPage) },
  { path: '**', redirectTo: '' }
];
