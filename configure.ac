AC_INIT([enigma2-plugin-extentions-dreamplex],[2.0])
AM_INIT_AUTOMAKE([dist-bzip2 foreign no-define tar-pax])
AC_CONFIG_HEADERS([enigma2-plugins-config.h])

# Silent rules are available since 1.11, but older versions
# are still in use. So don't use them unconditionally.
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

AC_USE_SYSTEM_EXTENSIONS
AC_SYS_LARGEFILE

AC_PROG_CC
AC_PROG_CXX
m4_ifdef([LT_INIT], [LT_INIT], [AC_PROG_LIBTOOL])
AC_CONFIG_MACRO_DIR([m4])

AC_CHECK_HEADERS([dbox/fp.h dbox/lcd-ks0713.h])

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))
AC_PATH_PROG(MSGINIT, msginit, AC_MSG_ERROR(Could not find msginit))
AC_PATH_PROG(MSGMERGE, msgmerge, AC_MSG_ERROR(Could not find msgmerge))
AC_PATH_PROG(MSGUNIQ, msguniq, AC_MSG_ERROR(Could not find msguniq))
AC_PATH_PROG(XGETTEXT, xgettext, AC_MSG_ERROR(Could not find xgettext))

AM_PATH_PYTHON
AX_PYTHON_DEVEL
AX_PTHREAD

AM_CONDITIONAL(IS_SH4, test "$TARGET_ARCH" = "sh4")

AC_CONFIG_FILES([
Makefile
meta/Makefile
po/Makefile
src/Makefile
src/skins/Makefile
src/skins/default/Makefile
src/skins/default/buttons/Makefile
src/skins/default/icons/Makefile
src/skins/default/images/Makefile
src/skins/default/picons/Makefile
src/skins/default_FHD/Makefile
src/skins/default_FHD/buttons/Makefile
src/skins/default_FHD/icons/Makefile
src/skins/default_FHD/images/Makefile
src/skins/default_FHD/picons/Makefile
])
AC_OUTPUT
