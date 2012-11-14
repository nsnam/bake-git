import unittest
# hack to save ourselves from having to use PYTHONPATH
import sys
import os
import commands
import re

from bake.Configuration import Configuration
from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger
from bake.ModuleSource import ModuleSource
from bake.Exceptions import TaskError
from bake.Bake import Bake


sys.path.append(os.path.join (os.getcwd(), '..'))

def compensate_third_runner():
    """ Compensates the name of the file, if a third party program is
        calling bake, as it is the case for running the tests from 
        inside eclipse."""
    fileName = sys.argv[0]
    if len(sys.argv) > 1:
        fileName = sys.argv[1]
    return fileName

class TestBake(unittest.TestCase):
    """Tests cases for the main Bake Class."""

           
    def setUp(self):
        """Common set Up environment, available for all tests."""
        pathname = os.path.dirname("/tmp/source/")  
        self._logger = StdoutModuleLogger();
        self._logger.set_verbose(1)
        self._env = ModuleEnvironment(self._logger, pathname, pathname, pathname)
#        testStatus = commands.getoutput('cp ' + pathname + '/bakefile.xml /tmp/.')
        testStatus = commands.getoutput('chmod 755 /tmp/source')
        testStatus = commands.getoutput('rm -rf /tmp/source')

        
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None
        pathname = os.path.dirname("/tmp/source")  
#        pathname = os.path.dirname(compensate_third_runner())  
        testStatus = commands.getoutput('rm -f ' + pathname +'/bakefile.xml')
        testStatus = commands.getoutput('chmod 755 /tmp/source')
        testStatus = commands.getoutput('rm -rf /tmp/source')
        testStatus = commands.getoutput('mv bc.xml bakeconf.xml ')
        testStatus = commands.getoutput('mv bf.xml bakefile.xml ')
        testStatus = commands.getoutput('mv ~/.bakerc_saved ~/.bakerc')

    def Dtest_simple_proceedings(self):
        """Tests the _check_source_code method of Class Bake. """

        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        mercurial.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        self._env._module_dir="bake"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)
        self.assertFalse(testResult)

        testStatus = commands.getoutput('cd /tmp/source/bake;./bake.py configure -e openflow-ns3')
        self.assertEquals(testStatus, "", "Should have worked the download of the code")
        testStatus = commands.getoutput('cd /tmp/source/bake;./bake.py download')
        self.assertTrue(testStatus.endswith(">> Download openflow-ns3 - OK"), 
                        "Should have worked the download of the code")
        testStatus = commands.getoutput('cd /tmp/source/bake;./bake.py build')
        self.assertTrue(testStatus.endswith(">> Built openflow-ns3 - OK"), 
                        "Should have worked the build of the code")
  
 
    def Dtest_read_resource_file(self):
        """Tests the _read_resource_file method of Class Bake."""
        
        configuration = Configuration("bakefile.xml")
        testStatus,testMessage = commands.getstatusoutput('mv ~/.bakerc ~/.bakerc_saved')
        self.assertTrue(testStatus==0 or testStatus==256,"Couldn't move the ressource file!")
        bake = Bake()
        
        testResult = bake._read_resource_file(configuration)
        self.assertFalse(testResult,"Shouldn't find a configuration!")
        
        testStatus = commands.getoutput('touch ~/.bakerc')
        testResult = bake._read_resource_file(configuration)
        self.assertFalse(testResult,"Configuration should be empty!")

        testStatus = commands.getoutput('cp ./bakeTest.rc ~/.bakerc')
        testResult = bake._read_resource_file(configuration)
        self.assertTrue(testResult[0].name=="my-ns3","Shouldn't find a configuration!")
        
        testStatus,testMessage = commands.getstatusoutput('mv ~/.bakerc_saved ~/.bakerc')
      
    def Dtest_save_resource_configuration(self):
        """Tests the _save_resource_configuration method of Class Bake."""
        
        pathname = os.path.dirname(compensate_third_runner())  
        if not pathname:
            pathname="."
        testStatus = commands.getoutput('python ' + pathname + 
                                        '/../bake.py -f ./ttt.xml configure ' 
                                        '--enable=openflow-ns3 ' 
                                        '--sourcedir=/tmp/source ' 
                                        '--installdir=/tmp/source')

        configuration = Configuration("./ttt.xml")
        configuration.read()
        testStatus,testMessage = commands.getstatusoutput('mv ~/.bakerc ~/.bakerc_saved')
        self.assertTrue(testStatus==0 or testStatus==256,
                        "Couldn't move the resource file!")
        fileName = os.path.join(os.path.expanduser("~"), ".bakerc")
        testStatus,testMessage = commands.getstatusoutput('rm -rf ./ttt.xml')
        bake = Bake()
        
        testResult = bake._save_resource_configuration(configuration)
        self.assertFalse(testResult,"Should have write configuration!")
        self.assertTrue(os.path.isfile(fileName), "Didn't create the .bakerc file")
        fin = open(fileName, "r")
        string = fin.read()
        fin.close()
        self.assertTrue("last" in string, "Didn't save the last configuration")
        self.assertTrue("openflow-ns3" in string, 
                        "Didn't save the last configuration")
        
        testStatus = commands.getoutput('cp ./bakeTest.rc ~/.bakerc')
        fin = open(fileName, "r")
        string = fin.read()
        fin.close()
        self.assertFalse("last" in string, "Did find last in the configuration")
        
        testResult = bake._save_resource_configuration(configuration)
        self.assertFalse(testResult,"Should have write configuration!")
        self.assertTrue(os.path.isfile(fileName), "Didn't create the .bakerc file")
        fin = open(fileName, "r")
        string = fin.read()
        fin.close()
        self.assertTrue("<predefined name=\"last\">" in string, "Didn't save the last configuration")
        self.assertTrue("<enable name=\"openflow-ns3\"/>" in string, 
                        "Didn't save the last configuration")


        testStatus,testMessage = commands.getstatusoutput('mv ~/.bakerc_saved ~/.bakerc')
  
   
    def Dtest_check_source_code(self):
        """Tests the _check_source_code method of Class Bake. """

        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        
        pathname = os.path.dirname(compensate_third_runner())  
        if not pathname:
            pathname="."
        testStatus = commands.getoutput('python ' + pathname + 
                                        '/../bake.py configure ' 
                                        '--enable=openflow-ns3 ' 
                                        '--sourcedir=/tmp/source ' 
                                        '--installdir=/tmp/source')

        mercurial.attribute("url").value = "http://code.nsnam.org/bhurd/openflow"
        self._env._module_name="openflow-ns3"
        self._env._module_dir="openflow-ns3"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)

        bake = Bake()
        config = "bakefile.xml" #bakefile.xml"
        args = []
        parser = bake._option_parser('build')
        parser.add_option('-j', '--jobs', 
                          help='Allow N jobs at once. Default is 1.',
                          type='int', action='store', dest='jobs', default=1)
        parser.add_option("--debug", action="store_true", 
                          dest="debug", default=True, 
                          help="Should we enable extra Bake debugging output ?")
        (options, args_left) = parser.parse_args(args)
#        bake.setMainOptions(options)
        Bake.main_options = options
        
        # Tests typical case, the module is there
        testResult = bake._check_source_code(config, options);
        self.assertEqual(testResult, None)
 
        # if the user has no permission to see the file
        testStatus = commands.getoutput('chmod 000 /tmp/source')
        testResult=None
        testResult = bake._check_source_code(config, options);
        self.assertFalse(testResult, None)    
        
        testStatus = commands.getoutput('chmod 755 /tmp/source')
           
        # if the folder is not where it should be
        testStatus = commands.getoutput('rm -rf /tmp/source')
        testResult=None
        testResult = bake._check_source_code(config, options);
        self.assertFalse(testResult, None)    
             

    def Dtest_check_build_version(self):
        """Tests the _check_source_code method of Class Bake. """

        # Environment settings        
        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        
        self._env._debug = True
        pathname = os.path.dirname(compensate_third_runner()) 
        if not pathname:
            pathname="."
 
        testStatus = commands.getoutput('python ' + pathname + 
                                        '/../bake.py configure' 
                                        ' --enable=openflow-ns3' 
                                        ' --sourcedir=/tmp/source' 
                                        ' --installdir=/tmp/source')

        mercurial.attribute("url").value = "http://code.nsnam.org/bhurd/openflow"
        self._env._module_name="openflow-ns3"
        self._env._module_dir="openflow-ns3"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)
#        try:
#            testResult = mercurial.download(self._env)
#            self.fail("The directory does not exist, this shouldn't work")
#        except TaskError as e:
#            self.assertNotEqual(e._reason, None)    
#            self.assertEqual(testResult, None)
        

        bake = Bake()
        config = "bakefile.xml" #bakefile.xml"
        args = []
        parser = bake._option_parser('build')
        parser.add_option('-j', '--jobs', help='Allow N jobs at once. Default is 1.',
                          type='int', action='store', dest='jobs', default=1)
        parser.add_option("--debug", action="store_true", 
                          dest="debug", default=False, 
                          help="Should we enable extra Bake debugging output ?")
        (options, args_left) = parser.parse_args(args)
#        bake.setMainOptions(options)
        Bake.main_options = options
        
        # Tests typical case, the module is there and the object directory is not
        self._env._installdir = self._env.srcdir+"/install_bake"
        testResult = bake._check_build_version(config, options);
        self.assertEqual(testResult, None)
 
        # if the user has no permission to see the file
        testStatus = commands.getoutput('chmod 000 /tmp/source')
        testResult=None
        testResult = bake._check_source_code(config, options);
        self.assertFalse(testResult, None)    
        
        testStatus = commands.getoutput('chmod 755 /tmp/source')
           
        # if the folder is not where it should be
        testStatus = commands.getoutput('rm -rf /tmp/source')
        testResult=None
        testResult = bake._check_source_code(config, options);
        self.assertFalse(testResult, None)    

    def test_check_configuration_file(self):
        """Tests the check_configuration_file method of Class Bake. """

        bakeInstance = Bake() 

        testResult = bakeInstance.check_configuration_file("strangeName")
        self.assertEqual(testResult, "strangeName", "New name is not respected")

        testResult = bakeInstance.check_configuration_file("bakeconf.xml")
        self.assertEqual(testResult, "bakeconf.xml", "Default file should"
                         " exist but it changed the name.")
        
        testStatus = commands.getoutput('mv bakeconf.xml bc.xml')
        testResult = bakeInstance.check_configuration_file("bakeconf.xml")
        self.assertTrue(testResult.endswith("/bakeconf.xml"), "Should have"
                        " returned the bakeconf but returned " + testResult)

        testStatus = commands.getoutput('mv bakeconf.xml bc.xml')
        testResult = bakeInstance.check_configuration_file("bakefile.xml", True)
        self.assertTrue(testResult.endswith("bakeconf.xml"), "Should have"
                        " returned the bakeconf but returned " + testResult)

        testStatus = commands.getoutput('mv bakeconf.xml bc.xml')
        testResult = bakeInstance.check_configuration_file("bakefile.xml")
        self.assertEqual(testResult, "bakefile.xml", "Default file should"
                         " be returned in the last case.")
        
        testStatus = commands.getoutput('mv bc.xml bakeconf.xml ')
        testStatus = commands.getoutput('mv bf.xml bakefile.xml ')
       

# main call for the tests        
if __name__ == '__main__':
    unittest.main()
