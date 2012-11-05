# -*- coding: utf-8 -*-
'''
DreamPlex Plugin by DonDavici, 2012
 
https://github.com/DonDavici/DreamPlex

Some of the code is from other plugins:
all credits to the coders :-)

DreamPlex Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

DreamPlex Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
'''
#===============================================================================
# IMPORT
#===============================================================================
import os
import sys
import gettext

from enigma import getDesktop, addFont
from skin import loadSkin, loadSingleSkinData
from Components.config import config
from Components.config import ConfigSubsection
from Components.config import ConfigSelection
from Components.config import ConfigInteger
from Components.config import ConfigSubList
from Components.config import ConfigSubDict
from Components.config import ConfigText
from Components.config import configfile
from Components.config import ConfigYesNo
from Components.config import ConfigPassword
from Components.config import ConfigIP
from Components.config import ConfigMAC
from Components.Language import language

import Plugins.Plugin

from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN, SCOPE_CURRENT_SKIN, SCOPE_LANGUAGE

from Plugins.Extensions.DreamPlex.__plugin__ import registerPlugin, Plugin

from Plugins.Extensions.DreamPlex.DP_LibMovies import DP_LibMovies
from Plugins.Extensions.DreamPlex.DP_LibShows import DP_LibShows

from Plugins.Extensions.DreamPlex.__common__ import registerPlexFonts, loadPlexSkin, checkPlexEnvironment, printl2 as printl

#===============================================================================
# CONFIG
#===============================================================================
currentVersion 			= "0.5 beta"
defaultPluginFolderPath = resolveFilename(SCOPE_PLUGINS, "Extensions/DreamPlex/")
defaultConfigFolderPath = "/hdd/dreamplex/"
defaultMediaFolderPath  = defaultConfigFolderPath + "media/"
defaultSkinFolderPath   = defaultPluginFolderPath + "skins/"
defaultSkin             = "blackDon"
defaultTmpFolderPath    = "/tmp/"
defaultLogFolderPath	= defaultTmpFolderPath
config.plugins.dreamplex = ConfigSubsection()

config.plugins.dreamplex.version 		   = ConfigText(default = currentVersion)
config.plugins.dreamplex.debugMode         = ConfigSelection(default="0", choices = [("0", _("Silent")),("1", _("Normal")),("2", _("High")),("3", _("All"))])
config.plugins.dreamplex.pluginfolderpath  = ConfigText(default = defaultPluginFolderPath)
config.plugins.dreamplex.skinfolderpath    = ConfigText(default = defaultSkinFolderPath)
config.plugins.dreamplex.tmpfolderpath     = ConfigText(default = defaultTmpFolderPath)
config.plugins.dreamplex.logfolderpath     = ConfigText(default = defaultLogFolderPath)
config.plugins.dreamplex.configfolderpath  = ConfigText(default = defaultConfigFolderPath, fixed_size=False)
config.plugins.dreamplex.mediafolderpath   = ConfigText(default = defaultMediaFolderPath, fixed_size=False)
config.plugins.dreamplex.skin              = ConfigText(default = defaultSkin)

config.plugins.dreamplex.stopTVOnPicture			= ConfigYesNo(default = True)
config.plugins.dreamplex.useBufferControl			= ConfigYesNo(default = True)
config.plugins.dreamplex.useQuicktimeUserAgent		= ConfigYesNo(default = True)
config.plugins.dreamplex.setBufferSize 				= ConfigYesNo(default = True)
config.plugins.dreamplex.setSeekOnStart 			= ConfigYesNo(default = True)

config.plugins.dreamplex.bufferSize 				= ConfigInteger(default = "8388606")
config.plugins.dreamplex.path 						= ConfigText(default = defaultConfigFolderPath, fixed_size=False)

config.plugins.dreamplex.entriescount              = ConfigInteger(0)
config.plugins.dreamplex.Entries                   = ConfigSubList()

config.plugins.dreamplex.plugins 	= ConfigSubsection()

#===============================================================================
# 
#===============================================================================
def initServerEntryConfig():
	'''
	'''
	printl("", "__init__::initServerEntryConfig", "S")
	
	config.plugins.dreamplex.Entries.append(ConfigSubsection())
	i = len(config.plugins.dreamplex.Entries) -1
	config.plugins.dreamplex.Entries[i].state 			= ConfigYesNo(default = True)
	config.plugins.dreamplex.Entries[i].connectionType  = ConfigSelection(default="0", choices = [("0", _("wan")),("1", _("lan"))])
	config.plugins.dreamplex.Entries[i].name 			= ConfigText(default = "PlexServer", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].ip 				= ConfigIP(default = [192,168,0,1])
	config.plugins.dreamplex.Entries[i].port 			= ConfigInteger(default=32400, limits=(1, 65555))
	config.plugins.dreamplex.Entries[i].transcode       = ConfigYesNo(default = True)
	config.plugins.dreamplex.Entries[i].transcodeType   = ConfigSelection(default="0", choices = [("0", _("m3u8")),("1", _("flv"))])
	config.plugins.dreamplex.Entries[i].quality         = ConfigSelection(default="0", choices = [("0", _("240p")),("1", _("320p")),("2", _("480p")),("3", _("720p")),("4", _("1080p"))])
	config.plugins.dreamplex.Entries[i].audioOutput     = ConfigSelection(default="2", choices = [("0", _("mp3,aac")),("1", _("mp3,aac,ac3")),("2", _("mp3,aac,ac3,dts"))])
	config.plugins.dreamplex.Entries[i].streamMode		= ConfigSelection(default="0", choices = [("0", _("HTTP Streaming")),("1", _("Local Buffer Mode")),("2", _("Direct Play"))])
	config.plugins.dreamplex.Entries[i].wol			    = ConfigYesNo(default = False)
	config.plugins.dreamplex.Entries[i].wol_mac         = ConfigText(default = "00AA00BB00CC", visible_width = 12, fixed_size = False)
	config.plugins.dreamplex.Entries[i].wol_delay		= ConfigInteger(default=60, limits=(1, 180))
	
	
	return config.plugins.dreamplex.Entries[i]
	
	printl("", "__init__::initServerEntryConfig", "C")

#===============================================================================
# 
#===============================================================================
def initPlexServerConfig():
	'''
	'''
	printl("", "__init__::initPlexServerConfig", "S")
	
	count = config.plugins.dreamplex.entriescount.value
	if count != 0:
		i = 0
		while i < count:
			initServerEntryConfig()
			i += 1
	
	printl("", "__init__::initPlexServerConfig", "C")
	
#===============================================================================
# 
#===============================================================================
def loadPlexPlugins():
	'''
	'''
	printl("", "__init__::loadPlexPlugins", "S")
	
	printl("registering ... movies", "__init__::loadPlexPlugins", "D")
	registerPlugin(Plugin(pid="movies", name=_("Movies"), start=DP_LibMovies, where=Plugin.MENU_VIDEOS))
	
	printl("registering ... tvhshows", "__init__::loadPlexPlugins", "D")
	registerPlugin(Plugin(pid="tvshows", name=_("TV Shows"), start=DP_LibShows, where=Plugin.MENU_VIDEOS))
	
	printl("", "__init__::loadPlexPlugins", "C")


#===============================================================================
# 
#===============================================================================
def localeInit():
	'''
	'''
	printl("", "__init__::localeInit", "S")
	
	lang = language.getLanguage()
	os.environ["LANGUAGE"] = lang[:2]
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain("DreamPlex", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/DreamPlex/locale/"))
	
	printl("", "__init__::localeInit", "C")

#===============================================================================
# 
#===============================================================================
def _(txt):
	'''
	'''
	printl("", "__init__::_(txt)", "S")
	
	if len(txt) == 0:
		return ""
	text = gettext.dgettext("DreamPlex", txt)
	if text == txt:
		text = gettext.gettext(txt)
	
	printl("text = " + str(text), "__init__::_(txt)", "X")	
	printl("", "__init__::_(txt)", "C")
	return text

#===============================================================================
# EXECUTE ON STARTUP
#===============================================================================
localeInit()
initPlexServerConfig()
checkPlexEnvironment()
registerPlexFonts()
loadPlexSkin()
loadPlexPlugins()

