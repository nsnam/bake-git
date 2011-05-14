from Module import Module,ModuleDependency
from ModuleSource import ModuleSource,InlineModuleSource
from ModuleBuild import ModuleBuild,InlineModuleBuild
import xml.etree.ElementTree as ET
from Exceptions import MetadataError
import os
import sys

class MetadataFile:
    def __init__(self, filename, h=''):
        import os
        self._filename = os.path.realpath(filename)
        self._h = h
    def filename(self):
        return self._filename
    def h(self):
         import hashlib
         m = hashlib.md5()
         try:
             f = open(self._filename)
             m.update(f.read())
             f.close()
             return m.hexdigest()
         except:
             return ''
    def is_hash_ok(self):
        return self.h() == self._h

class Configuration:
    def __init__(self, bakefile, relative_directory_root = None):
        self._enabled = []
        self._disabled = []
        self._modules = []
        self._installdir = None
        self._objdir = None
        self._sourcedir = None
        self._metadata_file = None
        self._bakefile = os.path.abspath(bakefile)
        if relative_directory_root is None:
            self._relative_directory_root = os.path.relpath(os.getcwd(), 
                                                            os.path.dirname(self._bakefile))
        else:
            self._relative_directory_root = relative_directory_root

    def read_metadata(self, filename):
        self._metadata_file = MetadataFile(filename)
        et = ET.parse(filename)
        self._read_metadata(et)

    def _check_mandatory_attributes(self, attribute_base, top_level_node, type_string, module_string):
        attributes_present = [child.get('name') for child in top_level_node.findall('attribute')]
        for attribute in attribute_base.attributes():
            if attribute.is_mandatory and not attribute.name in attributes_present:
                sys.stderr.write('Error: mandatory attribute "%s" is missing from module "%s" in node "%s"\n' % (attribute.name, module_string, type_string))
                sys.exit(1)

    def _read_attributes(self, attribute_base, top_level_node, type_string, module_string):
        # now, read the attributes from file.
        for attribute_node in top_level_node.findall('attribute'):
            attr_name = attribute_node.get('name')
            attr_value = attribute_node.get('value', None)
            if attribute_base.attribute(attr_name) is None:
                sys.stderr.write('Error: attribute "%s" is not supported by %s node of type "%s"\n' % 
                                 (attr_name, type_string, top_level_node.get('type')))
                sys.exit(1)
            attribute_base.attribute(attr_name).value = attr_value

    def _write_attributes(self, attribute_base, top_level_node):
        for attribute in attribute_base.attributes():
            if not attribute.value is None:
                node = ET.Element('attribute', {'name' : attribute.name,
                                                'value' : attribute.value})
                top_level_node.append(node)

    def _create_obj_from_node(self, node, classBase):
        if node.get('type') == 'inline':
            code_node = node.find('code')
            if node is None:
                sys.stderr.write('Error: no code tag in inline module\n')
                sys.exit(1)
            classname = node.get('classname')
            import codeop
            exec code_node.text in globals(), locals()
            obj = eval(classname + '()')
            obj.__hidden_source_code = code_node.text
        else:
            obj = classBase.create(node.get('type'))
        return obj

    def _create_node_from_obj(self, obj, node_string):
        if obj.__class__.name() == 'inline':
            node = ET.Element(node_string, {'type' : 'inline',
                                            'classname' : obj.__class__.__name__})
            code = ET.Element('code')
            code.text = obj.__hidden_source_code
            node.append(code)
        else:
            node = ET.Element(node_string, {'type' : obj.__class__.name()})
        return node

    def _read_libpath(self, node, build):
        for libpath in node.findall('addlibpath'):
            location = libpath.get('location', None)
            assert location != None
            build.add_libpath(location)

    def _write_libpath(self, node, build):
        for libpath in build.libpaths:
            libpath_node = ET.Element('addlibpath', {'location' : libpath})
            node.append(libpath_node)

    def _read_installed(self, node):
        installed = []
        for installed_node in node.findall('installed'):
            installed.append(installed_node.get('value', None))
        return installed

    def _write_installed(self, node, installed):
        for installed in installed:
            installed_node = ET.Element('installed', {'value' : installed})
            node.append(installed_node)

    
    def _read_metadata(self, et):
        # function designed to be called on two kinds of xml files.
        modules = et.findall('module')
        for module_node in modules:
            name = module_node.get('name')
            installed = self._read_installed(module_node)

            source_node = module_node.find('source')
            source = self._create_obj_from_node(source_node, ModuleSource)
            self._check_mandatory_attributes(source, source_node, 'source', name)
            self._read_attributes(source, source_node, 'source', name)

            build_node = module_node.find('build')
            build = self._create_obj_from_node(build_node, ModuleBuild)
            build._supports_objdir = False if build_node.get('objdir', 'srcdir') == 'srcdir' else True
            self._check_mandatory_attributes(build, build_node, 'build', name)
            self._read_attributes(build, build_node, 'build', name)
            self._read_libpath(build_node, build)

            dependencies = []
            for dep_node in module_node.findall('depends_on'):
                dependencies.append(ModuleDependency(dep_node.get('name'), 
                                                     bool(dep_node.get('optional', ''))))
            module = Module(name, source, build, dependencies = dependencies,
                            built_once = bool(module_node.get('built_once', '')),
                            installed = installed)
            self._modules.append(module)

    def _write_metadata(self, root):
        for module in reversed(self._modules):
            module_attrs = {'name' : module.name()}
            if module.is_built_once():
                module_attrs['built_once'] = 'True'
            module_node = ET.Element('module', module_attrs)
            self._write_installed(module_node, module.installed)

            source_node = self._create_node_from_obj(module.get_source(), 'source')
            self._write_attributes(module.get_source(), source_node)
            module_node.append(source_node)

            build_node = self._create_node_from_obj(module.get_build(), 'build')
            self._write_attributes(module.get_build(), build_node)
            module_node.append(build_node)
            build_node.attrib['objdir'] = 'any' if module.get_build().supports_objdir else 'srcdir'
            self._write_libpath(build_node, module.get_build())
            
            for dependency in module.dependencies():
                attrs = {'name' : dependency.name() }
                if dependency.is_optional():
                    attrs['optional'] = 'True'
                dep_node = ET.Element('depends_on', attrs)
                module_node.append(dep_node)
            root.append(module_node)

    def write(self):
        root = ET.Element('configuration', 
                          {'installdir' : self._installdir,
                           'sourcedir' : self._sourcedir,
                           'objdir' : self._objdir,
                           'relative_directory_root' : self._relative_directory_root,
                           'bakefile' : self._bakefile})
        if not self._metadata_file is None:
            metadata = ET.Element('metadata', {'filename' : self._metadata_file.filename(),
                                               'hash' : self._metadata_file.h()})
            root.append(metadata)

        # write enabled nodes
        for e in reversed(self._enabled):
            enable_node = ET.Element('enabled', {'name' : e.name()})
            root.append(enable_node)

        # write disabled nodes
        for e in reversed(self._disabled):
            disable_node = ET.Element('disabled', {'name' : e.name()})
            root.append(disable_node)

        self._write_metadata(root)
        et = ET.ElementTree(element=root)
        et.write(self._bakefile)

    def read(self):
        et = ET.parse(self._bakefile)
        self._read_metadata(et)
        root = et.getroot()
        self._installdir = root.get('installdir')
        self._objdir = root.get('objdir')
        self._sourcedir = root.get('sourcedir')
        self._relative_directory_root = root.get('relative_directory_root')
        original_bakefile = root.get('bakefile')
        metadata = root.find('metadata')
        self._metadata_file = MetadataFile (metadata.get('filename'),
                                            h = metadata.get('hash'))

        # read which modules are enabled
        modules = root.findall('enabled')
        for module in modules:
            enabled = self.lookup(module.get('name'))
            self.enable(enabled)

        # read which modules are disabled
        modules = root.findall('disabled')
        for module in modules:
            disabled = self.lookup(module.get('name'))
            self.disable(disabled)

        return self._metadata_file.is_hash_ok() and original_bakefile == self._bakefile

    def set_installdir(self, installdir):
        self._installdir = installdir
    def get_installdir(self):
        return self._installdir
    def set_objdir(self, objdir):
        self._objdir = objdir
    def get_objdir(self):
        return self._objdir
    def set_sourcedir(self, sourcedir):
        self._sourcedir = sourcedir
    def get_sourcedir(self):
        return self._sourcedir
    def get_relative_directory_root(self):
        return self._relative_directory_root
    def _compute_path(self, p):
        if os.path.isabs(p):
            return p
        else:
            tmp = os.path.join(os.path.dirname(self._bakefile), self._relative_directory_root, p)
            return os.path.normpath(tmp)
    def compute_sourcedir(self):
        return self._compute_path(self._sourcedir)
    def compute_installdir(self):
        return self._compute_path(self._installdir)
    def enable(self, module):
        if module in self._disabled:
            self._disabled.remove(module)
        else:
            self._enabled.append(module)
    def disable(self, module):
        if module in self._enabled:
            self._enabled.remove(module)
        else:
            self._disabled.append(module)
    def lookup(self, name):
        for module in self._modules:
            if module.name() == name:
                return module
        return None
    def enabled(self):
        return self._enabled
    def disabled(self):
        return self._disabled
    def modules(self):
        return self._modules
