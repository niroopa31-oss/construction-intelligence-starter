import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HierarchyEditorComponent } from '../../../shared/components/hierarchy-editor/hierarchy-editor.component';
import { DraftSummary, UpsertHierarchyNodeRequest } from '../../../core/models/hierarchy.models';
import { HierarchyEditorApiService } from '../../../core/services/hierarchy-editor-api.service';

@Component({
  selector: 'app-project-import-wizard',
  standalone: true,
  imports: [CommonModule, FormsModule, HierarchyEditorComponent],
  template: `
    <section class="page">
      <div class="page-header">
        <div>
          <h1>Import Project</h1>
          <p>Upload XML or Excel, review the generated hierarchy, and correct anything before saving the project.</p>
        </div>
      </div>

      <div class="toolbar">
        <label>Draft ID <input [(ngModel)]="draftId" placeholder="Paste draft id" /></label>
        <button type="button" (click)="loadDraft()">Load draft</button>
        <label>Project Type
          <select [(ngModel)]="projectTypeSelected">
            <option>high-rise residential</option>
            <option>villa project</option>
            <option>commercial building</option>
            <option>interior fit-out</option>
            <option>general construction</option>
          </select>
        </label>
        <button type="button" class="primary" [disabled]="!draft()" (click)="confirmDraft()">Create project</button>
      </div>

      <div class="status" *ngIf="message()">{{ message() }}</div>

      <app-hierarchy-editor
        *ngIf="draft() as currentDraft"
        [title]="'Hierarchy review for ' + currentDraft.projectName"
        [nodes]="currentDraft.tree"
        mode="draft"
        (addChild)="onAddDraftNode($event.parentId, $event.payload)"
        (updateNode)="onUpdateDraftNode($event.nodeId, $event.payload)"
        (moveNode)="onMoveDraftNode($event.nodeId, $event.newParentId)"
        (deleteNode)="onDeleteDraftNode($event.nodeId, $event.strategy)"
      ></app-hierarchy-editor>
    </section>
  `,
  styles: [`.page{padding:24px;display:grid;gap:16px}.page-header h1{margin:0 0 4px}.page-header p{margin:0;color:#64748b}.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:end;background:#fff;border:1px solid #e3e6eb;border-radius:16px;padding:16px}.toolbar label{display:flex;flex-direction:column;gap:6px}.toolbar input,.toolbar select{border:1px solid #d7dce3;border-radius:10px;padding:8px 10px;min-width:200px}.toolbar button{border:1px solid #d7dce3;background:#fff;border-radius:10px;padding:8px 12px;cursor:pointer}.toolbar .primary{background:#111827;color:#fff}.status{padding:12px 14px;border-radius:12px;background:#f8fafc;border:1px solid #e3e6eb}`]
})
export class ProjectImportWizardComponent {
  private readonly api = inject(HierarchyEditorApiService);
  private readonly router = inject(Router);

  draftId = '';
  projectTypeSelected = 'high-rise residential';
  readonly draft = signal<DraftSummary | null>(null);
  readonly message = signal('');

  loadDraft() {
    if (!this.draftId.trim()) {
      this.message.set('Enter a draft id from your preview/import flow.');
      return;
    }
    this.api.getDraft(this.draftId.trim()).subscribe({
      next: draft => {
        this.draft.set(draft);
        this.projectTypeSelected = draft.projectTypeSelected || draft.projectTypeSuggested || this.projectTypeSelected;
        this.message.set(`Loaded ${draft.nodeCount} nodes. Review and correct the hierarchy before saving.`);
      },
      error: () => this.message.set('Could not load the draft.')
    });
  }

  onAddDraftNode(parentId: string | null, payload: UpsertHierarchyNodeRequest) {
    if (!this.draft()) return;
    this.api.addDraftNode(this.draft()!.draftId, { ...payload, parentId }).subscribe(() => this.loadDraft());
  }

  onUpdateDraftNode(nodeId: string, payload: UpsertHierarchyNodeRequest) {
    if (!this.draft()) return;
    this.api.updateDraftNode(this.draft()!.draftId, nodeId, payload).subscribe(() => this.loadDraft());
  }

  onMoveDraftNode(nodeId: string, newParentId: string | null) {
    if (!this.draft()) return;
    this.api.moveDraftNode(this.draft()!.draftId, nodeId, { newParentId }).subscribe(() => this.loadDraft());
  }

  onDeleteDraftNode(nodeId: string, strategy: 'cascade' | 'moveChildrenToParent' | 'leafOnly') {
    if (!this.draft()) return;
    this.api.deleteDraftNode(this.draft()!.draftId, nodeId, {
      cascade: strategy === 'cascade',
      moveChildrenToParent: strategy === 'moveChildrenToParent',
    }).subscribe({
      next: () => this.loadDraft(),
      error: () => this.message.set('Delete failed. For non-leaf nodes choose delete branch or keep children.')
    });
  }

  confirmDraft() {
    if (!this.draft()) return;
    this.api.confirmDraft(this.draft()!.draftId, {
      projectName: this.draft()!.projectName,
      projectTypeSelected: this.projectTypeSelected,
      userId: '00000000-0000-0000-0000-000000000001'
    }).subscribe({
      next: projectId => this.router.navigate(['/projects', projectId]),
      error: () => this.message.set('Could not confirm draft.')
    });
  }
}
