import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Execution, ProviderId, QualitySummary, Scenario } from '../core/models';
@Injectable({ providedIn: 'root' })
export class ExecutionsApiService {
  private http = inject(HttpClient);
  execute(useCaseId: string, input: string, providers: ProviderId[], scenarioId?: string, customScenario?: Scenario) {
    return this.http.post<Execution>('/api/executions', { useCaseId, input, providers, scenarioId, customScenario });
  }
  executePlayground(useCaseId: string, input: string, providers: ProviderId[]) {
    return this.http.post<Execution>('/api/playground/executions', { useCaseId, input, providers });
  }
  quality(useCaseId: string) { return this.http.get<QualitySummary>('/api/quality/' + encodeURIComponent(useCaseId)); }
  list() { return this.http.get<Execution[]>('/api/executions'); }
  find(id: string) { return this.http.get<Execution>('/api/executions/' + encodeURIComponent(id)); }
}
