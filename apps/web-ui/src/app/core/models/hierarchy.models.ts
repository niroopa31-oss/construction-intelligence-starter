export interface HierarchyNode {
  id: string;
  parentId?: string | null;
  name: string;
  nodeType: string;
  tower?: string | null;
  floorName?: string | null;
  phase?: string | null;
  baselineStart?: string | null;
  baselineFinish?: string | null;
  sortOrder?: number | null;
  children: HierarchyNode[];
}

export interface DraftSummary {
  draftId: string;
  projectName: string;
  projectTypeSuggested: string;
  projectTypeSelected?: string | null;
  status: string;
  nodeCount: number;
  tree: HierarchyNode[];
}

export interface UpsertHierarchyNodeRequest {
  parentId?: string | null;
  name: string;
  nodeType: string;
  tower?: string | null;
  floorName?: string | null;
  phase?: string | null;
  baselineStart?: string | null;
  baselineFinish?: string | null;
  sortOrder?: number | null;
}

export interface MoveHierarchyNodeRequest {
  newParentId?: string | null;
  newSortOrder?: number | null;
}

export interface DeleteHierarchyNodeRequest {
  cascade?: boolean;
  moveChildrenToParent?: boolean;
}

export interface ImportDraftPreviewResponse {
  filename: string;
  draftCreated: boolean;
  draftId?: string;
  reviewUrl?: string;
  draftProjectName?: string;
  draftNodeCount?: number;
  nextStep?: string;
  preview?: {
    project_name?: string;
    project_type?: string;
    task_count?: number;
    warnings?: string[];
  };
}
