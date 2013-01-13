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
from Components.config import ConfigNumber
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

from Plugins.Extensions.DreamPlex.__common__ import registerPlexFonts, loadPlexSkin, checkPlexEnvironment, getBoxInformation ,printl2 as printl

#===============================================================================
# CONFIG
#===============================================================================
defaultPluginFolderPath = resolveFilename(SCOPE_PLUGINS, "Extensions/DreamPlex/")
defaultLogFolderPath    = "/tmp/"
defaultMediaFolderPath  = "/hdd/dreamplex/media/"
defaultPlayerTempPath  	= "/hdd/dreamplex/"

config.plugins.dreamplex = ConfigSubsection()

config.plugins.dreamplex.debugMode         = ConfigSelection(default="0", choices = [("0", _("Silent")),("1", _("Normal")),("2", _("High")),("3", _("All"))])
config.plugins.dreamplex.pluginfolderpath  = ConfigText(default = defaultPluginFolderPath)
config.plugins.dreamplex.logfolderpath     = ConfigText(default = defaultLogFolderPath, visible_width = 50, fixed_size = False)
config.plugins.dreamplex.mediafolderpath   = ConfigText(default = defaultMediaFolderPath, fixed_size=False)
config.plugins.dreamplex.showInMainMenu	   = ConfigYesNo(default = True)
config.plugins.dreamplex.showFilter	   	   = ConfigYesNo(default = True)
config.plugins.dreamplex.autoLanguage      = ConfigYesNo(default = False)


config.plugins.dreamplex.stopTVOnPicture			= ConfigYesNo(default = True)
config.plugins.dreamplex.useBufferControl			= ConfigYesNo(default = True)
config.plugins.dreamplex.useQuicktimeUserAgent		= ConfigYesNo(default = True)
config.plugins.dreamplex.setBufferSize 				= ConfigYesNo(default = True)
config.plugins.dreamplex.setSeekOnStart 			= ConfigYesNo(default = True)

config.plugins.dreamplex.bufferSize 				= ConfigNumber(default = 8)
config.plugins.dreamplex.playerTempPath 			= ConfigText(default = defaultPlayerTempPath, visible_width = 50, fixed_size=False)

config.plugins.dreamplex.entriescount              = ConfigInteger(0)
config.plugins.dreamplex.Entries                   = ConfigSubList()

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
	config.plugins.dreamplex.Entries[i].name 			= ConfigText(default = "PlexServer", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].connectionType  = ConfigSelection(default="0", choices = [("0", _("IP")),("1", _("DNS")), ("2", _("MYPLEX"))])
	config.plugins.dreamplex.Entries[i].ip 				= ConfigIP(default = [192,168,0,1])
	config.plugins.dreamplex.Entries[i].dns 			= ConfigText(default = "my.dns.url", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].myplexUrl		= ConfigText(default = "my.plexapp.com", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].port 			= ConfigInteger(default=32400, limits=(1, 65555))
	config.plugins.dreamplex.Entries[i].transcode       = ConfigYesNo(default = False)
	config.plugins.dreamplex.Entries[i].quality         = ConfigSelection(default="7", choices = [("0", _("64kbps, 128p, 3fps")), ("1", _("96kbps, 128p, 12fps")), ("2", _("208kbps, 160p, 15fps")), ("3", _("320kbps, 240p")),("4", _("720kbps, 320p")), ("5", _("1.5Mbps, 480p")), ("6", _("2Mbps, 720p")), ("7", _("3Mbps, 720p")), ("8", _("4Mbps, 720p")), ("9", _("8Mbps, 1080p")), ("10", _("10Mbps, 1080p")),("11", _("12Mbps, 1080p")),("12", _("20Mbps, 1080p"))])
	#config.plugins.dreamplex.Entries[i].streamMode		= ConfigSelection(default="0", choices = [("0", _("HTTP Streaming")),("1", _("Local Buffer Mode")),("2", _("Direct Play"))])
	
	# myPlex
	config.plugins.dreamplex.Entries[i].myplexUsername			= ConfigText(default = "", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].myplexPassword			= ConfigText(default = "", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].myplexToken   			= ConfigText(default = "", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].myplexTokenUsername		= ConfigText(default = "", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].renewMyplexToken		= ConfigYesNo(default = False)	
	
	# WOL
	config.plugins.dreamplex.Entries[i].wol			    = ConfigYesNo(default = False)
	config.plugins.dreamplex.Entries[i].wol_mac         = ConfigText(default = "00AA00BB00CC", visible_width = 12, fixed_size = False)
	config.plugins.dreamplex.Entries[i].wol_delay		= ConfigInteger(default=60, limits=(1, 180))
	
	printl("Server Settings: ","__init__::initServerEntryConfig", "I" )
	printl("state: " + str(config.plugins.dreamplex.Entries[i].state.value), "__init__::initServerEntryConfig", "I")
	printl("name: " + str(config.plugins.dreamplex.Entries[i].name.value), "__init__::initServerEntryConfig", "I")
	printl("connectionType: " + str(config.plugins.dreamplex.Entries[i].connectionType.value), "__init__::initServerEntryConfig", "I")
	printl("ip: " + str(config.plugins.dreamplex.Entries[i].ip.value), "__init__::initServerEntryConfig", "I")
	printl("dns: " + str(config.plugins.dreamplex.Entries[i].dns.value), "__init__::initServerEntryConfig", "I")
	printl("myplexUrl: " + str(config.plugins.dreamplex.Entries[i].myplexUrl.value), "__init__::initServerEntryConfig", "I")
	printl("port: " + str(config.plugins.dreamplex.Entries[i].port.value), "__init__::initServerEntryConfig", "I")
	printl("transcode: " + str(config.plugins.dreamplex.Entries[i].transcode.value), "__init__::initServerEntryConfig", "I")
	printl("quality: " + str(config.plugins.dreamplex.Entries[i].quality.value), "__init__::initServerEntryConfig", "I")
	printl("myplexUsername: " + str(config.plugins.dreamplex.Entries[i].myplexUsername.value), "__init__::initServerEntryConfig", "I", True, 8)
	printl("myplexPassword: " + str(config.plugins.dreamplex.Entries[i].myplexPassword.value), "__init__::initServerEntryConfig", "I", True, 4)
	printl("myplexToken: " + str(config.plugins.dreamplex.Entries[i].myplexToken.value), "__init__::initServerEntryConfig", "I", True, 8)
	printl("myplexTokenUsername: " + str(config.plugins.dreamplex.Entries[i].myplexTokenUsername.value), "__init__::initServerEntryConfig", "I", True, 8)
	printl("renewMyplexToken: " + str(config.plugins.dreamplex.Entries[i].renewMyplexToken.value), "__init__::initServerEntryConfig", "I")
	printl("wol: " + str(config.plugins.dreamplex.Entries[i].wol.value), "__init__::initServerEntryConfig", "I")
	printl("wol_mac: " + str(config.plugins.dreamplex.Entries[i].wol_mac.value), "__init__::initServerEntryConfig", "I")
	printl("wol_delay: " + str(config.plugins.dreamplex.Entries[i].wol_delay.value), "__init__::initServerEntryConfig", "I")
	
	printl("", "__init__::initServerEntryConfig", "C")
	return config.plugins.dreamplex.Entries[i]

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
	#printl("", "__init__::_(txt)", "S")
	
	if len(txt) == 0:
		return ""
	text = gettext.dgettext("DreamPlex", txt)
	if text == txt:
		text = gettext.gettext(txt)
	
	printl("text = " + str(text), "__init__::_(txt)", "X")	
	#printl("", "__init__::_(txt)", "C")
	return text

#===============================================================================
# 
#===============================================================================
def printEnvData():
	'''
	'''
	printl("", "__init__::printEnvData", "S")
	
	boxInfo = getBoxInformation()
	
	printl("Environment Data: ","__init__::printEnvData", "I" )
	printl("Boxinformation: " + str(boxInfo), "__init__::printEnvData", "I")
	
	printl("Global Settings: ","__init__::printEnvData", "I" )
	printl("debugMode: " + str(config.plugins.dreamplex.debugMode.value), "__init__::printEnvData", "I")
	printl("pluginfolderpath: " + str(config.plugins.dreamplex.pluginfolderpath.value), "__init__::printEnvData", "I")
	printl("logfolderpath: " + str(config.plugins.dreamplex.logfolderpath.value), "__init__::printEnvData", "I")
	printl("mediafolderpath: " + str(config.plugins.dreamplex.mediafolderpath.value), "__init__::printEnvData", "I")
	printl("playerTempPath: " + str(config.plugins.dreamplex.playerTempPath.value), "__init__::printEnvData", "I")
	printl("showInMainMenu: " + str(config.plugins.dreamplex.showInMainMenu.value), "__init__::printEnvData", "I")
	printl("showFilter: " + str(config.plugins.dreamplex.showFilter.value), "__init__::printEnvData", "I")
	printl("autoLanguage: " + str(config.plugins.dreamplex.autoLanguage.value), "__init__::printEnvData", "I")
	printl("stopTVOnPicture: " + str(config.plugins.dreamplex.stopTVOnPicture.value), "__init__::printEnvData", "I")
	printl("useBufferControl: " + str(config.plugins.dreamplex.useBufferControl.value), "__init__::printEnvData", "I")
	printl("useQuicktimeUserAgent: " + str(config.plugins.dreamplex.useQuicktimeUserAgent.value), "__init__::printEnvData", "I")
	printl("setBufferSize: " + str(config.plugins.dreamplex.setBufferSize.value), "__init__::printEnvData", "I")
	printl("setSeekOnStart: " + str(config.plugins.dreamplex.setSeekOnStart.value), "__init__::printEnvData", "I")
	printl("bufferSize: " + str(config.plugins.dreamplex.bufferSize.value), "__init__::printEnvData", "I")

	
	printl("", "__init__::printEnvData", "C")
	

#===============================================================================
# EXECUTE ON STARTUP
#===============================================================================
localeInit()
printEnvData()
initPlexServerConfig()
checkPlexEnvironment()
registerPlexFonts()
loadPlexSkin()
loadPlexPlugins()


