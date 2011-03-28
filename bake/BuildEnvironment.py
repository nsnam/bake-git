import os
import subprocess
import sys
import platform

class BuildEnvironment:
    def __init__(self, logger, installdir, sourcedir, objdir):
        self._logger = logger
        self._installdir = installdir
        self._sourcedir = sourcedir
        self._objdir = objdir
        self._module_name = None
        self._module_version = None
        self._module_supports_objdir = None
    def _module_directory(self):
        if self._module_version is not None:
            directory = self._module_name + '-' + self._module_version
        else:
            directory = self._module_name
        return directory
    @property
    def installdir(self):
        return self._installdir
    @property
    def srcdir(self):
        return os.path.join(self._sourcedir, self._module_directory())
    @property
    def srcrepo(self):
        return self._sourcedir
    @property
    def objdir(self):
        if not self._module_supports_objdir:
            obj = self.srcdir
        else:
            obj = os.path.join(self.srcdir, self._objdir)
        return obj

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
    def _lib_sep(self):
        lib_sep = {'Linux' : ':',
                   'Darwin' : ':',
                   'Windows' : ';'}
        if not lib_sep.has_key(platform.system()):
            sys.stderr('Error: Unsupported platform. Send email to mathieu.lacage@gmail.com (%s)' %
                       platform.system())
            sys.exit(1)
        return lib_sep[platform.system()]
        
    def _bin_var(self):
        return 'PATH'
    def _bin_path(self):
        return os.path.join(self._installdir, 'bin')
    def _bin_sep(self):
        return self._lib_sep()
    def _py_var(self):
        return 'PYTHONPATH'
    def _py_path(self):
        return os.path.join(self._installdir, 'lib', 
                            'python' + '.'.join(platform.python_version_tuple()[0:2]), 'site-packages')
    def _py_sep(self):
        return ':'
    def _append_path(self, d, name, value, sep):
        if not d.has_key(name):
            d[name] = value
        else:
            d[name] = d[name] + sep + value

    def start_source(self, name, version):
        assert self._module_supports_objdir is None
        self._module_name = name
        self._module_version = version
        self._logger.set_current_module(name, version)
        # ensure source directory exists
        if not os.path.isdir(self._sourcedir):
            os.mkdir(self._sourcedir)

    def end_source(self):
        self._module_name = None
        self._module_version = None
        self._logger.clear_current_module()

    def start_build(self, name, version, supports_objdir):
        assert self._module_supports_objdir is None
        self._module_name = name
        self._module_version = version
        self._module_supports_objdir = supports_objdir
        self._logger.set_current_module(name, version)
        # ensure build directories exist
        if supports_objdir and not os.path.isdir(self.objdir):
            os.mkdir(self.objdir)
        if not os.path.isdir(self.installdir):
            os.mkdir(self.installdir)


    def end_build(self):
        self._module_name = None
        self._module_version = None
        self._module_supports_objdir = None
        self._logger.clear_current_module()

    def run(self, args, directory = None, env = dict(), interactive = False):
        if not interactive:
            env_string = ''
            if len(env) != 0:
                env_string = ' '.join([a + '=' + b for a,b in env.items()])
            args_string = ' '.join(args)
            self._logger.commands.write(env_string + ' ' + args_string + ' dir=' + str(directory) + '\n')
            stdin = None
            stdout = self._logger.stdout
            stderr = self._logger.stderr
        else:
            stdin = sys.stdin
            stdout = sys.stdout
            stderr = sys.stderr            
        tmp = dict(os.environ.items() + env.items())
        self._append_path(tmp, self._lib_var(), self._lib_path(), self._lib_sep())
        self._append_path(tmp, self._bin_var(), self._bin_path(), self._bin_sep())
        self._append_path(tmp, self._py_var(), self._py_path(), self._py_sep())
        popen = subprocess.Popen(args,
                                 stdin = stdin,
                                 stdout = stdout,
                                 stderr = stderr,
                                 cwd = directory,
                                 env = tmp)
        retcode = popen.wait()
        if retcode != 0:
            raise TaskError('Subprocess failed with error %d: %s' % (retcode, str(args)))

        
