from __future__ import annotations
import re
from collections import defaultdict
from datetime import date as date_type, datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from openpyxl import load_workbook          # ← ADD
from sklearn.metrics.pairwise import cosine_similarity

from app.models.canonical_models import (
    CanonicalTask, ImportPreview, MappingCandidate, NodeType, SheetProfile,
)
from app.services.project_type_inference import infer_project_type

# ── helpers (must be defined before use) ─────────────────────────────────────
def _t(value: Optional[str], length: int = 100) -> Optional[str]:
    return value[:length] if value else value

def _safe_float(s) -> Optional[float]:
    try: return float(s)
    except (ValueError, TypeError): return None

def _is_percent(value) -> bool:
    try: return 0 <= float(str(value).replace("%", "").strip()) <= 100
    except Exception: return False

def _date_ratio(series: pd.Series) -> float:
    count = 0
    for v in list(series):
        try:
            if isinstance(v, pd.Timestamp) and not pd.isna(v) and v.year >= 1970: count += 1
            elif isinstance(v, (datetime, date_type)) and v.year >= 1970: count += 1
            elif isinstance(v, str) and re.search(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}", v): count += 1
            elif isinstance(v, (int, float)) and 25569 <= float(v) < 2958466: count += 1
        except Exception: pass
    return count / max(len(list(series)), 1)

_DATE_STRING_PAT = re.compile(
    r"^\d{4}-\d{2}-\d{2}|^\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}"
)

def _is_date_like_value(value: Any) -> bool:
    if isinstance(value, (pd.Timestamp, datetime, date_type)):
        return True
    if isinstance(value, str) and _DATE_STRING_PAT.search(value.strip()):
        return True
    return False

def _column_is_mostly_dates(series: pd.Series) -> bool:
    non_null = [v for v in series if pd.notna(v)]
    if not non_null: return False
    return sum(1 for v in non_null[:40] if _is_date_like_value(v)) / max(len(non_null[:40]), 1) > 0.4

def _parse_date(value: Any) -> Optional[str]:
    """Convert any date-like value to ISO string."""
    if value is None or value is pd.NaT: return None
    try:
        if not isinstance(value, (pd.Timestamp, datetime, date_type)) and pd.isna(value): return None
    except (TypeError, ValueError): pass
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat() if not pd.isna(value) and 1970 <= value.year <= 2100 else None
    if isinstance(value, datetime):
        return value.date().isoformat() if 1970 <= value.year <= 2100 else None
    if isinstance(value, date_type):
        return value.isoformat() if 1970 <= value.year <= 2100 else None
    if isinstance(value, (int, float)):
        try:
            d = pd.to_datetime(float(value), unit='D', origin='1899-12-30').date()
            return d.isoformat() if 1970 <= d.year <= 2100 else None
        except Exception: return None
    if isinstance(value, str):
        for fmt in ["%d-%m-%Y","%d/%m/%Y","%Y-%m-%d","%d-%b-%Y","%d-%b-%y",
                    "%d/%m/%y","%m/%d/%Y","%d.%m.%Y","%d %b %Y","%d %B %Y","%d-%m-%y"]:
            try:
                d = datetime.strptime(value.strip(), fmt).date()
                return d.isoformat() if 1970 <= d.year <= 2100 else None
            except ValueError: pass
        try:
            d = pd.to_datetime(value.strip(), dayfirst=True).date()
            return d.isoformat() if 1970 <= d.year <= 2100 else None
        except Exception: pass
    return None

# ── constants ─────────────────────────────────────────────────────────────────
MILESTONE_HINTS = ["handover", "completion", "complete", "approval", "ready", "handing over"]
PHASE_RULES = {
    "superstructure": ["slab","column","beam","concrete","rcc","reinforcement","railing","structure","structural","shuttering","formwork","casting","pour","footing","foundation","pile","raft","retaining wall","shear wall","core wall","staircase","lift pit","basement","podium"],
    "mep":            ["electrical","plumbing","hvac","fire","duct","conduit","cable","sanitary","drainage","water supply","firefighting","sprinkler","bms","ems","lift","elevator","escalator","generator","switchgear","panel","wiring","earthing"],
    "finishing":      ["marble","tiles","tile","painting","putty","joinery","ceiling","flooring","plaster","gypsum","false ceiling","dado","granite","wood","door","window","glazing","facade","cladding","waterproofing","screed","grout","skirting","kitchen","toilet","bathroom","fixture","punning","ledge"],
    "handover":       ["handover","snag","closeout","handing over","possession","noc","completion certificate"],
    "qa_qc":          ["inspection","qa","qc","checklist","testing","commissioning","trial"],
    "civil":          ["masonry","brick","block work","backfill","excavation","earth work","soil","pest control","pest"],
}
DISCIPLINE_RULES = {
    "civil":         ["slab","column","beam","rcc","concrete","railing","masonry","structure","structural","shuttering","formwork","footing","foundation","pile","raft","staircase","excavation","backfill","earth","pest"],
    "mep":           ["electrical","plumbing","hvac","fire","conduit","cable","sanitary","drainage","water supply","firefighting","sprinkler","bms","lift","elevator","generator","panel","wiring","flush valve","switch board","ac unit","cp and sanitary"],
    "architectural": ["marble","tiles","tile","painting","joinery","ceiling","flooring","plaster","gypsum","false ceiling","dado","granite","wood","door","window","glazing","facade","cladding","kitchen","toilet","bathroom","fixture","screed","punning","ledge","railing","balcony","sit out","modular"],
}
STATUS_PROGRESS_MAP = {
    "completed": 100.0, "complete": 100.0, "done": 100.0, "finished": 100.0,
    "in progress": 50.0, "in-progress": 50.0, "ongoing": 50.0, "started": 25.0,
    "not started": 0.0, "not-started": 0.0, "pending": 0.0, "yet to start": 0.0,
}

# ── Matrix sheet detector & parser ───────────────────────────────────────────
def _is_matrix_sheet(df: pd.DataFrame) -> bool:
    """
    Detect sheets where:
    - columns 2+ are mostly dates (activities as column headers, dates as values)
    - column 0/1 are floor/serial numbers
    """
    if len(df.columns) < 4: return False
    date_col_count = sum(
        1 for c in list(df.columns)[2:]
        if _column_is_mostly_dates(df[c].dropna().head(20))
    )
    return date_col_count / max(len(df.columns) - 2, 1) > 0.5


def _normalize_activity_name(name: str) -> str:
    """Normalize activity names to consistent Title Case regardless of source casing."""
    # Strip extra whitespace
    name = re.sub(r"\s+", " ", name.strip())
    # Title case but preserve known acronyms
    ACRONYMS = {"HVAC", "RCC", "MEP", "BMS", "EMS", "NOC", "QA", "QC", "AC", "CP", "SLD", "COM"}
    words = []
    for word in name.split():
        if word.upper() in ACRONYMS:
            words.append(word.upper())
        else:
            words.append(word.capitalize())
    return " ".join(words)


def _find_floor_col_idx(headers: List[str], data_df: pd.DataFrame) -> int:
    """
    Find the floor column index robustly:
    1. Look for header name matching floor/flat/level pattern
    2. Fall back to first column whose values are mostly small integers (floor numbers)
    """
    FLOOR_PAT = re.compile(r"flat|floor|level|lvl|storey|unit", re.I)

    # Try by header name
    for i, h in enumerate(headers):
        if FLOOR_PAT.search(h):
            return i

    # Try by content: first col with mostly small integers (1-200) or unit codes (>999)
    for i, h in enumerate(headers):
        if h not in data_df.columns:
            continue
        sample = data_df[h].dropna().head(20)
        num_count = 0
        for v in sample:
            f = _safe_float(str(v))
            if f is not None and (1 <= f <= 200 or 1000 <= f <= 99999):
                num_count += 1
        if num_count / max(len(sample), 1) > 0.5:
            return i

    # Default to first column
    return 0


def _parse_matrix_sheet(
    sheet_name: str,
    raw_df: pd.DataFrame,
    color_map: Optional[Dict[Tuple[int, int], str]] = None,
) -> List[CanonicalTask]:
    print(f"  [MATRIX] Parsing '{sheet_name}' as matrix sheet")

    df = raw_df.copy()
    color_map = color_map or {}

    # Find header row
    header_row_idx = None
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        text_count = sum(1 for v in vals if isinstance(v, str) and len(v) > 2 and not _is_date_like_value(v))
        if text_count >= 3:
            header_row_idx = i
            break

    if header_row_idx is None:
        print(f"  [MATRIX] Could not find header row in '{sheet_name}'")
        return []

    print(f"  [MATRIX] header_row_idx={header_row_idx} (0-based) → excel row {header_row_idx + 1}")

    headers = [
        re.sub(r"\s+", " ", str(v).strip()) if pd.notna(v) and str(v).strip() else f"col_{j}"
        for j, v in enumerate(df.iloc[header_row_idx])
    ]
    data_df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
    data_df.columns = headers
    data_df = data_df.dropna(how="all").reset_index(drop=True)

    floor_col_idx = _find_floor_col_idx(headers, data_df)
    floor_col = headers[floor_col_idx]

    activity_cols = []
    for i, col in enumerate(headers):
        if i == floor_col_idx: continue
        if col.startswith("col_"): continue
        if col not in data_df.columns: continue
        if _column_is_mostly_dates(data_df[col].dropna().head(20)):
            activity_cols.append(col)

    tower = _extract_tower_from_sheet(sheet_name)
    tasks: List[CanonicalTask] = []
    tower_cache: Dict[str, CanonicalTask] = {}
    floor_cache: Dict[str, CanonicalTask] = {}
    stage_parent_id = f"sheet::{sheet_name}"

    if tower:
        tower_id = f"tower::{sheet_name}::{tower}"[:100]
        if tower_id not in tower_cache:
            tower_cache[tower_id] = CanonicalTask(
                external_id=tower_id,
                external_parent_id=_t(stage_parent_id),
                source_type="excel", source_sheet=_t(sheet_name),
                name=_t(tower), normalized_name=_t(tower),
                node_type=NodeType.stage, tower=_t(tower),
                confidence=0.99,
                metadata={"generated": True, "level": "tower"},
            )
            tasks.append(tower_cache[tower_id])
        tower_parent_id = tower_id
    else:
        tower_parent_id = stage_parent_id

    for idx, row in data_df.iterrows():
        raw_floor = str(row.get(floor_col, "")).strip() if floor_col else ""
        floor = _normalize_floor_value(raw_floor)
        if not floor:
            continue

        floor_id = f"floor::{sheet_name}::{tower or 'NA'}::{floor}"[:100]
        if floor_id not in floor_cache:
            floor_cache[floor_id] = CanonicalTask(
                external_id=floor_id,
                external_parent_id=_t(tower_parent_id),
                source_type="excel", source_sheet=_t(sheet_name),
                name=_t(floor), normalized_name=_t(floor),
                node_type=NodeType.task,
                tower=_t(tower), floor=_t(floor),
                confidence=0.97,
                metadata={"generated": True, "level": "floor"},
            )
            tasks.append(floor_cache[floor_id])

        for act_col in activity_cols:
            raw_date = row.get(act_col)
            planned_start = _parse_date(raw_date)
            if not planned_start:
                continue

            activity_name = _normalize_activity_name(act_col)
            phase      = _infer_phase(activity_name)
            discipline = _infer_discipline(activity_name)
            is_milestone = any(k in activity_name.lower() for k in MILESTONE_HINTS)

            # ── Color-derived status ──
            # pandas idx is 0-based from data start
            # excel row = header_row_idx (0-based) + 1 (excel is 1-based) + 1 (header row itself) + idx (data row)
            col_idx_1based   = headers.index(act_col) + 1
            excel_row_1based = header_row_idx + 2 + int(idx)   # ← FIXED offset
            cell_status   = color_map.get((excel_row_1based, col_idx_1based), "not_started")
            cell_progress = _status_to_progress(cell_status)

            # Debug first few
            if int(idx) < 3 and act_col == activity_cols[0]:
                print(f"  [COLOR] sheet={sheet_name} floor={floor} col={act_col} "
                      f"excel_row={excel_row_1based} col={col_idx_1based} → {cell_status}")

            tasks.append(CanonicalTask(
                external_id=f"row::{sheet_name}::{floor}::{_slug(activity_name)}"[:100],
                external_parent_id=_t(floor_id),
                source_type="excel", source_sheet=_t(sheet_name),
                source_row=excel_row_1based,
                name=_t(activity_name),
                normalized_name=_t(activity_name),
                node_type=NodeType.milestone if is_milestone else NodeType.sub_task,
                tower=_t(tower), floor=_t(floor),
                phase=_t(phase), discipline=_t(discipline),
                planned_start=planned_start,
                planned_finish=planned_start,
                actual_progress=cell_progress,
                status=cell_status,
                confidence=0.90,
                metadata={"sheet_name": sheet_name, "matrix": True, "color_status": cell_status},
            ))

    print(f"  [MATRIX] Generated {len(tasks)} tasks for '{sheet_name}'")
    return tasks


def _extract_tower_from_sheet(sheet_name: str) -> Optional[str]:
    s = sheet_name.strip()
    # "Tower-A", "D-Tower", "E-Tower" etc.
    m = re.search(r"(tower[-\s]?[a-z0-9]+|[a-z0-9]+[-\s]?tower|block[-\s]?[a-z0-9]+)", s, re.I)
    return m.group(0).title() if m else s


def _normalize_floor_value(raw: str) -> Optional[str]:
    if not raw or _is_date_like_value(raw): return None
    s = raw.strip()
    if re.fullmatch(r"[s\.?no\.?|sl|sr|serial].*", s, re.I): return None
    f = _safe_float(s)
    if f is not None:
        n = int(f) if f == int(f) else None
        if n is None: return None
        # Large unit codes like 4004 → extract floor portion (4004 → floor 40, flat 04)
        if n > 999:
            floor_num = n // 100
            return f"Floor {floor_num}"
        return f"Floor {n}" if -5 <= n <= 200 else None
    return s if len(s) <= 30 else None


def _safe_floor_number(raw: str) -> Optional[int]:
    f = _safe_float(raw)
    if f is None: return None
    n = int(f)
    if n > 999: return n // 100
    return n if -5 <= n <= 200 else None


def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:50]


def _infer_phase(activity: str) -> str:
    name = activity.lower()
    for phase, kws in PHASE_RULES.items():
        if any(k in name for k in kws): return phase
    return "general"


def _infer_discipline(activity: str) -> str:
    name = activity.lower()
    for disc, kws in DISCIPLINE_RULES.items():
        if any(k in name for k in kws): return disc
    return "general"


# ── Main service ──────────────────────────────────────────────────────────────
class ExcelNormalizationService:

    def parse_workbook(self, file_path: str, project_name_hint: Optional[str] = None) -> ImportPreview:
        workbook = pd.ExcelFile(file_path)
        sheet_profiles: List[SheetProfile] = []
        flat_tasks: List[CanonicalTask] = []
        warnings: List[str] = []
        project_name = project_name_hint or self._project_name_from_workbook(workbook)

        # ── Pre-pass: build color map for ALL sheets ──
        color_map_all = _build_color_map(file_path)

        SKIP_SHEETS = re.compile(r"^(sheet\d*|status|marble|summary|dashboard)$", re.I)

        for sheet_name in workbook.sheet_names:
            if SKIP_SHEETS.match(sheet_name.strip()):
                print(f"[SKIP] sheet '{sheet_name}'")
                sheet_profiles.append(SheetProfile(
                    sheet_name=sheet_name, total_rows=0,
                    detected_role="skipped", confidence=1.0,
                ))
                continue

            raw_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            if raw_df.empty:
                sheet_profiles.append(SheetProfile(
                    sheet_name=sheet_name, total_rows=0,
                    detected_role="empty", confidence=1.0,
                ))
                continue

            print(f"\n{'='*60}\n[SHEET] {sheet_name}  shape={raw_df.shape}")

            if _is_matrix_sheet(raw_df):
                rows = _parse_matrix_sheet(
                    sheet_name, raw_df,
                    color_map=color_map_all.get(sheet_name, {})   # ← pass colors
                )
                role, conf = "matrix", 0.95
            else:
                cleaned = self._clean_dataframe(raw_df)
                rows = self._parse_standard_sheet(sheet_name, cleaned)
                role, conf = "progress", 0.70

            sheet_profiles.append(SheetProfile(
                sheet_name=sheet_name,
                total_rows=len(raw_df),
                detected_role=role,
                confidence=conf,
                warnings=[],
            ))
            flat_tasks.extend(rows)

        flat_tasks = self._dedupe_tasks(flat_tasks)
        flat_tasks = self._rollup_dates(flat_tasks)
        tree = self._build_tree(flat_tasks)
        inferred = infer_project_type(project_name, flat_tasks)

        task_count = len([t for t in flat_tasks if t.node_type != NodeType.milestone])
        milestone_count = len([t for t in flat_tasks if t.node_type == NodeType.milestone])

        if not flat_tasks:
            warnings.append("No tasks extracted.")

        return ImportPreview(
            project_name=project_name,
            project_type=inferred["projectType"],
            project_type_confidence=inferred["confidence"],
            source_type="excel",
            task_count=task_count,
            milestone_count=milestone_count,
            hierarchy_strategy="sheet(tower) → floor → activity",
            sheets=sheet_profiles,
            flat_tasks=flat_tasks,
            tree=tree,
            warnings=warnings,
        )

    # ── standard (non-matrix) sheet fallback ─────────────────────────────────
    def _parse_standard_sheet(self, sheet_name: str, df: pd.DataFrame) -> List[CanonicalTask]:
        """Fallback for non-matrix sheets (labour reports etc.)"""
        tasks: List[CanonicalTask] = []
        tower = _extract_tower_from_sheet(sheet_name)

        # find likely activity column
        act_col = None
        for col in df.columns:
            series = df[col].dropna()
            str_vals = [v for v in series if isinstance(v, str) and len(v.strip()) > 4]
            if len(str_vals) >= 3 and not _column_is_mostly_dates(series.head(20)):
                act_col = col; break

        if not act_col: return tasks

        start_col = next((c for c in df.columns if _column_is_mostly_dates(df[c].dropna().head(20))), None)
        finish_col = next((c for c in df.columns
                           if c != start_col and _column_is_mostly_dates(df[c].dropna().head(20))), None)

        stage_parent_id = f"sheet::{sheet_name}"
        tower_id = f"tower::{sheet_name}::{tower}"[:100] if tower else stage_parent_id

        if tower:
            tasks.append(CanonicalTask(
                external_id=tower_id, external_parent_id=_t(stage_parent_id),
                source_type="excel", source_sheet=_t(sheet_name),
                name=_t(tower), normalized_name=_t(tower),
                node_type=NodeType.stage, tower=_t(tower), confidence=0.9,
                metadata={"generated": True, "level": "tower"},
            ))

        for idx, row in df.iterrows():
            activity = str(row.get(act_col, "")).strip()
            if not activity or _is_date_like_value(activity): continue
            if re.fullmatch(r"\d+", activity): continue

            tasks.append(CanonicalTask(
                external_id=f"row::{sheet_name}::{idx}::{_slug(activity)}"[:100],
                external_parent_id=_t(tower_id),
                source_type="excel", source_sheet=_t(sheet_name),
                name=_t(activity), normalized_name=_t(activity.title()),
                node_type=NodeType.sub_task,
                tower=_t(tower),
                phase=_t(_infer_phase(activity)),
                discipline=_t(_infer_discipline(activity)),
                planned_start=_parse_date(row.get(start_col)) if start_col else None,
                planned_finish=_parse_date(row.get(finish_col)) if finish_col else None,
                confidence=0.65,
                metadata={"sheet_name": sheet_name},
            ))
        return tasks

    # ── utilities ─────────────────────────────────────────────────────────────
    def _project_name_from_workbook(self, workbook) -> str:
        stem = getattr(workbook, "io", "Imported Project")
        if isinstance(stem, str): stem = stem.split("/")[-1].rsplit(".", 1)[0]
        return str(stem).replace("_", " ").strip() or "Imported Project"

    def _build_tree(self, tasks: List[CanonicalTask]) -> List[CanonicalTask]:
        root = CanonicalTask(
            external_id="project::root", source_type="excel",
            name="Project Root", node_type=NodeType.project, confidence=1.0,
        )
        by_id: Dict[str, CanonicalTask] = {root.external_id: root}
        cloned = [CanonicalTask(**t.model_dump(exclude={"children"})) for t in tasks]
        for t in cloned: by_id[t.external_id] = t
        for t in cloned:
            by_id.get(t.external_parent_id or root.external_id, root).children.append(t)
        return root.children

    def _dedupe_tasks(self, tasks: List[CanonicalTask]) -> List[CanonicalTask]:
        seen: Dict[str, CanonicalTask] = {}
        for t in tasks: seen[t.external_id] = t
        return list(seen.values())

    def _rollup_dates(self, tasks: List[CanonicalTask]) -> List[CanonicalTask]:
        by_id = {t.external_id: t for t in tasks}
        children_of: Dict[str, List[CanonicalTask]] = defaultdict(list)
        for t in tasks:
            if t.external_parent_id and t.external_parent_id in by_id:
                children_of[t.external_parent_id].append(t)

        def _rollup(task: CanonicalTask):
            children = children_of.get(task.external_id, [])
            for c in children: _rollup(c)
            starts   = [c.planned_start  for c in children if c.planned_start]
            finishes = [c.planned_finish for c in children if c.planned_finish]
            progs    = [c.actual_progress for c in children if c.actual_progress is not None]
            if starts   and not task.planned_start:  task.planned_start  = min(starts)
            if finishes and not task.planned_finish: task.planned_finish = max(finishes)
            if progs    and task.actual_progress is None:
                task.actual_progress = round(sum(progs) / len(progs), 2)

        roots = [t for t in tasks if not t.external_parent_id or t.external_parent_id not in by_id]
        for r in roots: _rollup(r)
        return tasks

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        return df


def get_cell_status(cell) -> tuple[str, int]:
    """Returns (status, progress_percent) based on cell background color."""
    fill = cell.fill
    if fill and fill.fgColor and fill.fgColor.type == "rgb":
        rgb = fill.fgColor.rgb.upper()
        # Green = Completed
        if any(rgb.startswith(g) for g in ["FF00B050", "FF92D050", "FF70AD47", "FF00FF00"]):
            return "completed", 100
        # Yellow = In Progress
        if any(rgb.startswith(y) for y in ["FFFFFF00", "FFFFEB9C", "FFFFC000", "FFFFEB84"]):
            return "in_progress", 50
        # Red = Overdue
        if any(rgb.startswith(r) for r in ["FFFF0000", "FFFF5050", "FFFF4040", "FFFF4B4B", "FFFF0000"]):
            return "overdue", 0
    return "not_started", 0


def _build_color_map(file_path: str) -> Dict[str, Dict[Tuple[int, int], str]]:
    """Pre-pass: extract cell background colors keyed by (row, col) per sheet."""
    wb = load_workbook(file_path, data_only=True)
    color_map: Dict[str, Dict[Tuple[int, int], str]] = {}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_colors: Dict[Tuple[int, int], str] = {}
        for row in ws.iter_rows():
            for cell in row:
                status = _rgb_to_status(cell)
                if status != "not_started":
                    sheet_colors[(cell.row, cell.column)] = status
        color_map[sheet_name] = sheet_colors

    wb.close()
    return color_map


def _rgb_to_status(cell) -> str:
    fill = cell.fill
    if not fill or not fill.fgColor:
        return "not_started"
    
    color_type = fill.fgColor.type
    rgb = ""
    
    if color_type == "rgb":
        rgb = fill.fgColor.rgb.upper()
    elif color_type == "theme":
        return "not_started"
    
    if not rgb or rgb in ("00000000", "FFFFFFFF", "FF000000"):
        return "not_started"

    # Green shades → Completed
    if any(rgb.startswith(g) for g in [
        "FF00B050", "FF92D050", "FF70AD47", "FF00FF00",
        "FF548235", "FF375623", "FFA9D18E"
    ]):
        return "completed"

    # Yellow shades → In Progress
    if any(rgb.startswith(y) for y in [
        "FFFFFF00", "FFFFEB9C", "FFFFC000", "FFFFEB84",
        "FFFFD966", "FFFFCC00", "FFFF9900", "FFFFE699"
    ]):
        return "in_progress"

    # Red shades → Overdue
    if any(rgb.startswith(r) for r in [
        "FFFF0000", "FFFF5050", "FFFF4040", "FFFF4B4B",
        "FFC00000", "FF9C0006", "FFFF6666", "FFFF0000"
    ]):
        return "overdue"

    return "not_started"


def _status_to_progress(status: str) -> float:
    return {"completed": 100.0, "in_progress": 50.0, "overdue": 0.0}.get(status, 0.0)


def parse_excel(file_path: str, project_name_hint: str | None = None) -> dict:
    wb = load_workbook(file_path, data_only=True)
    
    all_tasks = []
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        # Find header row (row 3 based on your Excel screenshot)
        header_row_idx = 3
        headers = []
        for col in range(1, ws.max_column + 1):
            val = ws.cell(row=header_row_idx, column=col).value
            headers.append(str(val).strip() if val else f"col_{col}")

        for row_idx in range(header_row_idx + 1, ws.max_row + 1):
            floor_cell = ws.cell(row=row_idx, column=1)  # PATTY/FLOORS column
            floor_val = floor_cell.value
            if not floor_val:
                continue

            task_row = {
                "floor": str(floor_val),
                "tower": sheet_name,
                "sub_tasks": []
            }

            # Each column after first = a discipline/trade
            for col_idx in range(2, len(headers) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                status, progress = get_cell_status(cell)
                date_val = cell.value

                task_row["sub_tasks"].append({
                    "name": headers[col_idx - 1],
                    "planned_start": str(date_val) if date_val else None,
                    "status": status,
                    "progress_percent": progress,
                })

            all_tasks.append(task_row)

    completed = sum(
        1 for t in all_tasks
        for s in t["sub_tasks"] if s["status"] == "completed"
    )
    in_progress = sum(
        1 for t in all_tasks
        for s in t["sub_tasks"] if s["status"] == "in_progress"
    )
    overdue = sum(
        1 for t in all_tasks
        for s in t["sub_tasks"] if s["status"] == "overdue"
    )
    total = sum(len(t["sub_tasks"]) for t in all_tasks)

    return {
        "project_name": project_name_hint or wb.active.title,
        "tasks": all_tasks,
        "summary": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
            "not_started": total - completed - in_progress - overdue,
        },
        "warnings": []
    }
