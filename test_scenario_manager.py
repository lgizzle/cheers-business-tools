import unittest
import os
import shutil
import json
import tempfile
from scenario_manager import ScenarioManager, ScenarioError
from validator import ValidationError

class TestScenarioManager(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.scenario_manager = ScenarioManager(scenarios_dir=self.temp_dir)

        # Sample scenario data for testing
        self.valid_scenario = {
            "params": {
                "small_deal_minimum": 30,
                "bulk_deal_minimum": 60,
                "payment_terms": 30
            },
            "products": [
                {
                    "product_name": "Test Product",
                    "current_price": 25.0,
                    "bulk_price": 20.0,
                    "cases_on_hand": 10,
                    "cases_per_year": 100,
                    "bottles_per_case": 12
                }
            ]
        }

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_list_scenarios_empty(self):
        # Test listing scenarios when none exist
        scenarios = self.scenario_manager.list_scenarios()
        self.assertEqual(scenarios, [])

    def test_save_and_load_scenario(self):
        # Test saving a scenario
        result = self.scenario_manager.save_scenario("test_scenario", self.valid_scenario)
        self.assertTrue(result)

        # Check that the file was created
        file_path = os.path.join(self.temp_dir, "test_scenario.json")
        self.assertTrue(os.path.exists(file_path))

        # Test loading the scenario
        loaded_scenario = self.scenario_manager.load_scenario("test_scenario")
        self.assertEqual(loaded_scenario["params"]["small_deal_minimum"], 30)
        self.assertEqual(loaded_scenario["params"]["bulk_deal_minimum"], 60)
        self.assertEqual(loaded_scenario["products"][0]["product_name"], "Test Product")

    def test_save_invalid_scenario(self):
        # Test saving an invalid scenario
        invalid_scenario = {
            "params": {
                "small_deal_minimum": 30,
                "bulk_deal_minimum": 20,  # Invalid: smaller than small_deal_minimum
                "payment_terms": 30
            },
            "products": [
                {
                    "product_name": "Test Product",
                    "current_price": 25.0,
                    "bulk_price": 20.0,
                    "cases_on_hand": 10,
                    "cases_per_year": 100,
                    "bottles_per_case": 12
                }
            ]
        }

        with self.assertRaises(ScenarioError):
            self.scenario_manager.save_scenario("invalid_scenario", invalid_scenario)

    def test_list_scenarios(self):
        # Save multiple scenarios
        self.scenario_manager.save_scenario("scenario1", self.valid_scenario)
        self.scenario_manager.save_scenario("scenario2", self.valid_scenario)

        # Test listing scenarios
        scenarios = self.scenario_manager.list_scenarios()
        self.assertEqual(len(scenarios), 2)
        self.assertIn("scenario1", scenarios)
        self.assertIn("scenario2", scenarios)

    def test_delete_scenario(self):
        # Save a scenario
        self.scenario_manager.save_scenario("scenario_to_delete", self.valid_scenario)

        # Test deleting the scenario
        result = self.scenario_manager.delete_scenario("scenario_to_delete")
        self.assertTrue(result)

        # Check that the file was deleted
        file_path = os.path.join(self.temp_dir, "scenario_to_delete.json")
        self.assertFalse(os.path.exists(file_path))

        # Test deleting a non-existent scenario
        result = self.scenario_manager.delete_scenario("nonexistent_scenario")
        self.assertFalse(result)

    def test_load_nonexistent_scenario(self):
        # Test loading a scenario that doesn't exist
        with self.assertRaises(ScenarioError):
            self.scenario_manager.load_scenario("nonexistent_scenario")

    def test_sanitize_for_json(self):
        # Test sanitizing numpy types
        try:
            import numpy as np

            # Create a scenario with numpy types
            scenario_with_numpy = {
                "params": {
                    "small_deal_minimum": np.int64(30),
                    "bulk_deal_minimum": np.int64(60),
                    "payment_terms": np.int64(30)
                },
                "products": [
                    {
                        "product_name": "Test Product",
                        "current_price": np.float64(25.0),
                        "bulk_price": np.float64(20.0),
                        "cases_on_hand": np.int64(10),
                        "cases_per_year": np.int64(100),
                        "bottles_per_case": np.int64(12)
                    }
                ]
            }

            # Sanitize the data
            sanitized = self.scenario_manager._sanitize_for_json(scenario_with_numpy)

            # Check that numpy types were converted
            self.assertIsInstance(sanitized["params"]["small_deal_minimum"], int)
            self.assertIsInstance(sanitized["products"][0]["current_price"], float)

            # Check that the data can be serialized to JSON
            json_str = json.dumps(sanitized)
            self.assertIsInstance(json_str, str)

        except ImportError:
            # Skip if numpy is not available
            pass

if __name__ == '__main__':
    unittest.main()
