import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Execution, ProviderId, QualitySummary } from '../core/models';
@Injectable({ providedIn: 'root' })
export class ExecutionsApiService {
  private http = inject(HttpClient);
  execute(useCaseId: string, input: string, providers: ProviderId[], scenarioId?: string) {
    return this.http.post<Execution>('/api/executions', { useCaseId, input, providers, scenarioId });
  }
  quality(useCaseId: string) { return this.http.get<QualitySummary>('/api/quality/' + encodeURIComponent(useCaseId)); }
  list() { return this.http.get<Execution[]>('/api/executions'); }
  find(id: string) { return this.http.get<Execution>('/api/executions/' + encodeURIComponent(id)); }
}
