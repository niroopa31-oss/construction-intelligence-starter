from typing import Any, Dict, List
import pandas as pd

def load_excel_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Load data from an Excel file."""
    return pd.read_excel(file_path, sheet_name=sheet_name)

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the DataFrame by cleaning and normalizing column names."""
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    df = df.dropna(how='all').reset_index(drop=True)
    return df

def extract_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Extract relevant columns from the DataFrame for mapping."""
    column_mapping = {
        "activity": [],
        "tower": [],
        "floor": [],
        "planned_start": [],
        "planned_finish": [],
        "actual_start": [],
        "actual_finish": [],
        "progress": [],
        "contractor": [],
        "remarks": [],
        "qty": [],
        "uom": []
    }
    
    for col in df.columns:
        if "activity" in col:
            column_mapping["activity"].append(col)
        elif "tower" in col:
            column_mapping["tower"].append(col)
        elif "floor" in col:
            column_mapping["floor"].append(col)
        elif "start" in col:
            if "planned" in col:
                column_mapping["planned_start"].append(col)
            else:
                column_mapping["actual_start"].append(col)
        elif "finish" in col:
            if "planned" in col:
                column_mapping["planned_finish"].append(col)
            else:
                column_mapping["actual_finish"].append(col)
        elif "progress" in col:
            column_mapping["progress"].append(col)
        elif "contractor" in col:
            column_mapping["contractor"].append(col)
        elif "remarks" in col:
            column_mapping["remarks"].append(col)
        elif "qty" in col or "quantity" in col:
            column_mapping["qty"].append(col)
        elif "uom" in col or "unit" in col:
            column_mapping["uom"].append(col)

    return column_mapping

def load_and_preprocess(file_path: str, sheet_name: str) -> Dict[str, Any]:
    """Load and preprocess the Excel data, returning a mapping of columns."""
    df = load_excel_data(file_path, sheet_name)
    df = preprocess_data(df)
    column_mapping = extract_columns(df)
    return {
        "data": df,
        "column_mapping": column_mapping
    }