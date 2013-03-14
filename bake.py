#!/usr/bin/env python

# bake.py
#
# Bake executable, in fact it is just a wrapper for the main Bake class.  

import sys
import bake

try:
    b = bake.Bake()
    b.main(sys.argv)
except SystemExit: 
    pass
except: 
    print("  >Unexpected exception, please contact the bake developers!<")
