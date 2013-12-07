# - Try to find tess2
# Once done this will define
#  TESS_FOUND - System has tess2
#  TESS_INCLUDE_DIRS - The tess2 include directories
#  TESS_LIBRARIES - The libraries needed to use tess2
#  TESS_DEFINITIONS - Compiler switches required for using tess2

find_package( PkgConfig )

pkg_check_modules( TESS QUIET tess2 )

set( TESS_DEFINITIONS ${TESS_CFLAGS_OTHER} )

find_path( TESS_INCLUDE_DIR
	NAMES tesselator.h
	HINTS ${TESS_INCLUDEDIR} ${TESS_INCLUDE_DIRS}
)

find_library( TESS_LIBRARY
	NAMES ${TESS_LIBRARIES}
	HINTS ${TESS_LIBDIR} ${TESS_LIBRARY_DIRS}
)

set( TESS_LIBRARIES    ${TESS_LIBRARY}     )
set( TESS_INCLUDE_DIRS ${TESS_INCLUDE_DIR} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set TESS_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( tess2 DEFAULT_MSG
	TESS_LIBRARY TESS_INCLUDE_DIR
)

mark_as_advanced( TESS_INCLUDE_DIR TESS_LIBRARY )

