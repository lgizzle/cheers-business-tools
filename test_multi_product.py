import unittest
import os
from multi_product_calculator import MultiProductBuyingCalculator

class TestMultiProductCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = MultiProductBuyingCalculator()
        self.calc.set_parameters(30, 60, 30)
        self.calc.add_product(
            "Test Product",
            10.0,
            8.0,
            0,
            120,
            12,
            bulk_quantity=60,
        )

    def tearDown(self):
        # Clean up any test scenario file
        filename = os.path.join('scenarios', 'unittestscenario.json')
        if os.path.exists(filename):
            os.remove(filename)

    def test_calculation_returns_values(self):
        results = self.calc.calculate()
        self.assertEqual(len(results['products']), 1)
        prod = results['products'][0]
        self.assertIn('roi', prod)
        self.assertTrue(prod['roi'] >= 0)

    def test_save_load_delete_scenario(self):
        name = 'UnitTestScenario'
        file_path = self.calc.save_scenario(name)
        self.assertTrue(os.path.exists(file_path))

        loader = MultiProductBuyingCalculator()
        self.assertTrue(loader.load_scenario(name))
        self.assertEqual(len(loader.products), 1)

        self.assertTrue(loader.delete_scenario(name))
        self.assertFalse(os.path.exists(file_path))

if __name__ == '__main__':
    unittest.main()
