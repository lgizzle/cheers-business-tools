import unittest
import os
import shutil
import json
import tempfile
from exporter import MultiProductExporter, ExportError

class TestExporter(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = MultiProductExporter(output_dir=self.temp_dir)

        # Sample scenario data for testing
        self.scenario_data = {
            "params": {
                "small_deal_minimum": 30,
                "bulk_deal_minimum": 60,
                "payment_terms": 30
            },
            "products": [
                {
                    "product_name": "Test Product 1",
                    "current_price": 25.0,
                    "bulk_price": 20.0,
                    "cases_on_hand": 10,
                    "cases_per_year": 100,
                    "bottles_per_case": 12,
                    "bulk_quantity": 25
                },
                {
                    "product_name": "Test Product 2",
                    "current_price": 45.0,
                    "bulk_price": 40.0,
                    "cases_on_hand": 5,
                    "cases_per_year": 80,
                    "bottles_per_case": 6,
                    "bulk_quantity": 35
                }
            ]
        }

        # Sample product metrics for testing
        self.product_metrics = {
            "product_metrics": [
                {
                    "product_name": "Test Product 1",
                    "daily_cases": 0.274,
                    "savings_per_case": 60.0,
                    "total_savings": 1500.0,
                    "days_of_stock": 36.5,
                    "days_of_stock_after": 127.7,
                    "holding_time_days": 91.2,
                    "holding_time_years": 0.25,
                    "peak_investment": 5000.0,
                    "average_investment": 2500.0,
                    "holding_cost": 100.0,
                    "net_savings": 1400.0,
                    "roi": 0.28,
                    "annual_roi": 1.12
                },
                {
                    "product_name": "Test Product 2",
                    "daily_cases": 0.219,
                    "savings_per_case": 30.0,
                    "total_savings": 1050.0,
                    "days_of_stock": 22.8,
                    "days_of_stock_after": 182.1,
                    "holding_time_days": 159.8,
                    "holding_time_years": 0.44,
                    "peak_investment": 8400.0,
                    "average_investment": 4200.0,
                    "holding_cost": 150.0,
                    "net_savings": 900.0,
                    "roi": 0.11,
                    "annual_roi": 0.25
                }
            ],
            "total_savings": 2550.0,
            "total_holding_cost": 250.0,
            "net_savings": 2300.0,
            "total_peak_investment": 13400.0,
            "total_average_investment": 6700.0,
            "overall_roi": 0.17,
            "weighted_holding_time": 0.36,
            "overall_annual_roi": 0.47
        }

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_export_to_excel(self):
        # Test exporting to Excel
        file_path = self.exporter.export_to_excel("test_scenario", self.scenario_data, self.product_metrics)

        # Check that the file was created
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith(".xlsx"))

        # Check that the file has the right extension
        self.assertEqual(os.path.splitext(file_path)[1], ".xlsx")

        # Check that the file has a non-zero size
        self.assertGreater(os.path.getsize(file_path), 0)

    def test_export_debug_info(self):
        # Test exporting debug info
        file_path = self.exporter.export_debug_info("test_scenario", self.scenario_data, self.product_metrics)

        # Check that the file was created
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith("_debug.json"))

        # Check that the file contains valid JSON
        with open(file_path, 'r') as f:
            debug_data = json.load(f)

        # Check that the JSON contains the expected fields
        self.assertIn("scenario_name", debug_data)
        self.assertIn("input_data", debug_data)
        self.assertIn("calculation_results", debug_data)

        # Check some specific values
        self.assertEqual(debug_data["scenario_name"], "test_scenario")
        self.assertEqual(debug_data["input_data"]["params"]["bulk_deal_minimum"], 60)
        self.assertEqual(debug_data["calculation_results"]["total_savings"], 2550.0)

    def test_sanitize_for_json(self):
        # Test sanitizing numpy types
        try:
            import numpy as np

            # Create data with numpy types
            data_with_numpy = {
                "int_value": np.int64(42),
                "float_value": np.float64(3.14),
                "array_value": np.array([1, 2, 3]).tolist()  # Convert array to list
            }

            # Sanitize the data
            sanitized = self.exporter._sanitize_for_json(data_with_numpy)

            # Check that numpy types were converted
            self.assertIsInstance(sanitized["int_value"], int)
            self.assertIsInstance(sanitized["float_value"], float)

            # Check that the data can be serialized to JSON
            json_str = json.dumps(sanitized)
            self.assertIsInstance(json_str, str)

        except ImportError:
            # Skip if numpy is not available
            pass

if __name__ == '__main__':
    unittest.main()
