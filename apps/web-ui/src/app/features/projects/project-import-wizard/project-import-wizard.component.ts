import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, signal, ViewChild, ElementRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HierarchyEditorComponent } from '../../../shared/components/hierarchy-editor/hierarchy-editor.component';
import { DraftSummary, UpsertHierarchyNodeRequest, ImportDraftPreviewResponse } from '../../../core/models/hierarchy.models';
import { HierarchyEditorApiService } from '../../../core/services/hierarchy-editor-api.service';

@Component({
  selector: 'app-project-import-wizard',
  standalone: true,
  imports: [CommonModule, FormsModule, HierarchyEditorComponent],
  templateUrl: './project-import-wizard.component.html',
  styleUrls: ['./project-import-wizard.component.css'],
})
export class ProjectImportWizardComponent {
  private readonly api = inject(HierarchyEditorApiService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  draftId = '';
  projectNameOverride = '';
  projectTypeSelected = 'high-rise residential';

  readonly selectedFile = signal<File | null>(null);
  readonly uploading = signal(false);
  readonly isDragOver = signal(false);
  readonly previewResult = signal<ImportDraftPreviewResponse | null>(null);
  readonly draft = signal<DraftSummary | null>(null);
  readonly message = signal('');

  /* ─── Drag & drop ─── */
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) this.handleFileSelection(files[0]);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) this.handleFileSelection(input.files[0]);
  }

  private handleFileSelection(file: File) {
    const allowed = ['.xml', '.xlsx', '.xls', '.xlsm'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowed.includes(ext)) {
      this.message.set(`Unsupported file type "${ext}". Please upload .xlsx, .xls, .xlsm, or .xml files.`);
      return;
    }
    this.selectedFile.set(file);
    this.previewResult.set(null);
    this.message.set('');
  }

  /* ─── Upload & parse ─── */
  uploadFile() {
    const file = this.selectedFile();
    if (!file) return;
    this.uploading.set(true);
    this.message.set('');
    this.previewResult.set(null);

    this.api.uploadForDraft(file, {
      projectType: this.projectTypeSelected,
      projectName: this.projectNameOverride || undefined,
      userId: '00000000-0000-0000-0000-000000000001',
      createDraft: true,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: result => {
        this.uploading.set(false);
        this.previewResult.set(result);
        if (result.draftId) this.draftId = result.draftId;
        this.message.set('File parsed successfully! Review the result below.');
      },
      error: err => {
        this.uploading.set(false);
        this.message.set(`Upload failed: ${err.error?.detail || err.message || 'Unknown error'}`);
      },
    });
  }

  /* ─── Load draft ─── */
  loadCreatedDraft() {
    const result = this.previewResult();
    if (result?.draftId) {
      this.draftId = result.draftId;
      this.loadDraft();
    }
  }

  loadDraft() {
    if (!this.draftId.trim()) {
      this.message.set('Enter a draft id from your preview/import flow.');
      return;
    }
    this.message.set('Loading draft…');
    this.api.getDraft(this.draftId.trim()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: draft => {
        this.draft.set(draft);
        this.projectTypeSelected = draft.projectTypeSelected || draft.projectTypeSuggested || this.projectTypeSelected;
        this.message.set(`Loaded ${draft.nodeCount} nodes. Review and correct the hierarchy before saving.`);
      },
      error: () => this.message.set('Could not load the draft. Check the ID and try again.'),
    });
  }

  /* ─── Draft node operations ─── */
  onAddDraftNode(parentId: string | null, payload: UpsertHierarchyNodeRequest) {
    if (!this.draft()) return;
    this.api.addDraftNode(this.draft()!.draftId, { ...payload, parentId })
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.loadDraft());
  }

  onUpdateDraftNode(nodeId: string, payload: UpsertHierarchyNodeRequest) {
    if (!this.draft()) return;
    this.api.updateDraftNode(this.draft()!.draftId, nodeId, payload)
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.loadDraft());
  }

  onMoveDraftNode(nodeId: string, newParentId: string | null) {
    if (!this.draft()) return;
    this.api.moveDraftNode(this.draft()!.draftId, nodeId, { newParentId })
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => this.loadDraft());
  }

  onDeleteDraftNode(nodeId: string, strategy: 'cascade' | 'moveChildrenToParent' | 'leafOnly') {
    if (!this.draft()) return;
    this.api.deleteDraftNode(this.draft()!.draftId, nodeId, {
      cascade: strategy === 'cascade',
      moveChildrenToParent: strategy === 'moveChildrenToParent',
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => this.loadDraft(),
      error: () => this.message.set('Delete failed. For non-leaf nodes choose delete branch or keep children.'),
    });
  }

  /* ─── Confirm draft → real project ─── */
  confirmDraft() {
    if (!this.draft()) return;
    this.message.set('Creating project…');
    this.api.confirmDraft(this.draft()!.draftId, {
      projectName: this.draft()!.projectName,
      projectTypeSelected: this.projectTypeSelected,
      userId: '00000000-0000-0000-0000-000000000001',
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (res: any) => {
        const projectId = typeof res === 'string' ? res : res.projectId;
        this.router.navigate(['/projects', projectId]);
      },
      error: () => this.message.set('Could not confirm draft.'),
    });
  }

  /* ─── Reset ─── */
  resetWizard() {
    this.draft.set(null);
    this.previewResult.set(null);
    this.selectedFile.set(null);
    this.draftId = '';
    this.projectNameOverride = '';
    this.message.set('');
    if (this.fileInput?.nativeElement) this.fileInput.nativeElement.value = '';
  }

  /* ─── Helpers ─── */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
}
