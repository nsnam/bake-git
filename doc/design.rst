Bake, a software construction tool
==================================

Bake is not a make replacement. It is not a 

Usage
=====

bake -c .config.xml configure -f bakefile.xml 
bake -c .config.xml download
bake update
bake build
bake build --start-at=foo
bake update --all
bake update --one=foo
bake download --all
bake download --one=foo
bake build --one=foo
