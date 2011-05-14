from Configuration import Configuration
from ModuleEnvironment import ModuleEnvironment
from ModuleLogger import StdoutModuleLogger,LogfileModuleLogger,LogdirModuleLogger
from optparse import OptionParser
from Dependencies import Dependencies,DependencyUnmet
from Exceptions import MetadataError
import sys

class MyOptionParser(OptionParser):
    def format_description(self, formatter):
        import os
        import sys
        return self.description % os.path.basename(sys.argv[0])
        

class Bake:
    def __init__(self):
        pass

    def _reconfigure(self,config,args):
        parser = OptionParser(usage = 'usage: %prog reconfigure [options]')
        self._enable_disable_options(parser)
        parser.add_option("-c", "--conffile", action="store", type="string", 
                          dest="bakeconf", default="bakeconf.xml", 
                          help="The Bake metadata configuration file to use. Default: %default.")
        (options, args_left) = parser.parse_args(args)
        old_config = Configuration(config)
        old_config.read()
        new_config = Configuration(config, 
                                   relative_directory_root = old_config.get_relative_directory_root())
        new_config.read_metadata(options.bakeconf)
        new_config.set_installdir(old_config.get_installdir())
        new_config.set_objdir(old_config.get_objdir())
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
                new_build.attribute(old_variable.name).value = old_attribute.value

        new_config.write()

    def _enable_disable_options(self, parser):
        parser.add_option("-e", "--enable", action="append", type="string", dest="enable",
                          default=[],
                          help="A module to enable in the Bake configuration")
        parser.add_option("-d", "--disable", action="append", type="string", dest="disable",
                          default=[],
                          help="A module to disable in the Bake configuration")

    def _parse_enable_disable(self, options, configuration):
        for module_name in options.enable:
            module = configuration.lookup(module_name)
            if module is not None:
                configuration.enable(module)
        for module_name in options.disable:
            module = configuration.lookup(module_name)
            if module is not None:
                configuration.disable(module)

    def _configure(self,config,args):
        parser = OptionParser(usage = 'usage: %prog configure [options]')
        self._enable_disable_options(parser)
        parser.add_option("-c", "--conffile", action="store", type="string", 
                          dest="bakeconf", default="bakeconf.xml", 
                          help="The Bake metadata configuration file to use. Default: %default.")
        parser.add_option("-g", "--gui", action="store_true", 
                          dest="gui", default="False", 
                          help="Use a GUI to define the configuration.")
        parser.add_option("-s", "--set", action="append", type="string", dest="set",
                          default=[],
                          help="Format: module:name=value. A variable to set in the Bake "
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
        (options, args_left) = parser.parse_args(args)
        configuration = Configuration(config)
        configuration.read_metadata(options.bakeconf)
        configuration.set_sourcedir(options.sourcedir)
        configuration.set_objdir(options.objdir)
        configuration.set_installdir(options.installdir)
        self._parse_enable_disable(options, configuration)
        for variable in options.set:
            data = variable.split(":")
            if len(data) == 1:
                name, value = variable.split("=")
                found = False
                for module in configuration.modules():
                    if not module.get_build().attribute(name) is None:
                        found = True
                        module.get_build().attribute(name).value = value
                if not found:
                    print 'Error: no module contains variable %s' % name
            elif len(data) == 2:
                name, value = data[1].split("=")
                module = configuration.lookup(module_name)
                if module is None:
                    print 'Error: non-existing module %s in variable specification %s' % (module_name, variable)
                    sys.exit(1)
                if module.get_build().attribute(name) is None:
                    print 'Error: non-existing variable %s in module %s' % (name, module_name)
                    sys.exit(1)
                module.get_build().attribute(name).value = value
            else:
                print 'Error: invalid variable specification: ' + variable
                sys.exit(1)
        configuration.write()

    def _iterate(self, configuration, functor, targets):
        deps = Dependencies()
        class Wrapper:
            def __init__(self, module):
                self._module = module
            def function(self):
                retval = functor(self._module)
                configuration.write()
                return retval
        for m in configuration.modules():
            wrapper = Wrapper(m)
            deps.add_dst(m, wrapper.function)
        for m in configuration.modules():
            for dependency in m.dependencies():
                src = configuration.lookup (dependency.name())
                if not src in configuration.disabled():
                    deps.add_dep(src, m, optional = dependency.is_optional())
        try:
            deps.resolve(targets)
        except DependencyUnmet as error:
            sys.stderr.write(error.failed().name() + ' failed\n')
            sys.exit(1)

    def _read_config(self, config):
        configuration = Configuration(config)
        if not configuration.read():
            sys.stderr.write('The configuration file has been changed or has moved.\n'
                             'You should consider running \'reconfigure\'.\n')
            self._reconfigure(config, [])
            configuration = Configuration(config)
        return configuration

    def _option_parser(self, operation_name):
        parser = OptionParser(usage='usage: %prog ' + operation_name + ' [options]')
        parser.add_option('--logfile', help='File in which we want to store log output '
                          'of requested operation', action="store", type="string", dest="logfile",
                          default='')
        parser.add_option('--logdir', help='Directory in which we want to store log output '
                          'of requested operation. One file per module.', action="store", 
                          type="string", dest="logdir",
                          default='')
        parser.add_option('-v', '--verbose', action='count', dest='verbose', default=2,
                          help='Increase the log verbosity level')
        parser.add_option('-q', '--quiet', action='count', dest='quiet', default=0,
                          help='Increase the log quietness level')
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
        return parser

    def _do_operation(self, config, options, functor):
        configuration = self._read_config(config)
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
                               configuration.get_objdir())
        must_disable = []
        if options.one != '':
            if options.all or options.start != '' or options.after != '':
                print 'Error: incompatible options'
                sys.exit(1)
            module = configuration.lookup(options.one)
            functor(configuration, module, env)
            configuration.write()
        elif options.all:
            if options.start != '' or options.after != '':
                print 'Error: incompatible options'
                sys.exit(1)
            def _iterator(module):
                return functor (configuration, module, env)
            self._iterate(configuration, _iterator, configuration.modules())
        elif options.start != '':
            if options.after != '':
                print 'Error: incompatible options'
                sys.exit(1)
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

    def _download(self,config,args):
        parser = self._option_parser('download')
        (options, args_left) = parser.parse_args(args)
        self._check_source_version(config, options)
        def _do_download(configuration, module, env):
            return module.download(env)
        self._do_operation(config, options, _do_download)

    def _update(self,config,args):
        parser = self._option_parser('update')
        (options, args_left) = parser.parse_args(args)
        self._check_source_version(config, options)
        def _do_update(configuration, module, env):
            return module.update(env)
        self._do_operation(config, options, _do_update)

    def _check_build_version(self, config, options):
        def _do_check(configuration, module, env):
            if not module.check_build_version(env):
                print 'Error: Could not find build tool for module "%s"' % \
                    module.name()
                sys.exit(1)
            return True
        self._do_operation(config, options, _do_check)

    def _check_source_version(self, config, options):
        def _do_check(configuration, module, env):
            if not module.check_source_version(env):
                print 'Error: Could not find source tool for module %s' % module.name()
                sys.exit(1)
            return True
        self._do_operation(config, options, _do_check)

    def _check_source_code(self, config, options):
        # let's check that we have downloaded the matching source code
        def _do_check(configuration, module, env):
            if not module.is_downloaded(env):
                print 'Error: Could not find source code for module %s. Try %s download first.' % \
                    (module.name(), sys.argv[0])
                sys.exit(1)
            return True
        self._do_operation(config, options, _do_check)


    def _build(self,config,args):
        parser = self._option_parser('build')
        parser.add_option('-j', '--jobs', help='Allow N jobs at once. Default is 1.',
                          type='int', action='store', dest='jobs', default=1)
        (options, args_left) = parser.parse_args(args)
        self._check_source_code(config, options)
        self._check_build_version(config, options)
        def _do_build(configuration, module, env):
            retval = module.build(env, options.jobs)
            if retval:
                module.update_libpath(env)
            return retval
        self._do_operation(config, options, _do_build)

    def _clean(self, config, args):
        parser = self._option_parser('clean')
        (options, args_left) = parser.parse_args(args)
        self._check_build_version(config, options)
        def _do_clean(configuration, module, env):
            module.clean(env)
            return True
        self._do_operation(config, options, _do_clean)

    def _uninstall(self, config, args):
        parser = self._option_parser('uninstall')
        (options, args_left) = parser.parse_args(args)
        def _do_uninstall(configuration, module, env):
            module.uninstall(env)
            return True
        self._do_operation(config, options, _do_uninstall)

    def _shell(self, config, args):
        parser = self._option_parser('build')
        (options, args_left) = parser.parse_args(args)
        def _do_env_update(configuration, module, env):
            module.update_libpath(env)
            return True
        env = self._do_operation(config, options, _do_env_update)
        import os
        env.run([os.environ['SHELL']], directory=env.installdir, interactive = True)

    def _query(self, config, args):
        parser = OptionParser(usage='usage: %prog query [options]')
        parser.add_option('--all', action='store_true', dest='all', default=False,
                          help='Display all known information about current configuration')
        parser.add_option('--modules', action='store_true', dest='modules', default=False,
                          help='Display information about existing modules')
        parser.add_option('--enabled-modules', action='store_true', dest='enabled_modules', 
                          default=False, help='Display information about existing enabled modules')
        (options, args_left) = parser.parse_args(args)
        configuration = self._read_config(config)
        if options.all:
            options.modules = True
        if options.modules:
            enabled = []
            def _iterator(module):
                enabled.append(module)
                return True
            self._iterate(configuration, _iterator, configuration.enabled())
            for module in configuration.modules():
                if module in configuration.enabled():
                    prefix = '++'
                elif module in enabled:
                    prefix = '+ '
                elif module in configuration.disabled():
                    prefix = '--'
                else:
                    prefix = '. '
                print '%s %s' % (prefix, module.name())
        elif options.enabled_modules:
            enabled = []
            def _iterator(module):
                enabled.append(module)
                return True
            self._iterate(configuration, _iterator, configuration.enabled())
            for module in enabled:
                print module.name()
            

    def main(self, argv):
        parser = MyOptionParser(usage = 'usage: %prog [options] command [command options]',
                                description = """Where command is one of:
  configure   : Setup the build configuration (source, build, install directory,
                and per-module build options) from the module descriptions
  reconfigure : Update the build configuration from a newer module description
  download    : Download all modules enabled during configure
  update      : Update the source tree of all modules enabled during configure
  build       : Build all modules enabled during configure
  clean       : Cleanup the source tree of all modules built previously
  shell       : Start a shell and setup relevant environment variables
  uninstall   : Remove all files that were installed during build

To get more help about each command, try:
  %s command --help
""")
        parser.add_option("-f", "--file", action="store", type="string", 
                          dest="config_file", default="bakefile.xml", 
                          help="The Bake file to use. Default: %default.")
        parser.disable_interspersed_args()
        (options, args_left) = parser.parse_args(argv[1:])
        if len(args_left) == 0:
            parser.print_help()
            sys.exit(1)
        ops = [ ['configure', self._configure],
                ['reconfigure', self._reconfigure],
                ['download', self._download],
                ['update', self._update],
                ['build', self._build],
                ['clean', self._clean],
                ['shell', self._shell],
                ['uninstall', self._uninstall],
                ['query', self._query],
               ]
        for name, function in ops:
            if args_left[0] == name:
                function(config=options.config_file, args=args_left[1:])
