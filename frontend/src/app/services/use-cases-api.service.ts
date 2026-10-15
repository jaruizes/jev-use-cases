import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { UseCase } from '../core/models';
@Injectable({ providedIn: 'root' })
export class UseCasesApiService {
  private http = inject(HttpClient);
  list() { return this.http.get<UseCase[]>('/api/use-cases'); }
}
