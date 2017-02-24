"""
Runs all available tests for this project
"""
if __name__ == "__main__":
    import glob
    import unittest

    testSuite = unittest.TestSuite()
    test_file_strings = glob.glob('*/test_*.py')

    # convert file path into module path
    testmodules = [s[0:len(s) - 3].replace("\\", ".").replace('/', '.')
                   for s in test_file_strings]

    suite = unittest.TestSuite()

    for t in testmodules:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

    unittest.TextTestRunner().run(suite)
