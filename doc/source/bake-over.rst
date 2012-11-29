BAKE - Introduction
*******************

About Bake
==========

Bake is not a make, autoconf, or automake replacement. Bake is not a replacement for the package management tool that can be found on your how system. In short, Bake is not quite like what you are used to see around. Instead, Bake is an integration tool which is used by software developers to automate the reproducible build of a number of projects which depend on each other and which might be developed, and hosted by unrelated parties.

Bake was developed to automate the reproducible build of ns-3 taking into account that this build may be composed by a number of interdependent projects. Bake was developed to simplify the assembly of these pieces of software in a coherent and useful way.  This tutorial will show how to use bake and how to perform small configurations. Bake is an open source tool implemented in python, a deeper documentation of it can be found at `Bake's main page <http://planete.inria.fr/software/bake/index.html>`_. 

Features
========

* Automatic handling of dependencies
* Automatic download of the required sources
* Automatic correct build of the required modules
* Off-line instalation and build capabilities
* Transparency, from the user's point of view, of the methods/tools used to store and build the used modules
* Fully configurable: Possible to add new modules, create complex build tasks, create predefined builds, among others

Limitations
===========

* Currently it works under linux like systems
* The required missing system tools have to be installed by the user

Prerequisites
=============
 First of all Bake is implemented in Python, so Python is required. Bake wraps a series of commands to make the life of the user's easier.  However, it is required to have installed in the machine the third part tools used to download and build the modules. The user can verify the missing tools by calling 'bake.py check'. 
| > bake.py check
|  > Python - Ok
|  > Mercurial - Ok
|  > CVS - Ok
|  > GIT - Ok
|  > Bazaar - Ok
|  > Tar tool - Ok
|  > Unzip tool - Ok
|  > Unrar tool - Ok
|  > 7z  data compression utility - Ok
|  > XZ data compression utility - Ok
|  > Make - Ok
|  > cMake - Ok
|  > path tool - Ok
|  > Autotools - Ok

Basic usage
===========
A typical user session should be:::

  > wget http://code.nsnam.org/bake/raw-file/tip/bakeconf.xml
  > bake.py show --available
  > bake.py configure -e <one of the available modules>
  > bake.py install

The result:

* The wget command will download the last version of the bake configuration file
* **bake.py show --available** will show all the available modules
* After configuring bake with **bake.py configure** a bakefile.xml, containning the output of configuration step should be created on the same directory the user called bake configure
* After calling **bake.py install** two directories, build and source should have been created. Source will have one directory for each module downloaded and the build will contains the installed object files for all the built modules. 

The installation process may be breaked into download and build, in this way the user just need to be online to perform the download and the build may be done later, even offline. 

In this case the steps should be:::

  > wget http://code.nsnam.org/bake/raw-file/tip/bakeconf.xml
  > bake.py show --available
  > bake.py configure -e <one of the available modules>
  > bake.py download
  > bake.py build

