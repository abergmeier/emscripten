import os
import io
import re
import WebIDL
from WebIDL import enum, IDLType

headers = {}
tabspaces = 2

def addParentDependency( idl ):
  if idl.parent:
    try:
      entry = headers[idl.filename()]
    except KeyError:
      class extensible(dict):
        pass
      entry = extensible

    try:
      includes = entry.includes
    except AttributeError:
      includes = entry.includes = []

    includes.append( idl.parent.filename() )

class TypeMapping:
  def nullable():
    pass
    
class c:
  class char16():
    def __str__(self):
      return 'char16_t'
  
  class ptr():
    def __init__(self, element_type):
      self._element_type = element_type
    
    def __str__(self):
      return '%s*' % self._element_type()
    
    def nullable(self):
      return True
    
  class char16_ptr(ptr):
    def __init__(self):
      c.ptr.__init__(self, c.char16)
  
  class void_ptr(ptr):
    def __init__(self):
      class void_type:
        def __str__(self):
          return 'void'
      c.ptr.__init__(self, void_type)

class TypeConverter:
  @staticmethod
  def valueToC( idlValue ):
    # We need to handle False and True special because Python is moronic
    mapping = { (False, IDLType.Tags.bool)  : 'EM_FALSE',
                (True, IDLType.Tags.bool)   : 'EM_TRUE',
                (None, IDLType.Tags.interface) : 'EM_NULL'
    }
    
    if idlValue.type.tag() == IDLType.Tags.int32:
      return idlValue.value
    
    #print idlValue.type.tag() == IDLType.Tags.interface
    return mapping[ (idlValue.value, idlValue.type.tag()) ]

  @staticmethod
  def idlToC( typeInfo ):
    try:
      tag = typeInfo.tag()
    except AttributeError:
      typeInfo = typeInfo.type
      tag = typeInfo.tag()
    
    mapping = { IDLType.Tags.int8  : 'int8',
                IDLType.Tags.uint8 : 'uint8',
                IDLType.Tags.int16 : 'int16',
                IDLType.Tags.uint16: 'uint16',
                IDLType.Tags.int32 : 'int32' ,
                IDLType.Tags.uint32: 'uint32',
                # TODO: Should we REALLY support this
                IDLType.Tags.int64 : 'int64' ,
                IDLType.Tags.uint64: 'uint64',
                IDLType.Tags.bool  : 'EM_BOOL' ,
                # TODO: What is that?
                IDLType.Tags.unrestricted_float: 'float',
                IDLType.Tags.float : 'float',
                IDLType.Tags.unrestricted_double: 'double',
                IDLType.Tags.double: 'double',
    }
    
    if typeInfo.name == 'WindowProxy':
      return 'WindowProxy'
    try:
      return mapping[ tag ]
    except KeyError:
      # Not a simple mapping
      def convertDict():
        print typeInfo
        
      def convertInterface():
        return "%s*" % typeInfo.name
      
      def convertCallback():
        print 'Callback'
        return c.void_ptr()
      
      def convertUnion():
        print 'Union'
        return c.void_ptr()
        
      mapping = { IDLType.Tags.any       : c.void_ptr,
                  IDLType.Tags.dictionary: convertDict,
                  IDLType.Tags.interface : convertInterface,
                  IDLType.Tags.domstring : c.char16_ptr,
                  IDLType.Tags.callback  : convertCallback,
                  IDLType.Tags.union     : convertUnion,
      }
      
      return mapping[ tag ]()

class extensible(dict):
  pass

PREFIX = extensible()
PREFIX.camel = 'Emscripten'
PREFIX.lower = PREFIX.camel.lower()
PREFIX.upper = PREFIX.camel.upper()

class PathConverter:

  def __init__(self, root_path):
    self._root_path = root_path
  
  def _rel_path(self, idl):
    return os.path.relpath(idl.location.filename(), os.path.join(self._root_path, 'src', 'idl'))

  def impl_path(self, idl):
    relpath = self._rel_path( idl )
    newpath = os.path.splitext(relpath)[0] + '.c'
    return os.path.join(self._root_path, 'system', 'lib', 'idl_c', newpath)
  
  def header_path(self, idl):
    relpath = self._rel_path( idl )
    newpath = os.path.splitext(relpath)[0] + '.h'
    return os.path.join(self._root_path, 'system', 'include', 'idl_c', newpath)

class writer:
  def __init__( self, path ):
    self.file = open(path, 'w')
      
  def formatline(self, line, *args):
    self.writeline(line.format(*args))
  def printline(self, line, *args):
    self.writeline(line % args)
  def writeline(self, line):
    #TODO: Handle unicode once we are at python 3
    self.file.write(line + '\n')

class NameConverter:
  @staticmethod
  def camelToSnake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
  
  @staticmethod
  def camelToDefine(name):
    return NameConverter.camelToSnake( name )

class Entity:
  def __init__(self, idl, root_path):
    self.idl = idl
    self.path_converter = PathConverter(root_path)
    self.impl = extensible()
    self.impl.file = writer(self.path_converter.impl_path(idl))
    
    self.header = extensible()
    self.header.file = writer(self.path_converter.header_path(idl))
    self.dependencies = []
  
  def add_dependency(self, typeInfo):
    self.dependencies.append(typeInfo)
  
  def post(self):
    for dep in self.dependencies:
      print dep.location

class Interface(Entity):
  def __init__(self, idl, root_path):
    Entity.__init__(self, idl, root_path)

  def pre(self):
    if self.idl.isExternal():
      return
    addParentDependency( self.idl )
  
  def convert(self):
    if self.idl.isExternal():
      print 'Ignore external Interface %s' % self.idl.identifier.name
      return

    print 'Interface %s' % self.idl.identifier.name

class Union(Entity):
  def __init__(self, idl, root_path):
    Entity.__init(self, idl, root_path)
    raise Exception() 
    
class Enumeration(Entity):
  def __init__(self, idl, root_path):
    Entity.__init__(self, idl, root_path)
    self.name = idl.identifier.name
    self.snakedName = NameConverter.camelToSnake(self.name).lower()
    self.absSnakedName = '%s_%s' % (PREFIX.lower, self.snakedName)
    self.header = extensible()
    self.header.file = writer(self.path_converter.header_path(idl))
  
  def pre(self):
    pass
  
  def convert(self):
    formatline = self.header.file.formatline
    printline  = self.header.file.printline
    printline('enum %s%s {', PREFIX.camel, self.name                           )

    for value in self.idl.values():
      printline('\t%s', NameConverter.camelToDefine(value).upper()             )
    printline('};'                                                             )
    
    for value in self.idl.values():
      printline('#define %s_%s_%s "%s"', PREFIX.upper, NameConverter.camelToDefine(value).upper(), self.name.upper(), value)
  
class Dictionary(Entity):
  def __init__(self, idl, root_path):
    Entity.__init__(self, idl, root_path)
    self.name = idl.identifier.name
    self.snakedName = NameConverter.camelToSnake(self.name).lower()
    self.absSnakedName = '%s_%s' % (PREFIX.lower, self.snakedName)
    
    self.functions = extensible()
    self.functions.new   = '%s_new'   % self.absSnakedName
    self.functions.init  = '%s_init'  % self.absSnakedName
    self.functions.clear = '%s_clear' % self.absSnakedName
    self.functions.ref   = '%s_ref'   % self.absSnakedName
    self.functions.unref = '%s_unref' % self.absSnakedName
    
    is_baseless = self.idl.parent is None

    self.parent = extensible()
    if is_baseless:
      self.parent.typedef = 'emscripten_type_base'
      self.parent.init    = 'emscripten_type_base_init'
      self.parent.ref     = 'emscripten_type_base_ref'
      self.parent.unref   = 'emscripten_type_base_unref'
    else:
      self.parent.typedef = self.idl.parent.identifier.name
      base_name = '%s_%s' % (PREFIX.lower, NameConverter.camelToSnake(self.parent.typedef).lower())
      self.parent.init    = '%s_init' % base_name
      self.parent.ref     = '%s_ref' % base_name
      self.parent.unref   = '%s_unref' % base_name
    
  def pre( self ):
    addParentDependency( self.idl )
  
  def convert( self ):
    formatline = self.header.file.formatline
    writeline  = self.header.file.writeline
    printline  = self.header.file.printline
    printline('struct _%s {', self.name)
    # Add base class
    printline('\t%s __base;', self.parent.typedef                              )
    
    for member in self.idl.members:
      if member.type.isDictionary():
        raise Error("Unhandled")
      try:
        c_type = TypeConverter.idlToC(member.type)
      except KeyError:
        print 'Unhandled %s' % member.type
        raise
      if member.type.nullable():
        printline('\t%s* %s;', c_type, member.identifier.name)
      else:
        printline('\t%s %s;', c_type, member.identifier.name)
      # TODO: Howto handle readonly?
    
    writeline ('};'                                                            )
    formatline('typedef _{0} {0};', self.name                                  )
    printline ('%s* %s();', self.name, self.functions.new                      )
    formatline('{0}* {1}({0}*);', self.name, self.functions.init               )
    printline ('void %s(%s*);'  , self.absSnakedName, self.functions.clear     )
    formatline('{0}* {1}({0}*);', self.name, self.functions.ref                )
    formatline('{0}* {1}({0}*);', self.name, self.functions.unref              )
  
  def post( self ):
    formatline = self.impl.file.formatline
    writeline  = self.impl.file.writeline
    printline  = self.impl.file.printline
    # Create init
    formatline ('{0}* {1}({0}* instance) {{', self.name, self.functions.init   )
    #TODO: First call base class init
    writeline  ('\tassert( instance ); // Don\'t you dare!'                    )
    printline  ('\t%s(&instance->__base);', self.parent.init                   )
    for member in self.idl.members:
      printline('\tinstance->%s = %s;', member.identifier.name, TypeConverter.valueToC(member.defaultValue))
    writeline  ('\treturn instance;'                                           )
    writeline  ('}'                                                            )

    # Create ref
    formatline('{0}* {1}({0}* instance) {{', self.name, self.functions.ref     )
    printline ('\t%s(&instance->__base);', self.parent.ref                     )
    writeline ('\treturn instance;'                                            )
    writeline ('}'                                                             )
    
    # Create unref
    formatline('{0}* {1}({0}* instance);', self.name, self.functions.unref     )
    printline ('\t%s* present = %s(&instance->__base);', self.parent.typedef, self.parent.unref)
    writeline ('\tif( present )'                                               )
    writeline ('\t\treturn instance;'                                          )
    printline ('\t%s(instance);', self.functions.clear                         )
    writeline ('\treturn EM_NULL;'                                             )
    writeline ('}'                                                             )
    
    """
    typedef void*(Event* event)
    typedef EventHandlerNonNull EventHandler;
    emscripten_set_global_event_handlers_onabort(EventHandler);
    """

class Callback(Entity):
  def __init__(self, idl, root_path):
    Entity.__init__(self, idl, root_path)
    self.name = idl.name
    self.absCamelName = '%s%s' % (PREFIX.camel, self.name)
  
  def pre(self):
    pass
  
  def convert(self):
    formatline = self.header.file.formatline
    writeline  = self.header.file.writeline
    printline  = self.header.file.printline
    signature = list(self.idl.signatures()[0])
    returnType = signature.pop(0)
    self.add_dependency(returnType)
    signature = signature.pop(0)
    for i in range(len(signature)):
      c_signature = TypeConverter.idlToC(signature[i])
      self.add_dependency(c_signature)
      signature[i] = c_signature
    
    signature_string = ", ".join(signature)
    printline('typedef %s(*%s)(%s)', TypeConverter.idlToC(returnType), self.absCamelName, signature_string)
  
class Typedef(Entity):
  def __init__(self, idl, root_path):
    Entity.__init__(self, idl, root_path)
  
  def pre(self):
    pass
  
  def convert(self):
    printline  = self.header.file.printline

    if self.idl.nullable():
      if TypeConverter.idlToC(self.idl.inner.inner).nullable():
        # Type not yet nullable so handle as pointer
        format_str = 'typedef %s* %s;' %(self.idl.inner.inner.identifier.name, self.idl.name)
      else:
        format_str = 'typedef %s %s;' % (self.idl.inner.inner.identifier.name, self.idl.name)
    else:
      format_str = 'typedef %s %s;' % (self.idl.inner.identifier.name, self.idl.name)
    printline(format_str)

