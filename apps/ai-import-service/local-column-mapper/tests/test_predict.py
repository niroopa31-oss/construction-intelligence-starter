from unittest import TestCase
from src.model.predict import load_model, predict_columns

class TestColumnMappingPredictor(TestCase):

    def setUp(self):
        self.model_path = 'src/model/saved/model.pkl'  # Adjust the path as necessary
        self.model = load_model(self.model_path)

    def test_predict_columns(self):
        sample_data = {
            'Column1': ['Task A', 'Task B', 'Task C'],
            'Column2': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'Column3': ['Contractor X', 'Contractor Y', 'Contractor Z']
        }
        expected_output = {
            'Column1': 'activity',
            'Column2': 'planned_start',
            'Column3': 'contractor'
        }
        predicted_mapping = predict_columns(sample_data, self.model)
        self.assertEqual(predicted_mapping, expected_output)

    def test_load_model(self):
        self.assertIsNotNone(self.model)

    def test_invalid_model_path(self):
        with self.assertRaises(FileNotFoundError):
            load_model('invalid/path/to/model.pkl')