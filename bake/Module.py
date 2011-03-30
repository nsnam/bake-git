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
                 built_once = False):
        self._name = name
        self._version = version
        self._dependencies = copy.copy(dependencies)
        self._source = source
        self._build = build
        self._built_once = built_once

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
        env.start_build(self._name, self._version,
                        self._build.supports_objdir)
        if not self._build.check_version(env):
            print 'Error: could not find build tools for module ' + self.name()
            return False
        try:
            # delete in case this is a new build configuration
            # and there are old files around
            if not self._built_once and os.path.isdir(env.objdir):
                self._build.clean(env)
            self._build.build(env, jobs)
            env.end_build()
            self._built_once = True
            return True
        except:
            env.end_build()
            import Utils
            Utils.print_backtrace()
            return False

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
