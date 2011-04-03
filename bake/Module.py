import copy
import os

class ModuleDependency:
    def __init__(self, name, version = None, optional = False):
        self._name = name
        self._version = version
        self._optional = optional
    def name(self):
        return self._name
    def version(self):
        return self._version
    def is_optional(self):
        return self._optional

class Module:
    def __init__(self, name, 
                 source,
                 build,
                 version = None,
                 dependencies = [],
                 built_once = False,
                 installed = []):
        self._name = name
        self._version = version
        self._dependencies = copy.copy(dependencies)
        self._source = source
        self._build = build
        self._built_once = built_once
        self._installed = []

    @property
    def installed(self):
        return self._installed

    def _directory(self):
        if self._version is not None:
            directory = self._name + '-' + self._version
        else:
            directory = self._name
        return directory

    def download(self, env):
        env.start_source(self._name, self._version)
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
        env.start_source(self._name, self._version)
        try:
            self._source.update(env)
            env.end_source()
            return True
        except:
            import Utils
            Utils.print_backtrace()
            env.end_source()
            return False

    def build(self, env, jobs):
        # delete installed files
        for installed in self._installed:
            os.remove(installed)
        # delete directories where files were installed if they are empty
        for installed in self._installed:
            dirname = os.path.dirname(installed)
            try:
                os.removedirs(dirname)
            except OSError:
                pass
        # setup the monitor
        monitor = FilesystemMonitor(env.installdir)
        monitor.start()

        env.start_build(self._name, self._version,
                        self._build.supports_objdir)
        try:
            # delete in case this is a new build configuration
            # and there are old files around
            if not self._built_once and os.path.isdir(env.objdir):
                self._build.clean(env)
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
        env.start_build(self._name, self._version,
                        self._build.supports_objdir)
        retval = self._build.check_version(env)
        env.end_build()
        return retval

    def is_downloaded(self, env):
        env.start_source(self._name, self._version)
        retval = os.path.isdir(env.srcdir)
        env.end_source()
        return retval

    def check_source_version(self, env):
        env.start_source(self._name, self._version)
        retval = self._source.check_version(env)
        env.end_source()
        return retval


    def update_libpath(self, env):
        env.start_build(self._name, self._version,
                        self._build.supports_objdir)
        env.add_libpaths(self._build.libpaths)
        env.end_build()

    def clean(self, env):
        env.start_build(self._name, self._version,
                        self._build.supports_objdir)
        try:
            self._build.clean(env)
            env.end_build()
            self._built_once = False
            return True
        except:
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
    def version(self):
        return self._version
    def dependencies(self):
        return self._dependencies
