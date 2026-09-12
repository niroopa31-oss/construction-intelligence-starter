import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HierarchyNode, UpsertHierarchyNodeRequest } from '../../../core/models/hierarchy.models';

@Component({
  selector: 'app-hierarchy-editor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './hierarchy-editor.component.html',
  styleUrl: './hierarchy-editor.component.css'
})
export class HierarchyEditorComponent implements OnChanges {
  @Input() nodes: HierarchyNode[] = [];
  @Input() title = 'Hierarchy Review';
  @Input() mode: 'draft' | 'project' = 'draft';

  @Output() addChild = new EventEmitter<{ parentId: string | null; payload: UpsertHierarchyNodeRequest }>();
  @Output() updateNode = new EventEmitter<{ nodeId: string; payload: UpsertHierarchyNodeRequest }>();
  @Output() moveNode = new EventEmitter<{ nodeId: string; newParentId: string | null }>();
  @Output() deleteNode = new EventEmitter<{ nodeId: string; strategy: 'cascade' | 'moveChildrenToParent' | 'leafOnly' }>();

  readonly expanded = signal<Record<string, boolean>>({});
  readonly selectedId = signal<string | null>(null);
  readonly newNodeParentId = signal<string | null>(null);
  readonly newNode = signal<UpsertHierarchyNodeRequest>({ name: '', nodeType: 'task' });
  readonly editModel = signal<Record<string, UpsertHierarchyNodeRequest>>({});

  /** Cached signal – updated only when @Input() nodes changes, not on every CD cycle */
  private readonly nodesRef = signal<HierarchyNode[]>([]);
  readonly flatNodes = computed(() => this.flattenInternal(this.nodesRef()));

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['nodes']) {
      this.nodesRef.set(this.nodes);
    }
  }

  toggle(nodeId: string) {
    this.expanded.update(v => ({ ...v, [nodeId]: !v[nodeId] }));
  }

  isExpanded(nodeId: string) {
    return !!this.expanded()[nodeId];
  }

  selectNode(node: HierarchyNode) {
    this.selectedId.set(node.id);
    this.editModel.update(current => ({
      ...current,
      [node.id]: {
        parentId: node.parentId ?? null,
        name: node.name,
        nodeType: node.nodeType,
        tower: node.tower ?? null,
        floorName: node.floorName ?? null,
        phase: node.phase ?? null,
        baselineStart: node.baselineStart ?? null,
        baselineFinish: node.baselineFinish ?? null,
        sortOrder: node.sortOrder ?? null,
      }
    }));
  }

  openAddChild(parentId: string | null) {
    this.newNodeParentId.set(parentId);
    this.newNode.set({ parentId, name: '', nodeType: 'task' });
  }

  submitNewNode() {
    const payload = this.newNode();
    if (!payload.name?.trim()) return;
    this.addChild.emit({ parentId: this.newNodeParentId(), payload: { ...payload, parentId: this.newNodeParentId() } });
    this.newNode.set({ name: '', nodeType: 'task' });
  }

  saveSelected() {
    const id = this.selectedId();
    if (!id) return;
    const payload = this.editModel()[id];
    if (!payload?.name?.trim()) return;
    this.updateNode.emit({ nodeId: id, payload });
  }

  requestMove(nodeId: string, parentId: string | null) {
    this.moveNode.emit({ nodeId, newParentId: parentId });
  }

  requestDelete(nodeId: string, strategy: 'cascade' | 'moveChildrenToParent' | 'leafOnly') {
    this.deleteNode.emit({ nodeId, strategy });
  }

  /** Used internally by the cached computed signal – not called from template */
  private flattenInternal(nodes: HierarchyNode[], acc: HierarchyNode[] = []): HierarchyNode[] {
    for (const node of nodes) {
      acc.push(node);
      if (node.children?.length) {
        this.flattenInternal(node.children, acc);
      }
    }
    return acc;
  }
}
