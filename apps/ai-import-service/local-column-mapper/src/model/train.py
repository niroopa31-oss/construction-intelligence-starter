from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import joblib
import os

class ColumnMapperModel:
    def __init__(self):
        self.model = RandomForestClassifier()
        self.columns = None

    def preprocess_data(self, data: pd.DataFrame):
        # Convert categorical columns to numerical
        data = pd.get_dummies(data, drop_first=True)
        self.columns = data.columns
        return data

    def train(self, data: pd.DataFrame, target: pd.Series):
        processed_data = self.preprocess_data(data)
        X_train, X_test, y_train, y_test = train_test_split(processed_data, target, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        return self.model.score(X_test, y_test)

    def save_model(self, model_path: str):
        joblib.dump(self.model, model_path)

    def load_model(self, model_path: str):
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)

    def predict(self, data: pd.DataFrame):
        processed_data = self.preprocess_data(data)
        return self.model.predict(processed_data)

def main():
    # Example usage
    # df = pd.read_excel('path_to_excel_file.xlsx')
    # target = df['target_column']
    # df.drop(columns=['target_column'], inplace=True)

    # model = ColumnMapperModel()
    # accuracy = model.train(df, target)
    # print(f'Model trained with accuracy: {accuracy}')
    # model.save_model('local_column_mapper/model/saved/column_mapper_model.pkl')

if __name__ == "__main__":
    main()