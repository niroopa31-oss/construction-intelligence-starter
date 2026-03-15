import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PersistImportRequest, PersistImportResponse, PreviewResponse } from '../models/import-preview.model';

@Injectable({ providedIn: 'root' })
export class ImportWizardApiService {
  private readonly http = inject(HttpClient);
  private readonly coreApiBase = 'http://localhost:8080/api';

  preview(file: File, projectType?: string, projectName?: string): Observable<PreviewResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (projectType) {
      formData.append('projectType', projectType);
    }
    if (projectName) {
      formData.append('projectName', projectName);
    }
    return this.http.post<PreviewResponse>(`${this.coreApiBase}/imports/preview`, formData);
  }

  confirmImport(payload: PersistImportRequest): Observable<PersistImportResponse> {
    return this.http.post<PersistImportResponse>(`${this.coreApiBase}/imports/confirm`, payload);
  }
}