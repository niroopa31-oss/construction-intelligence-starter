from typing import List, Dict, Any
import pandas as pd
import re

class LocalColumnMapper:
    def __init__(self):
        self.activity_candidates = [
            "activity", "task", "work", "description", "item", "activity name",
            "particulars", "scope", "scope of work", "work description",
            "activity description", "component", "element", "subject",
            "boq item", "detail", "details", "name of activity",
            "name of work", "nature of work", "trade", "schedule item",
            "work item", "work package", "package", "activity/description",
            "description of work", "description of activity",
        ]
        self.floor_candidates = ["floor", "flats/floor", "flat", "level", "lvl", "storey", "story", "floor no", "floor number", "flat no"]
        self.tower_candidates = ["tower", "block", "wing", "building", "bldg"]
        self.start_candidates = ["start", "start date", "planned start", "baseline start", "commence", "commencement", "commencement date", "from", "begin", "begin date"]
        self.finish_candidates = ["finish", "end", "planned finish", "baseline finish", "date", "target date", "completion date", "end date", "to", "target", "due date", "due"]
        self.progress_candidates = ["progress", "% progress", "actual progress", "ach %", "completion", "% complete", "status", "done", "% done", "achieved", "% achieved", "work done", "% work done", "physical progress", "% physical progress"]
        self.contractor_candidates = ["contractor", "agency", "vendor", "subcontractor", "sub contractor", "assigned to", "responsible"]
        self.remarks_candidates = ["remarks", "remark", "comments", "status remarks", "note", "observation", "notes", "comment"]
        self.qty_candidates = ["qty", "quantity", "planned qty", "balance qty", "actual qty", "total qty", "total quantity"]
        self.uom_candidates = ["uom", "unit of measurement", "unit"]

    def map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        cols = {self._normalize_column_name(c): c for c in df.columns}
        mapping = {
            "activity": self._pick(cols, self.activity_candidates),
            "tower": self._pick(cols, self.tower_candidates),
            "floor": self._pick(cols, self.floor_candidates),
            "planned_start": self._pick(cols, self.start_candidates),
            "planned_finish": self._pick(cols, self.finish_candidates),
            "actual_start": None,
            "actual_finish": None,
            "progress": self._pick(cols, self.progress_candidates),
            "contractor": self._pick(cols, self.contractor_candidates),
            "remarks": self._pick(cols, self.remarks_candidates),
            "qty": self._pick(cols, self.qty_candidates),
            "uom": self._pick_uom(cols, df),
        }
        return mapping

    def _pick(self, cols: Dict[str, str], candidates: List[str]) -> str:
        for candidate in candidates:
            norm = self._normalize_column_name(candidate)
            if norm in cols:
                return cols[norm]
        return None

    def _pick_uom(self, cols: Dict[str, str], df: pd.DataFrame) -> str:
        candidate = self._pick(cols, self.uom_candidates)
        if not candidate:
            return None
        sample = df[candidate].dropna().head(30)
        short_count = sum(1 for v in sample if isinstance(v, str) and len(v.strip()) <= 20)
        if short_count / max(len(sample), 1) > 0.5:
            return candidate
        return None

    def _normalize_column_name(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9%]+", " ", str(value).lower()).strip()