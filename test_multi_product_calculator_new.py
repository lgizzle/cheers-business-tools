import unittest
import os
import shutil
import tempfile
from multi_product_calculator_new import MultiProductCalculator

class TestMultiProductCalculator(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for scenarios and reports
        self.temp_dir = tempfile.mkdtemp()
        self.scenarios_dir = os.path.join(self.temp_dir, "scenarios")
        self.reports_dir = os.path.join(self.temp_dir, "reports")

        # Create directories
        os.makedirs(self.scenarios_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        # Create calculator
        self.calculator = MultiProductCalculator()
        self.calculator.scenario_manager.scenarios_dir = self.scenarios_dir
        self.calculator.exporter.output_dir = self.reports_dir

        # Sample products for testing
        self.test_products = [
            {
                "product_name": "Test Product 1",
                "current_price": 25.0,
                "bulk_price": 20.0,
                "cases_on_hand": 10,
                "cases_per_year": 100,
                "bottles_per_case": 12
            },
            {
                "product_name": "Test Product 2",
                "current_price": 45.0,
                "bulk_price": 40.0,
                "cases_on_hand": 5,
                "cases_per_year": 80,
                "bottles_per_case": 6
            },
            {
                "product_name": "Test Product 3",
                "current_price": 14.0,
                "bulk_price": 10.0,
                "cases_on_hand": 0,
                "cases_per_year": 60,
                "bottles_per_case": 24
            }
        ]

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_set_params(self):
        # Test setting parameters
        self.calculator.set_params({
            "small_deal_minimum": 40,
            "bulk_deal_minimum": 80,
            "payment_terms": 45
        })

        self.assertEqual(self.calculator.params["small_deal_minimum"], 40)
        self.assertEqual(self.calculator.params["bulk_deal_minimum"], 80)
        self.assertEqual(self.calculator.params["payment_terms"], 45)

        # Test invalid parameters
        with self.assertRaises(ValueError):
            self.calculator.set_params({
                "small_deal_minimum": 100,
                "bulk_deal_minimum": 50  # Invalid: smaller than small_deal_minimum
            })

    def test_add_product(self):
        # Test adding a product
        self.calculator.add_product(self.test_products[0])

        self.assertEqual(len(self.calculator.products), 1)
        self.assertEqual(self.calculator.products[0]["product_name"], "Test Product 1")

        # Test invalid product
        with self.assertRaises(ValueError):
            self.calculator.add_product({
                "product_name": "Invalid Product",
                "current_price": -10  # Invalid: negative price
            })

    def test_set_products(self):
        # Test setting multiple products
        self.calculator.set_products(self.test_products)

        self.assertEqual(len(self.calculator.products), 3)
        self.assertEqual(self.calculator.products[0]["product_name"], "Test Product 1")
        self.assertEqual(self.calculator.products[1]["product_name"], "Test Product 2")
        self.assertEqual(self.calculator.products[2]["product_name"], "Test Product 3")

    def test_suggest_quantities_proportional(self):
        # Set products
        self.calculator.set_products(self.test_products)

        # Test proportional allocation
        result = self.calculator.suggest_quantities("proportional")

        # Check that quantities were allocated
        self.assertTrue(all("bulk_quantity" in p for p in result))

        # Check that total meets minimum
        total_quantity = sum(p["bulk_quantity"] for p in result)
        self.assertGreaterEqual(total_quantity, self.calculator.params["bulk_deal_minimum"])

        # Check that Product 1 has the highest allocation (highest annual sales)
        product_1 = next(p for p in result if p["product_name"] == "Test Product 1")
        product_2 = next(p for p in result if p["product_name"] == "Test Product 2")
        product_3 = next(p for p in result if p["product_name"] == "Test Product 3")

        self.assertGreater(product_1["bulk_quantity"], product_2["bulk_quantity"])
        self.assertGreater(product_1["bulk_quantity"], product_3["bulk_quantity"])

    def test_suggest_quantities_roi(self):
        # Set products
        self.calculator.set_products(self.test_products)

        # Test ROI allocation
        result = self.calculator.suggest_quantities("roi")

        # Check that quantities were allocated
        self.assertTrue(all("bulk_quantity" in p for p in result))

        # Check that total meets minimum
        total_quantity = sum(p["bulk_quantity"] for p in result)
        self.assertGreaterEqual(total_quantity, self.calculator.params["bulk_deal_minimum"])

    def test_suggest_quantities_with_min_days_stock(self):
        # Set products
        self.calculator.set_products(self.test_products)

        # Test with minimum days of stock
        result = self.calculator.suggest_quantities("proportional", min_days_stock=30)

        # Check that quantities were allocated
        self.assertTrue(all("bulk_quantity" in p for p in result))

        # Check that total meets minimum
        total_quantity = sum(p["bulk_quantity"] for p in result)
        self.assertGreaterEqual(total_quantity, self.calculator.params["bulk_deal_minimum"])

        # Product 3 has 0 on hand, should have at least 5 cases to meet 30 days
        # (60 cases/year ÷ 365) × 30 days = ~5 cases
        product_3 = next(p for p in result if p["product_name"] == "Test Product 3")
        self.assertGreaterEqual(product_3["bulk_quantity"], 4.9)

    def test_calculate(self):
        # Set products and suggest quantities
        self.calculator.set_products(self.test_products)
        self.calculator.suggest_quantities("proportional")

        # Calculate results
        results = self.calculator.calculate()

        # Check that results were calculated
        self.assertIsNotNone(results)
        self.assertIn("product_metrics", results)
        self.assertIn("total_savings", results)
        self.assertIn("overall_roi", results)

        # Check that each product has metrics
        self.assertEqual(len(results["product_metrics"]), 3)

        # Check specific metrics
        product_1_metrics = next(pm for pm in results["product_metrics"] if pm["product_name"] == "Test Product 1")
        self.assertIn("roi", product_1_metrics)
        self.assertIn("total_savings", product_1_metrics)

    def test_save_and_load_scenario(self):
        # Set up scenario
        self.calculator.set_products(self.test_products)
        self.calculator.suggest_quantities("proportional")
        self.calculator.calculate()

        # Save scenario
        self.calculator.save_scenario("test_scenario")

        # Create a new calculator
        new_calculator = MultiProductCalculator()
        new_calculator.scenario_manager.scenarios_dir = self.scenarios_dir

        # Load scenario
        new_calculator.load_scenario("test_scenario")

        # Check that scenario was loaded correctly
        self.assertEqual(len(new_calculator.products), 3)
        self.assertEqual(new_calculator.products[0]["product_name"], "Test Product 1")
        self.assertTrue(all("bulk_quantity" in p for p in new_calculator.products))

    def test_export_to_excel(self):
        # Set up scenario
        self.calculator.set_products(self.test_products)
        self.calculator.suggest_quantities("proportional")
        self.calculator.calculate()

        # Export to Excel
        file_path = self.calculator.export_to_excel("test_export")

        # Check that file was created
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith(".xlsx"))

    def test_export_debug_info(self):
        # Set up scenario
        self.calculator.set_products(self.test_products)
        self.calculator.suggest_quantities("proportional")
        self.calculator.calculate()

        # Export debug info
        file_path = self.calculator.export_debug_info("test_debug")

        # Check that file was created
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith("_debug.json"))

if __name__ == '__main__':
    unittest.main()
