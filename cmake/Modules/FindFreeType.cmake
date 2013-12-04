# - Try to find FreeType
# Once done this will define
#  FREETYPE_FOUND - System has FreeType
#  FREETYPE_INCLUDE_DIRS - The FreeType include directories
#  FREETYPE_LIBRARIES - The libraries needed to use FreeType
#  FREETYPE_DEFINITIONS - Compiler switches required for using FreeType

find_package( PkgConfig )

pkg_check_modules( FREETYPE QUIET freetype )

set( FREETYPE_DEFINITIONS ${FREETYPE_CFLAGS_OTHER} )

find_path( FREETYPE_INCLUDE_DIR
	NAMES ft2build.h
	HINTS ${FREETYPE_INCLUDEDIR} ${FREETYPE_INCLUDE_DIRS}
)

find_library( FREETYPE_LIBRARY
	NAMES ${FREETYPE_LIBRARIES}
	HINTS ${FREETYPE_LIBDIR} ${FREETYPE_LIBRARY_DIRS}
)

set( FREETYPE_LIBRARIES    ${FREETYPE_LIBRARY}     )
set( FREETYPE_INCLUDE_DIRS ${FREETYPE_INCLUDE_DIR} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set FREETYPE_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( FreeType DEFAULT_MSG
	FREETYPE_LIBRARY FREETYPE_INCLUDE_DIR
)

mark_as_advanced( FREETYPE_INCLUDE_DIR FREETYPE_LIBRARY )

