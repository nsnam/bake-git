import subprocess
from bake.Exceptions import TaskError
import os

def print_backtrace():
    import sys
    import traceback
    trace = ""
    exception = ""
    exc_list = traceback.format_exception_only (sys.exc_type, sys.exc_value)
    for entry in exc_list:
        exception += entry
    tb_list = traceback.format_tb(sys.exc_info()[2])
    for entry in tb_list:
        trace += entry
    sys.stderr.write("%s\n%s" % (exception, trace))

def splitArgs(stringP):
    "Split arguments respecting agregated strings "
    
    returnValue = []
    rawSplit = stringP.split()
    compensateElement=False
    elementStr = ''
    for element in rawSplit:
        if "'" in element :
            if element.count("'") % 2 != 0 :
                if compensateElement :
                    compensateElement = False
                    returnValue.append(elementStr + " " + str(element))
                    elementStr = ''
                    element = None
                elif element.find("'") == element.rfind("'") :
                    compensateElement = True
            
        if compensateElement :
            if len(elementStr) > 0 :
                elementStr = elementStr + " " + element
            else :
                elementStr = element 
        else : 
            if element :
                returnValue.append(element)
    
    return returnValue

class ModuleAttribute:
    def __init__(self, name, value, help, mandatory):
        self._name = name
        self.value = value
        self._help = help
        self._mandatory = mandatory
    @property
    def name(self):
        return self._name
    @property
    def help(self):
        return self._help
    @property
    def is_mandatory(self):
        return self._mandatory

class ModuleAttributeBase(object):
    def __init__(self):
        self._attributes = dict()
        self._children = []
    def children(self):
        return self._children
    def add_child(self, child, name):
        self._children.append([child, name])
    def add_attribute(self, name, value, help, mandatory = False):
        assert not self._attributes.has_key(name)
        self._attributes[name] = ModuleAttribute(name, value, help, mandatory)
    def attributes(self):
        return self._attributes.values()
    def attribute(self, name):
        if not self._attributes.has_key(name):
            return None
        else:
            return self._attributes[name]

