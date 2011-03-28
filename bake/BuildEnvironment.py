import os
import subprocess

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

    def run(self, args, directory = None, env = dict()):
        self._logger.commands.write(str(args) + ' dir=' + str(directory) + '\n')
        tmp = dict(os.environ.items() + env.items())
        popen = subprocess.Popen(args,
                                 stdout = self._logger.stdout,
                                 stderr = self._logger.stderr,
                                 cwd = directory,
                                 env = tmp)
        retcode = popen.wait()
        if retcode != 0:
            raise TaskError('Subprocess failed with error %d: %s' % (retcode, str(args)))

        
