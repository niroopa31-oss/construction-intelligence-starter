import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  DraftSummary,
  HierarchyNode,
  UpsertHierarchyNodeRequest,
  MoveHierarchyNodeRequest,
  DeleteHierarchyNodeRequest,
  ImportDraftPreviewResponse
} from '../models/hierarchy.models';

@Injectable({ providedIn: 'root' })
export class HierarchyEditorApiService {
  private readonly http = inject(HttpClient);

  uploadForDraft(file: File, payload: { projectType?: string; projectName?: string; userId?: string; createDraft?: boolean } = {}) {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (payload.projectType) params.set('projectType', payload.projectType);
    if (payload.projectName) params.set('projectName', payload.projectName);
    if (payload.userId) params.set('userId', payload.userId);
    params.set('createDraft', String(payload.createDraft ?? true));

    const query = params.toString();
    return this.http.post<ImportDraftPreviewResponse>(`/api/imports/preview${query ? `?${query}` : ''}`, formData);
  }

  getDraft(draftId: string) {
    return this.http.get<DraftSummary>(`/api/import-drafts/${draftId}`);
  }

  addDraftNode(draftId: string, payload: UpsertHierarchyNodeRequest) {
    return this.http.post<HierarchyNode>(`/api/import-drafts/${draftId}/nodes`, payload);
  }

  updateDraftNode(draftId: string, nodeId: string, payload: UpsertHierarchyNodeRequest) {
    return this.http.patch<HierarchyNode>(`/api/import-drafts/${draftId}/nodes/${nodeId}`, payload);
  }

  moveDraftNode(draftId: string, nodeId: string, payload: MoveHierarchyNodeRequest) {
    return this.http.post<void>(`/api/import-drafts/${draftId}/nodes/${nodeId}/move`, payload);
  }

  deleteDraftNode(draftId: string, nodeId: string, payload: DeleteHierarchyNodeRequest) {
    return this.http.request<void>('delete', `/api/import-drafts/${draftId}/nodes/${nodeId}`, { body: payload });
  }

  confirmDraft(draftId: string, payload: { projectName: string; projectTypeSelected: string; userId: string; }) {
    return this.http.post<{ projectId: string; projectName: string; taskCount: number }>(`/api/import-drafts/${draftId}/confirm`, payload);
  }

  getProjectHierarchy(projectId: string) {
    return this.http.get<HierarchyNode[]>(`/api/projects/${projectId}/hierarchy`);
  }

  addProjectNode(projectId: string, payload: UpsertHierarchyNodeRequest) {
    return this.http.post<HierarchyNode>(`/api/projects/${projectId}/hierarchy/nodes`, payload);
  }

  updateProjectNode(projectId: string, nodeId: string, payload: UpsertHierarchyNodeRequest) {
    return this.http.patch<HierarchyNode>(`/api/projects/${projectId}/hierarchy/nodes/${nodeId}`, payload);
  }

  moveProjectNode(projectId: string, nodeId: string, payload: MoveHierarchyNodeRequest) {
    return this.http.post<void>(`/api/projects/${projectId}/hierarchy/nodes/${nodeId}/move`, payload);
  }

  deleteProjectNode(projectId: string, nodeId: string, payload: DeleteHierarchyNodeRequest) {
    return this.http.request<void>('delete', `/api/projects/${projectId}/hierarchy/nodes/${nodeId}`, { body: payload });
  }
}
