#!/usr/bin/env python2

import sys, os, urllib, zipfile, tarfile, shutil, subprocess
import mimetypes, StringIO, bz2, tempfile, stat, gzip, glob, json
from urlparse import urlparse
from urlparse import urljoin
from urlparse import urlsplit

from tools import shared

# For version comparison 
from distutils.version import LooseVersion

def mergesort( lst ):
	def merge( left, right ):
		result = []
		i ,j = 0, 0
		while i < len(left) and j < len(right):
			if left[i] <= right[j]:
				result.append(left[i])
				i += 1
			else:
				result.append(right[j])
				j += 1
		result += left[i:]
		result += right[j:]
		return result

	if len(lst) <= 1:
		return lst
	middle = int( len(lst) / 2 )
	left  = mergesort( lst[:middle] )
	right = mergesort( lst[middle:] )
	return merge( left, right )

EM_LIBS = "~/.emscripten-libs"

rel_search_paths = [ os.path.join( 'lib'  , 'pkgconfig'),
                     os.path.join( 'share', 'pkgconfig')  ]

class LibDir:
	def __init__( self ):
		self.dirname = os.path.expanduser( EM_LIBS )
		self.system_versions_selector = os.path.join( self.get_system_path(), '*', '*' )
	
	def get_path( self, path ):
		return os.path.join( self.dirname, path )
	
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
		repo_config_path = self.get_path( 'repos' )
		
		def read_config_file():
			with open( repo_config_path, 'r' ) as file:
				for line in file:
					repos.append( line.strip(' \t\n\r') )
		try:
			read_config_file()
		except:
			print >> repo_config_path, 'https://raw.github.com/abergmeier/emscripten-libs/master'
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

class Version:
	def __init__(self, package, config):
		self.package = package

		commands = config.get( "build" )
		if commands is str:
			self.build_commands = [commands]
		else:
			self.build_commands = commands
		if self.build_commands is None:
			try:
				self.build_commands = self.package.build_commands
			except AttributeError:
				self.build_commands = []

		self.string = Version.version_string( config )
		assert self.string is not None
		
		self.version = Version.version_id( config )

		# Get where we should retrieve the source
		self.uri = config.get( "src" )
		if self.uri is None:
			try:
				self.uri = self.package.uri
			except AttributeError:
				pass
		assert self.uri is not None
		
		self.ignore_archive_root = config.get( "ignore_archive_root" )
		
		if self.ignore_archive_root is None:
			try:
				self.ignore_archive_root = self.package.ignore_archive_root
			except AttributeError:
				self.ignore_archive_root = False
	@staticmethod
	def version_string( version_config ):
		return version_config.get( "version" )
	
	@staticmethod
	def version_id( version_config ):
		return LooseVersion( Version.version_string(version_config) )
	
	def path( self ):
		return os.path.join( self.package.path(), self.string )
	
	def system_path( self ):
		return os.path.join( self.package.system_path(), self.string )
	
	def set_prefix( self ):
		os.environ["prefix"] = self.path()
	
	def build( self ):
		if len( self.build_commands ) is 0:
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
	
		for build_command in self.build_commands:
			has_url = False
			try:
				build_command = build_command.get( 'url' )
				has_url = True
			except AttributeError:
				pass
			
			if has_url:
				# Download first
				temp_tuple = tempfile.mkstemp( suffix='.py', text=True )
				temp_file_path = temp_tuple[1]
				urllib.urlretrieve( build_command, temp_file_path )
				# Make sure we have exec permissions
				#os.chmod( temp_file_path, stat.S_IRUSR | stat.S_IEXEC | stat.S_IWUSR )
				build_command = [ 'python2', temp_file_path ]
				# We have to close the file for this process because most os do not allow
				# for multiple processes accessing the same file concurrently
				os.close( temp_tuple[0] )
				try:
					subprocess.check_call( build_command, cwd=self.path(), env=env )
				finally:
					os.remove( temp_file_path )
			else:
				subprocess.check_call( ['sh', '-c', build_command], cwd=self.path(), env=env )
		
	
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
		if self.ignore_archive_root:
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
		
		if self.ignore_archive_root:
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
				urllib.urlretrieve( self.uri, temp_file.name )
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
	def __init__( self, package_name ):
		self.name = package_name
		self.uri  = None
		self.ignore_archive_root = None
		self.build_commands = []
		self.versions       = []
		version_dict = dict()
		
		# Load all information top down
		for repo_uri in lib_dir.repositories():
			repo_uri = urljoin( repo_uri + '/', package_name + '/versions' )
			
			with tempfile.NamedTemporaryFile() as temp_file:
				urllib.urlretrieve( repo_uri, temp_file.name )

				config = json.load( temp_file )

			if self.uri is None:
				self.uri    = config.get( "src" )
			
			if self.uri is None:
				self.ignore_archive_root = config.get( "ignore_archive_root" )
		
			if len( self.build_commands ) is 0:
				commands = config.get( "build" )
				if commands is str:
					self.build_commands = [commands]
				else:
					self.build_commands = commands
		
			for version_config in config.get("versions"):
				#FIXME: This is stricter, than looseversion is
				id = Version.version_string( version_config )
				if id in version_dict:
					continue
				version_dict[ id ] = Version( self, version_config )

		for key, version in version_dict.iteritems():
			self.versions.append( version )
		
		mergesort( self.versions )
	
	def path( self ):
		return lib_dir.get_source_path( self.name )
	
	def system_path( self ):
		return lib_dir.get_system_path( self.name )
	
	def highest_version( self ):
		return self.versions[0]
		
		
