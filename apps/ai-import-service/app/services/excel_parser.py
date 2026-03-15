from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from app.models.canonical_models import (
    CanonicalTask,
    ImportPreview,
    MappingCandidate,
    NodeType,
    SheetProfile,
)
from app.services.project_type_inference import infer_project_type

DATE_CANDIDATES = ["date", "start date", "end date", "planned start", "planned finish", "finish", "end", "target date"]
PROGRESS_CANDIDATES = ["progress", "% progress", "actual progress", "ach %", "completion", "% complete", "status"]
ACTIVITY_CANDIDATES = [
    "activity", "task", "work", "description", "item", "activity name",
    "particulars", "scope", "scope of work", "work description",
    "activity description", "component", "element", "subject",
    "boq item", "detail", "details", "name of activity",
    "name of work", "nature of work", "trade", "schedule item",
]
FLOOR_CANDIDATES = ["floor", "flats/floor", "flat", "level", "lvl", "storey", "story"]
TOWER_CANDIDATES = ["tower", "block", "wing", "building", "bldg"]
START_CANDIDATES = ["start", "start date", "planned start", "baseline start", "commence", "commencement"]
FINISH_CANDIDATES = ["finish", "end", "planned finish", "baseline finish", "date", "target date", "completion date", "end date"]
CONTRACTOR_CANDIDATES = ["contractor", "agency", "vendor", "subcontractor", "sub contractor"]
REMARKS_CANDIDATES = ["remarks", "remark", "comments", "status remarks", "note", "observation"]
QTY_CANDIDATES = ["qty", "quantity", "planned qty", "balance qty", "actual qty", "total qty"]
UOM_CANDIDATES = ["uom", "unit", "units"]

MILESTONE_HINTS = ["handover", "completion", "complete", "approval", "ready", "casting"]
PHASE_RULES = {
    "superstructure": ["slab", "column", "beam", "concrete", "rcc", "reinforcement", "railing"],
    "mep": ["electrical", "plumbing", "hvac", "fire", "duct", "conduit", "cable"],
    "finishing": ["marble", "tiles", "painting", "putty", "joinery", "ceiling", "flooring"],
    "handover": ["handover", "snag", "closeout"],
    "qa_qc": ["inspection", "qa", "qc", "checklist"],
}
DISCIPLINE_RULES = {
    "civil": ["slab", "column", "beam", "rcc", "concrete", "railing", "masonry"],
    "mep": ["electrical", "plumbing", "hvac", "fire", "conduit", "cable"],
    "architectural": ["marble", "tiles", "painting", "joinery", "ceiling", "flooring"],
}


class ExcelNormalizationService:
    def parse_workbook(self, file_path: str, project_name_hint: Optional[str] = None) -> ImportPreview:
        workbook = pd.ExcelFile(file_path)
        sheet_profiles: List[SheetProfile] = []
        flat_tasks: List[CanonicalTask] = []
        warnings: List[str] = []
        project_name = project_name_hint or self._project_name_from_workbook(workbook)

        for sheet_name in workbook.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if df.empty:
                sheet_profiles.append(
                    SheetProfile(sheet_name=sheet_name, total_rows=0, detected_role="empty", confidence=1.0)
                )
                continue

            cleaned = self._clean_dataframe(df)
            profile, rows = self._parse_sheet(sheet_name, cleaned)
            sheet_profiles.append(profile)
            flat_tasks.extend(rows)

        flat_tasks = self._dedupe_tasks(flat_tasks)
        milestone_tasks = self._generate_milestones(flat_tasks)
        flat_tasks.extend(milestone_tasks)
        flat_tasks = self._dedupe_tasks(flat_tasks)
        tree = self._build_tree(flat_tasks)

        inferred = infer_project_type(project_name, flat_tasks)
        warnings.extend(self._global_warnings(sheet_profiles, flat_tasks))

        return ImportPreview(
            project_name=project_name,
            project_type=inferred["projectType"],
            project_type_confidence=inferred["confidence"],
            source_type="excel",
            task_count=len([t for t in flat_tasks if t.node_type != NodeType.milestone]),
            milestone_count=len([t for t in flat_tasks if t.node_type == NodeType.milestone]),
            hierarchy_strategy="sheet -> tower/block -> floor -> activity",
            sheets=sheet_profiles,
            flat_tasks=flat_tasks,
            tree=tree,
            warnings=warnings,
        )

    def _parse_sheet(self, sheet_name: str, df: pd.DataFrame) -> Tuple[SheetProfile, List[CanonicalTask]]:
        cols = {self._normalize_column_name(c): c for c in df.columns}
        tower_default = self._tower_from_sheet(sheet_name)

        # ── Pass 1: header-name matching ──
        mapping = {
            "tower": self._pick(cols, TOWER_CANDIDATES),
            "floor": self._pick(cols, FLOOR_CANDIDATES),
            "activity": self._pick(cols, ACTIVITY_CANDIDATES),
            "planned_start": self._pick(cols, START_CANDIDATES),
            "planned_finish": self._pick(cols, FINISH_CANDIDATES),
            "progress": self._pick(cols, PROGRESS_CANDIDATES),
            "contractor": self._pick(cols, CONTRACTOR_CANDIDATES),
            "remarks": self._pick(cols, REMARKS_CANDIDATES),
            "qty": self._pick(cols, QTY_CANDIDATES),
            "uom": self._pick(cols, UOM_CANDIDATES),
        }

        # ── Pass 2: content-based intelligent detection for missing columns ──
        used_cols = {v for v in mapping.values() if v is not None}
        mapping, content_warnings = self._infer_columns_from_content(df, mapping, used_cols)

        role, role_confidence = self._detect_sheet_role(sheet_name, cols)
        warnings: List[str] = list(content_warnings)

        # Fallback: if still no activity column, pick the best text-heavy column
        if not mapping["activity"] and role != "labour":
            best_col = self._guess_activity_column(df, exclude=used_cols)
            if best_col:
                mapping["activity"] = best_col
                warnings.append(f"No standard activity column detected; using '{best_col}' as best guess.")
            else:
                warnings.append("No activity/task column detected; sheet skipped.")
                profile = SheetProfile(
                    sheet_name=sheet_name,
                    total_rows=len(df.index),
                    detected_role=role,
                    confidence=role_confidence,
                    mapping=[MappingCandidate(logical_name=k, column_name=v, confidence=1.0 if v else 0.0) for k, v in mapping.items()],
                    warnings=warnings,
                )
                return profile, []

        tasks: List[CanonicalTask] = []
        tower_cache: Dict[str, CanonicalTask] = {}
        floor_cache: Dict[str, CanonicalTask] = {}

        for idx, row in df.iterrows():
            activity = self._clean(row.get(mapping["activity"])) if mapping["activity"] else None
            if not activity:
                continue

            tower = self._clean(row.get(mapping["tower"])) if mapping["tower"] else tower_default
            floor = self._normalize_floor(self._clean(row.get(mapping["floor"]))) if mapping["floor"] else None
            planned_start = self._dateish(row.get(mapping["planned_start"])) if mapping["planned_start"] else None
            planned_finish = self._dateish(row.get(mapping["planned_finish"])) if mapping["planned_finish"] else None
            progress = self._progressish(row.get(mapping["progress"])) if mapping["progress"] else None
            contractor = self._clean(row.get(mapping["contractor"])) if mapping["contractor"] else None
            remarks = self._clean(row.get(mapping["remarks"])) if mapping["remarks"] else None
            qty = self._floatish(row.get(mapping["qty"])) if mapping["qty"] else None
            uom = self._clean(row.get(mapping["uom"])) if mapping["uom"] else None

            stage_parent_id = f"sheet::{sheet_name}"
            if tower:
                tower_id = f"tower::{sheet_name}::{tower}"
                if tower_id not in tower_cache:
                    tower_cache[tower_id] = CanonicalTask(
                        external_id=tower_id,
                        external_parent_id=stage_parent_id,
                        source_type="excel",
                        source_sheet=sheet_name,
                        name=tower,
                        normalized_name=tower,
                        node_type=NodeType.stage,
                        tower=tower,
                        confidence=0.98,
                        metadata={"generated": True, "level": "tower"},
                    )
                    tasks.append(tower_cache[tower_id])
                parent_id = tower_id
            else:
                parent_id = stage_parent_id

            if floor:
                floor_id = f"floor::{sheet_name}::{tower or 'NA'}::{floor}"
                if floor_id not in floor_cache:
                    floor_cache[floor_id] = CanonicalTask(
                        external_id=floor_id,
                        external_parent_id=parent_id,
                        source_type="excel",
                        source_sheet=sheet_name,
                        name=floor,
                        normalized_name=floor,
                        node_type=NodeType.task,
                        tower=tower,
                        floor=floor,
                        confidence=0.96,
                        metadata={"generated": True, "level": "floor"},
                    )
                    tasks.append(floor_cache[floor_id])
                parent_id = floor_id

            phase = self._infer_phase(activity)
            discipline = self._infer_discipline(activity)
            node_type = NodeType.milestone if self._looks_like_milestone(activity, planned_start, planned_finish) else NodeType.sub_task
            task = CanonicalTask(
                external_id=f"row::{sheet_name}::{idx + 2}::{self._slug(activity)}",
                external_parent_id=parent_id,
                source_type="excel",
                source_sheet=sheet_name,
                source_row=int(idx) + 2,
                name=activity,
                normalized_name=self._normalize_activity(activity),
                node_type=node_type,
                project_hint=sheet_name,
                tower=tower,
                floor=floor,
                phase=phase,
                discipline=discipline,
                planned_start=planned_start,
                planned_finish=planned_finish,
                actual_progress=progress,
                planned_qty=qty,
                uom=uom,
                contractor=contractor,
                remarks=remarks,
                confidence=0.78 if tower or floor else 0.66,
                metadata={"sheet_role": role, "sheet_name": sheet_name},
            )
            tasks.append(task)

        profile = SheetProfile(
            sheet_name=sheet_name,
            total_rows=len(df.index),
            detected_role=role,
            confidence=role_confidence,
            mapping=[
                MappingCandidate(logical_name=k, column_name=v, confidence=0.95 if v else 0.0)
                for k, v in mapping.items()
            ],
            warnings=warnings,
        )
        return profile, tasks

    def _global_warnings(self, profiles: Iterable[SheetProfile], tasks: List[CanonicalTask]) -> List[str]:
        warnings: List[str] = []
        if not tasks:
            warnings.append("No tasks were extracted from workbook.")
        if not any(t.planned_finish or t.planned_start for t in tasks):
            warnings.append("No usable date columns detected; forecasting will be limited.")
        if not any(t.floor for t in tasks):
            warnings.append("No floor/level column detected; hierarchy may be flatter than expected.")
        skipped = [p.sheet_name for p in profiles if any("skipped" in w.lower() for w in p.warnings)]
        if skipped:
            warnings.append(f"Some sheets were skipped due to missing activity columns: {', '.join(skipped[:5])}")
        return warnings

    def _project_name_from_workbook(self, workbook: pd.ExcelFile) -> str:
        stem = getattr(workbook, "io", "Imported Project")
        if isinstance(stem, str):
            stem = stem.split("/")[-1].rsplit(".", 1)[0]
        return str(stem).replace("_", " ").strip() or "Imported Project"

    def _build_tree(self, tasks: List[CanonicalTask]) -> List[CanonicalTask]:
        root = CanonicalTask(
            external_id="project::root",
            source_type="excel",
            name="Project Root",
            node_type=NodeType.project,
            confidence=1.0,
        )
        by_id = {root.external_id: root}
        cloned = [CanonicalTask(**t.model_dump(exclude={"children"})) for t in tasks]
        for task in cloned:
            by_id[task.external_id] = task

        for task in cloned:
            parent_id = task.external_parent_id or root.external_id
            parent = by_id.get(parent_id, root)
            parent.children.append(task)

        return root.children

    def _generate_milestones(self, tasks: List[CanonicalTask]) -> List[CanonicalTask]:
        milestones: List[CanonicalTask] = []
        by_parent: Dict[str, List[CanonicalTask]] = defaultdict(list)
        for task in tasks:
            if task.node_type == NodeType.sub_task and task.external_parent_id:
                by_parent[task.external_parent_id].append(task)

        for parent_id, siblings in by_parent.items():
            if len(siblings) < 2:
                continue
            dated = [t for t in siblings if t.planned_finish]
            if not dated:
                continue
            last = sorted(dated, key=lambda x: x.planned_finish or "")[0 if False else -1]
            floor = last.floor or "Package"
            tower = last.tower or "Scope"
            milestone_name = f"{tower} {floor} completion"
            milestones.append(
                CanonicalTask(
                    external_id=f"milestone::{parent_id}",
                    external_parent_id=parent_id,
                    source_type="excel",
                    source_sheet=last.source_sheet,
                    name=milestone_name,
                    normalized_name=milestone_name,
                    node_type=NodeType.milestone,
                    tower=last.tower,
                    floor=last.floor,
                    phase="handover" if "handover" in milestone_name.lower() else last.phase,
                    discipline=last.discipline,
                    planned_finish=last.planned_finish,
                    confidence=0.72,
                    metadata={"generated": True, "reason": "latest sibling finish date"},
                )
            )
        return milestones

    def _dedupe_tasks(self, tasks: List[CanonicalTask]) -> List[CanonicalTask]:
        seen: Dict[str, CanonicalTask] = {}
        for task in tasks:
            seen[task.external_id] = task
        return list(seen.values())

    def _detect_sheet_role(self, sheet_name: str, cols: Dict[str, str]) -> Tuple[str, float]:
        joined = f"{sheet_name.lower()} {' '.join(cols.keys())}"
        if "labour" in joined or "nmr" in joined:
            return "labour", 0.94
        if "dashboard" in joined or "status" in joined:
            return "dashboard", 0.85
        if any(k in joined for k in ["marble", "tiles", "finishing"]):
            return "progress", 0.76
        return "progress", 0.68

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)

        # Many construction Excel files have merged title / logo rows above the
        # real header. If the current column names don't look like a recognisable
        # header, scan the first 15 rows to find a better one.
        if not self._looks_like_header(df.columns):
            best_row, best_score = -1, 0
            scan_limit = min(15, len(df))
            for i in range(scan_limit):
                row_values = [str(v).strip() for v in df.iloc[i] if pd.notna(v) and str(v).strip()]
                score = self._header_score(row_values)
                if score > best_score:
                    best_score = score
                    best_row = i
            if best_row >= 0 and best_score > 0:
                new_headers = [str(v).strip() if pd.notna(v) else f"col_{j}"
                               for j, v in enumerate(df.iloc[best_row])]
                df = df.iloc[best_row + 1:].reset_index(drop=True)
                df.columns = new_headers
                df = df.dropna(how="all").reset_index(drop=True)

        return df

    def _looks_like_header(self, columns) -> bool:
        """Return True if the current column names contain at least one recognisable field."""
        all_candidates = (ACTIVITY_CANDIDATES + FLOOR_CANDIDATES + TOWER_CANDIDATES +
                          START_CANDIDATES + FINISH_CANDIDATES + PROGRESS_CANDIDATES +
                          QTY_CANDIDATES + UOM_CANDIDATES)
        norms = {self._normalize_column_name(c) for c in columns}
        for cand in all_candidates:
            norm_cand = self._normalize_column_name(cand)
            if norm_cand in norms:
                return True
            if any(norm_cand in n for n in norms):
                return True
        return False

    def _header_score(self, values: List[str]) -> int:
        """Score a row on how many of its cells look like known column headers."""
        all_candidates = (ACTIVITY_CANDIDATES + FLOOR_CANDIDATES + TOWER_CANDIDATES +
                          START_CANDIDATES + FINISH_CANDIDATES + PROGRESS_CANDIDATES +
                          QTY_CANDIDATES + UOM_CANDIDATES + CONTRACTOR_CANDIDATES +
                          REMARKS_CANDIDATES + ["s no", "sl no", "sr no", "sno", "serial"])
        score = 0
        for v in values:
            norm = self._normalize_column_name(v)
            if any(self._normalize_column_name(c) in norm or norm in self._normalize_column_name(c)
                   for c in all_candidates):
                score += 1
        return score

    # ────────────────────────────────────────────────────────────────
    # Content-based intelligent column detection
    # ────────────────────────────────────────────────────────────────
    def _infer_columns_from_content(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, Optional[str]],
        used_cols: set,
    ) -> Tuple[Dict[str, Optional[str]], List[str]]:
        """Analyse actual cell values to fill unmapped columns."""
        warnings: List[str] = []
        available = [c for c in df.columns if c not in used_cols
                     and not re.match(r"^(unnamed|col_?\d)", str(c), re.I)]
        sample_size = min(60, len(df))

        for col in available:
            series = df[col].head(sample_size).dropna()
            if series.empty:
                continue

            col_type = self._classify_column(series)

            if col_type == "date":
                if not mapping["planned_start"]:
                    mapping["planned_start"] = col
                    used_cols.add(col)
                    warnings.append(f"Detected date column '{col}' as Baseline Start (by content).")
                elif not mapping["planned_finish"]:
                    mapping["planned_finish"] = col
                    used_cols.add(col)
                    warnings.append(f"Detected date column '{col}' as Baseline Finish (by content).")
            elif col_type == "floor":
                if not mapping["floor"]:
                    mapping["floor"] = col
                    used_cols.add(col)
                    warnings.append(f"Detected floor column '{col}' (by content).")
            elif col_type == "tower":
                if not mapping["tower"]:
                    mapping["tower"] = col
                    used_cols.add(col)
                    warnings.append(f"Detected tower/block column '{col}' (by content).")
            elif col_type == "activity":
                if not mapping["activity"]:
                    mapping["activity"] = col
                    used_cols.add(col)
                    warnings.append(f"Detected activity column '{col}' (by content).")
            elif col_type == "progress":
                if not mapping["progress"]:
                    mapping["progress"] = col
                    used_cols.add(col)

        # Validate: if mapped floor column has garbage (large floats, etc.), unset it
        if mapping["floor"]:
            mapping["floor"] = self._validate_floor_column(df, mapping["floor"])

        return mapping, warnings

    def _classify_column(self, series: pd.Series) -> str:
        """Classify a column's role by analysing its values."""
        values = list(series)
        non_null = [v for v in values if pd.notna(v)]
        if not non_null:
            return "unknown"

        # ── Date detection ──
        date_count = 0
        for v in non_null[:40]:
            try:
                if isinstance(v, (pd.Timestamp,)):
                    date_count += 1
                elif isinstance(v, str) and re.search(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}", v):
                    date_count += 1
                elif hasattr(v, "year"):
                    date_count += 1
                else:
                    pd.to_datetime(v)
                    date_count += 1
            except Exception:
                pass
        if date_count / max(len(non_null[:40]), 1) > 0.5:
            return "date"

        # ── Numeric percentage (progress) ──
        pct_count = 0
        for v in non_null[:40]:
            try:
                f = float(str(v).replace("%", "").strip())
                if 0 <= f <= 100:
                    pct_count += 1
            except Exception:
                pass
        if pct_count / max(len(non_null[:40]), 1) > 0.7:
            # Distinguish: if most values are 0-100 with high density, it's progress
            return "progress"

        # ── Floor detection: small ints, or strings like "Floor 3", "Level 2", "B1" ──
        floor_pat = re.compile(
            r"^(floor|level|lvl|storey|basement|b|g|ground|roof|terrace|podium|mezzanine)"
            r"|\bfloor\b|\blevel\b|\blvl\b",
            re.I,
        )
        floor_count = 0
        for v in non_null[:40]:
            s = str(v).strip()
            if floor_pat.search(s):
                floor_count += 1
            elif re.fullmatch(r"-?\d{1,2}", s):  # small ints like 1-30
                floor_count += 1
        if floor_count / max(len(non_null[:40]), 1) > 0.4:
            return "floor"

        # ── Tower/block detection: single capital letters, "Tower-A", "Block 1" ──
        tower_pat = re.compile(r"^(tower|block|wing|bldg|building)\b", re.I)
        tower_count = 0
        for v in non_null[:40]:
            s = str(v).strip()
            if tower_pat.search(s):
                tower_count += 1
            elif re.fullmatch(r"[A-Z]", s):
                tower_count += 1
        if tower_count / max(len(non_null[:40]), 1) > 0.3:
            return "tower"

        # ── Activity/description: long strings, high uniqueness ──
        str_vals = [str(v).strip() for v in non_null if isinstance(v, str) and len(str(v).strip()) > 3]
        if len(str_vals) >= 3:
            avg_len = sum(len(s) for s in str_vals) / len(str_vals)
            unique_ratio = len(set(str_vals)) / len(str_vals)
            if avg_len > 8 and unique_ratio > 0.3:
                return "activity"

        return "unknown"

    def _validate_floor_column(self, df: pd.DataFrame, col: str) -> Optional[str]:
        """Return None if the mapped floor column contains implausible values (big floats, etc.)."""
        sample = df[col].dropna().head(30)
        bad_count = 0
        for v in sample:
            s = str(v).strip()
            try:
                f = float(s)
                if abs(f) > 200 or (f != int(f) and abs(f) > 30):
                    bad_count += 1
            except ValueError:
                pass  # string is fine
        if bad_count / max(len(sample), 1) > 0.3:
            return None  # unset — this isn't a floor column
        return col

    def _guess_activity_column(self, df: pd.DataFrame, exclude: Optional[set] = None) -> Optional[str]:
        """Pick the column with the most non-null unique text values (likely the activity column)."""
        skip_patterns = re.compile(r"^(unnamed|col_?\d|s\s*no|sl\s*no|sr\s*no|sno|serial)", re.I)
        exclude = exclude or set()
        best_col: Optional[str] = None
        best_score = 0.0
        for col in df.columns:
            if col in exclude:
                continue
            if skip_patterns.search(str(col)):
                continue
            series = df[col].dropna()
            if series.empty:
                continue
            # Must be mostly strings (not numbers/dates), at least 4 chars long
            str_count = sum(1 for v in series if isinstance(v, str) and len(v.strip()) > 3)
            if str_count < 3:
                continue
            unique_ratio = series.nunique() / max(len(series), 1)
            avg_len = sum(len(str(v)) for v in series if isinstance(v, str)) / max(str_count, 1)
            # Score favours: many unique long text strings
            score = str_count * unique_ratio * min(avg_len / 10, 3.0)
            if score > best_score:
                best_score = score
                best_col = col
        # Only accept if we got a reasonable score
        if best_col and best_score >= 3:
            return best_col
        return None

    def _pick(self, cols: Dict[str, str], candidates: List[str]) -> Optional[str]:
        for candidate in candidates:
            norm = self._normalize_column_name(candidate)
            if norm in cols:
                return cols[norm]
        for norm_col, original in cols.items():
            if any(candidate in norm_col for candidate in map(self._normalize_column_name, candidates)):
                return original
        return None

    def _normalize_column_name(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9%]+", " ", str(value).lower()).strip()

    def _tower_from_sheet(self, sheet_name: str) -> Optional[str]:
        name = sheet_name.strip()
        if re.search(r"(^|\b)(tower|block|wing)[-\s]?[a-z0-9]+", name, re.I):
            return name
        return None

    def _normalize_floor(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        s = value.strip()
        # Reject obvious non-floor values: large numbers, decimals, etc.
        try:
            f = float(s)
            if f != int(f) or abs(f) > 200:
                return None  # 9901.96, 8300.5 etc. aren't floors
            n = int(f)
            if 0 <= n <= 200:
                return f"Floor {n}"
            return None
        except ValueError:
            pass
        # Already a reasonable string like "Floor 3", "Basement", etc.
        if re.fullmatch(r"\d{1,3}", s):
            return f"Floor {s}"
        return s

    def _normalize_activity(self, activity: str) -> str:
        return re.sub(r"\s+", " ", activity).strip().title()

    def _slug(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]

    def _clean(self, value: Any) -> Optional[str]:
        if pd.isna(value):
            return None
        text = str(value).strip()
        return text or None

    def _dateish(self, value: Any) -> Optional[str]:
        if value is None or pd.isna(value):
            return None
        try:
            return pd.to_datetime(value).date().isoformat()
        except Exception:
            return str(value)

    def _progressish(self, value: Any) -> Optional[float]:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        try:
            progress = float(value)
            if progress <= 1:
                progress *= 100
            return round(max(0.0, min(progress, 100.0)), 2)
        except Exception:
            return None

    def _floatish(self, value: Any) -> Optional[float]:
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _looks_like_milestone(self, activity: str, start: Optional[str], finish: Optional[str]) -> bool:
        name = activity.lower()
        if any(k in name for k in MILESTONE_HINTS):
            return True
        return bool(start and finish and start == finish)

    def _infer_phase(self, activity: str) -> str:
        name = activity.lower()
        for phase, keywords in PHASE_RULES.items():
            if any(k in name for k in keywords):
                return phase
        return "unknown"

    def _infer_discipline(self, activity: str) -> str:
        name = activity.lower()
        for discipline, keywords in DISCIPLINE_RULES.items():
            if any(k in name for k in keywords):
                return discipline
        return "unknown"


def parse_excel(file_path: str, project_name_hint: Optional[str] = None) -> dict[str, Any]:
    service = ExcelNormalizationService()
    preview = service.parse_workbook(file_path, project_name_hint=project_name_hint)
    return preview.model_dump(mode="json")
