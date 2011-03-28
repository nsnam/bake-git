import sys

class ModuleLogger:
    def __init__(self):
        pass
    def set_current_module(self, name, version):
        pass
    def clear_current_module(self):
        pass
    @property
    def stdout(self):
        return sys.stdout
    @property
    def stderr(self):
        return sys.stdout
    @property
    def commands(self):
        return sys.stdout
