# -*- coding: utf-8 -*-
"""
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
"""
#===============================================================================
# IMPORT
#===============================================================================
import os
import gettext

from Components.config import config
from Components.config import ConfigSubsection
from Components.config import ConfigSelection
from Components.config import ConfigInteger
from Components.config import ConfigSubList
from Components.config import ConfigText
from Components.config import ConfigYesNo
from Components.config import ConfigIP
from Components.config import ConfigDirectory
from Components.Language import language

from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN, SCOPE_CURRENT_SKIN, SCOPE_LANGUAGE

from DPH_Singleton import Singleton

from __common__ import registerPlexFonts, loadPlexSkin, checkPlexEnvironment, getBoxInformation ,printl2 as printl, getXmlContent

#===============================================================================
#
#===============================================================================
version = "0.1"
source = "feed" # other option is "ipk"


defaultPluginFolderPath = resolveFilename(SCOPE_PLUGINS, "Extensions/DreamPlex/")
defaultSkinsFolderPath	= resolveFilename(SCOPE_PLUGINS, "Extensions/DreamPlex/skins")
defaultLogFolderPath    = "/tmp/"
defaultCacheFolderPath	= "/hdd/dreamplex/cache/"
defaultMediaFolderPath  = "/hdd/dreamplex/media/"
defaultPlayerTempPath  	= "/hdd/dreamplex/"
defaultConfigFolderPath	= "/hdd/dreamplex/config/"

# skin data
defaultSkin = "default"
skins = []

config.plugins.dreamplex = ConfigSubsection()
config.plugins.dreamplex.about                  	= ConfigSelection(default = "1", choices = [("1", " ")]) # need this for seperator in settings
config.plugins.dreamplex.debugMode         			= ConfigYesNo()
config.plugins.dreamplex.showInMainMenu	   			= ConfigYesNo(default = True)
config.plugins.dreamplex.showFilter	   	   			= ConfigYesNo(default = True)
config.plugins.dreamplex.autoLanguage      			= ConfigYesNo()
config.plugins.dreamplex.playTheme         			= ConfigYesNo()
config.plugins.dreamplex.showUnSeenCounts			= ConfigYesNo()
config.plugins.dreamplex.fastScroll		   			= ConfigYesNo()
config.plugins.dreamplex.summerizeSections 			= ConfigYesNo()
config.plugins.dreamplex.stopLiveTvOnStartup 		= ConfigYesNo()
config.plugins.dreamplex.useCache			 		= ConfigYesNo(default = True)
config.plugins.dreamplex.showInfobarOnBuffer 		= ConfigYesNo()
config.plugins.dreamplex.usePicCache			 	= ConfigYesNo(default = True)
config.plugins.dreamplex.useBackdropVideos		 	= ConfigYesNo()
config.plugins.dreamplex.showDetailsInList          = ConfigYesNo()
config.plugins.dreamplex.showDetailsInListDetailType = ConfigSelection(default = "1", choices = [("1", "user"), ("2", "server")])

if source != "ipk":
	config.plugins.dreamplex.showUpdateFunction		= ConfigYesNo()
else:
	config.plugins.dreamplex.showUpdateFunction	    = ConfigYesNo(default = True)

config.plugins.dreamplex.checkForUpdateOnStartup 	= ConfigYesNo()
config.plugins.dreamplex.updateType					= ConfigSelection(default = "1", choices = [("1", "Stable"), ("2", "Beta")])

config.plugins.dreamplex.pluginfolderpath  		= ConfigDirectory(default = defaultPluginFolderPath)
config.plugins.dreamplex.skinfolderpath			= ConfigDirectory(default = defaultSkinsFolderPath)

config.plugins.dreamplex.logfolderpath     		= ConfigDirectory(default = defaultLogFolderPath, visible_width = 50)
config.plugins.dreamplex.cachefolderpath  		= ConfigDirectory(default = defaultCacheFolderPath, visible_width = 50)
config.plugins.dreamplex.mediafolderpath   		= ConfigDirectory(default = defaultMediaFolderPath, visible_width = 50)
config.plugins.dreamplex.configfolderpath   	= ConfigDirectory(default = defaultConfigFolderPath, visible_width = 50)
config.plugins.dreamplex.playerTempPath   		= ConfigDirectory(default = defaultPlayerTempPath, visible_width = 50)

#movieViews = getViews("movies")
# showViews = getViews("shows")
# musicViews = getViews("music")

# counter = 0
# movieChoices = []
# for view in movieViews:
# 	movieChoices[counter] = (str(counter), str(view[0]))
# 	counter += 1

# TODO this should be dynamic
# view settings
config.plugins.dreamplex.defaultMusicView = ConfigSelection(default = 0, choices = [(0, "List"), (1, "long List"), (2, "Backdrop")])
config.plugins.dreamplex.defaultMovieView = ConfigSelection(default = 0, choices = [(0, "List"), (1, "long List"), (2, "Backdrop")])
config.plugins.dreamplex.defaultShowView = ConfigSelection(default = 0, choices = [(0, "List"), (1, "long List"), (2, "Backdrop")])

config.plugins.dreamplex.entriescount              = ConfigInteger(0)
config.plugins.dreamplex.Entries                   = ConfigSubList()

#===============================================================================
# 
#===============================================================================
def getVersion():
	printl("", "__init__::getVersion", "S")

	printl("", "__init__::getVersion", "C")
	return version

#===============================================================================
# 
#===============================================================================
def initBoxInformation():
	printl("", "__init__::getBoxInformation", "S")

	boxInfo = getBoxInformation()
	printl("=== BOX INFORMATION ===", "__init__::getBoxInformation", "I")
	printl("Box: " + str(boxInfo), "__init__::getBoxInformation", "I")

	printl("", "__init__::getBoxInformation", "C")

#===============================================================================
# 
#===============================================================================
def printGlobalSettings():
	printl("", "__init__::initGlobalSettings", "S")

	printl("=== VERSION ===", "__init__::getBoxInformation", "I")
	printl("current Version : " + str(version), "__init__::initGlobalSettings", "I")

	printl("=== GLOBAL SETTINGS ===", "__init__::getBoxInformation", "I")
	printl("debugMode: " + str(config.plugins.dreamplex.debugMode.value), "__init__::initGlobalSettings", "I")
	printl("pluginfolderpath: " + str(config.plugins.dreamplex.pluginfolderpath.value), "__init__::initGlobalSettings", "I")
	printl("logfolderpath: " + str(config.plugins.dreamplex.logfolderpath.value), "__init__::initGlobalSettings", "I")
	printl("mediafolderpath: " + str(config.plugins.dreamplex.mediafolderpath.value), "__init__::initGlobalSettings", "I")
	printl("cachefolderpath: " + str(config.plugins.dreamplex.cachefolderpath.value), "__init__::initGlobalSettings", "I")
	printl("playerTempPath: " + str(config.plugins.dreamplex.playerTempPath.value), "__init__::initGlobalSettings", "I")
	printl("showInMainMenu: " + str(config.plugins.dreamplex.showInMainMenu.value), "__init__::initGlobalSettings", "I")
	printl("showFilter: " + str(config.plugins.dreamplex.showFilter.value), "__init__::initGlobalSettings", "I")
	printl("autoLanguage: " + str(config.plugins.dreamplex.autoLanguage.value), "__init__::initGlobalSettings", "I")
	printl("stopLiveTvOnStartup: " + str(config.plugins.dreamplex.stopLiveTvOnStartup.value), "__init__::initGlobalSettings", "I")
	printl("playTheme: " + str(config.plugins.dreamplex.playTheme.value), "__init__::initGlobalSettings", "I")
	printl("fastScroll: " + str(config.plugins.dreamplex.fastScroll.value), "__init__::initGlobalSettings", "I")
	printl("summerizeSections: " + str(config.plugins.dreamplex.summerizeSections.value), "__init__::initGlobalSettings", "I")
	printl("useCache: " + str(config.plugins.dreamplex.useCache.value), "__init__::initGlobalSettings", "I")
	printl("showInfobarOnBuffer: " + str(config.plugins.dreamplex.showInfobarOnBuffer.value), "__init__::initGlobalSettings", "I")
	printl("usePicCache: " + str(config.plugins.dreamplex.usePicCache.value), "__init__::initGlobalSettings", "I")

	printl("", "__init__::initPlexSettings", "C")

#===============================================================================
# 
#===============================================================================
def initServerEntryConfig():
	printl("", "__init__::initServerEntryConfig", "S")

	config.plugins.dreamplex.Entries.append(ConfigSubsection())
	i = len(config.plugins.dreamplex.Entries) -1

	defaultName = "PlexServer"
	defaultIp = [192,168,0,1]
	defaultPort = 32400

	# SERVER SETTINGS
	config.plugins.dreamplex.Entries[i].id				= ConfigInteger(i)
	config.plugins.dreamplex.Entries[i].state 			= ConfigYesNo(default = True)
	config.plugins.dreamplex.Entries[i].autostart		= ConfigYesNo()
	config.plugins.dreamplex.Entries[i].name 			= ConfigText(default = defaultName, visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].connectionType  = ConfigSelection(default="0", choices = [("0", _("IP")),("1", _("DNS")), ("2", _("MYPLEX"))])
	config.plugins.dreamplex.Entries[i].ip				= ConfigIP(default = defaultIp)
	config.plugins.dreamplex.Entries[i].dns				= ConfigText(default = "my.dns.url", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].port 			= ConfigInteger(default = defaultPort, limits=(1, 65555))
	config.plugins.dreamplex.Entries[i].playbackType	= ConfigSelection(default="0", choices = [("0", _("Streamed")),("1", _("Transcoded")), ("2", _("Direct Local"))])
	config.plugins.dreamplex.Entries[i].localAuth	    = ConfigYesNo()

	printl("=== SERVER SETTINGS ===", "__init__::initServerEntryConfig", "D")
	printl("Server Settings: ","__init__::initServerEntryConfig", "D" )
	printl("id: " + str(config.plugins.dreamplex.Entries[i].id.value), "__init__::initServerEntryConfig", "D")
	printl("state: " + str(config.plugins.dreamplex.Entries[i].state.value), "__init__::initServerEntryConfig", "D")
	printl("autostart: " + str(config.plugins.dreamplex.Entries[i].autostart.value), "__init__::initServerEntryConfig", "D")
	printl("name: " + str(config.plugins.dreamplex.Entries[i].name.value), "__init__::initServerEntryConfig", "D")
	printl("connectionType: " + str(config.plugins.dreamplex.Entries[i].connectionType.value), "__init__::initServerEntryConfig", "D")
	printl("ip: " + str(config.plugins.dreamplex.Entries[i].ip.value), "__init__::initServerEntryConfig", "D")
	printl("dns: " + str(config.plugins.dreamplex.Entries[i].dns.value), "__init__::initServerEntryConfig", "D")
	printl("port: " + str(config.plugins.dreamplex.Entries[i].port.value), "__init__::initServerEntryConfig", "D")
	printl("playbackType: " + str(config.plugins.dreamplex.Entries[i].playbackType.value), "__init__::initServerEntryConfig", "D")

	# myPlex
	config.plugins.dreamplex.Entries[i].myplexUrl		= ConfigText(default = "my.plexapp.com", visible_width = 50, fixed_size = False)
	config.plugins.dreamplex.Entries[i].myplexUsername			= ConfigText(visible_width=50, fixed_size=False)
	config.plugins.dreamplex.Entries[i].myplexPassword			= ConfigText(visible_width=50, fixed_size=False)
	config.plugins.dreamplex.Entries[i].myplexToken				= ConfigText(visible_width=50, fixed_size=False)
	config.plugins.dreamplex.Entries[i].myplexTokenUsername		= ConfigText(visible_width=50, fixed_size=False)
	config.plugins.dreamplex.Entries[i].renewMyplexToken		= ConfigYesNo()

	printl("=== myPLEX ===", "__init__::initServerEntryConfig", "D")
	printl("myplexUrl: " + str(config.plugins.dreamplex.Entries[i].myplexUrl.value), "__init__::initServerEntryConfig", "D")
	printl("myplexUsername: " + str(config.plugins.dreamplex.Entries[i].myplexUsername.value), "__init__::initServerEntryConfig", "D", True, 8)
	printl("myplexPassword: " + str(config.plugins.dreamplex.Entries[i].myplexPassword.value), "__init__::initServerEntryConfig", "D", True, 6)
	printl("myplexToken: " + str(config.plugins.dreamplex.Entries[i].myplexToken.value), "__init__::initServerEntryConfig", "D", True, 8)
	printl("myplexTokenUsername: " + str(config.plugins.dreamplex.Entries[i].myplexTokenUsername.value), "__init__::initServerEntryConfig", "D", True, 8)
	printl("renewMyplexToken: " + str(config.plugins.dreamplex.Entries[i].renewMyplexToken.value), "__init__::initServerEntryConfig", "D")

	# STREAMED
	# no options at the moment

	# TRANSCODED
	config.plugins.dreamplex.Entries[i].universalTranscoder	= ConfigYesNo(default = True)

	# old transcoder settings
	config.plugins.dreamplex.Entries[i].quality				= ConfigSelection(default="7", choices = [("0", _("64kbps, 128p, 3fps")), ("1", _("96kbps, 128p, 12fps")), ("2", _("208kbps, 160p, 15fps")), ("3", _("320kbps, 240p")),("4", _("720kbps, 320p")), ("5", _("1.5Mbps, 480p")), ("6", _("2Mbps, 720p")), ("7", _("3Mbps, 720p")), ("8", _("4Mbps, 720p")), ("9", _("8Mbps, 1080p")), ("10", _("10Mbps, 1080p")),("11", _("12Mbps, 1080p")),("12", _("20Mbps, 1080p"))])
	config.plugins.dreamplex.Entries[i].segments 			= ConfigInteger(default=5, limits=(1, 10))

	# universal transcoder settings
	config.plugins.dreamplex.Entries[i].uniQuality = ConfigSelection(default="3", choices = [("0", _("420x240, 320kbps")), ("1", _("576x320, 720 kbps")), ("2", _("720x480, 1,5mbps")), ("3", _("1024x768, 2mbps")),("4", _("1280x720, 3mbps")), ("5", _("1280x720, 4mbps")), ("6", _("1920x1080, 8mbps")), ("7", _("1920x1080, 10mbps")), ("8", _("1920x1080, 12mbps")), ("9", _("1920x1080, 20mbps"))])


	printl("=== TRANSCODED ===", "__init__::initServerEntryConfig", "D")
	printl("transcode: " + str(config.plugins.dreamplex.Entries[i].universalTranscoder.value), "__init__::initServerEntryConfig", "D")
	printl("quality: " + str(config.plugins.dreamplex.Entries[i].quality.value), "__init__::initServerEntryConfig", "D")
	printl("segments: " + str(config.plugins.dreamplex.Entries[i].segments.value), "__init__::initServerEntryConfig", "D")
	printl("uniQuality: " + str(config.plugins.dreamplex.Entries[i].uniQuality.value), "__init__::initServerEntryConfig", "D")
	# TRANSCODED VIA PROXY

	# DIRECT LOCAL
	printl("=== DIRECT LOCAL ===", "__init__::initServerEntryConfig", "D")

	# DIRECT REMOTE
	config.plugins.dreamplex.Entries[i].smbUser = ConfigText(visible_width=50, fixed_size=False)
	config.plugins.dreamplex.Entries[i].smbPassword = ConfigText(visible_width=50, fixed_size=False)
	config.plugins.dreamplex.Entries[i].nasOverrideIp = ConfigIP(default=[192, 168, 0, 1])
	config.plugins.dreamplex.Entries[i].nasRoot = ConfigText(default="/", visible_width=50, fixed_size=False)

	printl("=== DIRECT REMOTE ===", "__init__::initServerEntryConfig", "D")
	printl("smbUser: " + str(config.plugins.dreamplex.Entries[i].smbUser.value), "__init__::initServerEntryConfig", "D", True)
	printl("smbPassword: " + str(config.plugins.dreamplex.Entries[i].smbPassword.value), "__init__::initServerEntryConfig", "D", True)
	printl("nasOverrideIp: " + str(config.plugins.dreamplex.Entries[i].nasOverrideIp.value), "__init__::initServerEntryConfig", "D")
	printl("nasRoot: " + str(config.plugins.dreamplex.Entries[i].nasRoot.value), "__init__::initServerEntryConfig", "D")

	# WOL
	config.plugins.dreamplex.Entries[i].wol				= ConfigYesNo()
	config.plugins.dreamplex.Entries[i].wol_mac			= ConfigText(default = "00AA00BB00CC", visible_width = 12, fixed_size = False)
	config.plugins.dreamplex.Entries[i].wol_delay		= ConfigInteger(default=60, limits=(1, 180))

	printl ("=== WOL ===", "__init__::initServerEntryConfig", "D")
	printl("wol: " + str(config.plugins.dreamplex.Entries[i].wol.value), "__init__::initServerEntryConfig", "D")
	printl("wol_mac: " + str(config.plugins.dreamplex.Entries[i].wol_mac.value), "__init__::initServerEntryConfig", "D")
	printl("wol_delay: " + str(config.plugins.dreamplex.Entries[i].wol_delay.value), "__init__::initServerEntryConfig", "D")

	printl("", "__init__::initServerEntryConfig", "C")
	return config.plugins.dreamplex.Entries[i]

#===============================================================================
# 
#===============================================================================
def registerSkinParamsInstance():
	printl("", "__init__::registerSkinParamsInstance", "S")

	configXml = getXmlContent("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value +"/params")
	Singleton().getSkinParamsInstance(configXml)

	printl("", "__init__::registerSkinParamsInstance", "C")
#===============================================================================
# 
#===============================================================================
def initPlexServerConfig():
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
	printl("", "__init__::loadPlexPlugins", "S")

	# we have to load them here because they are not ready though
	from DP_LibMovies import DP_LibMovies
	from DP_LibShows import DP_LibShows
	from DP_LibMusic import DP_LibMusic
	from __plugin__ import registerPlugin, Plugin

	printl("registering ... movies", "__init__::loadPlexPlugins", "D")
	registerPlugin(Plugin(pid="movies", name=_("Movies"), start=DP_LibMovies, where=Plugin.MENU_MOVIES))

	printl("registering ... tvshows", "__init__::loadPlexPlugins", "D")
	registerPlugin(Plugin(pid="tvshows", name=_("TV Shows"), start=DP_LibShows, where=Plugin.MENU_TVSHOWS))

	printl("registering ... music", "__init__::loadPlexPlugins", "D")
	registerPlugin(Plugin(pid="music", name=_("Music"), start=DP_LibMusic, where=Plugin.MENU_MUSIC))

	#printl("registering ... pictures", "__initgetBoxInformationt__::loadPlexPlugins", "D")
	#registerPlugin(Plugin(pid="tvshows", name=_("Music"), start=DP_LibPictures, where=Plugin.MENU_PICTURES))

	#printl("registering ... channels", "__initgetBoxInformationt__::loadPlexPlugins", "D")
	#registerPlugin(Plugin(pid="tvshows", name=_("Music"), start=DP_LibChannels, where=Plugin.MENU_CHANNELS))

	printl("", "__init__::loadPlexPlugins", "C")


#===============================================================================
# 
#===============================================================================
def localeInit():
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
def getInstalledSkins():
	printl("", "__init__::getInstalledSkins", "S")

	mySkins = []
	myDefaultSkin = "default"

	try:
		for skin in os.listdir(config.plugins.dreamplex.skinfolderpath.value):
			print("skin: " + str(skin), None, "D")
			if os.path.isdir(os.path.join(config.plugins.dreamplex.skinfolderpath.value, skin)):
				mySkins.append(skin)
	except Exception, ex:
		printl("no skin found in Dreamplex", "__init__::getInstalledSkins", "D")
		printl("Exception(" + str(type(ex)) + "): " + str(ex), "__init__::getInstalledSkins", "E")
		mySkins.append(myDefaultSkin)

	#Also check if a real enigma2 skin contains dreamplex screens
	try:
		skinPath = resolveFilename(SCOPE_SKIN)
		printl("__init__:: Current enigma2 skin " + resolveFilename(SCOPE_CURRENT_SKIN), "__init__::getInstalledSkins", "D")

		for skin in os.listdir(skinPath):
			path = os.path.join(skinPath, skin)
			if os.path.isdir(path):
				xml = os.path.join(path, "skin_dreamplex.xml")
				if os.path.isfile(xml):
					mySkins.append("~" + skin)
	except Exception, ex:
		printl("no skindata in enigma2 skin found", "__init__::getInstalledSkins", "D")
		printl("Exception(" + str(type(ex)) + "): " + str(ex), "__init__::getInstalledSkins", "E")

	printl("Found enigma2 skins \"%s\"" % str(mySkins), "__init__::getInstalledSkins", "D")

	config.plugins.dreamplex.skins	= ConfigSelection(default = myDefaultSkin, choices = mySkins)

	printl("", "__init__::getInstalledSkins", "C")

#===============================================================================
# 
#===============================================================================
def _(txt):
	#printl("", "__init__::_(txt)", "S")

	if len(txt) == 0:
		return ""
	text = gettext.dgettext("DreamPlex", txt)
	if text == txt:
		text = gettext.gettext(txt)

	printl("text = " + str(text), "__init__::_(txt)", "D")

	#printl("", "__init__::_(txt)", "C")
	return text

#===============================================================================
# EXECUTE ON STARTUP
#===============================================================================
def prepareEnvironment():
	localeInit()
	getInstalledSkins()
	initBoxInformation()
	printGlobalSettings()
	initPlexServerConfig()
	registerSkinParamsInstance()
	checkPlexEnvironment()
	registerPlexFonts()
	loadPlexSkin()
	loadPlexPlugins()

