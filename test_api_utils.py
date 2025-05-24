import unittest
import numpy as np
from api_utils import validate_required_fields, convert_numpy_types

class TestApiUtils(unittest.TestCase):
    def test_validate_required_fields_pass(self):
        data = {'a': 1, 'b': 'x', 'c': [1,2,3]}
        try:
            validate_required_fields(data, ['a', 'b', 'c'])
        except ValueError:
            self.fail('validate_required_fields raised ValueError unexpectedly!')

    def test_validate_required_fields_fail(self):
        data = {'a': 1, 'b': '', 'c': None}
        with self.assertRaises(ValueError):
            validate_required_fields(data, ['a', 'b', 'c'])

    def test_convert_numpy_types(self):
        obj = {
            'a': np.int32(5),
            'b': np.float64(3.14),
            'c': [np.int64(2), 7],
            'd': {'x': np.float32(1.23)},
            'e': 'native',
        }
        result = convert_numpy_types(obj)
        self.assertEqual(result['a'], 5)
        self.assertEqual(result['b'], 3.14)
        self.assertEqual(result['c'][0], 2)
        self.assertEqual(result['c'][1], 7)
        self.assertEqual(result['d']['x'], 1.23)
        self.assertEqual(result['e'], 'native')

if __name__ == '__main__':
    unittest.main()
