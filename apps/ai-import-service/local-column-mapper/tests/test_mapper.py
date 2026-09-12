from unittest import TestCase
from src.mapper import map_columns  # Assuming map_columns is the function to be tested

class TestColumnMapper(TestCase):

    def setUp(self):
        # Setup any necessary data or state before each test
        self.sample_data = {
            "Column1": ["Task A", "Task B", "Task C"],
            "Column2": ["Tower 1", "Tower 2", "Tower 1"],
            "Column3": ["Floor 1", "Floor 2", "Floor 1"],
            "Column4": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "Column5": ["100%", "50%", "0%"],
        }

    def test_map_columns(self):
        expected_mapping = {
            "Column1": "activity",
            "Column2": "tower",
            "Column3": "floor",
            "Column4": "planned_start",
            "Column5": "progress",
        }
        actual_mapping = map_columns(self.sample_data)
        self.assertEqual(actual_mapping, expected_mapping)

    def test_empty_data(self):
        empty_data = {}
        expected_mapping = {}
        actual_mapping = map_columns(empty_data)
        self.assertEqual(actual_mapping, expected_mapping)

    def test_invalid_data(self):
        invalid_data = {
            "InvalidColumn": ["Invalid Data"]
        }
        expected_mapping = {}
        actual_mapping = map_columns(invalid_data)
        self.assertEqual(actual_mapping, expected_mapping)

    def tearDown(self):
        # Clean up any state after each test if necessary
        pass