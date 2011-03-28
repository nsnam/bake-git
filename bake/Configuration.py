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
                sys.stderr.write('Error: no code tag in in inline module\n')
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
        

    def _read_metadata(self, et):
        # function designed to be called on two kinds of xml files.
        modules = et.findall('module')
        for module_node in modules:
            name = module_node.get('name')
            version = module_node.get('version', None)

            source_node = module_node.find('source')
            source = self._create_obj_from_node(source_node, ModuleSource)
            self._check_mandatory_attributes(source, source_node, 'source', name)
            self._read_attributes(source, source_node, 'source', name)

            build_node = module_node.find('build')
            build = self._create_obj_from_node(build_node, ModuleBuild)
            self._check_mandatory_attributes(build, build_node, 'build', name)
            self._read_attributes(source, source_node, 'build', name)

            dependencies = []
            for dep_node in module_node.findall('depends_on'):
                dependencies.append(ModuleDependency(dep_node.get('name'), 
                                                     dep_node.get('version', None),
                                                     bool(dep_node.get('optional', ''))))
            module = Module(name, source, build, version = version, dependencies = dependencies,
                            built_once = bool(module_node.get('built_once', '')))
            self._modules.append(module)

    def _write_metadata(self, root):
        for module in reversed(self._modules):
            module_attrs = {'name' : module.name()}
            if module.is_built_once():
                module_attrs['built_once'] = 'True'
            if not module.version() is None:
                module_attrs['version'] = module.version()
            module_node = ET.Element('module', module_attrs)

            source_node = self._create_node_from_obj(module.get_source(), 'source')
            self._write_attributes(module.get_source(), source_node)
            module_node.append(source_node)

            build_node = self._create_node_from_obj(module.get_build(), 'build')
            self._write_attributes(module.get_build(), build_node)
            module_node.append(build_node)
            
            for dependency in module.dependencies():
                attrs = {'name' : dependency.name() }
                if dependency.version() is not None:
                    attrs['version'] = dependency.version()
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
            
        for e in reversed(self._enabled):
            enable_node = ET.Element('enabled', {'name' : e.name()})
            if not e.version() is None:
                enable_node.attrib['version'] = e.version()
            root.append(enable_node)

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

        modules = root.findall('enabled')
        for module in modules:
            enabled = self.lookup(module.get('name'), version=module.get('version', None))
            self.enable(enabled)

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
        self._enabled.append(module)
    def disable(self, module):
        self._enabled.remove(module)
    def lookup(self, name, version = None):
        for module in self._modules:
            if module.name() == name:
                if version is not None and module.version() == version:
                    return module
                elif version is None:
                    return module
        return None
    def enabled(self):
        return self._enabled
    def modules(self):
        return self._modules
