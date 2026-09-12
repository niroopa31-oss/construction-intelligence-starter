export interface ProjectSummaryResponse {
  projectId: string;
  projectName: string;
  projectType: string;
  baselineFinish?: string | null;
  forecastFinish?: string | null;
  totalTasks: number;
  completedTasks: number;
  delayedTasks: number;
  milestoneCount: number;
  highRiskCount: number;
  overallProgress: number;
}

export interface TaskTreeNode {
  id: string;
  projectId: string;
  parentId?: string | null;
  name: string;
  nodeType: string;
  phase?: string | null;
  discipline?: string | null;
  tower?: string | null;
  floorName?: string | null;
  zoneName?: string | null;
  baselineStart?: string | null;
  baselineFinish?: string | null;
  actualStart?: string | null;
  actualFinish?: string | null;
  forecastFinish?: string | null;
  progressPercent?: number | null;
  criticalFlag?: boolean;
  confidenceScore?: number | null;
  status: 'on-track' | 'delayed' | 'at-risk' | 'completed' | 'not-started';
  delayedDays: number;
  documentCount: number;
  imageCount: number;
  discrepancyCount: number;
  contractorNames: string[];
  children: TaskTreeNode[];
}

export interface TaskAssignmentDto {
  id: string;
  contractorId: string;
  companyName: string;
  contactName?: string | null;
  email?: string | null;
  roleName?: string | null;
}

export interface ContractorOptionDto {
  id: string;
  companyName: string;
  contactName?: string | null;
  email?: string | null;
  tradeType?: string | null;
}

export interface TaskMeetingDto {
  id: string;
  title: string;
  agenda?: string | null;
  startTime?: string | null;
  endTime?: string | null;
  attendees?: string | null;
  status?: string | null;
  inviteSentAt?: string | null;
  calendarEventUid?: string | null;
}

export interface TaskReminderDto {
  id: string;
  subject: string;
  body?: string | null;
  recipients?: string | null;
  scheduledAt?: string | null;
  sentAt?: string | null;
  status?: string | null;
  sendError?: string | null;
}

export interface TaskDetailResponse {
  id: string;
  projectId: string;
  parentId?: string | null;
  name: string;
  nodeType: string;
  phase?: string | null;
  discipline?: string | null;
  tower?: string | null;
  floorName?: string | null;
  zoneName?: string | null;
  baselineStart?: string | null;
  baselineFinish?: string | null;
  actualStart?: string | null;
  actualFinish?: string | null;
  forecastFinish?: string | null;
  progressPercent?: number | null;
  plannedQty?: number | null;
  actualQty?: number | null;
  uom?: string | null;
  criticalFlag?: boolean;
  confidenceScore?: number | null;
  status: 'on-track' | 'delayed' | 'at-risk' | 'completed' | 'not-started';
  delayedDays: number;
  path: string[];
  contractorNames: string[];
  documents: TaskArtifact[];
  images: TaskArtifact[];
  discrepancies: TaskDiscrepancy[];
  aiSuggestions: string[];
  contractorAssignments: TaskAssignmentDto[];
  availableContractors: ContractorOptionDto[];
  meetings: TaskMeetingDto[];
  reminders: TaskReminderDto[];
}

export interface TaskArtifact {
  id: string;
  label: string;
  type: 'document' | 'image';
  uploadedAt?: string | null;
}

export interface TaskDiscrepancy {
  id: string;
  severity: 'low' | 'medium' | 'high';
  summary: string;
  status: string;
}

export interface CreateContractorRequest {
  companyName: string;
  contactName?: string | null;
  email?: string | null;
  phone?: string | null;
  tradeType?: string | null;
}

export interface AssignContractorRequest {
  contractorId: string;
  roleName?: string | null;
}

export interface CreateMeetingRequest {
  title: string;
  agenda?: string | null;
  startTime?: string | null;
  endTime?: string | null;
  attendees?: string | null;
  status?: string | null;
  sendInviteNow?: boolean;
  inviteBody?: string | null;
}

export interface CreateReminderRequest {
  subject: string;
  body?: string | null;
  recipients?: string | null;
  scheduledAt?: string | null;
  status?: string | null;
  sendNow?: boolean;
}

export interface AiSummaryResponse {
  summary_text: string;
  metrics: {
    total_towers: number;
    total_floors: number;
    total_activities: number;
    total_milestones: number;
    delayed_count: number;
    delayed_pct: number;
    in_progress_count: number;
    upcoming_30_days: number;
    project_start: string | null;
    project_finish: string | null;
    duration_days: number | null;
  };
  risk: { level: 'low' | 'medium' | 'high'; reasons: string[] };
  phase_breakdown: Record<string, number>;
  discipline_breakdown: Record<string, number>;
  tower_stats: Array<{
    tower: string; floors: number; activities: number;
    delayed: number; avg_progress: number | null;
    planned_start: string | null; planned_finish: string | null;
  }>;
  upcoming_milestones: Array<{
    name: string; tower: string; floor: string;
    planned_finish: string | null; days_away: number | null;
  }>;
  delayed_activities: Array<{
    name: string; tower: string; floor: string;
    phase: string; planned_finish: string | null; days_overdue: number | null;
  }>;
}
