#!/usr/bin/env python

# bake.py
#
# Bake executable, in fact it is just a wrapper for the main Bake class.  

import sys
import bake

try:
    b = bake.Bake()
    b.main(sys.argv)
except SystemExit as e: 
    sys.exit(e)
except: 
    print("  > Unexpected exception!\n" 
          "    Please register the error at https://www.nsnam.org/bugzilla, \n"
          "    with a copy of the trace below and, if possible, a list of steps to reproduce the error!<")
    sys.stdout.flush()
    bake.Utils.print_backtrace()