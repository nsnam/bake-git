import sys
import os
from bake.Exceptions import NotImplemented

class ModuleLogger:
    def __init__(self):
        self._verbose = None
        self._command_file = None
        self._std_file = None
    def _update_file(self, f):
        if self._verbose == 0:
            self._command_file = open(os.devnull, 'w')
            self._std_file = open(os.devnull, 'w')
        elif self._verbose == 1:
            self._command_file = f
            self._std_file = open(os.devnull, 'w')
        elif self._verbose == 2:
            self._command_file = f
            self._std_file = f
    def set_verbose(self, verbose):
        self._verbose = verbose if verbose <= 2 else 2
    def set_current_module(self, name):
        raise NotImplemented()
    def clear_current_module(self):
        raise NotImplemented()
    @property
    def stdout(self):
        return self._std_file
    @property
    def stderr(self):
        return self._std_file
    @property
    def commands(self):
        return self._command_file

class StdoutModuleLogger(ModuleLogger):
    def __init__(self):
        ModuleLogger.__init__(self)
        self._update_file(sys.stdout)
    def set_current_module(self, name):
        self._update_file(sys.stdout)
    def clear_current_module(self):
        pass

class LogfileModuleLogger(ModuleLogger):
    def __init__(self, filename):
        ModuleLogger.__init__(self)
        self._file = open(filename, 'w')
    def set_current_module(self, name):
        self._update_file(self._file)
    def clear_current_module(self):
        pass

class LogdirModuleLogger(ModuleLogger):
    def __init__(self, dirname):
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        self._dirname = dirname
        self._file = None
    def set_current_module(self, name):
        # XXX: we should be checking for other reserved characters
        import re
        filename = re.sub('/', '_', name)
        assert self._file is None
        self._file = open(os.path.join(self._dirname, filename + '.log'), 'w')
        self._update_file(self._file)
    def clear_current_module(self):
        self._file.close()
        self._file = None

