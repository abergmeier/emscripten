import os
import optparse
import WebIDL

if __name__ == '__main__':
    usage = """%prog [OPTIONS]
               Where TESTS are relative to the tests directory."""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-q', '--quiet', action='store_false', dest='verbose', default=True,
                      help="Don't print passing tests.")
    #options, tests = parser.parse_args()

    webidl_parser = WebIDL.Parser()
    path = '/home/andreas/Projects/emscripten/src/idl'
    idls = ['Touch.webidl', 'TouchList.webidl', 'TouchEvent.webidl']

    for idl in idls:
      webidl_parser.parse( "", os.path.join(path, idl) )

    print webidl_parser.finish( )

