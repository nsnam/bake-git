import Utils
import os
from Utils import ModuleAttributeBase
from Exceptions import NotImplemented

class ModuleBuild(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
        self._libpaths = []
    @classmethod
    def create(cls, name):
        for subclass in ModuleBuild.__subclasses__():
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
        # member variable is created by code in Configuration right after 
        # object instance is created. So evil... But works.
        return self._supports_objdir
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

class PythonModuleBuild(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'python'
    def build(self, env, jobs):
        env.run(['python', os.path.join(env.srcdir, 'setup.py'), 'build', 
                  '--build-base=' + env.objdir, 
                  'install', '--prefix=' + env.installdir], 
                 directory = env.srcdir)
    def clean(self, env):
        env.run(['python', os.path.join(env.srcdir, 'setup.py'), 'clean', 
                 '--build-base=' + env.objdir],
                directory = env.srcdir)
    def check_version(self, env):
        return True



class WafModuleBuild(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('extra_configure_options',  '', 'Options to pass to "waf configure"')
        self.add_attribute('extra_build_options',  '', 'Options to pass to "waf"')
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
        env['WAFCACHE'] = os.path.join(objdir, '.cache-wscript')
        env['WAFLOCK'] = os.path.join(objdir, '.lock-wscript')
        return env
    def build(self, env, jobs):
        extra_configure_options = []
        if self.attribute('extra_configure_options').value != '':
            extra_configure_options = [env.replace_variables(tmp) for tmp in
                                       self.attribute('extra_configure_options').value.split(' ')]
        extra_build_options = []
        if self.attribute('extra_build_options').value != '':
            extra_build_options = [env.replace_variables(tmp) for tmp in
                                   self.attribute('extra_build_options').value.split(' ')]
        env.run([self._binary(env.srcdir), '--srcdir=' + env.srcdir, '--blddir=' + env.objdir, 
                 '--prefix=' + env.installdir, 'configure'] + extra_configure_options,
                directory = env.objdir,
                env = self._env(env.objdir))
        env.run([self._binary(env.srcdir)] + extra_build_options + ['-j', str(jobs)],
                directory = env.objdir,
                env = self._env(env.objdir))
        env.run([self._binary(env.srcdir), 'install'],
                directory = env.objdir,
                env = self._env(env.objdir))
        
    def clean(self, env):
        if os.path.isfile(os.path.join(env.objdir, '.lock-wscript')):
            env.run([self._binary(env.srcdir), 'clean'],
                    directory = env.objdir,
                    env = self._env(env.objdir))
    def check_version(self, env):
        for path in [os.path.join(env.srcdir, 'waf'), 'waf']:
            if env.check_program(path, version_arg = '--version',
                                 version_regexp = '(\d+)\.(\d+)\.(\d+)',
                                 version_required = (1,5,9)):
                return True


class Cmake(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('extra_targets', '', 'Targets to make before install')
        self.add_attribute('extra_cmake_options', '', 'Command-line options to pass to cmake')
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
        if self.attribute('extra_cmake_options').value != '':
            options = self.attribute('extra_cmake_options').value.split(' ')
        env.run(['cmake', env.srcdir, '-DCMAKE_INSTALL_PREFIX=' + env.installdir] + 
                self._variables() + options,
                directory=env.objdir)
        env.run(['make', '-j', str(jobs)], directory = env.objdir)
        if self.attribute('extra_targets').value != '':
            env.run(['make'] + self.attribute('extra_targets').value.split(' '), 
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
        self.add_attribute('extra_configure_options', '', 'Command-line options to pass to configure')
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
        if self.attribute('extra_configure_options').value != '':
            options = self.attribute('extra_configure_options').value.split(' ')
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
            

