import os
import optparse
import sys
import importlib

__rootpath__ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def path_from_root(*pathelems):
  return os.path.join(__rootpath__, *pathelems)
sys.path = [path_from_root('..', 'third_party', 'ply')] + sys.path
from shared import *

import WebIDL
from WebIDL import enum, IDLType

variant = sys.argv[1]

glue = importlib.import_module("glue_%s" % variant)

if __name__ == '__main__':
    usage = """%prog [OPTIONS]
               Where TESTS are relative to the tests directory."""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-q', '--quiet', action='store_false', dest='verbose', default=True,
                      help="Don't print passing tests.")
    #options, tests = parser.parse_args()

    webidl_parser = WebIDL.Parser()

    idls = ['Touch', 'TouchList', 'TouchEvent', 'EventTarget', 'UIEvent', 'Event', 'Node', 'EventListener', 'EventHandler', 'Document', 'Element', 'NodeList']

    def parse( idl ):
      path = '/home/andreas/Projects/emscripten/src/idl'
      idl_path = os.path.join(path, idl) + ".webidl"
      with open(idl_path) as idl_file:
        webidl_parser.parse( idl_file.read(), idl_path )

    for idl in idls:
      parse( idl )

    generators = []

    for idl in webidl_parser.finish():
      if idl.isInterface():
        gen = glue.Interface
      elif idl.isEnum():
        gen = glue.Enumeration
      elif idl.isDictionary():
        gen = glue.Dictionary
      elif idl.isUnion():
        gen = glue.Union
      elif idl.isCallback():
        gen = glue.Callback
      elif isinstance(idl, WebIDL.IDLTypedefType):
        gen = glue.Typedef
      else:
        print idl
        assert( False )

      gen = gen(idl, __rootpath__)
      generators.append(gen)

    # Pre step
    for gen in generators:
      gen.pre()
    
    # Convert step
    for gen in generators:
      gen.convert()
    
    for gen in generators:
      gen.post()
