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

class TestBake(unittest.TestCase):
    """Tests cases for the main Bake Class."""
    
    def setUp(self):
        """Common set Up environment, available for all tests."""
        pathname = os.path.dirname("/tmp/source/")  
        self._logger = StdoutModuleLogger();
        self._logger.set_verbose(1)
        self._env = ModuleEnvironment(self._logger, pathname, pathname, pathname)
#        testStatus = commands.getoutput('cp '+pathname+'/bakefile.xml /tmp/.')

        
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None
        pathname = os.path.dirname("/tmp/source")  
        pathname = os.path.dirname(sys.argv[1])  
        testStatus = commands.getoutput('rm -f '+ pathname +'/bakefile.xml')
        testStatus = commands.getoutput('rm -rf /tmp/source')

   
    def test_check_source_code(self):
        """Tests the _check_source_code method of Class Bake. """

        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        
        pathname = os.path.dirname(sys.argv[1])  
        testStatus = commands.getoutput('python '+pathname+'/../bake.py configure --enable=openflow-ns3 --sourcedir=/tmp/source --installdir=/tmp/source')

        mercurial.attribute("url").value = "http://code.nsnam.org/bhurd/openflow"
        self._env._module_name="openflow-ns3"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)

        bake = Bake()
        config = "bakefile.xml"
        args = []
        parser = bake._option_parser('build')
        parser.add_option('-j', '--jobs', help='Allow N jobs at once. Default is 1.',
                          type='int', action='store', dest='jobs', default=1)
        (options, args_left) = parser.parse_args(args)
        
        # Tests typical case, the module is there
        testResult = bake._check_source_code(config, options);
        self.assertEqual(testResult, None)
 
        # if the user has no permission to see the file
        testStatus = commands.getoutput('chmod 000 /tmp/source')
        testResult=None
        try: 
            testResult = bake._check_source_code(config, options);
            self.fail("There was no problem, and the module does not exist. ")
        except Exception as e:
            self.assertNotEqual(e.message, None)    
            self.assertEqual(testResult, None)
        
        testStatus = commands.getoutput('chmod 755 /tmp/source')
           
        # if the folder is not where it should be
        testStatus = commands.getoutput('rm -rf /tmp/source')
        testResult=None
        try: 
            testResult = bake._check_source_code(config, options);
            self.fail("There was no problem, and the module does not exist. ")
        except Exception as e:
            self.assertNotEqual(e.message, None)    
            self.assertEqual(testResult, None)
             

    def test_check_build_version(self):
        """Tests the _check_source_code method of Class Bake. """

        # Environment settings        
        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)
        
        pathname = os.path.dirname(sys.argv[1])  
        testStatus = commands.getoutput('python '+pathname+'/../bake.py configure --enable=openflow-ns3 --sourcedir=/tmp/source --installdir=/tmp/source')

        mercurial.attribute("url").value = "http://code.nsnam.org/bhurd/openflow"
        self._env._module_name="openflow-ns3"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)

        bake = Bake()
        config = "bakefile.xml"
        args = []
        parser = bake._option_parser('build')
        parser.add_option('-j', '--jobs', help='Allow N jobs at once. Default is 1.',
                          type='int', action='store', dest='jobs', default=1)
        (options, args_left) = parser.parse_args(args)

        # Tests typical case, the module is there and the object directory is not
        testResult = bake._check_build_version(config, options);
        self.assertEqual(testResult, None)
 
        # if the user has no permission to see the file
        testStatus = commands.getoutput('chmod 000 /tmp/source')
        testResult=None
        try: 
            testResult = bake._check_source_code(config, options);
            self.fail("There was no problem, and the module does not exist. ")
        except Exception as e:
            self.assertNotEqual(e.message, None)    
            self.assertEqual(testResult, None)
        
        testStatus = commands.getoutput('chmod 755 /tmp/source')
           
        # if the folder is not where it should be
        testStatus = commands.getoutput('rm -rf /tmp/source')
        testResult=None
        try: 
            testResult = bake._check_source_code(config, options);
            self.fail("There was no problem, and the module does not exist. ")
        except Exception as e:
            self.assertNotEqual(e.message, None)    
            self.assertEqual(testResult, None)


# main call for the tests        
if __name__ == '__main__':
    unittest.main()
