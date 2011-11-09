import unittest
# hack to save ourselves from having to use PYTHONPATH
import sys
import os
import commands
import re

from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger
from bake.Exceptions import TaskError

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
        self._logger = StdoutModuleLogger();
        self._logger.set_verbose(1)
        self._env = ModuleEnvironment(self._logger, pathname, pathname, pathname)
       
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None
 
   

    def removeTemporaryData(self, command, dir):
        try:
            self._env.run(command, dir)
        except Exception as inst:
            print (inst)     # the exception instance
            self.fail("Could not clean up the temporary directory command %s over directory %s failed" % (command, dir))

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
        self._logger.set_current_module(self._env._module_name)
        
        #clean up the environment, just to be safe
        self.removeTemporaryData(["/bin/rm", "-rf", "bake"], "/tmp")
        testResult = mercurial.download(self._env)
        
        # if something goes wrong it should rise an exception so, None means 
        # everything is OK
        self.assertEqual(testResult, None)
        
        #after the test, clean the environment
        self.removeTemporaryData(["rm", "-rf", "bake"], "/tmp")
       
        # download a specific version
        mercurial.attribute("revision").value = "63"
        testResult = mercurial.download(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/bake;hg summary')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "63")

        # makes an update of the version to the last version
        mercurial.attribute("revision").value = "64"
        testResult = mercurial.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/bake;hg summary')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "64")
        
        # Verifies the update to the tip
        mercurial.attribute("revision").value = "tip"
        testResult = mercurial.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/bake;hg log')
        versionRepository = re.compile('\d+').search(testStatus).group()
        testStatus = commands.getoutput('cd /tmp/bake;hg summary')
        versionDownloaded = re.compile('\d+').search(testStatus).group()
        self.assertEqual(versionRepository, versionDownloaded)
        
        self.removeTemporaryData(["rm", "-rf", "bake"], "/tmp")
          
        # Not http should give you a TaskError exception
        mercurial.attribute("url").value = "code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        self._logger.set_current_module(self._env._module_name)
        
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was not problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        self.removeTemporaryData(["rm", "-rf", "bake"], "/tmp")
 
         # Try to get a wrong version
        mercurial.attribute("revision").value = "-44"
        try:
            testResult = mercurial.download(self._env)
            self.fail("Try to correct this, the version is wrong the file is not downloaded, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

  
        # last clean up
        self.removeTemporaryData(["rm", "-rf", "bake"], "/tmp")


# main call for the tests        
if __name__ == '__main__':
    unittest.main()
