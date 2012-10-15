''' 
 Exeptions.py

 This file stores the Exceptions raised by Bake.
''' 

class TaskError:
    """ Error found during the execution of the required options. """
    
    def __init__(self, reason = ''):
        self._reason = reason
        return
    @property
    def reason(self):
        return self._reason

class MetadataError:
    """ Error reading the configuration. """
    
    def __init__(self, reason = ''):
        self._reason = reason
        return
    def reason(self):
        return self._reason

class NotImplemented:
    """ A not yet implemented option was met. """
    
    def __init__(self):
        pass
