import unittest
import os
import shutil
from scenario_utils import save_scenario_file, load_scenario_file, delete_scenario_file, list_scenario_files

class TestScenarioUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = 'test_scenarios'
        os.makedirs(self.test_dir, exist_ok=True)
        self.scenario_name = 'TestScenario'
        self.products = [{'name': 'A', 'qty': 1}]
        self.small_deal_minimum = 10
        self.bulk_deal_minimum = 20
        self.payment_terms = 30

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_and_load_scenario(self):
        save_scenario_file(self.test_dir, self.scenario_name, self.products, self.small_deal_minimum, self.bulk_deal_minimum, self.payment_terms)
        loaded = load_scenario_file(self.test_dir, self.scenario_name)
        self.assertEqual(loaded['products'], self.products)
        self.assertEqual(loaded['small_deal_minimum'], self.small_deal_minimum)
        self.assertEqual(loaded['bulk_deal_minimum'], self.bulk_deal_minimum)
        self.assertEqual(loaded['payment_terms'], self.payment_terms)

    def test_list_and_delete_scenario(self):
        save_scenario_file(self.test_dir, self.scenario_name, self.products, self.small_deal_minimum, self.bulk_deal_minimum, self.payment_terms)
        scenarios = list_scenario_files(self.test_dir)
        self.assertIn(self.scenario_name, [s.replace('_', ' ').title() for s in scenarios])
        deleted = delete_scenario_file(self.test_dir, self.scenario_name)
        self.assertTrue(deleted)
        scenarios = list_scenario_files(self.test_dir)
        self.assertNotIn(self.scenario_name, [s.replace('_', ' ').title() for s in scenarios])

if __name__ == '__main__':
    unittest.main()
