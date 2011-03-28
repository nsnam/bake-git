from Exceptions import TaskError
import Utils
from Utils import run_command,ModuleAttributeBase

class ModuleSource(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
    @classmethod
    def create(cls, name):
        for subclass in ModuleSource.__subclasses__():
            if subclass.name() == name:
                return subclass()
        return None
    def diff(self, env):
        raise NotImplemented()
    def download(self, env):
        raise NotImplemented()
    def update(self, env):
        raise NotImplemented()

class NoneModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
    @classmethod
    def name(cls):
        return 'none'
    def diff(self, env):
        pass
    def download(self, env):
        pass
    def update(self, env):
        pass

class InlineModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
    @classmethod
    def name(cls):
        return 'inline'

class BazaarModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'The url to clone from',
                           mandatory = True)
        self.add_attribute('revision', None, 'The revision to update to after the clone.')
    @classmethod
    def name(cls):
        return 'bazaar'
    def diff(self, env):
        pass
    def download(self, env):
        rev_arg = []
        if not self.attribute('revision').value is None:
            rev_arg.extend(['-r', self.attribute('revision').value])
        env.run(['bzr', 'clone'] + rev_arg + [self.attribute('url').value, env.srcdir])

    def update(self, env):
        rev_arg = []
        if not self.attribute('revision').value is None:
            rev_arg.extend(['-r', self.attribute('revision').value])
        env.run(['bzr', 'pull'] + rev_arg + [self.attribute('url').value, env.srcdir])
    
class MercurialModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'The url to clone from',
                            mandatory = True)
        self.add_attribute('revision', 'tip', 'The revision to update to after the clone. '
                           'If no value is specified, the default is "tip"')
    @classmethod
    def name(cls):
        return 'mercurial'
    def download(self, env):
        env.run(['hg', 'clone', '-U', self.attribute('url').value, env.srcdir])
        env.run(['hg', 'update', '-r', self.attribute('revision').value],
                directory = env.srcdir)
    def update(self, env):
        env.run(['hg', 'pull'], directory = env.srcdir)
        env.run(['hg', 'update', '-r', self.attribute('revision').value],
                directory = env.srcdir)
        
class ArchiveModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', None, 'The url to clone from',
                           mandatory = True)
        self.add_attribute('extract_directory', None, 
                           'The name of the directory the source code will be extracted to naturally.'
                           ' If no value is specified, directory is assumed to be equal to the '
                           'of the archive without the file extension.')
    @classmethod
    def name(cls):
        return 'archive'
    def _decompress(self, filename, env):
        import tempfile
        import os
        tempdir = tempfile.mkdtemp()
        extensions = [
            ['tar', ['tar', 'xf']],
            ['tar.gz', ['tar', 'zxf']],
            ['tar.Z', ['tar', 'zxf']],
            ['tar.bz2', ['tar', 'jxf']],
            ['zip', ['unzip']],
            ['rar', ['unrar', 'e']]
            ]
        for extension, command in extensions:
            if filename.endswith(extension):
                env.run(command + [filename], directory = tempdir)
                if self.attribute('extract_directory').value is not None:
                    actual_extract_dir = self.attribute('extract_directory').value
                else:
                    actual_extract_dir = os.path.basename(filename)[0:-len(extension)-1]
                # finally, rename the extraction directory to the target directory name.
                os.rename(os.path.join(tempdir, actual_extract_dir), env.srcdir)
                return
        raise TaskError('Unknown Archive Type')

    def download(self, env):
        import urllib
        import urlparse
        import os
        filename = os.path.basename(urlparse.urlparse(self.attribute('url').value).path)
        tmpfile = os.path.join(env.srcrepo, filename)
        urllib.urlretrieve(self.attribute('url').value, filename=tmpfile)
        self._decompress(tmpfile, env)
        
    def update(self, env):
        # we really have nothing to do for archives. 
        pass
        
class CvsModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('root', '', 'Repository root specification to checkout from.',
                           mandatory = True)
        self.add_attribute('module', '', 'Module to checkout.', mandatory = True)
        self.add_attribute('checkout_directory', None, 'Name of directory checkout defaults to. '
                           'If unspecified, defaults to the name of the module being checked out.')
        self.add_attribute('date', None, 'Date to checkout')

    @classmethod
    def name(cls):
        return 'cvs'
    def download(self, env):
        import tempfile
        tempdir = tempfile.mkdtemp()
        env.run(['cvs', '-d', self.attribute('root').value, 'login'], 
                directory = tempdir)
        checkout_options = []
        if not self.attribute('date').value is None:
            checkout_options.extend(['-D', self.attribute('date').value])
        env.run(['cvs', '-d', self.attribute('root').value, 'checkout'] + checkout_options +
                [self.attribute('module').value],
                directory = tempdir)
        if self.attribute('checkout_directory').value is not None:
            actual_checkout_dir = self.attribute('checkout_directory').value
        else:
            actual_checkout_dir = self.attribute('module').value
        import os
        os.rename(os.path.join(tempdir, actual_checkout_dir), env.srcdir)

    def update(self, env):
        env.run(['cvs', 'up'], directory = env.srcdir)

class GitModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'Url to clone the source tree from.',
                           mandatory = True)
        self.add_attribute('revision', 'refs/remotes/origin/master', 
                           'Revision to checkout. Defaults to origin/master reference.')
    @classmethod
    def name(cls):
        return 'git'
    def download(self, env):
        import tempfile
        import os
        tempdir = tempfile.mkdtemp()
        env.run(['git', 'init'], directory = tempdir)
        env.run(['git', 'remote', 'add', 'origin', self.attribute('url').value], 
                directory = tempdir)
        env.run(['git', 'fetch'], 
                directory = tempdir)
        env.run(['git', 'checkout', self.attribute('revision').value],
                directory = tempdir)
        os.rename(tempdir, env.srcdir)

    def update(self, env):
        env.run(['git', 'fetch'], directory = env.srcdir)
        env.run(['git', 'checkout', self.attribute('revision').value],
                          directory = env.srcdir)
