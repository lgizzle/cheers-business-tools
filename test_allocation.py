import unittest
from allocation import get_allocation_strategy, AllocationStrategy, ProportionalAllocationStrategy
from allocation import ROIAllocationStrategy, MinimumAllocationStrategy

class TestAllocationStrategies(unittest.TestCase):

    def setUp(self):
        # Sample products for testing
        self.products = [
            {
                "product_name": "Product A",
                "current_price": 25.0,
                "bulk_price": 20.0,
                "cases_on_hand": 10,
                "cases_per_year": 100,
                "bottles_per_case": 12
            },
            {
                "product_name": "Product B",
                "current_price": 45.0,
                "bulk_price": 40.0,
                "cases_on_hand": 5,
                "cases_per_year": 80,
                "bottles_per_case": 6
            },
            {
                "product_name": "Product C",
                "current_price": 14.0,
                "bulk_price": 10.0,
                "cases_on_hand": 0,
                "cases_per_year": 60,
                "bottles_per_case": 24
            }
        ]

        # Default parameters
        self.params = {
            "small_deal_minimum": 30,
            "bulk_deal_minimum": 60,
            "payment_terms": 30
        }

    def test_get_allocation_strategy(self):
        # Test getting different strategies
        self.assertIsInstance(get_allocation_strategy("proportional"), ProportionalAllocationStrategy)
        self.assertIsInstance(get_allocation_strategy("roi"), ROIAllocationStrategy)
        self.assertIsInstance(get_allocation_strategy("minimum"), MinimumAllocationStrategy)

        # Test default for unknown mode
        self.assertIsInstance(get_allocation_strategy("unknown"), ProportionalAllocationStrategy)

        # Test case insensitivity
        self.assertIsInstance(get_allocation_strategy("ROI"), ROIAllocationStrategy)

    def test_proportional_allocation(self):
        strategy = ProportionalAllocationStrategy()
        result = strategy.allocate(self.products, self.params)

        # Check if all products have bulk_quantity
        for product in result:
            self.assertIn("bulk_quantity", product)

        # Calculate total bulk quantity
        total_quantity = sum(p["bulk_quantity"] for p in result)

        # Check if total meets minimum
        self.assertGreaterEqual(total_quantity, self.params["bulk_deal_minimum"])

        # Check proportions
        total_annual = sum(p["cases_per_year"] for p in self.products)

        # Get the quantities
        product_a = next(p for p in result if p["product_name"] == "Product A")
        product_b = next(p for p in result if p["product_name"] == "Product B")
        product_c = next(p for p in result if p["product_name"] == "Product C")

        # Check that Product A has the highest allocation (it has highest annual sales)
        self.assertGreater(product_a["bulk_quantity"], product_b["bulk_quantity"])
        self.assertGreater(product_a["bulk_quantity"], product_c["bulk_quantity"])

        # Note: With rounding and minimum fulfillment, B and C might be very close
        # Just ensure their allocations are roughly proportional to their sales
        b_to_c_sales_ratio = product_b["cases_per_year"] / product_c["cases_per_year"]  # 80/60 = 1.33
        b_to_c_alloc_ratio = product_b["bulk_quantity"] / product_c["bulk_quantity"]

        # Allow some flexibility due to rounding and adjustments
        self.assertGreaterEqual(b_to_c_alloc_ratio * 1.5, b_to_c_sales_ratio)
        self.assertGreaterEqual(b_to_c_sales_ratio * 1.5, b_to_c_alloc_ratio)

    def test_minimum_days_stock_constraint(self):
        # Set minimum days of stock
        params = self.params.copy()
        params["min_days_stock"] = 30

        # Allocate with proportional strategy
        strategy = ProportionalAllocationStrategy()
        result = strategy.allocate(self.products, params)

        # Product C has 0 on hand, needs at least 5 cases to meet 30 days stock
        # (60 cases/year ÷ 365) × 30 days = ~5 cases
        product_c = next(p for p in result if p["product_name"] == "Product C")
        self.assertGreaterEqual(product_c["bulk_quantity"], 5)

    def test_roi_allocation(self):
        strategy = ROIAllocationStrategy()
        result = strategy.allocate(self.products, self.params)

        # Calculate total bulk quantity
        total_quantity = sum(p["bulk_quantity"] for p in result)

        # Check if total meets minimum
        self.assertGreaterEqual(total_quantity, self.params["bulk_deal_minimum"])

        # Check that product C (highest savings per case) gets priority allocation
        # Product C: $4 savings * 24 bottles = $96 per case
        # Product A: $5 savings * 12 bottles = $60 per case
        # Product B: $5 savings * 6 bottles = $30 per case
        product_c = next(p for p in result if p["product_name"] == "Product C")
        product_a = next(p for p in result if p["product_name"] == "Product A")
        product_b = next(p for p in result if p["product_name"] == "Product B")

        # Product C should get a higher allocation relative to its annual sales
        c_proportion = product_c["bulk_quantity"] / product_c["cases_per_year"]
        a_proportion = product_a["bulk_quantity"] / product_a["cases_per_year"]

        self.assertGreaterEqual(c_proportion, a_proportion)

    def test_minimum_allocation(self):
        # The minimum allocation strategy should behave like proportional
        proportional = ProportionalAllocationStrategy()
        minimum = MinimumAllocationStrategy()

        result_prop = proportional.allocate(self.products, self.params)
        result_min = minimum.allocate(self.products, self.params)

        # Both should allocate the same total
        total_prop = sum(p["bulk_quantity"] for p in result_prop)
        total_min = sum(p["bulk_quantity"] for p in result_min)

        self.assertEqual(total_prop, total_min)

    def test_cap_maximum_inventory(self):
        # Test with a product that would exceed the cap
        products = [
            {
                "product_name": "Small Volume Product",
                "current_price": 25.0,
                "bulk_price": 20.0,
                "cases_on_hand": 5,
                "cases_per_year": 10,  # ~0.027 cases per day
                "bottles_per_case": 12,
                "bulk_quantity": 20  # This would create ~740 days of stock!
            }
        ]

        strategy = ProportionalAllocationStrategy()
        result = strategy._cap_maximum_inventory(products)

        # Max should be 90 days * 0.027 cases/day = ~2.5 cases
        # Plus 5 on hand = ~7.5 cases, but we cap to (90 days * 0.027) - 5 = ~2.5 cases
        self.assertLessEqual(result[0]["bulk_quantity"], 3)

    def test_round_preserving_total(self):
        # Test rounding while preserving total
        products = [
            {"product_name": "A", "bulk_quantity": 10.7},
            {"product_name": "B", "bulk_quantity": 20.2},
            {"product_name": "C", "bulk_quantity": 30.1}
        ]

        strategy = ProportionalAllocationStrategy()
        result = strategy._round_preserving_total(products, 61)

        # Check each product's rounded quantity
        self.assertEqual(result[0]["bulk_quantity"], 11)  # 10.7 rounded up
        self.assertEqual(result[1]["bulk_quantity"], 20)  # 20.2 rounded down
        self.assertEqual(result[2]["bulk_quantity"], 30)  # 30.1 rounded down

        # Check total is preserved
        total = sum(p["bulk_quantity"] for p in result)
        self.assertEqual(total, 61)

if __name__ == '__main__':
    unittest.main()
