import copy
import os
from FilesystemMonitor import FilesystemMonitor

class ModuleDependency:
    def __init__(self, name, optional = False):
        self._name = name
        self._optional = optional
    def name(self):
        return self._name
    def is_optional(self):
        return self._optional

class Module:
    def __init__(self, name, 
                 source,
                 build,
                 dependencies = [],
                 built_once = False,
                 installed = []):
        self._name = name
        self._dependencies = copy.copy(dependencies)
        self._source = source
        self._build = build
        self._built_once = built_once
        self._installed = installed

    @property
    def installed(self):
        return self._installed
    @installed.setter
    def installed(self, value):
        self._installed = copy.copy(value)

    def _directory(self):
        return self._name

    def download(self, env):
        env.start_source(self._name)
        if os.path.isdir(env.srcdir):
            env.end_source()
            return True
        try:
            self._source.download(env)
            env.end_source()
            return True
        except:
            import Utils
            Utils.print_backtrace()
            env.end_source()
            return False

    def update(self, env):
        env.start_source(self._name)
        try:
            self._source.update(env)
            env.end_source()
            return True
        except:
            import Utils
            Utils.print_backtrace()
            env.end_source()
            return False

    def uninstall(self, env):
        # delete installed files
        for installed in self._installed:
            try:
                os.remove(installed)
            except OSError:
                pass
        # delete directories where files were installed if they are empty
        dirs = [os.path.dirname(installed) for installed in self._installed]
        def uniq(seq):
            keys = {}
            for e in seq:
                keys[e] = 1
            return keys.keys()
        for d in uniq(dirs):
            try:
                os.removedirs(d)
            except OSError:
                pass
        self._installed = []

    def build(self, env, jobs):
        self.uninstall(env)
        # delete in case this is a new build configuration
        # and there are old files around
        if not self._built_once:
            self.clean(env)
        # setup the monitor
        monitor = FilesystemMonitor(env.installdir)
        monitor.start()

        env.start_build(self._name, 
                        self._build.supports_objdir)
        if not os.path.isdir(env.installdir):
            os.mkdir(env.installdir)
        if self._build.supports_objdir and not os.path.isdir(env.objdir):
            os.mkdir(env.objdir)

        try:
            self._build.build(env, jobs)
            self._installed = monitor.end()
            env.end_build()
            self._built_once = True
            return True
        except:
            self._installed = monitor.end()
            env.end_build()
            import Utils
            Utils.print_backtrace()
            return False

    def check_build_version(self, env):
        env.start_build(self._name, 
                        self._build.supports_objdir)
        if not os.path.isdir(env.objdir) or not os.path.isdir(env.srcdir):
            retval = True
        else:
            retval = self._build.check_version(env)
        env.end_build()
        return retval

    def is_downloaded(self, env):
        env.start_source(self._name)
        retval = os.path.isdir(env.srcdir)
        env.end_source()
        return retval

    def check_source_version(self, env):
        env.start_source(self._name)
        retval = self._source.check_version(env)
        env.end_source()
        return retval


    def update_libpath(self, env):
        env.start_build(self._name, 
                        self._build.supports_objdir)
        env.add_libpaths(self._build.libpaths)
        env.end_build()

    def clean(self, env):
        env.start_build(self._name, 
                        self._build.supports_objdir)
        if not os.path.isdir(env.objdir) or not os.path.isdir(env.srcdir):
            env.end_build()
            return
        try:
            self._build.clean(env)
            env.end_build()
            self._built_once = False
            return True
        except:
            env.end_build()
            import Utils
            Utils.print_backtrace()
            return False

    def is_built_once(self):
        return self._built_once
    def get_source(self):
        return self._source
    def get_build(self):
        return self._build
    def name(self):
        return self._name
    def dependencies(self):
        return self._dependencies
