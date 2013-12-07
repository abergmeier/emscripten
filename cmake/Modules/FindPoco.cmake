# - Try to find Poco
# Once done this will define
#  POCO_FOUND - System has Poco
#  POCO_INCLUDE_DIRS - The Poco include directories
#  POCO_LIBRARIES - The libraries needed to use Poco
#  POCO_DEFINITIONS - Compiler switches required for using Poco

find_package( PkgConfig )

pkg_check_modules( POCO QUIET poco )

set( POCO_DEFINITIONS ${POCO_CFLAGS_OTHER} )

find_path( POCO_INCLUDE_DIR
	NAMES Poco/Poco.h
	HINTS ${POCO_INCLUDEDIR} ${POCO_INCLUDE_DIRS}
)

set( POCO_LIBRARY_LIST "" )
set( index 0 )

foreach( POCO_LIB ${POCO_LIBRARIES} )

	# FIXME: need find_library with different variables,
	# since it works only for the first call
	find_library( POCO_LIBRARY${index}
		NAMES ${POCO_LIB}
		HINTS ${POCO_LIBDIR} ${POCO_LIBRARY_DIRS}
	)

	list( APPEND POCO_LIBRARY_LIST "${POCO_LIBRARY${index}}" )
	MATH(EXPR index "${index}+1")
endforeach()

set( POCO_LIBRARIES    ${POCO_LIBRARY_LIST} )
set( POCO_INCLUDE_DIRS ${POCO_INCLUDE_DIR} )

include( FindPackageHandleStandardArgs )

# handle the QUIETLY and REQUIRED arguments and set POCO_FOUND to TRUE
# if all listed variables are TRUE
find_package_handle_standard_args( Poco DEFAULT_MSG
	POCO_LIBRARY_LIST POCO_INCLUDE_DIR
)

mark_as_advanced( POCO_INCLUDE_DIR POCO_LIBRARY POCO_LIBRARY_LIST )

