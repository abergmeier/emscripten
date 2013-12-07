# - Try to find Kiss FFT
# Once done this will define
#  KISS_FOUND - System has Kiss FFT
#  KISS_INCLUDE_DIRS - The Kiss FFT include directories
#  KISS_LIBRARIES - The libraries needed to use Kiss FFT
#  KISS_DEFINITIONS - Compiler switches required for using KISS FFT

find_package( PkgConfig )

pkg_check_modules( KISS QUIET kiss-fft )

set( KISS_DEFINITIONS ${KISS_CFLAGS_OTHER} )

find_path( KISS_INCLUDE_DIR
	NAMES kiss_fft.h
	HINTS ${KISS_INCLUDEDIR} ${KISS_INCLUDE_DIRS}
)

find_library( KISS_LIBRARY
	NAMES ${KISS_LIBRARIES}
	HINTS ${KISS_LIBDIR} ${KISS_LIBRARY_DIRS}
)

set( KISS_LIBRARIES    ${KISS_LIBRARY}     )
set( KISS_INCLUDE_DIRS ${KISS_INCLUDE_DIR} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set KISS_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( "Kiss FFT" DEFAULT_MSG
	KISS_LIBRARY KISS_INCLUDE_DIR
)

mark_as_advanced( KISS_INCLUDE_DIR KISS_LIBRARY )

