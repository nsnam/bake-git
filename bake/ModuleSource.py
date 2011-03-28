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
    def diff(self, logger, directory):
        raise NotImplemented()
    def download(self, logger, sourcedir, directory):
        raise NotImplemented()
    def update(self, logger, directory):
        raise NotImplemented()

class NoneModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
    @classmethod
    def name(cls):
        return 'none'
    def diff(self, logger, directory):
        pass
    def download(self, logger, sourcedir, directory):
        pass
    def update(self, logger, directory):
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
    def diff(self, logger, directory):
        pass
    def download(self, logger, sourcedir, directory):
        rev_arg = []
        if not self.attribute('revision').value is None:
            rev_arg.extend(['-r', self.attribute('revision').value])
        Utils.run_command(['bzr', 'clone'] + rev_arg + [self.attribute('url').value, directory],
                          logger)

    def update(self, logger, directory):
        # XXX: 
        pass
    
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
    def download(self, logger, sourcedir, directory):
        Utils.run_command(['hg', 'clone', '-U', self.attribute('url').value, directory],
                          logger)
        Utils.run_command(['hg', 'update', '-r', self.attribute('revision').value],
                          logger, directory = directory)
    def update(self, logger, directory):
        Utils.run_command(['hg', 'pull'],
                      logger, directory = directory)
        Utils.run_command(['hg', 'update', '-r', self.attribute('revision').value],
                      logger, directory = directory)
        
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
    def _decompress(self, filename, logger, directory):
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
                Utils.run_command(command + [filename], logger, directory = tempdir)
                if self.attribute('extract_directory').value is not None:
                    actual_extract_dir = self.attribute('extract_directory').value
                else:
                    actual_extract_dir = os.path.basename(filename)[0:-len(extension)-1]
                # finally, rename the extraction directory to the target directory name.
                os.rename(os.path.join(tempdir, actual_extract_dir), directory)
                return
        raise TaskError('Unknown Archive Type')

    def download(self, logger, sourcedir, directory):
        import urllib
        import urlparse
        import os
        filename = os.path.basename(urlparse.urlparse(self.attribute('url').value).path)
        tmpfile = os.path.join(sourcedir,filename)
        logger.write ('downloading ' + self.attribute('url').value + ' as ' + tmpfile + '\n')
        urllib.urlretrieve(self.attribute('url').value, filename=tmpfile)
        self._decompress(tmpfile, logger, directory)
        
    def update(self, logger, directory):
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

    @classmethod
    def name(cls):
        return 'cvs'
    def download(self, logger, sourcedir, directory):
        import tempfile
        tempdir = tempfile.mkdtemp()
        Utils.run_command(['cvs', '-d', self.attribute('root').value, 'login'],
                      logger)
        Utils.run_command(['cvs', '-d', self.attribute('root').value, 'checkout', 
                           self.attribute('module').value],
                    logger, directory = tempdir)
        if self.attribute('checkout_directory').value is not None:
            actual_checkout_dir = self.attribute('checkout_directory').value
        else:
            actual_checkout_dir = self.attribute('module').value
        import os
        os.rename(os.path.join(tempdir, actual_checkout_dir), directory)

    def update(self, logger, directory):
        Utils.run_command(['cvs', 'up'], logger, directory = directory)

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
    def download(self, logger, sourcedir, directory):
        import tempfile
        import os
        tempdir = tempfile.mkdtemp()
        Utils.run_command(['git', 'init'], logger, directory = tempdir)
        Utils.run_command(['git', 'remote', 'add', 'origin', self.attribute('url').value], 
                          logger, directory = tempdir)
        Utils.run_command(['git', 'fetch'], logger, directory = tempdir)
        Utils.run_command(['git', 'checkout', self.attribute('revision').value],
                          logger, directory = tempdir)
        os.rename(tempdir, directory)

    def update(self, logger, directory):
        Utils.run_command(['git', 'fetch'], logger, directory = directory)
        Utils.run_command(['git', 'checkout', self.attribute('revision').value],
                          logger, directory = directory)
