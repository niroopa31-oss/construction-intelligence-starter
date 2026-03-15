export type NodeType = 'project' | 'stage' | 'task' | 'sub_task' | 'milestone' | 'summary' | 'unknown';

export interface CanonicalTask {
  external_id: string;
  external_parent_id?: string | null;
  source_type: string;
  source_sheet?: string | null;
  source_row?: number | null;
  name: string;
  normalized_name?: string | null;
  node_type: NodeType;
  project_hint?: string | null;
  tower?: string | null;
  block?: string | null;
  floor?: string | null;
  zone?: string | null;
  phase?: string | null;
  discipline?: string | null;
  planned_start?: string | null;
  planned_finish?: string | null;
  actual_start?: string | null;
  actual_finish?: string | null;
  actual_progress?: number | null;
  planned_qty?: number | null;
  actual_qty?: number | null;
  uom?: string | null;
  contractor?: string | null;
  remarks?: string | null;
  confidence: number;
  metadata?: Record<string, unknown>;
  children?: CanonicalTask[];
}

export interface MappingCandidate {
  logical_name: string;
  column_name?: string | null;
  confidence: number;
}

export interface SheetProfile {
  sheet_name: string;
  total_rows: number;
  detected_role: string;
  confidence: number;
  mapping: MappingCandidate[];
  warnings: string[];
}

export interface ImportPreview {
  project_name: string;
  project_type: string;
  project_type_confidence: number;
  source_type: string;
  task_count: number;
  milestone_count: number;
  hierarchy_strategy: string;
  sheets: SheetProfile[];
  flat_tasks: CanonicalTask[];
  tree: CanonicalTask[];
  warnings: string[];
}

export interface PreviewResponse {
  filename: string;
  preview: ImportPreview;
  warnings: string[];
  nextStep: string;
}

export interface PersistImportRequest {
  project: {
    userId: string;
    name: string;
    projectType: string;
    sourceType: string;
    location?: string | null;
    baselineStart?: string | null;
    baselineFinish?: string | null;
  };
  tasks: CanonicalTask[];
}

export interface PersistImportResponse {
  projectId: string;
  taskCount: number;
  message: string;
}