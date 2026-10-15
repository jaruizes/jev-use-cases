import { Routes } from '@angular/router';
export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/dashboard/dashboard.page').then(m => m.DashboardPage) },
  { path: 'playground/:id', loadComponent: () => import('./features/playground/playground.page').then(m => m.PlaygroundPage) },
  { path: 'results', loadComponent: () => import('./features/results/results.page').then(m => m.ResultsPage) },
  { path: 'test-scenarios', loadComponent: () => import('./features/test-scenarios/test-scenarios.page').then(m => m.TestScenariosPage) },
  { path: 'benchmarks', redirectTo: 'test-scenarios' },
  { path: '**', redirectTo: '' }
];
