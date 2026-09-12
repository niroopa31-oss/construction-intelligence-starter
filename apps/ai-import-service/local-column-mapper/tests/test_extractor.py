from src.features.extractor import extract_features
import pandas as pd
import pytest

def test_extract_features():
    # Sample data for testing
    sample_data = {
        "Activity": ["Excavate", "Pour Concrete", "Install Windows"],
        "Start Date": ["2023-01-01", "2023-01-10", "2023-01-15"],
        "End Date": ["2023-01-05", "2023-01-12", "2023-01-20"],
        "Contractor": ["Contractor A", "Contractor B", "Contractor C"],
        "Progress": [100, 50, 0]
    }
    
    df = pd.DataFrame(sample_data)

    # Extract features
    features = extract_features(df)

    # Assertions to validate the extracted features
    assert "activity" in features
    assert "start_date" in features
    assert "end_date" in features
    assert "contractor" in features
    assert "progress" in features

    assert features["activity"] == ["Excavate", "Pour Concrete", "Install Windows"]
    assert features["start_date"] == ["2023-01-01", "2023-01-10", "2023-01-15"]
    assert features["end_date"] == ["2023-01-05", "2023-01-12", "2023-01-20"]
    assert features["contractor"] == ["Contractor A", "Contractor B", "Contractor C"]
    assert features["progress"] == [100, 50, 0]