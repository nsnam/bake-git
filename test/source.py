import unittest
# hack to save ourselves from having to use PYTHONPATH
import sys
import os

from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger

from bake.ModuleSource import ModuleSource
from bake.ModuleSource import BazaarModuleSource
from bake.ModuleSource import CvsModuleSource
from bake.ModuleSource import GitModuleSource
from bake.ModuleSource import MercurialModuleSource
from bake.ModuleSource import InlineModuleSource
from bake.ModuleSource import NoneModuleSource

class TestModuleSource(unittest.TestCase):
    """Tests cases for the Module Environment Class."""
    
    def setUp(self):
        """Common set Up environment, available for all tests."""
        pathname = os.path.dirname("/tmp/")  
        logger = StdoutModuleLogger();
        logger.set_verbose(1)
        self._env = ModuleEnvironment(logger, pathname, pathname, pathname)
       
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None
 
   
    def test_mercurial(self):
        """Tests the MercurialModuleSource class. """
        
        # it first needs to be able to create the class otherwise will not be
        # able to do anything else
        mercurial = ModuleSource.create("mercurial")
        self.assertNotEqual(mercurial, None)
        
        # Verifies if the system has the mercurial installed, if not does not
        # even worth continuing
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)

        mercurial.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        testResult = mercurial.download(self._env)
        
        # if something goes wrong it should rise an exception so, None means 
        # everything is OK
        self.assertEqual(testResult, None)


# main call for the tests        
if __name__ == '__main__':
    unittest.main()
