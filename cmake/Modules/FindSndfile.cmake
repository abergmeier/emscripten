# - Try to find sndfile
# Once done this will define
#  SNDFILE_FOUND - System has sndfile
#  SNDFILE_INCLUDE_DIRS - The sndfile include directories
#  SNDFILE_LIBRARIES - The libraries needed to use sndfile
#  SNDFILE_DEFINITIONS - Compiler switches required for using sndfile

find_package( PkgConfig )

pkg_check_modules( SNDFILE QUIET sndfile )

set( SNDFILE_DEFINITIONS ${SNDFILE_CFLAGS_OTHER} )

set( SNDFILE_LIBRARY_LIST "" )
set( index 0 )

foreach( SNDFILE_LIB ${SNDFILE_LIBRARIES} )

	# FIXME: need find_library with different variables,
	# since it works only for the first call
	find_library( SNDFILE_LIBRARY${index}
		NAMES ${SNDFILE_LIB}
		HINTS ${SNDFILE_LIBDIR} ${SNDFILE_LIBRARY_DIRS}
	)

	list( APPEND SNDFILE_LIBRARY_LIST "${SNDFILE_LIBRARY${index}}" )
	MATH(EXPR index "${index}+1")
endforeach()

set( SNDFILE_LIBRARIES ${SNDFILE_LIBRARY_LIST} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set SNDFILE_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( sndfile DEFAULT_MSG
	SNDFILE_LIBRARY_LIST SNDFILE_INCLUDE_DIRS
)

mark_as_advanced( SNDFILE_INCLUDE_DIR SNDFILE_LIBRARY )

