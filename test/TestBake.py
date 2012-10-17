import unittest
# hack to save ourselves from having to use PYTHONPATH
import sys
import os
import commands
import re

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

   
    def test_check_source_code(self):
        """Tests the _check_source_code method of Class Bake. """

        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        
        pathname = os.path.dirname(self.compensate_third_runner())  
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
             

    def test_check_build_version(self):
        """Tests the _check_source_code method of Class Bake. """

        # Environment settings        
        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        
        self._env._debug = True
        
        file = compensate_third_runner()
           
        pathname = os.path.dirname(file)  
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


# main call for the tests        
if __name__ == '__main__':
    unittest.main()
