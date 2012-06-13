class TaskError:
    def __init__(self, reason = ''):
        self._reason = reason
        return
    @property
    def reason(self):
        return self._reason

class MetadataError:
    def __init__(self, reason = ''):
        self._reason = reason
        return
    def reason(self):
        return self._reason

class NotImplemented:
    def __init__(self):
        pass
