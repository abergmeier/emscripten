# - Try to find FreeImage
# Once done this will define
#  FREEIMAGE_FOUND - System has FreeImage
#  FREEIMAGE_INCLUDE_DIRS - The FreeImage include directories
#  FREEIMAGE_LIBRARIES - The libraries needed to use FreeImage
#  FREEIMAGE_DEFINITIONS - Compiler switches required for using FreeImage

find_package( PkgConfig )

pkg_check_modules( FREEIMAGE QUIET freeimage )

set( FREEIMAGE_DEFINITIONS ${FREEIMAGE_CFLAGS_OTHER} )

set( FREEIMAGE_LIBRARY_LIST "" )
set( index 0 )

foreach( FREEIMAGE_LIB ${FREEIMAGE_LIBRARIES} )

	# FIXME: need find_library with different variables,
	# since it works only for the first call
	find_library( FREEIMAGE_LIBRARY${index}
		NAMES ${FREEIMAGE_LIB}
		HINTS ${FREEIMAGE_LIBDIR} ${FREEIMAGE_LIBRARY_DIRS}
	)

	list( APPEND FREEIMAGE_LIBRARY_LIST "${FREEIMAGE_LIBRARY${index}}" )
	MATH(EXPR index "${index}+1")
endforeach()

set( FREEIMAGE_LIBRARIES ${FREEIMAGE_LIBRARY_LIST} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set FREEIMAGE_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( FreeImage DEFAULT_MSG
	FREEIMAGE_LIBRARY_LIST FREEIMAGE_INCLUDE_DIRS
)

mark_as_advanced( FREEIMAGE_INCLUDE_DIR FREEIMAGE_LIBRARY )

