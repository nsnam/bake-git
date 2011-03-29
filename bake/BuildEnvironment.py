import os
import subprocess
import sys
import platform

class BuildEnvironment:
    (HIGHER, LOWER, EQUAL) = range(0,3)

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

    def _program_location(self, program):
        def is_exe(path):
            return os.path.exists(path) and os.access(path, os.X_OK)
        path, name = os.path.split(program)
        if path:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
        return None

    def _check_version(self, found, required, match_type):
        assert len(found) == len(required)
        if match_type == self.HIGHER:
            for i in range(0,len(found)):
                if int(found[i]) < int(required[i]):
                    return False
            return True
        elif match_type == self.LOWER:
            for i in range(0,len(found)):
                if int(found[i]) > int(required[i]):
                    return False
            return True
        elif match_type == self.EQUAL:
            for i in range(0,len(found)):
                if int(found[i]) == int(required[i]):
                    return False
            return True
        else:
            assert False

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
        if self._program_location(program) is None:
            return False
        if version_arg is None and version_regexp is None and version_required is None:
            return True
        else:
            assert not (version_arg is None or version_regexp is None or version_required is None)
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
        self._append_path(tmp, self._lib_var(), self._lib_path(), os.pathsep)
        self._append_path(tmp, self._bin_var(), self._bin_path(), os.pathsep)
        self._append_path(tmp, self._py_var(), self._py_path(), os.pathsep)
        popen = subprocess.Popen(args,
                                 stdin = stdin,
                                 stdout = stdout,
                                 stderr = stderr,
                                 cwd = directory,
                                 env = tmp)
        retcode = popen.wait()
        if retcode != 0:
            raise TaskError('Subprocess failed with error %d: %s' % (retcode, str(args)))

        
