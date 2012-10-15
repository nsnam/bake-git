''' 
 FilesystemMonitor.py

 Monitors the file system to keep track of files changes.

 The idea is that we want to implement a version of this class
 that uses the OS native FS monitoring API. Someday, will do this
 but this code works well anywhere.
''' 

import os

class FilesystemMonitor:
    """ Main file monitoring class."""

    def __init__(self, dirname):
        self._files = None
        self._dirname = dirname
        
    def _parse(self, dirname):
        """ Search for the files on the target directory."""
    
        result = []
        for root, dirs, files in os.walk(dirname):
            result.extend([os.path.join(root, f) for f in files])
        result.sort()
        return result
    
    def start(self):
        self._files = self._parse(self._dirname)
        
    def _skip_until_different(self, a, ai, b, bi):
        """ Stops if find any difference between the presented lists."""
        
        while ai < len(a) and bi < len(b) and a[ai] == b[bi]:
            ai = ai + 1
            bi = bi + 1
        return (ai,bi)
    
    def _skip_until_equal(self, files, i, value):
        """ Stops if find the given file on the presented list."""
        
        while i < len(files) and files[i] != value:
            i = i + 1
        return i
    
    def end(self):
        """ Finds the changed files list."""
        
        files = self._parse(self._dirname)
        result = []
        i = 0
        j = 0
        while j < len(files):
            i, j = self._skip_until_different(self._files, i, files, j)
            if i != len(self._files):
                k = self._skip_until_equal(files, j, self._files[i])
            else:
                k = len(files)
            result.extend(files[j:k])
            j = k
        return result
