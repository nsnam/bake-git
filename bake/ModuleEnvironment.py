''' 
 ModuleEnvironment.py
 
 This file stores the class Module Environment responsible for the interaction
 between Bake and the execution of third party softwares and the operating 
 system.  
''' 

import os
import subprocess
import sys
import platform

from bake.Exceptions import TaskError 
from sets import Set

class ModuleEnvironment:
    ''' Main class to interact with the host system to execute the external 
    tools.
    '''
     
    (HIGHER, LOWER, EQUAL) = range(0,3)

    def __init__(self, logger, installdir, sourcedir, objdir, debug=False):
        ''' Internal variables initialization.'''
        
        self._logger = logger
        self._installdir = installdir
        self._sourcedir = sourcedir
        self._objdir = objdir
        self._module_name = None
        self._module_dir = None
        self._module_supports_objdir = None
        self._libpaths = Set([])
        self._binpaths = Set([])
        self._pkgpaths =  Set([])
        self._variables =  Set([])
        self._debug = debug

    def _module_directory(self):
        ''' Returns the name of the directory of the on use module.'''

        if not self._module_dir :
            return self._module_name
        return self._module_dir

    @property
    def installdir(self):
        ''' Returns the name of the set installation directory.'''
        
        return self._installdir
    
    @property
    def debug(self):
        ''' Returns if this execution was set to show the debug messages or not.'''

        return self._debug
    
    @property
    def srcdir(self):
        ''' Returns the directory where Bake stores the source of the present 
        module.
        '''
        
        try:
            return os.path.join(self._sourcedir, self._module_directory())
        except AttributeError as e:
            raise TaskError('Missing configuration: sourcedir= %s, ' 
                            'module_directory= %s, Error: %s' 
                            % (self._sourcedir,self._module_directory(), e))
        
    @property
    def srcrepo(self):
        ''' The root of the source repository, where all the sources for all 
        the modules will be stored.
        '''
        
        return self._sourcedir
    
    @property
    def objdir(self):
        ''' Returns the directory where Bake stores the object code of the  
        present module.
        '''
        
        if not self._module_supports_objdir:
            obj = self.srcdir
        else:
            try:
                obj = os.path.join(self.srcdir, self._objdir)
            except AttributeError as e:
                raise TaskError('Missing configuration: sourcedir= %s, '  
                                'objdir= %s, Error: %s' 
                                % (self._sourcedir, self._module_directory(), e))
        return obj

    def _pkgconfig_var(self):
        ''' Returns the PKG_CONFIG_PATH configured environment variable.'''

        return 'PKG_CONFIG_PATH'
    
    def _pkgconfig_path(self):
        ''' Returns the PKG_CONFIG_PATH configured path. '''
        
        return os.path.join(self._lib_path(), 'pkgconfig')
    
    def _lib_var(self):
        ''' Returns the value of the system configured library path.'''

        lib_var = {'Linux' : 'LD_LIBRARY_PATH',
                    'Darwin' : 'DYLD_LIBRARY_PATH',
                    'Windows' : 'PATH'}
        if not lib_var.has_key(platform.system()):
            sys.stderr('Error: Unsupported platform. Send email to ' 
                       'bake_support@inria.fr (%s)' % platform.system())
            sys.exit(1)
        return lib_var[platform.system()]
    
    def _lib_path(self):
        ''' Returns the value of the library path for the in-use module.'''
        
        return os.path.join(self._installdir, 'lib')
    
    def _bin_var(self):
        return 'PATH'
    def _bin_path(self):
        ''' Returns the value of the binary path for the in-use module.'''
        
        return os.path.join(self._installdir, 'bin')
    
    def _py_var(self):
        return 'PYTHONPATH'
    def _py_path(self):
        ''' Returns the value of the python path for the in-use module.'''
        
        return os.path.join(self._installdir, 'lib', 
                            'python'  
                            '.'.join(platform.python_version_tuple()[0:2]), 
                            'site-packages')
        
    def _append_path(self, d, name, value, sep):
        ''' Append the variable to the system in use configuration. '''
        
        if not d.has_key(name):
            d[name] = value
        else:
            d[name] = d[name] + sep + value

    def start_source(self, name, dir):
        ''' Sets the environment to be used by the given source module.'''
        
        assert self._module_supports_objdir is None
        self._module_name = name
        self._module_dir = dir
        self._logger.set_current_module(name)
        
        # ensure source directory exists
        if not os.path.isdir(self._sourcedir):
            os.mkdir(self._sourcedir)

    def end_source(self):
        ''' Cleans the environment regarding the informations of the last used
        source module.
        '''
        
        self._module_name = None
        self._module_dir = None
        self._logger.clear_current_module()

    def start_build(self, name, dir, supports_objdir):
        ''' Sets the environment to be used by the given build module.'''
        
        assert self._module_supports_objdir is None
        self._module_name = name
        self._module_dir = dir
        self._module_supports_objdir = supports_objdir
        self._logger.set_current_module(name)

    def end_build(self):
        ''' Cleans the environment regarding the informations of the last used
        build module.
        '''
        
        self._module_name = None
        self._module_dir = None
        self._module_supports_objdir = None
        self._logger.clear_current_module()
    
    def exist_file(self, file):
        ''' Finds if the file exists in the path.'''
        
        return os.path.exists(file)

    def _program_location(self, program):
        ''' Finds where the executable is located in the user's path.'''
        
        # function to verify if the program exists on the given path 
        # and if it is executable
        def is_exe(path):
            return os.path.exists(path) and os.access(path, os.X_OK)
        path, name = os.path.split(program)
        # if the path for the executable was passed as part of its name
        if path:
            if is_exe(program):
                return program
        else:
            # for all the directories in the path search for the executable
            for path in os.environ["PATH"].split(os.pathsep) + [self._bin_path()]:
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
        return None

    def _check_version(self, found, required, match_type):
        ''' Checks the version of the required executable.'''
        
        # I guess we should change here to accept different sizes
        # e.g. Version 4.2 is required, but 4.2.1 is already bigger so it is OK
        # the only change to make is to get the smaller length to control the 
        # for, and if different decide in accordance to if it is HIGHER or LOWER 
        assert len(found) == len(required)
        if match_type == self.HIGHER:
            for i in range(0,len(found)):
                if int(found[i]) < int(required[i]):
                    return False
                elif int(found[i]) > int(required[i]):
                    return True
            return True
        elif match_type == self.LOWER:
            for i in range(0,len(found)):
                if int(found[i]) > int(required[i]):
                    return False
                elif int(found[i]) < int(required[i]):
                    return True
            return True
        elif match_type == self.EQUAL:
            for i in range(0,len(found)):
                if int(found[i]) != int(required[i]):
                    return False
            return True
        else:
            assert False

    def add_libpaths(self, libpaths):
        ''' Adds the list of paths to the in-use library path environment 
        variable.
        '''
        
        for element in libpaths :
            self._libpaths.add(self.replace_variables(element))
        
    def add_binpaths(self, libpaths):
        ''' Adds the list of paths to the in-use binary path environment 
        variable.
        '''
        
        for element in libpaths :
            self._binpaths.add(self.replace_variables(element))
        
    def add_pkgpaths(self, libpaths):
        ''' Adds the list of paths to the in-use package path environment 
        variable.
        '''
        
        for element in libpaths :
            self._pkgpaths.add(self.replace_variables(element))

    def add_variables(self, libpaths):
        ''' Adds/replace the list of variables to the in-use set of environment 
        variables.
        '''
        
        for element in libpaths :
            self._variables.add(self.replace_variables(element))
            
    def create_environement_file(self, fileName):
        ''' Creates the set environment file to help users to call the Bake 
        built modules.
        '''
                
        script = "#!/bin/bash \n#### \n# Environment setting script. Automatically generated by Bake\n####\n\n"
        script = script + "echo \"> Call with . " + fileName + " or source " + fileName + "\"\n"
        self._binpaths.add(self._bin_path())
        self._libpaths.add(self._lib_path())
        
        if len(self._libpaths) > 0:
            script = script + self.add_onPath("LD_LIBRARY_PATH", self._libpaths) + "\n"
            
        if len(self._binpaths) > 0:
            script = script + self.add_onPath("PATH", self._binpaths) + "\n"
            
        if len(self._pkgpaths) > 0:
            script = script + self.add_onPath("PKG_CONFIG_PATH", self._pkgpaths) + "\n"
        
        for element in self._variables:
            script = script + " export " + element  + "\n"
        
        fout = open(fileName, "w")
        fout.write(script)
        fout.close()
        os.chmod(fileName, 0755)
        
        return script
        
    def add_onPath (self, variableName, vectorPath):
        ''' Format the variable to be added on the system.
        '''
        
        returnString = " export " + variableName + "=$" + variableName
        for element in vectorPath:
            returnString = returnString + ":" + element
            
        return returnString

    def replace_variables(self, string):
        ''' Replace the variables on the string, if they exist, by their 
        system real values.
        '''
        
        import re
        tmp = string
        tmp = re.sub('\$INSTALLDIR', self.installdir, tmp)
        tmp = re.sub('\$OBJDIR', self.objdir, tmp)
        tmp = re.sub('\$SRCDIR', self.srcdir, tmp)
        return tmp

    def check_program(self, program, version_arg = None,
                      version_regexp = None, version_required = None,
                      match_type=HIGHER):
        '''Checks if the program, with the desired version, exists in the 
        system.
        '''
        
        if self._program_location(program) is None:
            return False
        if version_arg is None and version_regexp is None and version_required is None:
            return True
        else:
            # This assert as it was avoided the checking of the version of the 
            # executable assert not (version_arg is None or version_regexp is 
            # None or version_required is None)
            assert not (version_arg is None and version_regexp is None and  version_required is None)
            popen = subprocess.Popen([self._program_location(program), 
                                        version_arg],
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.STDOUT)
            (out, err) = popen.communicate('')
            import re
            reg = re.compile(version_regexp)
            for line in out.splitlines():
                m = reg.search(line)
                if not m is None:
                    found = m.groups()
                    return self._check_version(found, version_required, match_type)

    def run(self, args, directory = None, env = dict(), interactive = False):
        '''Executes a system program adding the libraries and over the correct 
        directories.
        '''
        
        if not interactive:
            env_string = ''
            if len(env) != 0:
                env_string = ' '.join([a + '=' + b for a,b in env.items()])
            try:
                args_string = ' '.join(args)
            except TypeError as e:
                raise TaskError('Wrong argument type: %s, expected string,' 
                                ' error: %s' % (str(args), e))
               
            self._logger.commands.write(env_string + ' ' + args_string + 
                                        ' dir=' + str(directory) + '\n')
            stdin = None
            stdout = self._logger.stdout
            stderr = self._logger.stderr
        else:
            stdin = sys.stdin
            stdout = sys.stdout
            stderr = sys.stderr            
        tmp = dict(os.environ.items() + env.items())
        
        # sets the library and binary paths 
        for libpath in self._libpaths:
            self._append_path(tmp, self._lib_var(), libpath, os.pathsep)
            if self.debug:
                print(self._lib_var() + " " + libpath + " ")  
                        
        self._append_path(tmp, self._lib_var(), self._lib_path(), os.pathsep)
        
        for libpath in self._binpaths:
            self._append_path(tmp, self._bin_var(), libpath, os.pathsep)          
            if self.debug:
                print(self._bin_var() + " " + libpath + " ")          
                
        self._append_path(tmp, self._bin_var(), self._bin_path(), os.pathsep)
        
        for libpath in self._pkgpaths:
            self._append_path(tmp, self._pkgconfig_var(), libpath, os.pathsep)
            if self.debug:
                print(self._pkgconfig_var() + " " + libpath + " ")         
                 
        self._append_path(tmp, self._pkgconfig_var(), self._pkgconfig_path(), 
                          os.pathsep)

        self._append_path(tmp, self._py_var(), self._py_path(), os.pathsep)
        
        # Calls the third party executable with the whole context
        popen = subprocess.Popen(args,
                                 stdin = stdin,
                                 stdout = stdout,
                                 stderr = stderr,
                                 cwd = directory,
                                 env = tmp)
        # Waits for the full execution of the third party software
        retcode = popen.wait()
        if retcode != 0:
            raise TaskError('Subprocess failed with error %d: %s' % (retcode, str(args)))

        
