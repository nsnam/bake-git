''' 
 Bake.py

 This is the main Bake file, it stores all the classes related to the
 basic Bake operation. The class Bake is responsible to identify and 
 execute the defined options  
'''

from bake.Configuration import Configuration
from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger, LogfileModuleLogger, LogdirModuleLogger
from optparse import OptionParser
from bake.Dependencies import Dependencies, DependencyUnmet
from bake.Exceptions import MetadataError
from bake.Utils import ColorTool
import sys
import os
import signal

def signal_handler(signal, frame):
    """ Handles Ctrl+C keyboard interruptions """
    
    print (' > Bake was aborted! (Ctrl+C)')
    os._exit(0)
        
class MyOptionParser(OptionParser):
    def format_description(self, formatter):
        import os
        import sys
        return self.description % os.path.basename(sys.argv[0])
        

class Bake:
    """ Main Bake class """
    
    main_options = "" 
    
    def __init__(self):
        pass
    
    def _error(self, string):
        """ Handles hard exceptions, the kind of exceptions Bake should not 
        recover from.
        """

        import sys
        print(' > Error: %s ' % string)
        if Bake.main_options.debug:
            import bake.Utils
            bake.Utils.print_backtrace()           
        else:
            print('   For more information call Bake with --debug and/or'
                  ' -vvv (bake --help)')
        sys.exit(1)
        
    def _fix_config(self, config, args):
        """Handles the fix_cinfig command line option. It intends to fix 
        manually changed files and updates the in-use configuration with 
        new values."""
        
        parser = OptionParser(usage='usage: %prog fix-config [options]')
        self._enable_disable_options(parser)
        parser.add_option("-c", "--conffile", action="store", type="string",
                          dest="bakeconf", default="bakeconf.xml",
                          help="The Bake meta-data configuration from where to"
                          " get the updated modules file to use. Default: %default.")
        parser.add_option("--objdir", action="store", type="string",
                          dest="objdir", default=None,
                          help="The per-module directory where the object files of each module "
                          "will be compiled.")
        parser.add_option("--sourcedir", action="store", type="string",
                          dest="sourcedir", default=None,
                          help="The directory where the source code of all modules "
                          "will be downloaded.")
        parser.add_option("-i", "--installdir", action="store", type="string",
                          dest="installdir", default=None,
                          help="The directory where all modules will be installed.")

        parser.add_option("-t", "--target_file", action="store", type="string",
                          dest="targetfile", default=None,
                          help="New target file, if not defined Bake"
                          " overwrites the present configuration file.")

        (options, args_left) = parser.parse_args(args)

        # Stores the present configuration         
        old_config = Configuration(config)
        old_config.read()
        
        if options.targetfile:
            new_config = Configuration(options.targetfile,
                                   relative_directory_root=old_config.get_relative_directory_root())
        else:
            new_config = Configuration(config,
                                   relative_directory_root=old_config.get_relative_directory_root())
            
        new_config.read_metadata(options.bakeconf)
        
        # Checks if the directories where set and if so set the new config file
        # with the new parameters, or let the old ones
        if options.installdir:
            new_config.set_installdir(options.installdir)
        else:
            new_config.set_installdir(old_config.get_installdir())
        if options.objdir:
            new_config.set_objdir(options.objdir)
        else:
            new_config.set_objdir(old_config.get_objdir())
        if options.sourcedir:
            new_config.set_sourcedir(options.sourcedir)
        else:    
            new_config.set_sourcedir(old_config.get_sourcedir())

        # copy installed files.
        for old_module in old_config.modules():
            new_module = new_config.lookup(old_module.name())
            if new_module is None:
                # ignore old modules that do not exist in the new configuration
                continue
            new_module.installed = old_module.installed

        # copy which modules are enabled into new config
        for old_module in old_config.enabled():
            new_module = new_config.lookup(old_module.name())
            if new_module is None:
                # ignore old enabled modules that do not exist in the new configuration
                continue
            new_config.enable(new_module)

        # copy which modules are disabled into new config
        for old_module in old_config.disabled():
            new_module = new_config.lookup(old_module.name())
            if new_module is None:
                # ignore old disabled modules that do not exist in the new configuration
                continue
            new_config.disable(new_module)

        # now, parse new enabled/disabled options
        self._parse_enable_disable(options, new_config)

        # copy old variables into new config for all modules
        for old_module in old_config.modules():
            new_module = new_config.lookup(old_module.name())
            if new_module is None:
                # ignore old modules that do not exist in the new configuration
                continue
            old_build = old_module.get_build()
            new_build = new_module.get_build()
            for old_attribute in old_build.attributes():
                if new_build.attribute(old_attribute.value) is None:
                    continue
                new_build.attribute(old_attribute.name).value = old_attribute.value

        new_config.write()

    def _enable_disable_options(self, parser):
        """ Allows the parser to recognize --enable and --disable options."""

        parser.add_option("-e", "--enable", action="append", type="string", 
                          dest="enable", default=[],
                          help="A module to enable in the Bake configuration")
        parser.add_option("-d", "--disable", action="append", type="string", 
                          dest="disable", default=[],
                          help="A module to disable in the Bake configuration")
        parser.add_option("-a", "--enable-all", action="store_true",
                          dest="enable_all", default=None,
                          help="Enable all modules.")
        parser.add_option("-m", "--enable-minimal", action="store_true",
                          dest="enable_minimal", default=None,
                          help="Disable all non-mandatory dependencies.")

    def _enable(self, enable, configuration):
        """ Handles the --enable option, setting defined modules as enable."""
        
        for module_name in enable:
            module = configuration.lookup(module_name)
            if not module:
                self._error('Module "%s" not found' % module_name)
            configuration.enable(module)

    def _disable(self, disable, configuration):
        """ Handles the --disable option, setting the defined modules as disable."""

        for module_name in disable:
            module = configuration.lookup(module_name)
            if not module:
                self._error('Module "%s" not found' % module_name)
            configuration.disable(module)

    def _variables_process(self, items, configuration, is_append):
        """ Handles the defined configured variables ."""
        
        for module_name, name, value in items:
            if module_name:
                module = configuration.lookup(module_name)
                if not module:
                    self._error('Module "%s" not found' % module_name)
                if not module.get_build().attribute(name):
                    self._error('Module "%s" has no attribute "%s"' % 
                                (module_name, name))
                if is_append:
                    module.get_build().attribute(name).value = \
                        module.get_build().attribute(name).value + ' ' + value
                else:
                    module.get_build().attribute(name).value = value
            else:
                for module in configuration.modules():
                    if module.get_build().attribute(name):
                        if is_append and module.get_build().attribute(name).value :
                            module.get_build().attribute(name).value = \
                                module.get_build().attribute(name).value + ' ' + value
                        else:
                            module.get_build().attribute(name).value = value
        
    def _parse_enable_disable(self, options, configuration):
        """ Identify the enabled and disabled options passed as parameters 
        in the configuration.
        """
        
        # enables/disables the explicit enable/disable modules passed as argument
        self._enable(options.enable, configuration)
        self._disable(options.disable, configuration)
        
        # if the option -a is used, meaning all the modules should be enabled
        if options.enable_all:
            for module in configuration.modules():
                configuration.enable(module)
                
        # if the option -m is used, meaning the minimum configuration should be used
        # it disables all the non mandatory dependencies
        if options.enable_minimal:
            enabled = []
            def _enabled_iterator(module):
                """ Assigns the module as enabled."""    
                enabled.append(module)
                return True
            
            self._iterate(configuration, _enabled_iterator,
                          configuration.enabled(),
                          follow_optional=True)
            enabled_optional = []
            def _enabled_optional_iterator(module):
                enabled_optional.append(module)
                return True
            self._iterate(configuration, _enabled_optional_iterator,
                          configuration.enabled(),
                          follow_optional=False)
            for module in enabled:
                if not module in enabled_optional:
                    configuration.disable(module)

    def _parse_variable(self, string, configuration):
        """ Verifies if the module and requested attribute exists."""
        
        retval = []
        data = string.split(":")
        
        # if it is an setting for all the modules that contains such variable
        if len(data) == 1:
            name, value = string.split("=")
            for module in configuration.modules():
                if module.get_build().attribute(name):
                    retval.append((module, name, value))
            if not retval:
                print ('Error: no module contains variable %s' % name)
        # if it is a setting for a specific module 
        elif len(data) == 2:
            name, value = data[1].split("=")
            module = configuration.lookup(data[0])
            if not module:
                self._error('non-existing module %s in variable specification %s' % \
                                (name, string))
            if not module.get_build().attribute(name):
                self._error('non-existing variable %s in module %s' % 
                            (name, module._name))
            retval.append((module, name, value))
        # if the variable is set incorrectly 
        else:
            self._error('invalid variable specification: "%s"' % string)
        return retval
        
    def _configure(self, config, args):
        """ Handles the configuration option for %prog """
        
        # sets the options the parser should recognize for the configuration
        parser = OptionParser(usage='usage: %prog configure [options]')
        self._enable_disable_options(parser)
        parser.add_option("-c", "--conffile", action="store", type="string",
                          dest="bakeconf", default="bakeconf.xml",
                          help="The Bake meta-data configuration file to use. Default: %default.")
        parser.add_option("-g", "--gui", action="store_true",
                          dest="gui", default="False",
                          help="Use a GUI to define the configuration.")
        parser.add_option("-s", "--set", action="append", type="string", 
                          dest="set",
                          default=[],
                          help="Format: module:name=value. A variable to set in the Bake "
                          "configuration for the matching module.")
        parser.add_option("--append", action="append", type="string", 
                          dest="append", default=[],
                          help="Format: module:name=value. A variable to append to in the Bake "
                          "configuration for the matching module.")
        parser.add_option("--objdir", action="store", type="string",
                          dest="objdir", default="objdir",
                          help="The per-module directory where the object files of each module "
                          "will be compiled.")
        parser.add_option("--sourcedir", action="store", type="string",
                          dest="sourcedir", default="source",
                          help="The directory where the source code of all modules "
                          "will be downloaded.")
        parser.add_option("-i", "--installdir", action="store", type="string",
                          dest="installdir", default="build",
                          help="The directory where all modules will be installed.")
        parser.add_option("-p", "--predefined", action="store", type="string",
                          dest="predefined", default=None,
                          help="A predefined configuration to apply")

        # sets the configuration values got from the line command
        (options, args_left) = parser.parse_args(args)
        configuration = Configuration(config)
        configuration.read_metadata(options.bakeconf)
        configuration.set_sourcedir(options.sourcedir)
        configuration.set_objdir(options.objdir)
        configuration.set_installdir(options.installdir)
        
        # if used the predefined settings, reads the predefined configuration
        if options.predefined:
            data = options.predefined.split(':')
            requested = None
            predefined = configuration.read_predefined(options.bakeconf)
            if len(data) == 1:
                requested = data[0]
            elif len(data) == 2:
                predefined += configuration.read_predefined(data[0])
                requested = data[1]
            else:
                self._error('Invalid --predefined content: "%s"' % predefined)
            for p in requested.split(','):
                found = False
                for predef in predefined:
                    if predef.name == p:
                        found = True
                        self._enable(predef.enable, configuration)
                        self._disable(predef.disable, configuration)
                        self._variables_process(predef.variables_set, 
                                                configuration, is_append=False)
                        self._variables_process(predef.variables_append, 
                                                configuration, is_append=True)
                        directories = predef.directories
                        if 'sourcedir' in directories:
                            configuration.set_sourcedir(directories['sourcedir'])
                        if 'objdir' in directories:
                            configuration.set_objdir(directories['objdir'])
                        if 'installdir' in directories:
                            configuration.set_installdir(directories['installdir'])
                        break
                if not found:
                    self._error('--predefined: "%s" not found.' % p)
                    
        # Registers the modules are that enabled/disabled 
        # handles the -a, -m, --disable, --enable tags            
        self._parse_enable_disable(options, configuration)
        
        # handles the set command line option, to overwrite the specific 
        # module setting with the new specified value
        for variable in options.set:
            matches = self._parse_variable(variable, configuration)
            for module, name, value in matches:
                module.get_build().attribute(name).value = value

        # handles the append command line option, to add the new 
        # value to the module setting
        for variable in options.append:
            matches = self._parse_variable(variable, configuration)
            for module, name, value in matches:
                current_value = module.get_build().attribute(name).value
                module.get_build().attribute(name).value = current_value + ' ' + value
        configuration.write()

    def _iterate(self, configuration, functor, targets, follow_optional=True):
        """Iterates over the configuration modules applying the functor 
        function and solve reminding dependencies.
        """
        
        deps = Dependencies()
        class Wrapper:
            def __init__(self, module):
                self._module = module
            def function(self):
                retval = functor(self._module)
                configuration.write()
                return retval
        # for all the modules saves the configuration
        for m in configuration.modules():
            wrapper = Wrapper(m)
            deps.add_dst(m, wrapper.function)
        # Review the dependencies of all the configured modules
        for m in configuration.modules():
            for dependency in m.dependencies():
                src = configuration.lookup (dependency.name())
                
                # verifies if the dependency really exists in the configuration
                # if not we could have a problem of a corrupt, or badly 
                # configured xml file, e.g. misspelled module name  
                if src is None:
                    self._error('Dependency "%s" not found' % dependency.name())
                 
                if not src in configuration.disabled():
                    # if it is set to add even the optional modules, or the 
                    # dependency is not optional, add the module it depends on 
                    # as a dependency 
                    if follow_optional or not dependency.is_optional():
                        deps.add_dep(src, m, optional=dependency.is_optional())
                        
        try:
            deps.resolve(targets)
        except DependencyUnmet as error:
            self._error('%s failed' % error.failed().name())

    def _read_config(self, config, directory=None):
        """Reads the configuration file."""

        configuration = Configuration(config, directory)
        if not configuration.read():
            sys.stderr.write('The configuration file has been changed or has moved.\n'
                             'Running \'fix-config\'. You should consider running it\n'
                             'yourself to tweak some parameters if needed.\n')
            self._fix_config(config, [])
            configuration = Configuration(config)
            if not configuration.read():
                self._error('Oops. \'fix-config\' did not succeed. You should consider\n'
                            'deleting your bakefile and running \'configure\' again.')

        return configuration

    def _option_parser(self, operation_name):
        """Adds generic options to the options parser. Receives the name of the 
        present option as parameter.
        """
        
        parser = OptionParser(usage='usage: %prog ' + operation_name + ' [options]')
        parser.add_option('--logfile', help='File in which we want to store log output '
                          'of requested operation', action="store", type="string", dest="logfile",
                          default='')
        parser.add_option('--logdir', help='Directory in which we want to store log output '
                          'of requested operation. One file per module.', action="store",
                          type="string", dest="logdir",
                          default='')
        parser.add_option('-v', '--verbose', action='count', dest='verbose', 
                          default=0, help='Increase the log verbosity level')
        parser.add_option('-q', '--quiet', action='count', dest='quiet', 
                          default=0, help='Increase the log quietness level')
        parser.add_option("-o", "--one", action="store", type="string",
                          dest="one", default="",
                          help="Process only the module specified.")
        parser.add_option("-a", "--all", action="store_true",
                          dest="all", default=False,
                          help="Process all modules")
        parser.add_option("-s", "--start", action="store", type="string",
                          dest="start", default="",
                          help="Process all modules enabled starting from the module specified.")
        parser.add_option("--after", action="store", type="string",
                          dest="after", default="",
                          help="Process all modules enabled starting after the module specified.")
        parser.add_option("-i", "--environment_file_identification", 
                          action="store", type="string",
                          dest="environment_file_identification", 
                          default="bakeSetEnv.sh",
                          help="Name of the environment setting file")
        parser.add_option("-x", "--no_environment_file", action='store_true', 
                          dest='no_environment_file', default=False,
                          help='Do not create the environment file for this run')
        
        return parser

    def _do_operation(self, config, options, functor, directory=None):
        """Applies the function, passed as parameter, over the options."""
        
        configuration = self._read_config(config, directory)
        if options.logdir == '' and options.logfile == '':
            logger = StdoutModuleLogger()
        elif options.logdir != '':
            assert options.logfile == ''
            logger = LogdirModuleLogger(options.logdir)
        else:
            assert options.logfile != ''
            logger = LogfileModuleLogger(options.logfile)
        verbose = options.verbose - options.quiet
        verbose = verbose if verbose >= 0 else 0
        logger.set_verbose(verbose)

        env = ModuleEnvironment(logger,
                               configuration.compute_installdir(),
                               configuration.compute_sourcedir(),
                               configuration.get_objdir(), 
                               Bake.main_options.debug)
        must_disable = []
        if options.one != '':
            if options.all or options.start != '' or options.after != '':
                self._error('incompatible options')
            module = configuration.lookup(options.one)
            functor(configuration, module, env)
            configuration.write()
        elif options.all:
            if options.start != '' or options.after != '':
                self._error('incompatible options')
            def _iterator(module):
                return functor (configuration, module, env)
            self._iterate(configuration, _iterator, configuration.modules())
        elif options.start != '':
            if options.after != '':
                self._error('incompatible options')
            must_process = []
            first_module = configuration.lookup(options.start)
            def _iterator(module):
                if module == first_module:
                    must_process.append(0)
                if len(must_process) != 0:
                    return functor (configuration, module, env)
                else:
                    return True
            self._iterate(configuration, _iterator, configuration.enabled())
        elif options.after != '':
            # this is a list because the inner function below
            # is not allowed to modify the outer function reference
            must_process = [] 
            first_module = configuration.lookup(options.after)
            def _iterator(module):
                if len(must_process) != 0:
                    return functor (configuration, module, env)
                elif module == first_module:
                    must_process.append(1)
                return True
            self._iterate(configuration, _iterator, configuration.enabled())
        else:
            def _iterator(module):
                return functor (configuration, module, env)
            self._iterate(configuration, _iterator, configuration.enabled())
        return env

    def _install(self, config, args):
        """Handles the install command line option."""

        print("Installing selected module and dependencies.")
        print("Please, be patient, this may take a while!")
        returnValue = self._download(config, args);
        if not returnValue:
            return self._build(config, args)
        

    def _download(self, config, args):
        """Handles the download command line option."""

        parser = self._option_parser('download')
        (options, args_left) = parser.parse_args(args)
        self._check_source_version(config, options)
        def _do_download(configuration, module, env):
            return module.download(env)
        self._do_operation(config, options, _do_download)

    def _update(self, config, args):
        """Handles the update command line option."""

        parser = self._option_parser('update')
        (options, args_left) = parser.parse_args(args)
        self._check_source_version(config, options)
        def _do_update(configuration, module, env):
            return module.update(env)
        self._do_operation(config, options, _do_update)

    def _check_build_version(self, config, options):
        """Checks if the required build tools are available in the machine."""
        
        def _do_check(configuration, module, env):
            if not module.check_build_version(env):
                env._logger.commands.write('Could not find build tool for'
                                            ' module "%s"\n' % module.name())
                return False
            return True
        self._do_operation(config, options, _do_check)

    def _check_source_version(self, config, options):
        """Checks if the source can be handled by the programs in the machine."""
         
        def _do_check(configuration, module, env):
            if not module.check_source_version(env):
                env._logger.commands.write('Could not find source tool'
                                            ' for module %s' % module.name())
                return False
            return True
        self._do_operation(config, options, _do_check)

    def _check_source_code(self, config, options, directory=None):
        """ Checks if  we have already downloaded the matching source code."""
        
        def _do_check(configuration, module, env):
            if not module.is_downloaded(env):
                env._logger.commands.write('Could not find source code for'
                                            ' module %s. Try %s download first.'
                                             %(module.name(), sys.argv[0]))
                return False
            return True
        self._do_operation(config, options, _do_check, directory)


    def _build(self, config, args):
        """Handles the build command line option."""
        
        parser = self._option_parser('build')
        parser.add_option('-j', '--jobs', help='Allow N jobs at once.'
                          ' Default is 1.',type='int', action='store', 
                          dest='jobs', default=1)
        parser.add_option('--force_clean', help='Forces the call of the clean'
                          ' option for the build.', action="store_true", 
                          default=False, dest='force_clean')
        (options, args_left) = parser.parse_args(args)
        self._check_source_code(config, options)
        self._check_build_version(config, options)
        
        def _do_build(configuration, module, env):
            retval = module.build(env, options.jobs, options.force_clean)
            if retval:
                module.update_libpath(env)
            return retval
        env = self._do_operation(config, options, _do_build)
        
        if not options.no_environment_file:
            env.create_environement_file(options.environment_file_identification)

    def _clean(self, config, args):
        """Handles the clean command line option."""
        
        parser = self._option_parser('clean')
        (options, args_left) = parser.parse_args(args)
        self._check_build_version(config, options)
        
        def _do_clean(configuration, module, env):
            module.clean(env)
            return True
        self._do_operation(config, options, _do_clean)

    def _uninstall(self, config, args):
        """Handles the uninstall command line option."""
        
        parser = self._option_parser('uninstall')
        (options, args_left) = parser.parse_args(args)
        def _do_uninstall(configuration, module, env):
            module.uninstall(env)
            return True
        self._do_operation(config, options, _do_uninstall)

    def _shell(self, config, args):
        """Handles the shell command line option."""
        
        parser = self._option_parser('build')
        (options, args_left) = parser.parse_args(args)
        
        def _do_env_update(configuration, module, env):
            module.update_libpath(env)
            return True
        env = self._do_operation(config, options, _do_env_update)
        import os
        env.run([os.environ['SHELL']], directory=env.objdir, interactive=True)

    def _check(self, config, args):
        """Handles the check command line option."""
        
        checkPrograms = [['testas', 'error message'],
                         ['python', 'Python'],
                         ['hg', 'Mercurial'],
                         ['cvs', 'CVS'],
                         ['bzr', 'Bazaar'],
                         ['tar', 'Tar tool'],
                         ['unzip', 'Unzip tool'],
                         ['unrar', 'Unrar tool'],
                         ['git', 'GIT'],
                         ['make', 'Make'],
                         ['cmake', 'cMake'],
                         ['patch', 'path tool'],
                         ['autoreconf', 'Autotools']
                         ]
        parser = self._option_parser('build')
        (options, args_left) = parser.parse_args(args)
        def _do_env_check(configuration, module, env):
            return True
        
        env = self._do_operation(config, options, _do_env_check)
        
        colorTool = ColorTool()
        for element in checkPrograms:
            if env.check_program(element[0]):
                colorTool.cPrint(colorTool.OK, " > " + element[1] + " - Ok")                    
            else:
                colorTool.cPrint(colorTool.WARNING, " > " + element[1] + 
                                 " - is missing")


    def _show_one_builtin(self, builtin, string, variables):
        """Go over the available builtins handling tools."""

        import textwrap
        if builtin.name() != 'none':
            print ('%s %s' % (string, builtin.name()))
            if variables:
                for attribute in builtin().attributes():
                    print ('    %s=%s' % (attribute.name, attribute.value))
                    lines = ['      %s' % line for line in textwrap.wrap(attribute.help)]
                    print ('\n'.join(lines))

    def _show_variables(self, module):
        """Handles the show the variables available for source and build."""
        
        source = module.get_source()
        if source.attributes():
            print ('  source %s' % source.name())
            for attribute in source.attributes():
                print ('    %s=%s' % (attribute.name, attribute.value))
        build = module.get_build()
        
        if build.attributes():
            print ('  build %s' % build.name())
            for attribute in build.attributes():
                print ('    %s=%s' % (attribute.name, attribute.value))

    def _show_builtin(self, config, args):
        """Handles the show one builtin command line option."""
        
        from bake.ModuleSource import ModuleSource
        from bake.ModuleBuild import ModuleBuild
        parser = OptionParser(usage='usage: %prog show [options]')
        parser.add_option('-a', '--all', action='store_true', dest='all', 
                          default=False,
                          help='Display all known information about builtin source and build commands')
        parser.add_option('--source', action='store_true', dest='source', 
                          default=False,
                          help='Display information about builtin source commands')
        parser.add_option('--build', action='store_true', dest='build', 
                          default=False,
                          help='Display information about builtin build commands')
        parser.add_option('--variables', action='store_true', dest='variables', 
                          default=False,
                          help='Display variables for builtin commands')
        (options, args_left) = parser.parse_args(args)
            
        if options.all :
            options.source = True
            options.build = True
            options.variables = True
        elif not options.source and not options.build :
            options.source = True
            options.build = True
          
            
        if options.source:
            for source in ModuleSource.subclasses():
                self._show_one_builtin(source, 'source', options.variables)
                
        if options.build:
            for build in ModuleBuild.subclasses():
                self._show_one_builtin(build, 'build', options.variables)


    def show_module(self, state, options, label):
        """ Handles the printing of the information of modules and dependencies."""
        
        for module in state:
            print('module: %s (%s)' % (module.name(), label))
            dependencies = module.dependencies()
            if dependencies:
                print('  depends on:')
                for dependsOn in module.dependencies():
                    print('     %s (optional:%s)' % 
                          (dependsOn.name(), dependsOn.is_optional()))      
            else:
                print('  No dependencies!')
                
            if options.variables:
                self._show_variables(module)

        return module

    def _show(self, config, args):
        """Handles the show command line option."""
        
        parser = OptionParser(usage='usage: %prog show [options]')
        parser.add_option("-c", "--conffile", action="store", type="string",
                          dest="bakeconf", default="bakeconf.xml",
                          help="The Bake meta-data configuration file to use if a Bake file is "
                          "not specified. Default: %default.")
        parser.add_option('-a', '--all', action='store_true', dest='all', 
                          default=False,
                          help='Display all known information about current configuration')
        parser.add_option('--enabled', action='store_true', dest='enabled',
                          default=False, help='Display information about existing enabled modules')
        parser.add_option('--disabled', action='store_true', dest='disabled',
                          default=False, help='Display information about existing disabled modules')
        parser.add_option('--variables', action='store_true', dest='variables', 
                          default=False,
                          help='Display information on the variables set for the modules selected')
        parser.add_option('--predefined', action='store_true', dest='predefined', 
                          default=False,
                          help='Display information on the items predefined')
        parser.add_option('--directories', action='store_true', dest='directories', 
                          default=False,
                          help='Display information about which directories have been configured')
        (options, args_left) = parser.parse_args(args)

        # adds a default value so that show will show something even if there is
        # no option 
        if not args:
            options.enabled = True

        import os
        if os.path.isfile(config):
            configuration = self._read_config(config)
        else:
            configuration = Configuration(config)
            configuration.read_metadata(options.bakeconf)
            
        if options.all:
            options.enabled = True
            options.disabled = True
            options.directories = True
            options.variables = True
            options.predefined = True
            
        if options.directories:
            print ('installdir   : ' + configuration.compute_installdir())
            print ('sourcedir    : ' + configuration.compute_sourcedir())
            print ('objdir       : ' + configuration.get_objdir())


        enabled = []
        
        def _iterator(module):
            enabled.append(module)
            return True
        self._iterate(configuration, _iterator, configuration.enabled())
        disabled = filter(lambda module: not module in enabled, configuration.modules())

        if options.enabled:
            module = self.show_module(enabled, options, 'enabled')

        if options.disabled:
            module = self.show_module(disabled, options, 'disabled')

    options = ""
    

    def main(self, argv):
        """Main Bake function."""
       
        # catches Ctrl-c 
        signal.signal(signal.SIGINT, signal_handler)
        parser = MyOptionParser(usage='usage: %prog [options] command [command options]',
                                description="""Where command is one of:
  install      : Downloads the configured modules AND makes the build in one step
  configure    : Setup the build configuration (source, build, install directory,
                 and per-module build options) from the module descriptions
  fix-config  : Update the build configuration from a newer module description
  download     : Download all modules enabled during configure
  update       : Update the source tree of all modules enabled during configure
  build        : Build all modules enabled during configure
  clean        : Cleanup the source tree of all modules built previously
  shell        : Start a shell and setup relevant environment variables
  uninstall    : Remove all files that were installed during build
  show         : Report on build configuration
  show-builtin : Report on builtin source and build commands
  check        : Checks if all the required tools are available on the system

To get more help about each command, try:
  %s command --help
""")
        parser.add_option("-f", "--file", action="store", type="string",
                          dest="config_file", default="bakefile.xml",
                          help="The Bake file to use, and the target "
                          "configuration/reconfiguration. Default: %default.")
        parser.add_option("--debug", action="store_true",
                          dest="debug", default=False,
                          help="Prints out all the error messages and problems.")
        parser.disable_interspersed_args()
        (options, args_left) = parser.parse_args(argv[1:])
        
        Bake.main_options = options

        if len(args_left) == 0:
            parser.print_help()
            sys.exit(1)
        ops = [ ['install', self._install],
                ['configure', self._configure],
                ['fix-config', self._fix_config],
                ['download', self._download],
                ['update', self._update],
                ['build', self._build],
                ['clean', self._clean],
                ['shell', self._shell],
                ['uninstall', self._uninstall],
                ['show', self._show],
                ['show-builtin', self._show_builtin],
                ['check', self._check],
               ]
        
        for name, function in ops: 
            if args_left[0] == name:
                if options.debug:
                    function(config=options.config_file, args=args_left[1:])
                else:
                    try:
                        function(config=options.config_file, args=args_left[1:])
                    except Exception as e:
                        print (e.message)
                        sys.exit(1)
