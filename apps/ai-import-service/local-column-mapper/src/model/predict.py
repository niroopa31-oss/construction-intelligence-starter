from typing import Any, Dict, List
import joblib
import pandas as pd

class LocalColumnMapper:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = self.load_model()

    def load_model(self) -> Any:
        return joblib.load(self.model_path)

    def predict(self, columns: List[str]) -> Dict[str, str]:
        # Prepare the input for the model
        input_data = pd.DataFrame(columns).T
        predictions = self.model.predict(input_data)
        return {col: role for col, role in zip(columns, predictions)}

def map_columns(model_path: str, columns: List[str]) -> Dict[str, str]:
    mapper = LocalColumnMapper(model_path)
    return mapper.predict(columns)