import unittest
from validator import validate_numeric, validate_product, validate_calculator_params, validate_bulk_quantities, ValidationError

class TestValidator(unittest.TestCase):

    def test_validate_numeric(self):
        # Test valid numbers
        self.assertEqual(validate_numeric(10, "Test value"), 10.0)
        self.assertEqual(validate_numeric("10.5", "Test value"), 10.5)
        self.assertEqual(validate_numeric(0, "Test value"), 0.0)

        # Test invalid types
        with self.assertRaises(ValidationError):
            validate_numeric("abc", "Test value")

        # Test negative numbers
        with self.assertRaises(ValidationError):
            validate_numeric(-10, "Test value")

        # Test zero when not allowed
        with self.assertRaises(ValidationError):
            validate_numeric(0, "Test value", allow_zero=False)

        # Test minimum value
        with self.assertRaises(ValidationError):
            validate_numeric(5, "Test value", min_value=10)

        # Test integer only
        self.assertEqual(validate_numeric(10, "Test value", integer_only=True), 10.0)
        with self.assertRaises(ValidationError):
            validate_numeric(10.5, "Test value", integer_only=True)

    def test_validate_product(self):
        # Test valid product
        valid_product = {
            "product_name": "Test Product",
            "current_price": 25.0,
            "bulk_price": 20.0,
            "cases_on_hand": 10,
            "cases_per_year": 100,
            "bottles_per_case": 12
        }
        validated = validate_product(valid_product)
        self.assertEqual(validated["product_name"], "Test Product")
        self.assertEqual(validated["current_price"], 25.0)

        # Test with optional bulk_quantity
        valid_product["bulk_quantity"] = 20
        validated = validate_product(valid_product)
        self.assertEqual(validated["bulk_quantity"], 20.0)

        # Test missing required field
        invalid_product = valid_product.copy()
        del invalid_product["cases_on_hand"]
        with self.assertRaises(ValidationError):
            validate_product(invalid_product)

        # Test invalid product name
        invalid_product = valid_product.copy()
        invalid_product["product_name"] = ""
        with self.assertRaises(ValidationError):
            validate_product(invalid_product)

        # Test bulk price higher than current price
        invalid_product = valid_product.copy()
        invalid_product["bulk_price"] = 30.0
        with self.assertRaises(ValidationError):
            validate_product(invalid_product)

        # Test invalid numeric fields
        invalid_product = valid_product.copy()
        invalid_product["bottles_per_case"] = 0
        with self.assertRaises(ValidationError):
            validate_product(invalid_product)

        invalid_product = valid_product.copy()
        invalid_product["cases_per_year"] = -1
        with self.assertRaises(ValidationError):
            validate_product(invalid_product)

    def test_validate_calculator_params(self):
        # Test valid params
        valid_params = {
            "small_deal_minimum": 30,
            "bulk_deal_minimum": 60,
            "payment_terms": 30
        }
        validated = validate_calculator_params(valid_params)
        self.assertEqual(validated["small_deal_minimum"], 30.0)
        self.assertEqual(validated["bulk_deal_minimum"], 60.0)
        self.assertEqual(validated["payment_terms"], 30.0)

        # Test with optional min_days_stock
        valid_params["min_days_stock"] = 14
        validated = validate_calculator_params(valid_params)
        self.assertEqual(validated["min_days_stock"], 14.0)

        # Test missing required field
        invalid_params = valid_params.copy()
        del invalid_params["payment_terms"]
        with self.assertRaises(ValidationError):
            validate_calculator_params(invalid_params)

        # Test small_deal_minimum > bulk_deal_minimum
        invalid_params = valid_params.copy()
        invalid_params["small_deal_minimum"] = 70
        with self.assertRaises(ValidationError):
            validate_calculator_params(invalid_params)

        # Test invalid numeric fields
        invalid_params = valid_params.copy()
        invalid_params["payment_terms"] = -1
        with self.assertRaises(ValidationError):
            validate_calculator_params(invalid_params)

    def test_validate_bulk_quantities(self):
        # Test valid quantities
        products = [
            {"product_name": "Product 1", "bulk_quantity": 20},
            {"product_name": "Product 2", "bulk_quantity": 40},
            {"product_name": "Product 3", "bulk_quantity": 10}
        ]
        self.assertTrue(validate_bulk_quantities(products, 60))
        self.assertTrue(validate_bulk_quantities(products, 70))

        # Test insufficient quantities
        with self.assertRaises(ValidationError):
            validate_bulk_quantities(products, 80)

        # Test with missing bulk_quantity
        products = [
            {"product_name": "Product 1", "bulk_quantity": 20},
            {"product_name": "Product 2", "bulk_quantity": 40},
            {"product_name": "Product 3"}  # Missing bulk_quantity
        ]
        self.assertTrue(validate_bulk_quantities(products, 60))

        # Test with empty products list
        with self.assertRaises(ValidationError):
            validate_bulk_quantities([], 1)

if __name__ == '__main__':
    unittest.main()
