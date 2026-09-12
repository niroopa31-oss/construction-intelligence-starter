import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProjectTaskApiService } from '../../../core/services/project-task-api.service';
import {
  AiSummaryResponse,
  ProjectSummaryResponse,
  TaskTreeNode,
  TaskDetailResponse,
} from '../../../core/models/task-tree.models';

@Component({
  selector: 'app-project-overview',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './project-overview.component.html',
  styleUrls: ['./project-overview.component.css'],
})
export class ProjectOverviewComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ProjectTaskApiService);
  private readonly destroyRef = inject(DestroyRef);

  projectId = '';
  filterText = '';

  readonly loading = signal(true);
  readonly summary = signal<ProjectSummaryResponse | null>(null);
  readonly tree = signal<TaskTreeNode[]>([]);
  readonly detail = signal<TaskDetailResponse | null>(null);
  readonly selectedTaskId = signal<string | null>(null);
  readonly expanded = signal<Record<string, boolean>>({});
  readonly saving = signal(false);

  readonly showAiSummary = signal(false);
  readonly aiLoading = signal(false);
  readonly aiSummary = signal<AiSummaryResponse | null>(null);
  readonly aiError = signal<string | null>(null);

  editingSchedule = false;
  editingProgress = false;
  editDates = { baselineStart: '', baselineFinish: '', actualStart: '', actualFinish: '', forecastFinish: '' };
  editProgress = { progressPercent: 0, plannedQty: 0, actualQty: 0, uom: '', criticalFlag: false };
  newAssignment = { contractorId: '', roleName: '' };
  newMeeting = { title: '', agenda: '', startTime: '', endTime: '', attendees: '', sendInviteNow: false, inviteBody: '' };
  newReminder = { subject: '', body: '', recipients: '', scheduledAt: '', sendNow: false };

  ngOnInit(): void {
    this.projectId = this.route.snapshot.paramMap.get('id') || '';
    this.loadAll();
  }

  /* ─── AI Summary ─── */
  openAiSummary(): void {
    this.showAiSummary.set(true);
    if (this.aiSummary()) return;
    this.aiLoading.set(true);
    this.aiError.set(null);
    this.api.getAiSummary(this.projectId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: s => { this.aiSummary.set(s); this.aiLoading.set(false); },
        error: e => { this.aiError.set(e?.error?.message ?? 'Failed to generate summary'); this.aiLoading.set(false); },
      });
  }

  closeAiSummary(): void {
    this.showAiSummary.set(false);
  }

  boldify(text: string): string {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  phaseEntries(s: AiSummaryResponse): [string, number][] {
    return Object.entries(s.phase_breakdown).sort(([, a], [, b]) => b - a);
  }

  pct(val: number, total: number): number {
    return total > 0 ? Math.round((val / total) * 100) : 0;
  }

  /* ─── Data loading ─── */
  loadAll(): void {
    this.loading.set(true);
    this.api.getProjectSummary(this.projectId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: s => this.summary.set(s),
      error: () => this.summary.set(null),
    });
    this.api.getTaskTree(this.projectId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: tree => { this.tree.set(tree); this.autoExpandRoots(tree); this.loading.set(false); },
      error: () => { this.tree.set([]); this.loading.set(false); },
    });
  }

  selectTask(taskId: string): void {
    this.selectedTaskId.set(taskId);
    this.detail.set(null);
    this.editingSchedule = false;
    this.editingProgress = false;
    this.api.getTaskDetail(this.projectId, taskId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: d => { this.detail.set(d); this.populateEditModels(d); },
      error: () => this.detail.set(null),
    });
  }

  private populateEditModels(d: TaskDetailResponse): void {
    this.editDates = {
      baselineStart: d.baselineStart || '', baselineFinish: d.baselineFinish || '',
      actualStart: d.actualStart || '', actualFinish: d.actualFinish || '',
      forecastFinish: d.forecastFinish || '',
    };
    this.editProgress = {
      progressPercent: d.progressPercent ?? 0, plannedQty: d.plannedQty ?? 0,
      actualQty: d.actualQty ?? 0, uom: d.uom || '', criticalFlag: d.criticalFlag ?? false,
    };
  }

  /* ─── Tree helpers ─── */
  toggleExpand(nodeId: string): void { this.expanded.update(v => ({ ...v, [nodeId]: !v[nodeId] })); }
  isExpanded(nodeId: string): boolean { return !!this.expanded()[nodeId]; }

  private autoExpandRoots(tree: TaskTreeNode[]): void {
    const exp: Record<string, boolean> = {};
    for (const root of tree) exp[root.id] = true;
    this.expanded.set(exp);
  }

  matchesFilter(node: TaskTreeNode): boolean {
    if (!this.filterText.trim()) return true;
    return this.nodeMatchesRecursive(node, this.filterText.trim().toLowerCase());
  }

  private nodeMatchesRecursive(node: TaskTreeNode, q: string): boolean {
    if (node.name.toLowerCase().includes(q)) return true;
    if (node.nodeType.toLowerCase().includes(q)) return true;
    return node.children.some(c => this.nodeMatchesRecursive(c, q));
  }

  /* ─── Contractors ─── */
  assignContractor(): void {
    if (!this.newAssignment.contractorId) return;
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.api.assignContractor(this.projectId, taskId, {
      contractorId: this.newAssignment.contractorId,
      roleName: this.newAssignment.roleName || undefined,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: d => { this.detail.set(d); this.newAssignment = { contractorId: '', roleName: '' }; },
    });
  }

  removeAssignment(assignmentId: string): void {
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.api.removeAssignment(this.projectId, taskId, assignmentId)
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ next: d => this.detail.set(d) });
  }

  /* ─── Meetings ─── */
  createMeeting(): void {
    if (!this.newMeeting.title.trim()) return;
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.api.createMeeting(this.projectId, taskId, {
      title: this.newMeeting.title,
      agenda: this.newMeeting.agenda || undefined,
      startTime: this.newMeeting.startTime || undefined,
      endTime: this.newMeeting.endTime || undefined,
      attendees: this.newMeeting.attendees || undefined,
      sendInviteNow: this.newMeeting.sendInviteNow,
      inviteBody: this.newMeeting.inviteBody || undefined,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: d => {
        this.detail.set(d);
        this.newMeeting = { title: '', agenda: '', startTime: '', endTime: '', attendees: '', sendInviteNow: false, inviteBody: '' };
      },
    });
  }

  sendInvite(meetingId: string): void {
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.api.sendMeetingInvite(this.projectId, taskId, meetingId)
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ next: d => this.detail.set(d) });
  }

  /* ─── Reminders ─── */
  createReminder(): void {
    if (!this.newReminder.subject.trim()) return;
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.api.createReminder(this.projectId, taskId, {
      subject: this.newReminder.subject,
      body: this.newReminder.body || undefined,
      recipients: this.newReminder.recipients || undefined,
      scheduledAt: this.newReminder.scheduledAt || undefined,
      sendNow: this.newReminder.sendNow,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: d => {
        this.detail.set(d);
        this.newReminder = { subject: '', body: '', recipients: '', scheduledAt: '', sendNow: false };
      },
    });
  }

  sendReminder(reminderId: string): void {
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.api.sendReminder(this.projectId, taskId, reminderId)
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ next: d => this.detail.set(d) });
  }

  /* ─── Save schedule / progress ─── */
  saveSchedule(): void {
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.saving.set(true);
    this.api.updateTask(this.projectId, taskId, {
      baselineStart: this.editDates.baselineStart || null,
      baselineFinish: this.editDates.baselineFinish || null,
      actualStart: this.editDates.actualStart || null,
      actualFinish: this.editDates.actualFinish || null,
      forecastFinish: this.editDates.forecastFinish || null,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: d => { this.detail.set(d); this.populateEditModels(d); this.editingSchedule = false; this.saving.set(false); this.refreshTree(); },
      error: () => this.saving.set(false),
    });
  }

  saveProgress(): void {
    const taskId = this.selectedTaskId(); if (!taskId) return;
    this.saving.set(true);
    this.api.updateTask(this.projectId, taskId, {
      progressPercent: this.editProgress.progressPercent,
      plannedQty: this.editProgress.plannedQty || null,
      actualQty: this.editProgress.actualQty || null,
      uom: this.editProgress.uom || null,
      criticalFlag: this.editProgress.criticalFlag,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: d => { this.detail.set(d); this.populateEditModels(d); this.editingProgress = false; this.saving.set(false); this.refreshTree(); },
      error: () => this.saving.set(false),
    });
  }

  private refreshTree(): void {
    this.api.getTaskTree(this.projectId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ next: t => this.tree.set(t) });
    this.api.getProjectSummary(this.projectId).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({ next: s => this.summary.set(s) });
  }
}
