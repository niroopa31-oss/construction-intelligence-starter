from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    project = "project"
    stage = "stage"
    task = "task"
    sub_task = "sub_task"
    milestone = "milestone"
    summary = "summary"
    unknown = "unknown"


class CanonicalTask(BaseModel):
    external_id: str
    external_parent_id: Optional[str] = None
    source_type: str
    source_sheet: Optional[str] = None
    source_row: Optional[int] = None
    name: str
    normalized_name: Optional[str] = None
    node_type: NodeType = NodeType.sub_task
    project_hint: Optional[str] = None
    tower: Optional[str] = None
    block: Optional[str] = None
    floor: Optional[str] = None
    zone: Optional[str] = None
    phase: Optional[str] = None
    discipline: Optional[str] = None
    planned_start: Optional[str] = None
    planned_finish: Optional[str] = None
    actual_start: Optional[str] = None
    actual_finish: Optional[str] = None
    actual_progress: Optional[float] = None
    planned_qty: Optional[float] = None
    actual_qty: Optional[float] = None
    uom: Optional[str] = None
    contractor: Optional[str] = None
    remarks: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    children: List["CanonicalTask"] = Field(default_factory=list)


CanonicalTask.model_rebuild()


class MappingCandidate(BaseModel):
    logical_name: str
    column_name: Optional[str] = None
    confidence: float = 0.0


class SheetProfile(BaseModel):
    sheet_name: str
    total_rows: int
    detected_role: str
    confidence: float
    mapping: List[MappingCandidate] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ImportPreview(BaseModel):
    project_name: str
    project_type: str = "general construction"
    project_type_confidence: float = 0.0
    source_type: str
    task_count: int
    milestone_count: int
    hierarchy_strategy: str
    sheets: List[SheetProfile] = Field(default_factory=list)
    flat_tasks: List[CanonicalTask] = Field(default_factory=list)
    tree: List[CanonicalTask] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
