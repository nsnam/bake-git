import unittest
# hack to save ourselves from having to use PYTHONPATH
import sys
import os

from bake.ModuleEnvironment import ModuleEnvironment


sys.path.append(os.path.join (os.getcwd(), '..'))

class TestModuleEnvironment(unittest.TestCase):
    """Tests cases for the Module Environment Class."""
    
    def setUp(self):
        """Common set Up environment, available for all tests."""
        pathname = os.path.dirname(sys.argv[0])  
        self._env = ModuleEnvironment(None, pathname, pathname, pathname)
        
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None

   
    # TODO: see if the tests work in other OS environments, I would guess not
    # to be honest I am not even sure bake would work on other OS either
    # TODO:2 Test the search on the current dir/bin 
    def test_program_location(self):
        """Tests the _program_location method of Class ModuleEnvironment. """
        
        # searches for link, on unix systems, normally java would be a soft link
        testResult = self._env._program_location("tar");
        self.assertNotEqual(testResult, None)

        # specific program flow, when the directory is passed as parameter
        knownPlacement = "/bin/sh"
        testResult = self._env._program_location(knownPlacement);
        self.assertEqual(testResult, knownPlacement)

        # searches for link, on unix systems, normally java would be a soft 
        # link at least the first one in the /usr/bin, for example
        testResult = self._env._program_location("java");
        self.assertNotEqual(testResult, None)

        # Valid file, but not executable
        knownPlacement = "/etc/passwd"
        testResult = self._env._program_location(knownPlacement);
        self.assertEqual(testResult, None)

       # a program that do not exist should return None
        knownPlacement = "/bin/NotAProgramTestElement"
        testResult = self._env._program_location(knownPlacement);
        self.assertEqual(testResult, None)

        # a program that do not exist, in any directory, should return None
        knownPlacement = "NotAProgramTestElement"
        testResult = self._env._program_location(knownPlacement);
        self.assertEqual(testResult, None)

        # valid program in a valid directory, but a wrong one
        knownPlacement = "/tmp/sh"
        testResult = self._env._program_location(knownPlacement);
        self.assertEqual(testResult, None)

    # def check_program(self, program, version_arg = None,
    #                   version_regexp = None, version_required = None,
    #                   match_type=HIGHER):
    # TODO: Test the version parameters of the executable
    def test_check_program(self):
        """Tests the _check_program method of Class ModuleEnvironment. """
        
        # specific existent program
        programToCheck = "java"
        testResult = self._env.check_program(programToCheck);
        self.assertTrue(testResult)
  
        # specific inexistent program
        programToCheck = "/notADirectory/NotAProgramTestElement"
        testResult = self._env.check_program(programToCheck);
        self.assertFalse(testResult)
     
        # specific existent program version
#        programToCheck = "gcc"
#        testResult = self._env.check_program(programToCheck,"--version", "(\d+(\.\d+)*)+", "2.4");
#        self.assertTrue(testResult)
        

# main call for the tests        
if __name__ == '__main__':
    unittest.main()
