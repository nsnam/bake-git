import unittest
import sys
import os
import commands
import re

from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger
from bake.Exceptions import TaskError

from bake.ModuleSource import ModuleSource

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

    def executeCommand(self, command, dir):
        """Executes the given command, catching the exceptions."""
        
        try:
            self._env.run(command, dir)
        except Exception as inst:
            print (inst)     # the exception instance
            self.fail("Could not execute command %s over directory %s failed" % (command, dir))

    def test_generalFailures(self):
        """Tests Some general failures that could happen in the Module Source. """
        
        #Verifies the return of the creation of a non existent module
        module = ModuleSource.create("NonExistentModule")
        self.assertEqual(module, None)

    def test_archiveModuleSource(self):
        """Tests the ArchiveModuleSource class. """
        
        # it first needs to be able to create the class otherwise will not be
        # able to do anything else
        archive = ModuleSource.create("archive")
        self.assertNotEqual(archive, None)
        self.assertEqual(archive.name(), "archive")
        
        # Verifies if the system has the right tools installed, if not does not
        # even worth continuing
        
        # no file was declared yet, so the issue should be False
        testResult = archive.check_version(self._env)
        self.assertFalse(testResult)    
       
        # Unknown file type
        archive.attribute("url").value = "http://JustATest.com/File.unknownFileType"
        testResult = archive.check_version(self._env)
        self.assertFalse(testResult, "There is no tool to handle the target extension, the result should be false")    
        # zip
        archive.attribute("url").value = "http://JustATest.com/File.zip"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "unzip is not present on the system")    
        # rar
        archive.attribute("url").value = "http://JustATest.com/File.rar"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "unrar is not present on the system")    
        # tar
        archive.attribute("url").value = "http://JustATest.com/File.tar"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
        # tar.Z
        archive.attribute("url").value = "http://JustATest.com/File.tar.Z"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
        # tar.bz2
        archive.attribute("url").value = "http://JustATest.com/File.tar.bz2"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
        # tar.gz
        archive.attribute("url").value = "http://read.cs.ucla.edu/click/click-1.8.0.tar.gz"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
      
        
        self._env._module_name="click-1.8.0"
        self._logger.set_current_module(self._env._module_name)
        
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0.tar.gz"], "/tmp")
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0"], "/tmp")
        testResult = archive.download(self._env)
        
        # if something goes wrong it should rise an exception so, None means 
        # everything is OK
        self.assertEqual(testResult, None)
        
        # verifies that files are really there after the download
        testStatus = commands.getoutput('ls /tmp/click-1.8.0.tar.gz')
        self.assertEqual("/tmp/click-1.8.0.tar.gz", testStatus)
 
        testStatus = commands.getoutput('ls -d /tmp/click-1.8.0')
        self.assertEqual("/tmp/click-1.8.0", testStatus)
      
        #after the test, clean the environment
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0.tar.gz"], "/tmp")
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0"], "/tmp")

        # Searches for a valid file into an inexistent repository
        archive.attribute("url").value = "http://non.existent.host.com/click-1.8.0.tar.gz"
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, and the server does not exist. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # Try to download to a directory that the user has no permission
        archive.attribute("url").value = "http://read.cs.ucla.edu/click/click-1.8.0.tar.gz"
        testStatus = commands.getoutput('touch /tmp/click-1.8.0;chmod 000 /tmp/click-1.8.0')    
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, the user has no permission over the target directory. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/click-1.8.0; rm -f /tmp/click-1.8.0')

        # try to download to a non existent directory        
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, target directory does not exist and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')
 
        # no protocol download url gives you an error
        archive.attribute("url").value = "read.cs.ucla.edu/click/click-1.8.0.tar.gz"
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, the user didn't add the protocol for the url. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # just to be sure that the update does nothing
        testResult = archive.update(self._env)
        self.assertEqual(testResult, None)

        # Oddly enough, when the user has no permission in the target 
        # directory the system returns no error Right now I have no idea how
        # to fix it, or IF we should try to fix anyway.
#        self._env._sourcedir = "/tmp"
#        testStatus = commands.getoutput('mkdir /tmp/click-1.8.0;chmod 000 /tmp/click-1.8.0')       
#        try:
#            testResult = archive.download(self._env)
#            self.fail("There was not problem, the user has no permission over the target directory. ")
#        except TaskError as e:
#            self.assertNotEqual(e._reason, None)    
#            self.assertEqual(testResult, None)
#
#        testStatus = commands.getoutput('chmod 755 /tmp/click-1.8.0; rm -rf /tmp/click-1.8.0')


    def test_mercurial(self):
        """Tests the MercurialModuleSource class. """
        
        # it first needs to be able to create the class otherwise will not be
        # able to do anything else
        mercurial = ModuleSource.create("mercurial")
        self.assertNotEqual(mercurial, None)
        self.assertEqual(mercurial.name(), "mercurial")
       
        # Verifies if the system has the mercurial installed, if not does not
        # even worth continuing
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)

        mercurial.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        self._logger.set_current_module(self._env._module_name)
        
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "bake"], "/tmp")
        testResult = mercurial.download(self._env)
        
        # if something goes wrong it should rise an exception so, None means 
        # everything is OK
        self.assertEqual(testResult, None)
        
        #after the test, clean the environment
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
       
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
        
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
          
        # Not http should give you a TaskError exception
        mercurial.attribute("url").value = "code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        self._logger.set_current_module(self._env._module_name)
        
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was no problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
        testStatus = commands.getoutput('mkdir /tmp/bake;chmod 000 /tmp/bake')    
        mercurial.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was no problem and the user has no permission over the directory. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('chmod 755 /tmp/bake')    
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
        
        # try to download to a non existent directory
        # mercurial cretes the directory
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        testResult = mercurial.download(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
          
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')

 
        # Try to get a wrong version, there is a but in the mercurial
        # that permits negative revisions, such as -34, for example, 
        # however bigger than the tip version gives an error
        mercurial.attribute("revision").value = "9999999"
        try:
            testResult = mercurial.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
  
        # last clean up
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")

    def test_bazaar(self):
        """Tests the BazaarModuleSource class. """
        
        # checks if can create the class 
        bazaar = ModuleSource.create("bazaar")
        self.assertNotEqual(bazaar, None)
        self.assertEqual(bazaar.name(), "bazaar")
       
        # Verifies if Bazaar is installed
        testResult = bazaar.check_version(self._env)
        self.assertTrue(testResult)

        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        self._env._module_name="pybindgen"
        self._logger.set_current_module(self._env._module_name)
        
        ##### Normal Flow test
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "pybindgen"], "/tmp")
        testResult = bazaar.download(self._env)
        
        # None means everything was OK, since there were no exceptions
        self.assertEqual(testResult, None)
        
        testStatus = commands.getoutput('cd /tmp/pybindgen; bzr log')
        lastVersion = re.compile('\d+').search(testStatus).group()

        #after the test, clean the environment
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
       
        # download a specific version
        bazaar.attribute("revision").value = "794"
        testResult = bazaar.download(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/pybindgen; bzr log')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "794")

        # makes an update of the version to a latter version
        bazaar.attribute("revision").value = "795"
        testResult = bazaar.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/pybindgen; bzr log')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "795")
        
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
          
        # Wrong repository
        bazaar.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        self._logger.set_current_module(self._env._module_name)
        
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
 
        # No protocol http/https
        bazaar.attribute("url").value = "launchpad.net/pybindgen"
        bazaar.attribute("revision").value = None
        self._logger.set_current_module(self._env._module_name)
        
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
        
        testStatus = commands.getoutput('mkdir /tmp/pybindgen;chmod 000 /tmp/pybindgen')    
        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem and the user has no permission over the directory. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('chmod 755 /tmp/pybindgen')    
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
        
        # try to download to a non existent directory        
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem, target directory does not exist and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # try to download to a directory where the user has no permission    
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')
 
        # returns to the original state
        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        self._env._sourcedir = "/tmp"

        # Try to get an unavailable version
        bazaar.attribute("revision").value = str(int(lastVersion) + 1)
        try:
            testResult = bazaar.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
  
        # verifies the update to a inexistent version
        bazaar.attribute("revision").value = None
        testResult = bazaar.download(self._env)
        self.assertEqual(testResult, None)
                    
        # Invalid argument, it is int and should be string
        bazaar.attribute("revision").value = -60
        try:
            testResult = bazaar.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # can not go for a negative version
        bazaar.attribute("revision").value = str(-60)
        try:
            testResult = bazaar.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
  
        # last clean up
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")


# TODO: 
#    Tests for CvsModuleSource
#              GitModuleSource
#              InlineModuleSource (?!?!?!)

# main call for the tests        
if __name__ == '__main__':
    unittest.main()
