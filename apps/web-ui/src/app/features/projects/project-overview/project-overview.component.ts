import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HierarchyEditorComponent } from '../../../shared/components/hierarchy-editor/hierarchy-editor.component';
import { HierarchyNode, UpsertHierarchyNodeRequest } from '../../../core/models/hierarchy.models';
import { HierarchyEditorApiService } from '../../../core/services/hierarchy-editor-api.service';

@Component({
  selector: 'app-project-overview',
  standalone: true,
  imports: [CommonModule, HierarchyEditorComponent],
  template: `
    <section class="page">
      <div class="summary-grid">
        <div class="stat"><strong>{{ hierarchy().length }}</strong><span>Root Nodes</span></div>
        <div class="stat"><strong>{{ totalNodes() }}</strong><span>Total Items</span></div>
        <div class="stat"><strong>Editable</strong><span>Hierarchy</span></div>
        <div class="stat"><strong>Live</strong><span>Project Plan</span></div>
      </div>

      <app-hierarchy-editor
        [title]="'Project hierarchy editor'"
        [nodes]="hierarchy()"
        mode="project"
        (addChild)="onAddNode($event.parentId, $event.payload)"
        (updateNode)="onUpdateNode($event.nodeId, $event.payload)"
        (moveNode)="onMoveNode($event.nodeId, $event.newParentId)"
        (deleteNode)="onDeleteNode($event.nodeId, $event.strategy)"
      ></app-hierarchy-editor>
    </section>
  `,
  styles: [`.page{padding:24px;display:grid;gap:16px}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.stat{background:#fff;border:1px solid #e3e6eb;border-radius:16px;padding:16px;display:flex;flex-direction:column}.stat strong{font-size:28px}.stat span{color:#64748b}@media (max-width:900px){.summary-grid{grid-template-columns:1fr 1fr}}`]
})
export class ProjectOverviewComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(HierarchyEditorApiService);

  projectId = '';
  readonly hierarchy = signal<HierarchyNode[]>([]);

  ngOnInit(): void {
    this.projectId = this.route.snapshot.paramMap.get('id') || '';
    this.reload();
  }

  reload() {
    if (!this.projectId) return;
    this.api.getProjectHierarchy(this.projectId).subscribe(tree => this.hierarchy.set(tree));
  }

  totalNodes(): number {
    const walk = (nodes: HierarchyNode[]): number => nodes.reduce((sum, node) => sum + 1 + walk(node.children || []), 0);
    return walk(this.hierarchy());
  }

  onAddNode(parentId: string | null, payload: UpsertHierarchyNodeRequest) {
    this.api.addProjectNode(this.projectId, { ...payload, parentId }).subscribe(() => this.reload());
  }

  onUpdateNode(nodeId: string, payload: UpsertHierarchyNodeRequest) {
    this.api.updateProjectNode(this.projectId, nodeId, payload).subscribe(() => this.reload());
  }

  onMoveNode(nodeId: string, newParentId: string | null) {
    this.api.moveProjectNode(this.projectId, nodeId, { newParentId }).subscribe(() => this.reload());
  }

  onDeleteNode(nodeId: string, strategy: 'cascade' | 'moveChildrenToParent' | 'leafOnly') {
    this.api.deleteProjectNode(this.projectId, nodeId, {
      cascade: strategy === 'cascade',
      moveChildrenToParent: strategy === 'moveChildrenToParent',
    }).subscribe(() => this.reload());
  }
}
