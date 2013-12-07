# - Try to find FreeImage
# Once done this will define
#  FREEIMAGE_FOUND - System has FreeImage
#  FREEIMAGE_INCLUDE_DIRS - The FreeImage include directories
#  FREEIMAGE_LIBRARIES - The libraries needed to use FreeImage
#  FREEIMAGE_DEFINITIONS - Compiler switches required for using FreeImage

find_package( PkgConfig )

pkg_check_modules( FREEIMAGE QUIET freeimage )

set( FREEIMAGE_DEFINITIONS ${FREEIMAGE_CFLAGS_OTHER} )

find_path( FREEIMAGE_INCLUDE_DIR
	NAMES FreeImage.h
	HINTS ${FREEIMAGE_INCLUDEDIR} ${FREEIMAGE_INCLUDE_DIRS}
)

find_library( FREEIMAGE_LIBRARY
	NAMES ${FREEIMAGE_LIBRARIES}
	HINTS ${FREEIMAGE_LIBDIR} ${FREEIMAGE_LIBRARY_DIRS}
)

set( FREEIMAGE_LIBRARIES    ${FREEIMAGE_LIBRARY}     )
set( FREEIMAGE_INCLUDE_DIRS ${FREEIMAGE_INCLUDE_DIR} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set FREEIMAGE_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( FreeImage DEFAULT_MSG
	FREEIMAGE_LIBRARY FREEIMAGE_INCLUDE_DIR
)

mark_as_advanced( FREEIMAGE_INCLUDE_DIR FREEIMAGE_LIBRARY )

