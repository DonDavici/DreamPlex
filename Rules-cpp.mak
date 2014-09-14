AM_CFLAGS = \
	-Wall \
	@DEBUG_CFLAGS@

AM_CPPFLAGS = \
	@PYTHON_CPPFLAGS@ \
	-include Python.h \
	-include enigma2-plugins-config.h

AM_CXXFLAGS = \
	-Wall \
	-fno-exceptions \
	@DEBUG_CFLAGS@ \
	@ENIGMA2_CFLAGS@ \
	@GSTREAMER_CFLAGS@ \
	@LIBCRYPTO_CFLAGS@ \
	@PTHREAD_CFLAGS@

PLUGIN_LIBTOOL_FLAGS = \
	-avoid-version \
	-module \
	-shared
