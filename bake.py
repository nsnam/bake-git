#!/usr/bin/env python

# bake.py
#
# Bake executable, in fact it is just a wrapper for the main Bake class.  

import sys
import bake

b = bake.Bake()
b.main(sys.argv)
