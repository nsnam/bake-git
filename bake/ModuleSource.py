from Exceptions import TaskError
import Utils
from Utils import ModuleAttributeBase
import os
import urlparse
from datetime import date

class ModuleSource(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
        self.add_attribute('module_directory', '', 'Source module directory', mandatory=False)
    @classmethod
    def subclasses(self):
        return ModuleSource.__subclasses__()
    @classmethod
    def create(cls, name):
        """Instantiates the class that is called by the requested name."""
        
        # Runs over all the Classes and instantiates the one that has the name
        # equals to the name passed as parameter
        for subclass in ModuleSource.subclasses():
            if subclass.name() == name:
                return subclass()
        return None
    def diff(self, env):
        raise NotImplemented()
    def download(self, env):
        raise NotImplemented()
    def update(self, env):
        raise NotImplemented()
    def check_version(self, env):
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
    def check_version(self, env):
        return True

class InlineModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
    @classmethod
    def name(cls):
        return 'inline'

class BazaarModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a bazaar repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'The url to clone from',
                           mandatory=True)
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
        env.run(['bzr', 'pull'] + rev_arg + [self.attribute('url').value], directory=env.srcdir)
    def check_version(self, env):
        return env.check_program('bzr')

    
class MercurialModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a mercurial repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'The url to clone from',
                            mandatory=True)
        self.add_attribute('revision', 'tip', 'The revision to update to after the clone. '
                           'If no value is specified, the default is "tip"')
    @classmethod
    def name(cls):
        return 'mercurial'
    def download(self, env):
        env.run(['hg', 'clone', '-U', self.attribute('url').value, env.srcdir])
        env.run(['hg', 'update', '-r', self.attribute('revision').value],
                directory=env.srcdir)
    def update(self, env):
        env.run(['hg', 'pull', self.attribute('url').value], directory=env.srcdir)
        env.run(['hg', 'update', '-r', self.attribute('revision').value],
                directory=env.srcdir)
    def check_version(self, env):
        return env.check_program('hg')

import shutil
        
class ArchiveModuleSource(ModuleSource):
    """Handles the modules that have the sources as a single tarball like file."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', None, 'The url to clone from',
                           mandatory=True)
        self.add_attribute('extract_directory', None,
                           'The name of the directory the source code will be extracted to naturally.'
                           ' If no value is specified, directory is assumed to be equal to the '
                           'of the archive without the file extension.')
    @classmethod
    def name(cls):
        return 'archive'
    def _decompress(self, filename, env):
        """Uses the appropriate tool to uncompress the sources."""
        
        import tempfile
        import os
        tempdir = tempfile.mkdtemp(dir=env.srcrepo)
        extensions = [
            ['tar', ['tar', 'xf']],
            ['tar.gz', ['tar', 'zxf']],
            ['tar.Z', ['tar', 'zxf']],
            ['tar.bz2', ['tar', 'jxf']],
            ['zip', ['unzip']],
            ['rar', ['unrar', 'e']]
            ]
        
        # finds the right tool
        for extension, command in extensions:
            if filename.endswith(extension):
                env.run(command + [filename], directory=tempdir)
                if self.attribute('extract_directory').value is not None:
                    actual_extract_dir = self.attribute('extract_directory').value
                else:
                    actual_extract_dir = os.path.basename(filename)[0:-len(extension) - 1]
                # finally, rename the extraction directory to the target directory name.
                try:
                    os.rename(os.path.join(tempdir, actual_extract_dir), env.srcdir)
#                    os.remove(tempdir)
                    shutil.rmtree(tempdir) # delete directory
                except (OSError, IOError) as e:
                    raise TaskError('Rename problem for module: %s, from: %s, to: %s, Error: %s' 
                                    % (env._module_name, os.path.join(tempdir, actual_extract_dir), env.srcdir, e))

                return
        raise TaskError('Unknown Archive Type: %s, for module: %s' % (filename, env._module_name))

    def download(self, env):
        """Downloads the specific file."""
        
        import urllib
        import urlparse
        import os
         
        url_local = self.attribute('url').value
       
        filename = os.path.basename(urlparse.urlparse(url_local).path)
        tmpfile = os.path.join(env.srcrepo, filename)
        try:
            urllib.urlretrieve(url_local, filename=tmpfile)
        except IOError as e:
            raise TaskError('Download problem for module: %s, URL: %s, Error: %s' % (env._module_name, self.attribute('url').value, e))
            
        self._decompress(tmpfile, env)
        
    def update(self, env):
        # we really have nothing to do for archives. 
        pass

    def check_version(self, env):
        """Verifies if the right program exists in the system to handle the given compressed source file."""
        
        extensions = [
            ['tar', 'tar'],
            ['tar.gz', 'tar'],
            ['tar.Z', 'tar'],
            ['tar.bz2', 'tar'],
            ['zip', 'unzip'],
            ['rar', 'unrar']
            ]
        try:
            filename = os.path.basename(urlparse.urlparse(self.attribute('url').value).path)
        except AttributeError as e:
            return False

        for extension, program in extensions:
            if filename.endswith(extension):
                return env.check_program(program)
        return False
        
class SystemDependency(ModuleSource):
    """Handles the system dependencies for a given module, if the module is missing, and it is a linux box, 
    try to install the missing module using one of the default tools  i.e. yum apt-get."""
    
    dependencyMessage=''
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('dependency_test', None, 'The name of the installer',
                           mandatory=True)
        self.add_attribute('try_to_install', None, 'If should try to install or not',
                           mandatory=True)
        self.add_attribute('name_yum', None, 'The name of the module to install with  yum',
                           mandatory=False)
        self.add_attribute('name_apt-get', None, 'The name of the module to install with  apt-get',
                           mandatory=False)
        self.add_attribute('name_yast', None, 'The name of the module to install with  yast',
                           mandatory=False)
        self.add_attribute('more_information', None, 'Gives users a better hint of where to search for the module' ,
                           mandatory=True)
    @classmethod
    def name(cls):
        return 'system_dependency'
    
    def getCommand(self, distribution):
        """Finds the proper installer command line, given the linux distribution."""
        distributions = [
            ['debian', 'sudo apt-get -y install '],
            ['ubuntu', 'sudo apt-get -y install '],
            ['fedora', 'sudo yum -y install '],
            ['redhat', 'sudo yum -y install '],
            ['centos', 'sudo yum -y install '],
            ['suse', 'sudo yast --install '],
            ]
 
        for name, command in distributions:
            if distribution.startswith(name):
                return command
        return ''

    def remove(self, env):
        import platform 
        import re
        
        # if the download is dependent of the machine's architecture 
        osName = platform.system().lower()
        if(not osName.startswith('linux')):
            raise TaskError('Not a Linux machine, self installation is not possible in %s for module: %s,  %s' % (osName, env._module_name, self.attribute('error_message').value))
               
        (distribution, version, version_id) = platform.linux_distribution()
        distribution = distribution.lower()
        command = self.getCommand(distribution)
        command = command.rstrip().rsplit(' ', 1)[0] + ' remove'
        installerName = self.attribute('name_' + command.split()[1]).value
            
        # if didn't find the specific installer name uses the default one
        if(not installerName):
            installerName = self.attribute('dependency_test').value

        # uses apt-get to install the module
        try:
            env.run((command + " "+installerName).split(" "), directory=env.srcrepo)
        except IOError as e:
            raise TaskError('Removing module problem: \"%s\", Message: %s, Error: %s' % (env._module_name,  self.attribute('more_information').value, e))
        except TaskError as e1:
            raise TaskError('Removing module problem: \"%s\", Probably you miss root rights or the module is not present on your package management databases. Try calling bake with sudo or reviewing your library database to add \"%s\". Message: %s' % (env._module_name, installerName, self.attribute('more_information').value, e1._reason))
       
        return True

    def download(self, env):
        """Downloads the specific file."""
        
        import platform 
        import re

        # tests if the dependency exists or not        
        dependencyExists = env.check_program(self.attribute('dependency_test').value)
        
        # if the dependency exists there is nothing else to do
        if(dependencyExists) :
            return True

        selfInstalation = self.attribute('try_to_install').value
        
        # even if should try to install, if it is not a linux mahine we will not be able
        osName = platform.system().lower()
        if(osName.startswith('linux') and selfInstalation):
            (distribution, version, version_id) = platform.linux_distribution()
            distribution = distribution.lower()
            command = self.getCommand(distribution)
            
            installerName = self.attribute('name_' + command.split()[1]).value
            
            # if didn't find the specific installer name uses the default one
            if(not installerName):
                installerName = self.attribute('dependency_test').value
            
            if(not command):
                selfInstalation = False
            
        else :
                selfInstalation = False
        
        errorTmp = None
        if(not dependencyExists and selfInstalation):
            # Try to install if possible
            try:
                env.run((command + installerName).split(" "), directory=env.srcrepo)
                return True
            except IOError as e:
                errorTmp = ('Self installation problem for module: \"%s\", Error: %s' % (env._module_name,  e))
            except TaskError as e1:
                errorTmp = ('Self installation problem for module: \"%s\", Probably you miss root rights or the module is not present on your package management databases. Try calling bake with sudo or reviewing your library database to add \"%s\"' % (env._module_name, installerName))
                
        # if the dependency does not exist logs it on the message string
        if(not dependencyExists) :
            self.dependencyMessage = self.dependencyMessage + ('  > System dependency: %s : %s: \n' % (env._module_name,  self.attribute('more_information').value))
        
            if(errorTmp) :
                self.dependencyMessage = self.dependencyMessage + '      ... ' + errorTmp + '\n';
            
        return dependencyExists
    
    def update(self, env):
        # we really have nothing to do for archives. 
        pass
    
    def build(self, env):
        # we really have nothing to do for archives. 
        pass

    def check_version(self, env):
        """Verifies if the right program exists in the system to handle the given compressed source file."""
        
        distributions = [
            ['debian', 'apt-get'],
            ['ubuntu', 'apt-get'],
            ['fedora', 'yum'],
            ['redhat', 'yum'],
            ['centos', 'yum'],
            ['suse', 'yast'],
            ]

        import platform 
        
        osName = platform.system().lower()
        if(not osName.startswith('linux')):
            raise TaskError('This installation model works only on Linux platoforms, %s not supported for %s,  %s' % (osName, env._module_name, self.attribute('error_message').value))
               
        (distribution, version, version_id) = platform.linux_distribution()
        distribution = distribution.lower()
        for dist, program in distributions:
            if distribution.startswith(dist):
                return env.check_program(program)
        return False

class CvsModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a CVS repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('root', '', 'Repository root specification to checkout from.',
                           mandatory=True)
        self.add_attribute('module', '', 'Module to checkout.', mandatory=True)
        self.add_attribute('checkout_directory', None, 'Name of directory checkout defaults to. '
                           'If unspecified, defaults to the name of the module being checked out.')
        self.add_attribute('date', None, 'Date to checkout')

    @classmethod
    def name(cls):
        return 'cvs'
    def download(self, env):
        """ Downloads the CVS code from a specific date. """
        
        import tempfile
        try:
            tempdir = tempfile.mkdtemp(dir=env.srcrepo)
        except OSError as e:
            raise TaskError('Could not create temporary directory %s, Error: %s' % (env.srcrepo, e))

        env.run(['cvs', '-d', self.attribute('root').value, 'login'],
                directory=tempdir)
        checkout_options = []
        if not self.attribute('date').value is None:
            checkout_options.extend(['-D', self.attribute('date').value])
        env.run(['cvs', '-d', self.attribute('root').value, 'checkout'] + checkout_options + 
                [self.attribute('module').value],
                directory=tempdir)
        if self.attribute('checkout_directory').value is not None:
            actual_checkout_dir = self.attribute('checkout_directory').value
        else:
            actual_checkout_dir = self.attribute('module').value
        import os
        import shutil
        try:
            os.rename(os.path.join(tempdir, actual_checkout_dir), env.srcdir)
            shutil.rmtree(tempdir)
        except AttributeError as e:
            raise TaskError('Atribute type error expected String, Error: %s' % e)
        

    def update(self, env):
        """Updates the code for the date specified, or for the today's code. """
        
        # just update does not work, it has to give a date for the update
        # either a date is provided, or takes today as date
        update_options = []
        if not self.attribute('date').value is None:
            update_options.extend(['-D', self.attribute('date').value])
        else:
            update_options.extend(['-D', str(date.today())]) 
        
        env.run(['cvs', 'up'] + update_options, directory=env.srcdir)
        
    def check_version(self, env):
        return env.check_program('cvs')

class GitModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a git repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'Url to clone the source tree from.',
                           mandatory=True)
        self.add_attribute('revision', 'refs/remotes/origin/master',
                           'Revision to checkout. Defaults to origin/master reference.')
    @classmethod
    def name(cls):
        return 'git'
    def download(self, env):
        import tempfile
        import os
        try:
            tempdir = tempfile.mkdtemp(dir=env.srcrepo)
        except AttributeError as e1:
            raise TaskError('Atribute type error, expected String, Error: %s' % e1)
        except OSError as e2:
            raise TaskError('Could not create temporary file, Error: %s' % e2)
            
        env.run(['git', 'init'], directory=tempdir)
        env.run(['git', 'remote', 'add', 'origin', self.attribute('url').value],
                directory=tempdir)
        env.run(['git', 'fetch'],
                directory=tempdir)
        env.run(['git', 'checkout', self.attribute('revision').value],
                directory=tempdir)
        os.rename(tempdir, env.srcdir)

    def update(self, env):
        env.run(['git', 'fetch'], directory=env.srcdir)
        env.run(['git', 'checkout', self.attribute('revision').value],
                          directory=env.srcdir)

    def check_version(self, env):
        return env.check_program('git')
