''' 
 Module.py

 This file stores the generic implementation of the bake options. e.g. how 
 the download works, independently of the technology/repository used to  
 store the code.
''' 

import copy
import os
import sys
import shutil
from bake.FilesystemMonitor import FilesystemMonitor
from bake.Exceptions import TaskError

class ModuleDependency:
    """ Dependency information. """
    
    def __init__(self, name, optional = False):
        self._name = name
        self._optional = optional
        
    def name(self):
        return self._name
    
    def is_optional(self):
        return self._optional

class Module:
    def __init__(self, name, 
                 source,
                 build,
                 dependencies = [],
                 built_once = False,
                 installed = []):
        self._name = name
        self._dependencies = copy.copy(dependencies)
        self._source = source
        self._build = build
        self._built_once = built_once
        self._installed = installed


    @property
    def installed(self):
        """ Returns if the module was already installed or not. """
        return self._installed
    @installed.setter
    def installed(self, value):
        """ Stores the given value on the module installed option. """
        self._installed = copy.copy(value)

    def _directory(self):
        return self._name

    def _do_download(self, env, source, name, forceDownload):
        """ Recursive download function, do the download for each 
        target module. """
        
        srcDirTmp = name
        if source.attribute('module_directory').value :
            srcDirTmp = source.attribute('module_directory').value
            
        env.start_source(name, srcDirTmp)
        
        if forceDownload:
            try: # when forced download, removes the repository if it exists
                if os.path.isdir(env.srcdir):
                    shutil.rmtree(env.srcdir)
            except OSError as e:
                env._logger.commands.write('Could not remove source files'
                                            ' %s for module: %s \n Error: %s' % 
                                            (env.srcdir, env._module_name, 
                                             str(e)))
        
        if os.path.isdir(env.srcdir):
            env.end_source()
        else:
            try:
                source.download(env)
            finally:
                env.end_source()
        for child, child_name in source.children():
            self._do_download(env, child, os.path.join(name, child_name))

    def download(self, env, forceDownload):
        """ General download function. """
        
        if self._build.attribute('supported_os').value :
            if not self._build.check_os(self._build.attribute('supported_os').value) : 
                import platform
                osName = platform.system().lower()
                print('    Downloading, but this module works only on %s ' 
                      'platform(s), %s not supported in %s' % 
                      (self._build.attribute('supported_os').value, 
                       env._module_name, osName))
            
        try:
            print(" >> Downloading " + self._name )
            self._do_download(env, self._source, self._name, forceDownload)
            print(" >> Download " + self._name + " - OK")
            return True
        except TaskError as e:
            print(" >> Download " + self._name + " - Problem")
            print(e.reason)
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()           
            return False
        except:
            print(" >> Download " + self._name + " - Problem")
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()
            return False


    def _do_update(self, env, source, name):
        """ Recursive update function, do the update for each 
        target module. """
        
        srcDirTmp = name
        if source.attribute('module_directory').value :
            srcDirTmp = source.attribute('module_directory').value
            
        env.start_source(name, srcDirTmp)
        
        try:
            source.update(env)
        finally:
            env.end_source()
        for child, child_name in source.children():
            self._do_update(env, child, os.path.join(name, child_name))

    def update(self, env):
        """ Main update function. """
        
        try:
            self._do_update(env, self._source, self._name)
            print(" Update " + self._name + " - OK")
            return True
        except TaskError as e:
            print(e.reason)
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()           
            return False
        except:
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()
            return False
        
    def distclean(self, env):
        """ Main distclean function, deletes the source and installed files. """
        
        srcDirTmp = self._name
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value
            
        env.start_source(self._name, srcDirTmp)
        print(" >> Clean source " + self._name )
        try: 
            shutil.rmtree(env.srcdir)
        except Exception as e:
#            print (e)
            pass
        try: 
            shutil.rmtree(env.installdir)
        except:
            pass
        return True
         

    def uninstall(self, env):
        """ Main uninstall function, deletes the installed files. """
         
        for installed in self._installed:
            try:
                os.remove(installed)
            except OSError:
                pass
            
        # delete directories where files were installed if they are empty
        dirs = [os.path.dirname(installed) for installed in self._installed]
        def uniq(seq):
            keys = {}
            for e in seq:
                keys[e] = 1
            return keys.keys()
        for d in uniq(dirs):
            try:
                os.removedirs(d)
            except OSError:
                pass
        self._installed = []

    def build(self, env, jobs, force_clean):
        """ Main build function. """
        
        # if there is no build we do not need to proceed 
        if self._build.name() == 'none':
            return True
        
        # delete in case this is a new build configuration
        # and there are old files around
        if force_clean:
            self.uninstall(env)
            if not self._built_once:
                self.clean(env)

        srcDirTmp = self._name
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value
            
        env.start_build(self._name, srcDirTmp,
                        self._build.supports_objdir)
        
        # setup the monitor
        monitor = FilesystemMonitor(env.installdir)
        monitor.start()

        if self._build.attribute('supported_os').value :
            if not self._build.check_os(self._build.attribute('supported_os').value) : 
                import platform
                osName = platform.system().lower()
                raise TaskError('This installation model works only on %s' 
                                ' platform(s), %s not supported for %s' 
                                % (self._build.attribute('supported_os').value, 
                                   osName, env._module_name))

        if not os.path.isdir(env.installdir):
            os.mkdir(env.installdir)
        if self._build.supports_objdir and not os.path.isdir(env.objdir):
            os.mkdir(env.objdir)

        try:
            print(" >> Building " + self._name )
            if not os.path.isdir(env.srcdir):
                raise TaskError('Source is not available for module %s: '
                            'directory %s not found.  Try %s download first.' % 
                            (env._module_name,env.srcdir, sys.argv[0]))

            if self._build.attribute('pre_installation').value != '':
                self._build.perform_pre_installation(env)
            self._build.threat_variables(env)
            self._build.build(env, jobs)
            self._installed = monitor.end()
            if self._build.attribute('post_installation').value != '':
                self._build.perform_post_installation(env)
            env.end_build()
            self._built_once = True
            print(" >> Built " + self._name + " - OK")
            return True
        except TaskError as e:
            print(" >> Building " + self._name + " - Problem")
            print("   > " + e.reason)
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()           
            env.end_build()
            return False
        except:
            self._installed = monitor.end()
            env.end_build()
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()
            return False

    def check_build_version(self, env):
        """ Checks the version of the selected build tool in the machine. """
        
        srcDirTmp = self._name
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value
            
        env.start_build(self._name, srcDirTmp,
                        self._build.supports_objdir)
        
        retval = self._build.check_version(env)
        env.end_build()
        return retval

    def is_downloaded(self, env):
        """ Checks if the source code is not already available. """
        
        srcDirTmp = self._name
        if self._source.name() is 'system_dependency' :
            return True
        
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value

        env.start_source(self._name,srcDirTmp)
        retval = os.path.isdir(env.srcdir)
        env.end_source()
        return retval

    def check_source_version(self, env):
        """ Checks if the version of the available version control tool. """

        srcDirTmp = self._name
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value

        env.start_source(self._name, srcDirTmp)
        retval = self._source.check_version(env)
        env.end_source()
        return retval


    def update_libpath(self, env):
        """ Makes it available for the next modules the present libpath. """
        
        srcDirTmp = self._name
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value
            
        env.start_build(self._name, srcDirTmp,
                        self._build.supports_objdir)
        env.add_libpaths([env._lib_path()])
        env.end_build()

    def clean(self, env):
        """ Main cleaning build option handler. """
        
        srcDirTmp = self._name
        if self._source.attribute('module_directory').value :
            srcDirTmp = self._source.attribute('module_directory').value

        env.start_build(self._name, srcDirTmp,
                        self._build.supports_objdir)
        if not os.path.isdir(env.objdir) or not os.path.isdir(env.srcdir):
            env.end_build()
            return
        try:
            self._build.clean(env)
            env.end_build()
            self._built_once = False
            print(" >> Cleaning " + self._name + " - OK")
            return True
        except TaskError as e:
            print(" >> Cleaning " + self._name + " - Problem")
            print(e.reason)
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()           
            return False
        except:
            env.end_build()
            if env.debug :
                import bake.Utils
                bake.Utils.print_backtrace()
            return False

    def is_built_once(self):
        return self._built_once
    def get_source(self):
        return self._source
    def get_build(self):
        return self._build
    def name(self):
        return self._name
    def dependencies(self):
        return self._dependencies
