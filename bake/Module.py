import copy
import os

class NotImplemented:
    def __init__(self):
        return

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

    def download(self, logger, sourcedir):
        if not os.path.isdir(sourcedir):
            os.mkdir(sourcedir)
        dirname = os.path.join(sourcedir, self._directory())
        if os.path.isdir(dirname):
            return True
        try:
            self._source.download(logger, dirname)
            return True
        except:
            import Utils
            Utils.print_backtrace()
            return False

    def update(self, logger, sourcedir):
        dirname = os.path.join(sourcedir, self._directory())
        try:
            self._source.update(logger, dirname)
            return True
        except:
            import Utils
            Utils.print_backtrace()
            return False

    def build(self, logger, sourcedir, objdir, installdir):
        src = os.path.join(sourcedir, self._directory())
        obj = os.path.join(src,objdir)
        try:
            # delete in case this is a new build configuration
            # and there are old files around
            if not self._built_once and os.path.isdir(obj):
                self._build.clean(logger, src, obj)
            if not os.path.isdir(obj):
                os.mkdir(obj)
            if not os.path.isdir(installdir):
                os.mkdir(installdir)
            self._build.build(logger, src, obj, installdir)
            self._built_once = True
            return True
        except:
            import Utils
            Utils.print_backtrace()
            return False

    def clean(self, logger, sourcedir, objdir):
        src = os.path.join(sourcedir, self._directory())
        obj = os.path.join(src,objdir)
        try:
            self._build.clean(logger, src, obj)
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
    def _directory(self):
        if self._version is not None:
            directory = self._name + '-' + self._version
        else:
            directory = self._name
        return directory
