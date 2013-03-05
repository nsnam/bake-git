'''
BakeTestSuite.py

Calls all the available bake tests in sequence.
'''

import glob
import unittest

# finds the test files, should start with Test and finish with .py
test_file_strings = glob.glob('Test*.py')

#test_file_strings = ["TestModuleSource.py"]
# puts the file in the format of modules to be imported
module_strings = ["test."+str[0:len(str)-3] for str in test_file_strings]

# search for the tests on the modules
suites = [unittest.defaultTestLoader.loadTestsFromName(str) for str 
          in module_strings]

# adds the tests on the suite to be run
testSuite = unittest.TestSuite(suites)

# runs the full tests
text_runner = unittest.TextTestRunner().run(testSuite)
