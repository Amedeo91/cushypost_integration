import os
import unittest


dir_path = os.path.dirname(os.path.realpath(__file__))
suite = unittest.TestLoader().discover(dir_path, pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=3).run(suite)
print(result)
assert result.wasSuccessful()
