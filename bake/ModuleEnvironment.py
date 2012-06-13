import os
import subprocess
import sys
import platform

from Exceptions import TaskError 

class ModuleEnvironment:
    (HIGHER, LOWER, EQUAL) = range(0,3)

    def __init__(self, logger, installdir, sourcedir, objdir, debug=False):
        self._logger = logger
        self._installdir = installdir
        self._sourcedir = sourcedir
        self._objdir = objdir
        self._module_name = None
        self._module_supports_objdir = None
        self._libpaths = []
        self._debug = debug

    def _module_directory(self):
        return self._module_name

    @property
    def installdir(self):
        return self._installdir
    
    @property
    def debug(self):
        return self._debug
    
    @property
    def srcdir(self):
        try:
            return os.path.join(self._sourcedir, self._module_directory())
        except AttributeError as e:
            raise TaskError('Missing configuration: sourcedir= %s, module_directory= %s, Error: %s' % (self._sourcedir,self._module_directory(), e))
        
    @property
    def srcrepo(self):
        return self._sourcedir
    @property
    def objdir(self):
        if not self._module_supports_objdir:
            obj = self.srcdir
        else:
            try:
                obj = os.path.join(self.srcdir, self._objdir)
            except AttributeError as e:
                raise TaskError('Missing configuration: sourcedir= %s, objdir= %s, Error: %s' % (self._sourcedir,self._module_directory(), e))
        return obj

    def _pkgconfig_var(self):
        return 'PKG_CONFIG_PATH'
    def _pkgconfig_path(self):
        return os.path.join(self._lib_path(), 'pkgconfig')
    def _lib_var(self):
        lib_var = {'Linux' : 'LD_LIBRARY_PATH',
                    'Darwin' : 'DYLD_LIBRARY_PATH',
                    'Windows' : 'PATH'}
        if not lib_var.has_key(platform.system()):
            sys.stderr('Error: Unsupported platform. Send email to mathieu.lacage@gmail.com (%s)' %
                       platform.system())
            sys.exit(1)
        return lib_var[platform.system()]
    def _lib_path(self):
        return os.path.join(self._installdir, 'lib')
    def _bin_var(self):
        return 'PATH'
    def _bin_path(self):
        return os.path.join(self._installdir, 'bin')
    def _py_var(self):
        return 'PYTHONPATH'
    def _py_path(self):
        return os.path.join(self._installdir, 'lib', 
                            'python' + '.'.join(platform.python_version_tuple()[0:2]), 'site-packages')
    def _append_path(self, d, name, value, sep):
        if not d.has_key(name):
            d[name] = value
        else:
            d[name] = d[name] + sep + value

    def start_source(self, name):
        assert self._module_supports_objdir is None
        self._module_name = name
        self._logger.set_current_module(name)
        # ensure source directory exists
        if not os.path.isdir(self._sourcedir):
            os.mkdir(self._sourcedir)

    def end_source(self):
        self._module_name = None
        self._logger.clear_current_module()

    def start_build(self, name, supports_objdir):
        assert self._module_supports_objdir is None
        self._module_name = name
        self._module_supports_objdir = supports_objdir
        self._logger.set_current_module(name)

    def end_build(self):
        self._module_name = None
        self._module_supports_objdir = None
        self._logger.clear_current_module()

    def _program_location(self, program):
        """Finds where the executable is located in the user's path."""
        
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
        """Checks the version of the required executable."""
        
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
        self._libpaths.extend([self.replace_variables(path) for path in libpaths])

    def replace_variables(self, string):
        import re
        tmp = string
        tmp = re.sub('\$INSTALLDIR', self.installdir, tmp)
        tmp = re.sub('\$OBJDIR', self.objdir, tmp)
        tmp = re.sub('\$SRCDIR', self.srcdir, tmp)
        return tmp

    def check_program(self, program, version_arg = None,
                      version_regexp = None, version_required = None,
                      match_type=HIGHER):
        """Checks if the program, with the desired version, exists in the system."""
        
        if self._program_location(program) is None:
            return False
        if version_arg is None and version_regexp is None and version_required is None:
            return True
        else:
#            This assert as it was avoided the checking of the version of the executable
#            assert not (version_arg is None or version_regexp is None or version_required is None)
            assert not (version_arg is None and version_regexp is None and version_required is None)
            popen = subprocess.Popen([self._program_location(program), version_arg],
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
        """Executes a system program adding the libraries and over the correct directories."""
        
        if not interactive:
            env_string = ''
            if len(env) != 0:
                env_string = ' '.join([a + '=' + b for a,b in env.items()])
            try:
                args_string = ' '.join(args)
            except TypeError as e:
                raise TaskError('Wrong argument type: %s, expected string, error: %s' % (str(args), e))
               
            self._logger.commands.write(env_string + ' ' + args_string + ' dir=' + str(directory) + '\n')
            stdin = None
            stdout = self._logger.stdout
            stderr = self._logger.stderr
        else:
            stdin = sys.stdin
            stdout = sys.stdout
            stderr = sys.stderr            
        tmp = dict(os.environ.items() + env.items())
        
        # adds the libpath 
        for libpath in self._libpaths:
            self._append_path(tmp, self._lib_var(), libpath, os.pathsep)
        self._append_path(tmp, self._lib_var(), self._lib_path(), os.pathsep)
        self._append_path(tmp, self._bin_var(), self._bin_path(), os.pathsep)
        self._append_path(tmp, self._py_var(), self._py_path(), os.pathsep)
        self._append_path(tmp, self._pkgconfig_var(), self._pkgconfig_path(), os.pathsep)
        popen = subprocess.Popen(args,
                                 stdin = stdin,
                                 stdout = stdout,
                                 stderr = stderr,
                                 cwd = directory,
                                 env = tmp)
        retcode = popen.wait()
        if retcode != 0:
            raise TaskError('Subprocess failed with error %d: %s' % (retcode, str(args)))

        
