#!/usr/bin/env python2

import sys, os, urllib2, zipfile, tarfile, shutil, subprocess, contextlib
import mimetypes, StringIO, bz2, tempfile, stat, gzip, glob, json
from urlparse import urlparse
from functools import partial

from tools import shared
from string import Template

class extensible(object):
  pass

sys.path = [shared.path_from_root('third_party', 'requests')] + sys.path
import requests

# For version comparison 
from distutils.version import LooseVersion

rel_search_paths = [ os.path.join( 'lib'  , 'pkgconfig'),
                     os.path.join( 'share', 'pkgconfig')
]

def get_platform_paths():
  # Incredibly ugly platform path handling
  if sys.platform.startswith('linux'):
    import xdg
    from xdg import BaseDirectory
    return BaseDirectory.xdg_data_home, BaseDirectory.xdg_config_home

  elif sys.platform.startswith('darwin'):
    from AppKit import NSSearchPathForDirectoriesInDomains
    # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
    # NSApplicationSupportDirectory = 14
    # NSUserDomainMask = 1
    # True for expanding the tilde into a fully qualified path
    data_path = NSSearchPathForDirectoriesInDomains(14, 1, True)[0]
    # TODO: See whether there is something more similar to a config directory in OSX
    return data_path, data_path

  elif sys.platform.startswith('win'):
    from win32com.shell import shellcon, shell
    return shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_APPDATA, 0, 0), shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)

  else:
    raise Exception('User path handling for platform %s missing' % sys.platform)

CONFIG = extensible()
CONFIG.dirs = extensible()
CONFIG.dirs.data, CONFIG.dirs.config = get_platform_paths()
CONFIG.folder = 'emscripten-libs'

class LibDir:
	def __init__( self ):
		self.dirname = os.path.join( CONFIG.dirs.data, CONFIG.folder )
		self.system_versions_selector = os.path.join( self.get_system_path(), '*', '*' )
	
	def get_path( self, path ):
		return os.path.join( self.dirname, path )

	def get_config_path( self, path ):
		return os.path.join( CONFIG.dirs.config, CONFIG.folder, path );
	
	def get_source_path( self, path=None ):
		sourcePath = self.get_path( 'sources' )
		if path is None:
			return sourcePath
		else:
			return os.path.join( sourcePath, path )
	
	def get_system_path( self, path=None ):
		systemPath = self.get_path( 'system' )
		if path is None:
			return systemPath
		else:
			return os.path.join( systemPath, path )
	
	def ensure( self ):
		if not os.path.isdir( self.dirname ):
			os.makedirs( self.dirname )
	
	def config_search_paths( self ):
		result = []
		
		for versionPath in glob.glob( self.system_versions_selector ):
			for rel_search_path in rel_search_paths:
				result.append( os.path.join(versionPath, rel_search_path) )
		return result
	
	def repositories( self ):
		repos = []
		repo_config_path = self.get_config_path( 'repos' )
		
		def read_config_file():
			with open( repo_config_path, 'r' ) as file:
				for line in file:
					repos.append( line.strip(' \t\n\r') )
		try:
			read_config_file()
		except IOError:
			os.makedirs( os.path.dirname(repo_config_path) )

			with open(repo_config_path, 'w') as config_file:
				print >> config_file, 'https://raw.github.com/abergmeier/emscripten-libs/master'
			read_config_file()
		return repos

class Extract:
	@staticmethod
	def zip( src, dest ):
		with zipfile.ZipFile( src, 'r' ) as zip:
			zip.extractall( dest )

	@staticmethod
	def tar( src, dest ):
		with tarfile.TarFile( src, 'r' ) as tar:
			tar.extractall( dest )
	
	@staticmethod
	def tarbz2( src, dest ):
		tardata = StringIO.StringIO()
		def unpack():
			with open( src ) as file:
				tardata.write( bz2.decompress(file.read()) )
		unpack()
		tardata.seek(0)
		with tarfile.TarFile( fileobj=tardata, mode='r' ) as tar:
			tar.extractall( dest )
	
	@staticmethod
	def targzip( src, dest ):
		tardata = StringIO.StringIO()
		def unpack():
			with gzip.open( src ) as file:
				tardata.write( file.read() )
		unpack()
		tardata.seek(0)
		with tarfile.TarFile( fileobj=tardata, mode='r' ) as tar:
			tar.extractall( dest )
	
	@staticmethod
	def tarxz( src, dest ):
		# Since xz support is only available in 3.4 python, try commandline
		# TODO: Replace this by python impl when switching to python3
		
		if not src.endswith( '.tar.xz' ):
			# We need file extension for tar
			new_src = src + '.tar.xz'

			try:
				os.remove( new_src )
			except:
				pass
			os.rename( src, new_src )

			src = new_src
		
		command = [ 'tar', '-C', dest, '-xJf', src ]
		subprocess.check_call( command )


lib_dir = LibDir()

class Stamp:
	stamp_name = '.emscripten_stamp'
	
	@staticmethod
	def fetch( dir_path ):
		with open( os.path.join(dir_path, stamp_name) ) as file:
			return json.load( file )

	@staticmethod
	def is_outdated( dir_path ):
		Stamp.fetch( dir_path )['version'] != shared.EMSCRIPTEN_VERSION

	@staticmethod
	def create( dir_path ):
		print >> os.path.join(dir_path, stamp_name), '{ "version": "' + shared.EMSCRIPTEN_VERSION + '" }'
		
class BaseConfig:
	def __init__(self, jsonConfig):
		try:
			self.name = jsonConfig['name']
		except KeyError:
			pass
		
		try:
			self.version = jsonConfig['version']
		except KeyError:
			pass
		
		try:
			contributors = jsonConfig['contributors']
			self.contributors = extensible()
		except KeyError:
			contributors = None
		
		if contributors:
			for contributor in contributors:
				self.contributors.name  = contributor['name']
				self.contributors.email = contributor['email']
		
		builders = None
		
		try:
			scripts = jsonConfig['scripts']
		except KeyError:
			scripts = None
		
		if scripts:
			try:
				builders = scripts['build']
			except KeyError:
				pass
		
		if builders:
			if builders is str:
				builders = [builders]
	
			self.builders = []
		
			for builder_config in builders:
				try:
					builder_name = builder_config[ 'builder' ]
				except (KeyError, TypeError):
					# Shell is default
					builder_name = 'sh'
					
				
				BUILDERS = { 'pkg-config': Builders.pkg_config,
				             'sh'        : Builders.shell
				}
				
				bound_builder = partial(BUILDERS[builder_name], builder_config)
				
				self.builders.append(bound_builder)

		try:
			self.ignore_archive_root = jsonConfig['ignore_archive_root']
		except KeyError:
			pass
		
		try:
			licenses = jsonConfig['licenses']
		except KeyError:
			licenses = None
		
		if licenses:
			if licenses is str:
				licenses = [licenses]

			self.licenses = licenses

class VersionConfig(BaseConfig):
	def __init__(self, package, config):
		BaseConfig.__init__(self, config)
		
		self.parent = package.config
		
		try:
			self.name
		except AttributeError:
			self.name = self.parent.name
		
		try:
			self.version
		except AttributeError:
			self.version = self.parent.version
		
		try:
			self.contributors
		except AttributeError:
			try:
				self.contributors = self.parent.contributors
			except AttributeError:
				self.contributors = []
		
		try:
			self.builders
		except AttributeError:
			# For now we force builders to be present
			self.builders = self.parent.builders
		
		try:
			self.ignore_archive_root
		except AttributeError:
			try:
				self.ignore_archive_root = self.parent.ignore_archive_root
			except AttributeError:
				# Fallback to default
				self.ignore_archive_root = False
		
		try:
			self.licenses
		except AttributeError:
			try:
				self.licenses = self.parent.licenses
			except AttributeError:
				raise RuntimeError('Config error - license information missing.')

class Version:
	def __init__(self, package, config):
		self.package = package
		
		self.config = VersionConfig(package, config)

		self.string = self.config.version
		assert self.string is not None
		
		self.version = self.version_id()

		# Get where we should retrieve the source
		self.uri = config['src']

	def version_id(self):
		return LooseVersion( self.string )
	
	def path( self ):
		return os.path.join( self.package.path(), self.string )
	
	def system_path( self ):
		return os.path.join( self.package.system_path(), self.string )
	
	def set_prefix( self ):
		os.environ["prefix"] = self.system_path()
	
	def build( self ):
		if len( self.config.builders ) is 0:
			print 'no build commands specified - nothing to invoke'
			return
		
		lib_dir.ensure()
	
		self.set_prefix()
		env = os.environ.copy()
		search_paths = lib_dir.config_search_paths()

		env[ 'PKG_CONFIG_LIBDIR'     ] = os.pathsep.join( search_paths )
		env[ 'PATH'                  ] += os.pathsep + shared.__rootpath__
		env[ 'EMSCRIPTEN_SYSTEM_ROOT'] = self.system_path()
		env[ 'EMSCRIPTEN_ROOT'       ] = shared.__rootpath__.replace('\\', '/')

		for builder in self.config.builders:
			builder( self.path(), env )
	
	def is_built( self ):
		versionPath = self.path()
		return os.path.isdir( versionPath )
	
	@staticmethod
	def mimeTuple( file_path ):
		archiveMime  = mimetypes.guess_type( file_path, strict=False )
		
		if (archiveMime is None or (archiveMime[0] is None and archiveMime[1] is None)):
			# Manual hardcoded detection
			if file_path.endswith( 'tar.xz' ):
				archiveMime = ('application/x-tar', 'xz')
		
		return archiveMime
	
	def fetch_archive( self, archive_path ):
		if self.config.ignore_archive_root:
			# Extract indirectly, since we do not want the whole archive
			dir_path = lib_dir.get_path( '.package_folder' )
			try:
				shutil.rmtree( dir_path )
			except os.error:
				pass
		else:
			dir_path = self.path()
	
		os.makedirs( dir_path )

		archiveMime = Version.mimeTuple( archive_path )
		
		{ ('application/zip'  , None       ): Extract.zip,
		  ('application/tar'  , None       ): Extract.tar,
		  ('application/x-tar', 'bzip2'    ): Extract.tarbz2,
		  ('application/x-tar', 'gzip'     ): Extract.targzip,
		  ('application/x-tar', 'compress' ): None, #TODO implement
		  ('application/x-tar', 'xz'       ): Extract.tarxz
		}[ archiveMime ]( archive_path, dir_path )
		
		if self.config.ignore_archive_root:
			root_dirs = os.listdir( dir_path )
			assert len(root_dirs) is 1

			shutil.move( os.path.join(dir_path, root_dirs[0]), self.path() )
	
	def fetch_dir( self, dir_path ):
		shutil.copytree( dir_path, self.path() )
	
	def fetch( self ):
		lib_dir.ensure()
		
		#if os.path.isdir( self.path() ):
			#TODO: add request
		try:
			shutil.rmtree( self.path() )
		except os.error:
			pass
		
		url_tuple = urlparse( self.uri )
		if url_tuple.scheme == 'file' and os.path.isdir( url_tuple.path ):
			# fetch a directory
			self.fetch_dir( url_tuple.path )
		else: 
			# fetch a single file
			# We need to preserve filename, so mime type can be
			# detected later on
			file_name = os.path.basename( url_tuple.path )

			with tempfile.NamedTemporaryFile( suffix=file_name, dir=lib_dir.dirname ) as temp_file:
				with contextlib.closing( urllib2.urlopen(self.uri) ) as file:
					temp_file.write( file.read() )
					# We have to flush or the data does not get written
					temp_file.flush()
				self.fetch_archive( temp_file.name )
		

	def __lt__( self, other ):
		return self.version < other.version

	def __le__( self, other ):
		return self.version <= other.version
	
	def __eq__( self, other ):
		return self.version == other.version
	
	def __gt__( self, other ):
		return self.version > other.version
	
	def __ge__( self, other ):
		return self.version >= other.version

class Package:
	@staticmethod
	def validate( package_name ):
		return package_name.replace(" ","").replace("_","-")

	def __init__( self, package_name ):
		valid_name = Package.validate(package_name)
		if not valid_name == package_name:
			raise Exception( "Did you mean %s" % valid_name )
		self.name = package_name
		
		repositories = lib_dir.repositories()
		
		repo_uri = repositories[0]
		package_uri = repo_uri + '/' + package_name + '/'
		
		package_request = requests.get(package_uri + 'package.json')
		
		version_requests = []
		for repo_uri in repositories:
			package_uri = repo_uri + '/' + package_name + '/'
			version_uri = package_uri + 'versions'
			
			version_requests.append(requests.get(version_uri))

		enabled_versions = []

		for version_request in version_requests:
			try:
				version_request.raise_for_status()
			except requests.exceptions.HTTPError:
				continue
			
			for version in version_request.text.splitlines():
				if not version:
					continue
				enabled_versions.append(version)
		
		del version_requests[:]
		
		if len(enabled_versions) is 0:
			raise LookupError('No versions for package \'%s\' were found.' % package_name)

		try:
			base_config = package_request.json()
		except:
			base_config = dict()
		
		self.config = BaseConfig(base_config)
		self._version_dict = dict()
		
		# Search for versions in all repositories
		for repo_uri in repositories:
			package_uri = repo_uri + '/' + package_name + '/'
			
			for version in enabled_versions:
				version_request = requests.get(package_uri + version + '/package.json')
				version_requests.append( version_request )
			
		for version_request in version_requests:
			json = version_request.json()
			version = Version( self, json )
			self._version_dict[version.string] = version

		self._versions = []
		for key, version in self._version_dict.iteritems():
			self._versions.append( version )
		
		list.sort(self._versions)
	
	def path( self ):
		return lib_dir.get_source_path( self.name )
	
	def system_path( self ):
		return lib_dir.get_system_path( self.name )
	
	def highest_version( self ):
		return self._versions[-1]
	
	def version(self, name):
		try:
			return self._version_dict[name]
		except KeyError:
			raise LookupError('Version \'%s\' not known' % name)
		
class Builders:
	@staticmethod
	def pkg_config( command, cwd, env ):
		arguments = command[ "arguments" ]

		file    = Template( arguments["file"   ] ).substitute( env )
		prefix  = Template( arguments["prefix" ] ).substitute( env )
		name    = Template( arguments["name"   ] ).substitute( env )
		version = Template( arguments["version"] ).substitute( env )

		try:
			description = arguments[ "description" ]
		except KeyError:
			try:
				description = arguments[ "desc" ]
			except KeyError:
				description = ""

		try:
			libs = arguments[ "libs" ]
		except KeyError:
			libs = ""

		try:
			cflags = arguments[ "cflags" ]
		except KeyError:
			cflags = ""
		
		shared.safe_ensure_dirs( os.path.dirname(file) )

		with open( file, "w" ) as config_file:
			config_file.write( "prefix=%s\n"
			                   "exec_prefix=${prefix}\n"
			                   "libdir=${exec_prefix}/lib\n"
			                   "sharedlibdir=${libdir}\n"
			                   "includedir=${prefix}/include\n"
			                   "Name:%s\n"
			                   "Description:%s\n"
			                   "Version:%s\n"
			                   "Libs:%s\n"
			                   "Cflags:%s\n" % (prefix, name, description, version, libs, cflags)
			)

	@staticmethod
	def shell( command, cwd, env ):
		subprocess.check_call( ['sh', '-c', command], cwd=cwd, env=env )

