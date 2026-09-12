import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  AssignContractorRequest,
  CreateContractorRequest,
  CreateMeetingRequest,
  CreateReminderRequest,
  ProjectSummaryResponse,
  TaskDetailResponse,
  TaskTreeNode,
  AiSummaryResponse
} from '../models/task-tree.models';

@Injectable({ providedIn: 'root' })
export class ProjectTaskApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/projects';

  getProjectSummary(projectId: string): Observable<ProjectSummaryResponse> {
    return this.http.get<ProjectSummaryResponse>(`${this.baseUrl}/${projectId}/summary`);
  }

  getTaskTree(projectId: string): Observable<TaskTreeNode[]> {
    return this.http.get<TaskTreeNode[]>(`${this.baseUrl}/${projectId}/tasks/tree`);
  }

  getTaskDetail(projectId: string, taskId: string): Observable<TaskDetailResponse> {
    return this.http.get<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/detail`);
  }

  createContractor(projectId: string, payload: CreateContractorRequest): Observable<any> {
    return this.http.post(`${this.baseUrl}/${projectId}/contractors`, payload);
  }

  assignContractor(projectId: string, taskId: string, payload: AssignContractorRequest): Observable<TaskDetailResponse> {
    return this.http.post<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/collaboration/assignments`, payload);
  }

  removeAssignment(projectId: string, taskId: string, assignmentId: string): Observable<TaskDetailResponse> {
    return this.http.delete<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/collaboration/assignments/${assignmentId}`);
  }

  createMeeting(projectId: string, taskId: string, payload: CreateMeetingRequest): Observable<TaskDetailResponse> {
    return this.http.post<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/collaboration/meetings`, payload);
  }

  sendMeetingInvite(projectId: string, taskId: string, meetingId: string, inviteBody?: string | null): Observable<TaskDetailResponse> {
    return this.http.post<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/collaboration/meetings/${meetingId}/send-invite`, { inviteBody });
  }

  createReminder(projectId: string, taskId: string, payload: CreateReminderRequest): Observable<TaskDetailResponse> {
    return this.http.post<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/collaboration/reminders`, payload);
  }

  sendReminder(projectId: string, taskId: string, reminderId: string): Observable<TaskDetailResponse> {
    return this.http.post<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}/collaboration/reminders/${reminderId}/send`, {});
  }

  updateTask(projectId: string, taskId: string, updates: Record<string, unknown>): Observable<TaskDetailResponse> {
    return this.http.patch<TaskDetailResponse>(`${this.baseUrl}/${projectId}/tasks/${taskId}`, updates);
  }

  getAiSummary(projectId: string): Observable<any> {
    return this.http.get(`/api/projects/${projectId}/ai-summary`);
  }
}
