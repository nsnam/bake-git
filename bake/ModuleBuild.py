import Utils
import os
import re;
from Utils import ModuleAttributeBase
from Exceptions import NotImplemented
from Exceptions import TaskError 


class ModuleBuild(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
        self._libpaths = []
        self.add_attribute('objdir', 'no', 'Module supports objdir != srcdir.')
    @classmethod
    def subclasses(self):
        return ModuleBuild.__subclasses__()
    @classmethod
    def create(cls, name):
        for subclass in ModuleBuild.subclasses():
            if subclass.name() == name:
                instance = subclass()
                return instance
        return None
    @property
    def libpaths(self):
        return self._libpaths
    def add_libpath(self, path):
        self._libpaths.append(path)
    @property
    def supports_objdir(self):
        return self.attribute('objdir').value == 'yes'
    def build(self, env, jobs):
        raise NotImplemented()
    def clean(self, env):
        raise NotImplemented()
    def check_version(self, env):
        raise NotImplemented()

class NoneModuleBuild(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'none'
    def build(self, env, jobs):
        pass
    def clean(self, env):
        pass
    def check_version(self, env):
        return True


class InlineModuleBuild(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'inline'
    
    @classmethod
    def className(self, code): 
        if code :
            myre = re.compile(".*class (?P<class_name>[a-zA-Z0-9_-]*)\(.*")
            m = myre.match(code)
            if m :
                return m.groupdict()['class_name']
        
        return self.__class__.__name__

class PythonModuleBuild(ModuleBuild):
    """ Performs the build for python based projects."""
    
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'python'
    def build(self, env, jobs):
        
        # TODO: Add the options, there is no space for the configure_arguments
        env.run(['python', os.path.join(env.srcdir, 'setup.py'), 'build', 
                  '--build-base=' + env.objdir, 
                  'install', '--prefix=' + env.installdir], 
                 directory = env.srcdir)
    def clean(self, env):
        env.run(['python', os.path.join(env.srcdir, 'setup.py'), 'clean', 
                 '--build-base=' + env.objdir],
                directory = env.srcdir)
    def check_version(self, env):
        """Verifies only if python exists in the machine. """
        
        try: 
            env.run(['python', '--version'])
        except TaskError as e:
            return False
            
        return True

class WafModuleBuild(ModuleBuild):
    """ Performs the build for Waf based projects."""

    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('configure_arguments',  '', 'Arguments to pass to "waf configure"')
        self.add_attribute('build_arguments',  '', 'Arguments to pass to "waf"')
    @classmethod
    def name(cls):
        return 'waf'
    def _binary(self, srcdir):
        if os.path.isfile(os.path.join(srcdir, 'waf')):
            waf_binary = os.path.join(srcdir, 'waf')
        else:
            waf_binary = 'waf'
        return waf_binary
    def _env(self, objdir):
        env = dict()
        for a,b in [['CC', 'CC'], 
                    ['CXX', 'CXX'],
                    ['CFLAGS', 'CFLAGS'],
                    ['CXXFLAGS', 'CXXFLAGS'],
                    ['LDFLAGS', 'LINKFLAGS']]:
            if self.attribute(a).value != '':
                env[b] = self.attribute(a).value
        env['WAFLOCK'] = '.lock-%s' % os.path.basename(objdir)
        return env
    def _is_1_6_x(self, env):
        return env.check_program(self._binary(env.srcdir), version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)\.(\d+)',
                                 version_required = (1,6,0))
    def build(self, env, jobs):
        extra_configure_options = []
        if self.attribute('configure_arguments').value != '':
            extra_configure_options = [env.replace_variables(tmp) for tmp in
                                       self.attribute('configure_arguments').value.split(' ')]
        extra_build_options = []
        if self.attribute('build_arguments').value != '':
            extra_build_options = [env.replace_variables(tmp) for tmp in
                                   self.attribute('build_arguments').value.split(' ')]
        if self._is_1_6_x(env):
            env.run([self._binary(env.srcdir), '--top=' + env.srcdir, '--out=' + env.objdir, 
                     '--prefix=' + env.installdir, 'configure'] + extra_configure_options,
                    directory = env.srcdir,
                    env = self._env(env.objdir))
        else:
            env.run([self._binary(env.srcdir), '--srcdir=' + env.srcdir, '--blddir=' + env.objdir, 
                     '--prefix=' + env.installdir, 'configure'] + extra_configure_options,
                    directory = env.srcdir,
                    env = self._env(env.objdir))
        env.run([self._binary(env.srcdir)] + extra_build_options + ['-j', str(jobs)],
                directory = env.srcdir,
                env = self._env(env.objdir))
        env.run([self._binary(env.srcdir), 'install'],
                directory = env.srcdir,
                env = self._env(env.objdir))
        
    def clean(self, env):
        wlockfile = '.lock-%s' % os.path.basename(env.objdir)
        if os.path.isfile(os.path.join(env.srcdir, wlockfile)):
            env.run([self._binary(env.srcdir), '-k', 'clean'],
                    directory = env.srcdir,
                    env = self._env(env.objdir))
    def check_version(self, env):
        for path in [os.path.join(env.srcdir, 'waf'), 'waf']:
            if env.check_program(path, version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)\.(\d+)',
                                 version_required = (1,5,9)):
                return True
        return False


class Cmake(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('build_targets', '', 'Targets to make before install')
        self.add_attribute('cmake_arguments', '', 'Command-line arguments to pass to cmake')
    @classmethod
    def name(cls):
        return 'cmake'
    def _variables(self):
        variables = []
        for a,b in [['CC', 'C_COMPILER'], 
                    ['CXX', 'CXX_COMPILER'],
                    ['CFLAGS', 'CFLAGS'],
                    ['CXXFLAGS', 'CXXFLAGS'],
                    ['LDFLAGS', 'EXE_LINKER_FLAGS']]:
            if self.attribute(a).value != '':
                variables.append('-DCMAKE_%s=%s' %(b, self.attribute(a).value))
        return variables

    def build(self, env, jobs):
        options = []
        if self.attribute('cmake_arguments').value != '':
            options = self.attribute('cmake_arguments').value.split(' ')
        
        # if the object directory does not exist, it should create it, to
        # avoid build error, since the cmake does not create the directory
        # it also makes it orthogonal to waf, that creates the target object dir
        try:
            env.run(['mkdir', env.objdir],
                    directory=env.srcdir)
        except TaskError as e:
            # assume that if an error is thrown is because the directory already 
            # exist, otherwise re-propagates the error
            if not "error 1" in e._reason :
                raise TaskError(e._reason)

            directory=env.objdir

        env.run(['cmake', env.srcdir, '-DCMAKE_INSTALL_PREFIX=' + env.installdir] + 
                self._variables() + options,
                directory=env.objdir)
        env.run(['make', '-j', str(jobs)], directory = env.objdir)
        if self.attribute('build_targets').value != '':
            env.run(['make'] + self.attribute('build_targets').value.split(' '), 
                    directory = env.objdir)
        env.run(['make', 'install'], directory = env.objdir)
    def clean(self, env):
        if not os.path.isfile(os.path.join(env.objdir, 'Makefile')):
            return
        env.run(['make', 'clean'], directory = env.objdir)
    def check_version(self, env):
        if not env.check_program('cmake', version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)\.(\d+)',
                                 version_required = (2,8,2)):
            return False
        if not env.check_program('make', version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)',
                                 version_required = (3,80)):
            return False
        return True


class Autotools(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('maintainer', 'no', 'Maintainer mode ?')
        self.add_attribute('configure_arguments', '', 'Command-line arguments to pass to configure')
    @classmethod
    def name(cls):
        return 'autotools'
    def _variables(self):
        variables = []
        for tmp in ['CC','CXX', 'CFLAGS', 'CXXFLAGS', 'LDFLAGS']:
            if self.attribute(tmp).value != '':
                variables.append('%s=%s' % (tmp, self.attribute(tmp).value))
        return variables
    def build(self, env, jobs):
        if self.attribute('maintainer').value != 'no':
            env.run(['autoreconf', '--install'], 
                    directory = env.srcdir)
        options = []
        if self.attribute('configure_arguments').value != '':
            options = self.attribute('configure_arguments').value.split(' ')
        env.run([os.path.join(env.srcdir, 'configure'),
                 '--prefix=' + env.installdir] + 
                self._variables() + options, 
                directory = env.objdir)
        env.run(['make', '-j', str(jobs)], directory = env.objdir)
        env.run(['make', 'install'], directory = env.objdir)

    def clean(self, env):
        if not os.path.isfile(os.path.join(env.objdir,'Makefile')):
            return
        if self.attribute('maintainer').value != 'no':
            env.run(['make', '-k', 'maintainerclean'], directory = env.objdir)
        else:
            env.run(['make', '-k', 'distclean'], directory = env.objdir)
        try:
            os.remove(os.path.join(env.objdir, 'config.cache'))
        except OSError:
            pass
    def check_version(self, env):
        if not env.check_program('autoreconf', version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)',
                                 version_required = (2,66)):
            return False
        if not env.check_program('make', version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)',
                                 version_required = (3,80)):
            return False
        return True
            

