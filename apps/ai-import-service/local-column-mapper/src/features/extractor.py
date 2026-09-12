from typing import List, Dict, Any
import pandas as pd

class ColumnMapper:
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

    def map_columns(self, columns: List[str]) -> Dict[str, str]:
        mapping = {}
        for col in columns:
            normalized_col = self.normalize_column_name(col)
            if normalized_col in self.activity_candidates:
                mapping[col] = "activity"
            elif normalized_col in self.floor_candidates:
                mapping[col] = "floor"
            elif normalized_col in self.tower_candidates:
                mapping[col] = "tower"
            elif normalized_col in self.start_candidates:
                mapping[col] = "planned_start"
            elif normalized_col in self.finish_candidates:
                mapping[col] = "planned_finish"
            elif normalized_col in self.progress_candidates:
                mapping[col] = "progress"
            elif normalized_col in self.contractor_candidates:
                mapping[col] = "contractor"
            elif normalized_col in self.remarks_candidates:
                mapping[col] = "remarks"
            elif normalized_col in self.qty_candidates:
                mapping[col] = "qty"
            elif normalized_col in self.uom_candidates:
                mapping[col] = "uom"
            else:
                mapping[col] = "ignore"
        return mapping

    def normalize_column_name(self, value: Any) -> str:
        return re.sub(r"[^a-z0-9%]+", " ", str(value).lower()).strip()

    def extract_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        columns = df.columns.tolist()
        column_mapping = self.map_columns(columns)
        return {
            "column_mapping": column_mapping,
            "sample_data": df.head().to_dict(orient="records")
        }