import Utils
import os
from Utils import ModuleAttributeBase

class ModuleBuild(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
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
        return 'none-build'
    def build(self, logger, srcdir, blddir, installdir):
        pass
    def clean(self, logger, srcdir, blddir):
        pass

class Cmake(ModuleBuild):
    def __init__(self):
        ModuleBuild.__init__(self)
        self.add_attribute('CC',       '', 'C compiler to use')
        self.add_attribute('CXX',      '', 'C++ compiler to use')
        self.add_attribute('CFLAGS',   '', 'Flags to use for C compiler')
        self.add_attribute('CXXFLAGS', '', 'Flags to use for C++ compiler')
        self.add_attribute('LDFLAGS',  '', 'Flags to use for Linker')
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
        Utils.run_command(['make', 'doc'], logger, directory = blddir)
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
        self.add_attribute('blddir',   'srcdir', 
                           'Does this module support building in blddir != srcdir ? '
                           'Defaults to blddir == srcdir. ')
        self.add_attribute('maintainer', 'no', 'Maintainer mode ?')
    @classmethod
    def name(cls):
        return 'autotools'
    def build(self, logger, srcdir, blddir, installdir):
        if self.attribute('maintainer').value != 'no':
            Utils.run_command(['autoreconf', '--install'], logger,
                        directory = srcdir)
        if self.attribute('blddir').value == 'srcdir':
            blddir = srcdir
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
            

