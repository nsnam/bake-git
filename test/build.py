import unittest
# hack to save ourselves from having to use PYTHONPATH
import sys
import os
import commands
import re

from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger
from bake.ModuleSource import ModuleSource
from bake.ModuleBuild import ModuleBuild
from bake.Exceptions import TaskError
from bake.Bake import Bake


sys.path.append(os.path.join (os.getcwd(), '..'))

class TestBuild (unittest.TestCase):
    """Tests cases for the build process, mainly the ModuleBuild Class and subclasses."""
    
    def setUp(self):
        """Common set Up environment, available for all tests."""
        pathname = os.path.dirname("/tmp/source/")  
        testStatus = commands.getoutput('rm -rf ' + pathname)
        self._logger = StdoutModuleLogger();
        self._logger.set_verbose(1)
        self._env = ModuleEnvironment(self._logger, pathname, pathname, pathname+"/obj")
#        testStatus = commands.getoutput('cp '+pathname+'/bakefile.xml /tmp/.')

        
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None
        pathname = os.path.dirname("/tmp/source")  
        pathname = os.path.dirname(sys.argv[1])  
        testStatus = commands.getoutput('rm -f '+ pathname +'/bakefile.xml')
        testStatus = commands.getoutput('rm -rf /tmp/source')

    def test_ModuleBuild(self):
        """Tests the WafModuleBuild Class from ModuleBuild. """

        build = ModuleBuild.create("non_Existing_Build_Tool")
        self.assertEqual(build  , None)

   
    def test_PythonModuleBuild(self):
        """Tests the WafModuleBuild Class from ModuleBuild. """

        # creating python build module test
        python = ModuleBuild.create("python")
        self.assertNotEqual(python, None)
        self.assertEqual(python.name(), "python")

        
        #checks that the machine has python installed
        self._logger.set_current_module(self._env._module_name)
        testResult = python.check_version(self._env)
        self.assertTrue(testResult)

        # set up the environment: create directories and download the target code
        archive = ModuleSource.create("archive")
        archive.attribute("url").value = "http://switch.dl.sourceforge.net/project/pygccxml/pygccxml/pygccxml-1.0/pygccxml-1.0.0.zip"
        self._env._module_name="pygccxml"
        testStatus = commands.getoutput('rm -rf /tmp/source/pygccxml')
        testStatus = commands.getoutput('mkdir /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = archive.download(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/pygccxml|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")
     
        # Expected case test
        self._env.objdir = self._env.srcdir+"/object_bake"
        self._env._installdir = self._env.srcdir+"/install_bake"
        
        # test patch
        self.assertEqual(python.attribute('patch').value, '')
        python.attribute('patch').value = 'test.patch'
        self.assertEqual(python.attribute('patch').value, 'test.patch')

        testResult = None
        try:
            testResult = python.add_attribute('patch',  'ERRROR', 'SHOULD NOT HAVE BEEN ADDED')
            self.fail("The attribute patch exists already, should not be able to add it. ")
        except AssertionError as e:
            self.assertNotEqual(e, None)    
            self.assertEqual(testResult, None)
        
        try:
            testResult = python.build(self._env, "1")
            self.fail("The patch does not exist, should not have being able to find the path file and give an error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # creates the file, empty, but created    
        testStatus = commands.getoutput('touch ' + self._env.srcdir + '/test.patch')
       
        testResult = python.build(self._env, "1")
        self.assertEqual(testResult, None)       
        
        python.attribute('patch').value = ''
       
        testStatus = commands.getoutput('rm -rf '+self._env.objdir)
        testStatus = commands.getoutput('rm -rf '+self._env._installdir)
        testResult = python.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/pygccxml/object_bake|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")
        testStatus = commands.getoutput('ls /tmp/source/pygccxml/install_bake|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")
        

        # No permission in the target directories 
        self._env.objdir = "/tmp/source/test1/testobj"
        self._env._installdir = "/tmp/source/test1/testinst"
        testStatus = commands.getoutput('rm -rf '+ "/tmp/source/test1")
        testStatus = commands.getoutput('mkdir '+ "/tmp/source/test1")
        testStatus = commands.getoutput('chmod 000 '+"/tmp/source/test1")
        testResult = None
        try:
            testResult = python.build(self._env, "1")
            self.fail("Has no permission in the target directory, and passed any way. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('chmod 755 '+"/tmp/source/test1")
        testStatus = commands.getoutput('rm -rf '+ "/tmp/source/test1")


        # call the clean to remove the build
        # TODO:  The clean does not work, the call is correct but I guess it is a
        # problem with the pygccxml clean that does nothing.    
#        self._env.objdir = self._env.srcdir+"/object_bake"
#        self._env._installdir = self._env.srcdir+"/install_bake"
#        testResult = python.clean(self._env)
#        self.assertEqual(testResult, None)
#        testStatus = commands.getoutput('ls /tmp/source/pygccxml/object_bake|wc')
#        created = re.compile('\d+').search(testStatus).group()
#        self.assertEqual(created, "0")
#        testStatus = commands.getoutput('ls /tmp/source/pygccxml/install_bake|wc')
#        created = re.compile('\d+').search(testStatus).group()
#        self.assertEqual(created, "0")
        

    def test_WafModuleBuild(self):
        """Tests the WafModuleBuild Class from ModuleBuild. """

        waf = ModuleBuild.create("waf")
        self.assertNotEqual(waf, None)
        self.assertEqual(waf.name(), "waf")
        
        testStatus = commands.getoutput('cp test.patch /tmp/source/openflow-ns3/test.patch' )
       

        testResult = None
        try:
            testResult = waf.check_version(self._env)
            self.fail("There was a miss configuration problem and there was no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)

        mercurial.attribute("url").value = "http://code.nsnam.org/bhurd/openflow"
        self._env._module_name="openflow-ns3"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)
        self.assertEqual(testResult, None)

        #check that has the waf version required installed in the machine
        testResult = waf.check_version(self._env)
        self.assertTrue(testResult)
 
        # Verirfies the path to the waf file
        testResult = waf._binary(self._env.srcdir)
        self.assertEqual(testResult, "/tmp/source/openflow-ns3/waf")
      
        # wrong path
        testResult = waf._binary("/tmp/source")
        self.assertEqual(testResult, "waf")
        
        # non existing path
        testResult = waf._binary("/NonExistant/Path")
        self.assertEqual(testResult, "waf")
        
        # Expected case test
        self._env.objdir = self._env.srcdir+"/object"
        
        # test patch
        self.assertEqual(waf.attribute('patch').value, '')
        waf.attribute('patch').value = 'testN.patch'
        self.assertEqual(waf.attribute('patch').value, 'testN.patch')

        testResult = None
        try:
            testResult = waf.add_attribute('patch',  'ERRROR', 'SHOULD NOT HAVE BEEN ADDED')
            self.fail("The attribute patch exists already, should not be able to add it. ")
        except AssertionError as e:
            self.assertNotEqual(e, None)    
            self.assertEqual(testResult, None)
        
        try:
            testResult = waf.build(self._env, "1")
            self.fail("The patch does not exist, should not have being able to find the path file and give an error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
 
        testStatus = commands.getoutput('cp test.patch /tmp/source/openflow-ns3/test.patch' )
       
        # creates the file, empty, but created    
        waf.attribute('patch').value = 'test.patch'
        self.assertEqual(waf.attribute('patch').value, 'test.patch')
    
        testResult = waf.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/openflow-ns3/object|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")
        waf.attribute('patch').value = ''

        # call the clean to remove the build
        # TODO:  Find a solution for the remaining directories
        #    - It is strange because the waf does not remove the directories, 
        # just the object files.... Should this  be like that??!?!        
        testResult = waf.clean(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/openflow-ns3/object/default/lib|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertEqual(created, "0")
        
        # Call with extra options
        # TODO: find a solution either use another packet, like pybindgen, that
        # uses waf, or see to fix the openflow, because open flow does not accept
        # the configure arguments even though it is in the example of the
        # man page --enable-examples --enable-tests does not compile gives an error
        # flolowed the steps of http://www.nsnam.org/docs/models/html/openflow-switch.html
        waf.attribute("CFLAGS").value = "-g"
#        waf.attribute("configure_arguments").value = " "
#        waf.attribute("build_arguments").value = "-O2"
        
        testResult = waf.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls -l /tmp/source/openflow-ns3/object|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")
        
        # TODO: 
        # test if the object dir is equal to the source dir, for the open flow 
        # case it is not allowed but I am not sure for everyone else 
        
        self._env.objdir = self._env.srcdir
        try:
            testResult = waf.build(self._env, "1")
            self.fail("The source and destination are the same but it passed without an exception. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # TODO: 
        # non existing path
        # need to find a good case of test for this
        # testResult = waf._is_1_6_x(self._env)
        # self.assertFalse(testResult)

    def test_WafModuleBuildPybind(self):
        """Tests the WafModuleBuild Class from ModuleBuild. """

        waf = ModuleBuild.create("waf")
        self.assertNotEqual(waf, None)
        self.assertEqual(waf.name(), "waf")

        testResult = None
        try:
            testResult = waf.check_version(self._env)
            self.fail("There was a miss configuration problem and there was no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # Environment settings        
        bazaar = ModuleSource.create("bazaar")
        testResult = bazaar.check_version(self._env)
        self.assertTrue(testResult)
        
        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        self._env._module_name="pybindgen"
        self._logger.set_current_module(self._env._module_name)
#        bazaar.attribute("revision").value = "revno:795"

        self._env._module_name="pybindgen"
        testStatus = commands.getoutput('mkdir /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = bazaar.download(self._env)
        self.assertEqual(testResult, None)

        #check that has the waf version required installed in the machine
        testResult = waf.check_version(self._env)
        self.assertTrue(testResult)
 
        # Verirfies the path to the waf file
        testResult = waf._binary(self._env.srcdir)
        self.assertEqual(testResult, "/tmp/source/pybindgen/waf")
      
        # wrong path
        testResult = waf._binary("/tmp/source")
        self.assertEqual(testResult, "waf")
        
        # non existing path
        testResult = waf._binary("/NonExistant/Path")
        self.assertEqual(testResult, "waf")
        
        # Expected case test
        self._env.objdir = self._env.srcdir+"/object"

        # test patch
        self.assertEqual(waf.attribute('patch').value, '')
        waf.attribute('patch').value = 'test.patch'
        self.assertEqual(waf.attribute('patch').value, 'test.patch')

        testResult = None
        try:
            testResult = waf.add_attribute('patch',  'ERRROR', 'SHOULD NOT HAVE BEEN ADDED')
            self.fail("The attribute patch exists already, should not be able to add it. ")
        except AssertionError as e:
            self.assertNotEqual(e, None)    
            self.assertEqual(testResult, None)
        
        try:
            testResult = waf.build(self._env, "1")
            self.fail("The patch does not exist, should not have being able to find the path file and give an error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # creates the file, empty, but created    
        testStatus = commands.getoutput('touch ' + self._env.srcdir + '/test.patch')
        
        testStatus = commands.getoutput('rm -rf /tmp/source/pybindgen/object')
        
        testResult = waf.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/pybindgen/object|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")

        # call the clean to remove the build
        # TODO:  Find a solution for the remaining directories
        #    - It is strange because the waf does not remove the directories, 
        # just the object files.... Should this  be like that??!?!        
        testResult = waf.clean(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/pybindgen/object/default/tests|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertEqual(created, "0")
        
        # TODO: neighter the --generate-version appears but I couldn't also 
        # find a configuration argument for pybindgen :(
        # Call with extra options
        waf.attribute("CFLAGS").value = "-g"
#        waf.attribute("configure_arguments").value = "--enable-examples --enable-tests"
        waf.attribute("build_arguments").value = "--generate-version"
        
        testResult = waf.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls -l /tmp/source/openflow-ns3/object|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")
        
        
        # TODO: 
        # non existing path
        # need to find a good case of test for this
        # testResult = waf._is_1_6_x(self._env)
        # self.assertFalse(testResult)
          
    def test_CmakeModule(self):
        """Tests the WafModuleBuild Class from ModuleBuild. """

        cmake = ModuleBuild.create("cmake")
        self.assertNotEqual(cmake, None)
        self.assertEqual(cmake.name(), "cmake")

        # Environment settings        
        cvs = ModuleSource.create("cvs")
        testResult = cvs.check_version(self._env)
        self.assertTrue(testResult)
        cvs.attribute("root").value = ":pserver:anoncvs:@www.gccxml.org:/cvsroot/GCC_XML"
        cvs.attribute("module").value="gccxml"
        cvs.attribute("date").value="2009-09-21"
       
        self._env._module_name="gccxml"
        self._logger.set_current_module(self._env._module_name)
#        bazaar.attribute("revision").value = "revno:795"

        testStatus = commands.getoutput('mkdir /tmp/source')
        testResult = cvs.download(self._env)
        self.assertEqual(testResult, None)

        #check that has the cmake version required is installed in the machine
        testResult = cmake.check_version(self._env)
        self.assertTrue(testResult)
        
        # Expected case test
        self._env.objdir = self._env.srcdir+"/object"
        
        # test patch
        self.assertEqual(cmake.attribute('patch').value, '')
        cmake.attribute('patch').value = 'test.patch'
        self.assertEqual(cmake.attribute('patch').value, 'test.patch')

        testResult = None
        try:
            testResult = cmake.add_attribute('patch',  'ERRROR', 'SHOULD NOT HAVE BEEN ADDED')
            self.fail("The attribute patch exists already, should not be able to add it. ")
        except AssertionError as e:
            self.assertNotEqual(e, None)    
            self.assertEqual(testResult, None)
        
        try:
            testResult = cmake.build(self._env, "1")
            self.fail("The patch does not exist, should not have being able to find the path file and give an error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # creates the file, empty, but created    
        testStatus = commands.getoutput('touch ' + self._env.srcdir + '/test.patch')

        testStatus = commands.getoutput('rm -rf /tmp/source/gccxml/object')
        testResult = cmake.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/gccxml/object|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")

        # call the clean to remove the build
        # TODO:  Find a solution for the remaining directories
        #    - It is strange because the waf does not remove the directories, 
        # just the object files.... Should this  be like that??!?!        
        testResult = cmake.clean(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/gccxml/object/GCC/gcc/CMakeFiles/backend.dir/*.o|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertEqual(created, "0")
        
        # TODO: neighter the --generate-version appears but I couldn't also 
        # find a configuration argument for pybindgen :(
        # Call with extra options
        cmake.attribute("CFLAGS").value = "-g"
#        waf.attribute("configure_arguments").value = "--enable-examples --enable-tests"
#        cmake.attribute("build_arguments").value = "--generate-version"
        
        testResult = cmake.build(self._env, "1")
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls -l /tmp/source/openflow-ns3/object|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertNotEqual(created, "0")

    def test_makeModule(self):
        """Tests the WafModuleBuild Class from ModuleBuild. """

        make = ModuleBuild.create("make")
        self.assertNotEqual(make, None)
        self.assertEqual(make.name(), "make")

        # Environment settings        
        mercurial = ModuleSource.create("mercurial")
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)

        mercurial.attribute("url").value = "http://code.nsnam.org/mathieu/readversiondef"
        self._env._module_name="readversiondef"
        testStatus = commands.getoutput('rm -rf /tmp/source')
        self._logger.set_current_module(self._env._module_name)
        testResult = mercurial.download(self._env)
        self.assertEqual(testResult, None)

        #check that has the make version required is installed in the machine
        testResult = make.check_version(self._env)
        self.assertTrue(testResult)
        
        # Expected case test
        self._env.objdir = self._env.srcdir+"/object"
        
        # test patch
        self.assertEqual(make.attribute('patch').value, '')
        make.attribute('patch').value = 'test.patch'
        self.assertEqual(make.attribute('patch').value, 'test.patch')
        
        testResult = None
        try:
            testResult = make.add_attribute('patch',  'ERRROR', 'SHOULD NOT HAVE BEEN ADDED')
            self.fail("The attribute patch exists already, should not be able to add it. ")
        except AssertionError as e:
            self.assertNotEqual(e, None)    
            self.assertEqual(testResult, None)
        
        try:
            testResult = make.build(self._env, "1")
            self.fail("The patch does not exist, should not have being able to find the path file and give an error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # creates the file, empty, but created    
        testStatus = commands.getoutput('touch ' + self._env.srcdir + '/test.patch')

        testStatus = commands.getoutput('rm -rf /tmp/source/gccxml/object')
        testResult = make.build(self._env, "1")
        self.assertEqual(testResult, None)
        make.attribute('patch').value = ''

#        testStatus = commands.getoutput('ls /tmp/source/gccxml/object|wc')
#        created = re.compile('\d+').search(testStatus).group()
#        self.assertNotEqual(created, "0")

        # call the clean to remove the build
        # TODO:  Find a solution for the remaining directories
        #    - It is strange because the waf does not remove the directories, 
        # just the object files.... Should this  be like that??!?!        
        testResult = make.clean(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('ls /tmp/source/readversiondef/*.o|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertEqual(created, "1")
        
        # TODO: neither the --generate-version appears but I couldn't also 
        # find a configuration argument for pybindgen :(
        # Call with extra options
        make.attribute("configure_arguments").value = "all"
        
        testResult = make.build(self._env, "1")
        self.assertEqual(testResult, None)
        make.attribute('configure_arguments').value = ''

        make.attribute("post_installation").value = "rm /tmp/source/readversiondef/readversiondef.o"
        testResult = make.build(self._env, "1")
        self.assertEqual(testResult, None)
        make.attribute('post_installation').value = ''
        testStatus = commands.getoutput('ls /tmp/source/readversiondef/*.o|wc')
        created = re.compile('\d+').search(testStatus).group()
        self.assertEqual(created, "0")


#        testStatus = commands.getoutput('ls -l /tmp/source/openflow-ns3/object|wc')
#        created = re.compile('\d+').search(testStatus).group()
#        self.assertNotEqual(created, "0")

# main call for the tests        
if __name__ == '__main__':
    unittest.main()
