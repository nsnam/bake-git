from Configuration import Configuration
from BuildEnvironment import BuildEnvironment
from ModuleLogger import ModuleLogger
from optparse import OptionParser
from Dependencies import Dependencies,DependencyUnmet
from Exceptions import MetadataError
import sys

class Bake:
    def __init__(self):
        pass

    def _reconfigure(self,config,args):
        parser = OptionParser(usage = 'usage: %prog reconfigure [options]')
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

        # copy which modules are enabled into new config
        for old_module in old_config.enabled():
            new_module = new_config.lookup(old_module.name())
            if new_module is None:
                # ignore old enabled modules that do not exist in the new configuration
                continue
            new_config.enable(new_module)

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

    def _configure(self,config,args):
        parser = OptionParser(usage = 'usage: %prog configure [options]')
        parser.add_option("-c", "--conffile", action="store", type="string", 
                          dest="bakeconf", default="bakeconf.xml", 
                          help="The Bake metadata configuration file to use. Default: %default.")
        parser.add_option("-g", "--gui", action="store_true", 
                          dest="gui", default="False", 
                          help="Use a GUI to define the configuration.")
        parser.add_option("-e", "--enable", action="append", type="string", dest="enable",
                          default=[],
                          help="A module to enable in the Bake configuration")
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
        for module_name in options.enable:
            module = configuration.lookup(module_name)
            if module is not None:
                configuration.enable(module)
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

    def _iterate(self, configuration, functor):
        deps = Dependencies()
        class Wrapper:
            def __init__(self, module):
                self._module = module
            def function(self):
                return functor(self._module)
        for m in configuration.modules():
            wrapper = Wrapper(m)
            deps.add_dst(m, wrapper.function)
        for m in configuration.modules():
            for dependency in m.dependencies():
                src = configuration.lookup (dependency.name(), dependency.version())
                deps.add_dep(src, m, optional = dependency.is_optional())
        try:
            deps.resolve(configuration.enabled())
        except DependencyUnmet as error:
            sys.stderr.write(error.failed().name() + ' failed\n')
            sys.exit(1)

    def _options(self, parser):
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

    def _do_operation(self, config, args, operation_name, functor):
        parser = OptionParser(usage='usage: %prog ' + operation_name + ' [options]')
        self._options(parser)
        (options, args_left) = parser.parse_args(args)
        configuration = Configuration(config)
        if not configuration.read():
            sys.stderr.write('The configuration file has been changed or has moved.\n'
                             'You should consider running \'reconfigure\'.\n')
            sys.exit(1)
        env = BuildEnvironment(ModuleLogger(), 
                               configuration.compute_installdir(),
                               configuration.compute_sourcedir(), 
                               configuration.get_objdir())
        if options.one != '':
            if options.all or options.start != '' or options.after != '':
                print 'Error: incompatible options'
                sys.exit(1)
            return functor(configuration, configuration.lookup(options.one), env)
        elif options.all:
            if options.start != '' or options.after != '':
                print 'Error: incompatible options'
                sys.exit(1)
            for module in configuration.modules():
                configuration.enable(module)
        elif options.start != '':
            if options.after != '':
                print 'Error: incompatible options'
                sys.exit(1)
            must_process = []
            def _iterator(module):
                if module.name() == options.start:
                    must_process.append(0)
                if len(must_process) != 0:
                    return functor (configuration, module, env)
                else:
                    return True
            self._iterate(configuration, _iterator)
        elif options.after != '':
            # this is a list because the inner function below
            # is not allowed to modify the outer function reference
            must_process = [] 
            def _iterator(module):
                if len(must_process) != 0:
                    return functor (configuration, module, env)
                elif module.name() == options.after:
                    must_process.append(1)
                return True
            self._iterate(configuration, _iterator)
        else:
            def _iterator(module):
                return functor (configuration, module, env)
            self._iterate(configuration, _iterator)
        configuration.write()

    def _download(self,config,args):
        def _do_download(configuration, module, env):
            return module.download(env)
        self._do_operation(config, args, 'download', _do_download)

    def _update(self,config,args):
        def _do_update(configuration, module, env):
            return module.update(env)
        self._do_operation(config, args, 'update', _do_update)

    def _build(self,config,args):
        def _do_build(configuration, module, env):
            return module.build(env)
        self._do_operation(config, args, 'build', _do_build)

    def _clean(self, config, args):
        def _do_clean(configuration, module, env):
            return module.clean(env)
        self._do_operation(config, args, 'clean', _do_clean)


    def main(self, argv):
        parser = OptionParser(usage = 'usage: %prog [options] command [command options]',
                              description = "where command is one of: configure, reconfigure, "
                              "download, update, build, or clean.")
        parser.add_option("-f", "--file", action="store", type="string", 
                          dest="config_file", default="bakefile.xml", 
                          help="The Bake file to use. Default: %default.")
        parser.disable_interspersed_args()
        (options, args_left) = parser.parse_args(argv[1:])
        if len(args_left) == 0:
            parser.print_help()
            sys.exit(1)
        if args_left[0] == 'configure':
            self._configure(config=options.config_file, args=args_left[1:])
        if args_left[0] == 'reconfigure':
            self._reconfigure(config=options.config_file, args=args_left[1:])
        elif args_left[0] == 'download':
            self._download(config=options.config_file, args=args_left[1:])
        elif args_left[0] == 'update':
            self._update(config=options.config_file, args=args_left[1:])
        elif args_left[0] == 'build':
            self._build(config=options.config_file, args=args_left[1:])
        elif args_left[0] == 'clean':
            self._clean(config=options.config_file, args=args_left[1:])
