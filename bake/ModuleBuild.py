import Utils
import os
from Utils import ModuleAttributeBase

class ModuleBuild(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
        self.add_attribute('objdir', 'srcdir', 
                           'Does this module support building in objdir != srcdir ? '
                           'Defaults to objdir == srcdir. ')
    @classmethod
    def create(cls, name):
        for subclass in ModuleBuild.__subclasses__():
            if subclass.name() == name:
                return subclass()
        return None
    def build(self, logger, srcdir, blddir, installdir):
        raise NotImplemented()
    def clean(self, logger, srcdir, blddir):
        raise NotImplemented()

class NoneModuleBuild(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
    @classmethod
    def name(cls):
        return 'none'
    def build(self, logger, srcdir, blddir, installdir):
        pass
    def clean(self, logger, srcdir, blddir):
        pass

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
    def build(self, logger, srcdir, blddir, installdir):
        Utils.run_command(['python', os.path.join(srcdir, 'setup.py'), 'build', 
                           '--build-base=' + blddir, 
                           'install', '--prefix=' + installdir], 
                          logger, directory = srcdir)
    def clean(self, logger, srcdir, blddir):
        Utils.run_command(['python', os.path.join(srcdir, 'setup.py'), 'clean', 
                           '--build-base=' + blddir],
                          logger, directory = srcdir)


class WafModuleBuild(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
    @classmethod
    def name(cls):
        return 'waf'
    def _binary(self, srcdir):
        if os.path.isfile(os.path.join(srcdir, 'waf')):
            waf_binary = os.path.join(srcdir, 'waf')
        else:
            waf_binary = 'waf'
        return waf_binary
    def _env(self, blddir):
        env = dict()
        for a,b in [['CC', 'CC'], 
                    ['CXX', 'CXX'],
                    ['CFLAGS', 'CFLAGS'],
                    ['CFLAGS', 'CFLAGS'],
                    ['LDFLAGS', 'LINKFLAGS']]:
            if self.attribute(a).value != '':
                env[b] = self.attribute(a).value
        env['WAFCACHE'] = blddir
        env['WAFLOCK'] = os.path.join(blddir, '.lock-wscript')
        return env
    def build(self, logger, srcdir, blddir, installdir):
        Utils.run_command([self._binary(srcdir), '--srcdir=' + srcdir, '--blddir=' + blddir, 
                           '--prefix=' + installdir, 'configure'],
                          logger, directory = blddir,
                          env = self._env(blddir))
        Utils.run_command([self._binary(srcdir)],
                          logger, directory = blddir,
                          env = self._env(blddir))
        Utils.run_command([self._binary(srcdir), 'install'],
                          logger, directory = blddir,
                          env = self._env(blddir))
        
    def clean(self, logger, srcdir, blddir):
        if os.path.isfile(os.path.join(blddir, '.lock-wscript')):
            Utils.run_command([self._binary(srcdir), 'clean'],
                              logger, directory = blddir,
                              env = self._env(blddir))


class Cmake(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('extra_targets', '', 'Targets to make before install')
    @classmethod
    def name(cls):
        return 'cmake'
    def build(self, logger, srcdir, blddir, installdir):
        variables = []
        if self.attribute('CC').value != '':
            variables.append('-DCMAKE_C_COMPILER=' + self.attribute('CC').value)
        if self.attribute('CFLAGS').value != '':
            variables.append('-DCMAKE_CFLAGS=' + self.attribute('CFLAGS').value)
        if self.attribute('CXX').value != '':
            variables.append('-DCMAKE_CXX_COMPILER=' + self.attribute('CXX').value)
        if self.attribute('CXXFLAGS').value != '':
            variables.append('-DCMAKE_CXXFLAGS=' + self.attribute('CXXFLAGS').value)
        if self.attribute('LDFLAGS').value != '':
            variables.append('-DCMAKE_EXE_LINKER_FLAGS=' + self.attribute('LDFLAGS').value)
        Utils.run_command(['cmake', srcdir, '-DCMAKE_INSTALL_PREFIX=' + installdir] + variables, 
                          logger,
                          directory=blddir)
        Utils.run_command(['make'], logger, directory = blddir)
        if self.attribute('extra_targets').value != '':
            Utils.run_command(['make'] + self.attribute('extra_targets').split(' '), 
                              logger, directory = blddir)
        Utils.run_command(['make', 'install'], logger, directory = blddir)
    def clean(self, logger, srcdir, blddir):
        pass


class Autotools(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
        self.add_attribute('maintainer', 'no', 'Maintainer mode ?')
    @classmethod
    def name(cls):
        return 'autotools'
    def build(self, logger, srcdir, blddir, installdir):
        if self.attribute('maintainer').value != 'no':
            Utils.run_command(['autoreconf', '--install'], logger,
                        directory = srcdir)
        Utils.run_command([os.path.join(srcdir, 'configure'),
                           '--prefix=' + installdir, 
                           'CC=' + self.attribute('CC').value,
                           'CXX=' + self.attribute('CXX').value,
                           'CFLAGS=' + self.attribute('CFLAGS').value,
                           'CXXFLAGS=' + self.attribute('CXXFLAGS').value,
                           'LDFLAGS=' + self.attribute('LDFLAGS').value], 
                          logger,
                          directory = blddir)
        Utils.run_command(['make'], logger, directory = blddir)
        Utils.run_command(['make', 'install'], logger, directory = blddir)

    def clean(self, logger, srcdir, blddir):
        if self.attribute('blddir').value  == 'srcdir':
            blddir = srcdir
        if not os.path.isfile(os.path.join(blddir,'Makefile')):
            return
        if self.attribute('maintainer').value != 'no':
            Utils.run_command(['make', '-k', 'maintainerclean'], logger, directory = blddir)
        else:
            Utils.run_command(['make', '-k', 'distclean'], logger, directory = blddir)
        try:
            os.remove(os.path.join(blddir, 'config.cache'))
        except OSError:
            pass
            

