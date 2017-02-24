"""
Runs all integration tests
"""
if __name__ == "__main__":
    import glob
    import unittest

    testSuite = unittest.TestSuite()
    test_file_strings = glob.glob('test_*.py')
    testmodules = [string[0:len(string) - 3] for string in test_file_strings]

    suite = unittest.TestSuite()

    for t in testmodules:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

    unittest.TextTestRunner().run(suite)
