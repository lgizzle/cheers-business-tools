import unittest
import calculator

class TestCalculator(unittest.TestCase):

    def test_calculate_savings_per_case(self):
        # Test with regular values
        self.assertEqual(calculator.calculate_savings_per_case(25.0, 23.5, 12), 18.0)
        # Test with zero difference
        self.assertEqual(calculator.calculate_savings_per_case(25.0, 25.0, 12), 0.0)
        # Test with negative difference (shouldn't happen in real life, but test anyway)
        self.assertEqual(calculator.calculate_savings_per_case(23.0, 25.0, 12), -24.0)

    def test_calculate_total_savings(self):
        # Test with regular values
        self.assertEqual(calculator.calculate_total_savings(25.0, 23.5, 10, 12), 180.0)
        # Test with zero quantity
        self.assertEqual(calculator.calculate_total_savings(25.0, 23.5, 0, 12), 0.0)
        # Test with zero difference
        self.assertEqual(calculator.calculate_total_savings(25.0, 25.0, 10, 12), 0.0)

    def test_calculate_days_of_stock(self):
        # Test with regular values
        self.assertAlmostEqual(calculator.calculate_days_of_stock(10, 100), 36.5, places=1)
        # Test with zero cases per year
        self.assertEqual(calculator.calculate_days_of_stock(10, 0), 0)
        # Test with zero on-hand
        self.assertEqual(calculator.calculate_days_of_stock(0, 100), 0)

    def test_calculate_days_of_stock_after_purchase(self):
        # Test with regular values
        self.assertAlmostEqual(calculator.calculate_days_of_stock_after_purchase(10, 20, 100), 109.5, places=1)
        # Test with zero cases per year
        self.assertEqual(calculator.calculate_days_of_stock_after_purchase(10, 20, 0), 0)
        # Test with zero on-hand but positive purchase
        self.assertAlmostEqual(calculator.calculate_days_of_stock_after_purchase(0, 20, 100), 73.0, places=1)

    def test_calculate_daily_cases(self):
        # Test with regular values
        self.assertAlmostEqual(calculator.calculate_daily_cases(365), 1.0, places=1)
        self.assertAlmostEqual(calculator.calculate_daily_cases(730), 2.0, places=1)
        # Test with zero
        self.assertEqual(calculator.calculate_daily_cases(0), 0)

    def test_calculate_holding_time(self):
        # Test with regular values
        self.assertAlmostEqual(calculator.calculate_holding_time(10, 365), 10.0, places=1)
        # Test with zero cases per year
        self.assertEqual(calculator.calculate_holding_time(10, 0), 0)
        # Test with max days limit
        self.assertEqual(calculator.calculate_holding_time(1000, 1, 30), 30)

    def test_calculate_peak_investment(self):
        # Test with zero daily cases (no depletion)
        # 25.0 (price) * 12 (bottles) * 10 (cases) = 3000.0
        self.assertEqual(
            calculator.calculate_peak_investment(25.0, 12, 10, 0, 30),
            3000.0
        )

        # Test with daily cases that partially deplete during payment terms
        # Initial cost: 3000.0
        # Daily depletion: 0.5 * 25.0 * 12 = 150.0
        # 10 day depletion: 150.0 * 10 = 1500.0
        # Remaining: 3000.0 - 1500.0 = 1500.0
        self.assertEqual(
            calculator.calculate_peak_investment(25.0, 12, 10, 0.5, 10),
            1500.0
        )

        # Test where all inventory is depleted during payment terms
        # Initial cost: 3000.0
        # Days to deplete: 10 / 0.5 = 20 days
        # Payment terms: 30 days
        # Depletion: min(30, 20) * 150.0 = 20 * 150.0 = 3000.0
        # Remaining: 3000.0 - 3000.0 = 0.0
        self.assertEqual(
            calculator.calculate_peak_investment(25.0, 12, 10, 0.5, 30),
            0.0
        )

    def test_calculate_daily_carrying_cost(self):
        # Test with regular values
        self.assertAlmostEqual(
            calculator.calculate_daily_carrying_cost(1000, 0.08),
            1000 * 0.08 / 365, places=4
        )
        # Test with zero investment
        self.assertEqual(calculator.calculate_daily_carrying_cost(0, 0.08), 0)

    def test_calculate_average_investment(self):
        # Test with regular values
        # 25.0 (price) * 12 (bottles) * 10 (cases) * 20 (days to sell) / (2 * 365) = 82.19
        self.assertAlmostEqual(
            calculator.calculate_average_investment(25.0, 12, 10, 0.5),
            82.19, places=2
        )

        # Test with zero daily cases
        # With zero daily cases, we return half the initial investment
        self.assertEqual(
            calculator.calculate_average_investment(25.0, 12, 10, 0),
            1500.0
        )

    def test_calculate_roi(self):
        # Test with regular values
        self.assertEqual(calculator.calculate_roi(180, 1500), 0.12)
        # Test with zero investment
        self.assertEqual(calculator.calculate_roi(180, 0), 0)

    def test_calculate_annualized_roi(self):
        # Test with regular values
        self.assertAlmostEqual(calculator.calculate_annualized_roi(0.12, 30), 1.46, places=2)
        # Test with zero holding time
        self.assertEqual(calculator.calculate_annualized_roi(0.12, 0), 0)
        # Test with zero ROI
        self.assertEqual(calculator.calculate_annualized_roi(0, 30), 0)

    def test_calculate_minimum_stock_needed(self):
        # Test when current stock is below minimum
        self.assertEqual(calculator.calculate_minimum_stock_needed(5, 0.5, 14), 2)
        # Test when current stock meets minimum
        self.assertEqual(calculator.calculate_minimum_stock_needed(7, 0.5, 14), 0)
        # Test with zero daily cases
        self.assertEqual(calculator.calculate_minimum_stock_needed(5, 0, 14), 0)
        # Test with None min_days_stock
        self.assertEqual(calculator.calculate_minimum_stock_needed(5, 0.5, None), 0)

    def test_calculate_maximum_stock(self):
        # Test with regular values
        self.assertEqual(calculator.calculate_maximum_stock(0.5, 90, 5), 40)
        # Test with zero daily cases
        self.assertEqual(calculator.calculate_maximum_stock(0, 90, 5), 10)
        # Test when current stock exceeds max
        self.assertEqual(calculator.calculate_maximum_stock(0.5, 90, 50), 0)

if __name__ == '__main__':
    unittest.main()
