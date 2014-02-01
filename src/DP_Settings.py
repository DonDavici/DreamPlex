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
#=================================
#IMPORT
#=================================
import time

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen

from __common__ import printl2 as printl, getBoxInformation
from __init__ import initServerEntryConfig, getVersion, _ # _ is translation

from DP_Mappings import DPS_Mappings
from DP_PathSelector import DPS_PathSelector
from DPH_PlexGdm import PlexGdm

#===============================================================================
#
#===============================================================================
class DPS_Settings(Screen, ConfigListScreen, HelpableScreen):

	_hasChanged = False
	_session = None
	skins = None
	
	def __init__(self, session):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self.cfglist = []
		ConfigListScreen.__init__(self, self.cfglist, session, on_change = self._changed)
		
		self._session = session
		self._hasChanged = False

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["help"] = StaticText()
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "DPS_Settings"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.ok,
			"left": self.keyLeft,
			"right": self.keyRight,
			"bouquet_up":	self.keyBouquetUp,
			"bouquet_down":	self.keyBouquetDown,
		}, -2)
		
		self.createSetup()
		
		self["config"].onSelectionChanged.append(self.updateHelp)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def setCustomTitle(self):
		printl("", self, "S")
		
		self.setTitle(_("Settings"))

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def createSetup(self):
		printl("", self, "S")
		
		separator = "".ljust(90,"_")
		
		self.cfglist = []
		
		# GENERAL SETTINGS
		self.cfglist.append(getConfigListEntry(_("General Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Used Skin"), config.plugins.dreamplex.skins, _("If you change the skin you have to restart at least the GUI!")))
		self.cfglist.append(getConfigListEntry(_("> Show Plugin in Main Menu"), config.plugins.dreamplex.showInMainMenu, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Use Cache for Sections"), config.plugins.dreamplex.useCache, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Use Picture Cache"), config.plugins.dreamplex.usePicCache, _("Use this if you do not have enough space on your box e.g. no hdd drive just flash.")))
		self.cfglist.append(getConfigListEntry(_("> Show Infobar when buffer drained"), config.plugins.dreamplex.showInfobarOnBuffer, _(" ")))
		
		self.cfglist.append(getConfigListEntry(_("> Stop Live TV on startup"), config.plugins.dreamplex.stopLiveTvOnStartup, _(" ")))
		# playing themes stops live tv for this reason we enable this only if live stops on startup is set
		# also backdrops as video needs to turn of live tv
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			self.cfglist.append(getConfigListEntry(_(">> Show Backdrops as Videos"), config.plugins.dreamplex.useBackdropVideos, _("Use this if you have m1v videos as backdrops")))

			# if backdrop videos are active we have to turn off theme playback
			if config.plugins.dreamplex.useBackdropVideos.value:
				config.plugins.dreamplex.playTheme.value = False
			else:
				self.cfglist.append(getConfigListEntry(_(">> Play Themes in TV Shows"), config.plugins.dreamplex.playTheme, _(" ")))
		else:
			# if the live startup stops is not set we have to turn of playtheme automatically
			config.plugins.dreamplex.playTheme.value = False
			config.plugins.dreamplex.useBackdropVideos.value = False

		if config.plugins.dreamplex.showUpdateFunction.value:
			self.cfglist.append(getConfigListEntry(_("> Check for updates on startup"), config.plugins.dreamplex.checkForUpdateOnStartup, _("If activated on each start we will check if there is a new version depending on your update type.")))
			self.cfglist.append(getConfigListEntry(_("> Updatetype"), config.plugins.dreamplex.updateType, _("Use Beta only if you really want to help with testing")))
		# USERINTERFACE SETTINGS
		self.cfglist.append(getConfigListEntry(_("Userinterface Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Summerize Sections"), config.plugins.dreamplex.summerizeSections, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Show Filter for Section"), config.plugins.dreamplex.showFilter, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Show Seen/Unseen count in TvShows"), config.plugins.dreamplex.showUnSeenCounts, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Use fastScroll as default"), config.plugins.dreamplex.fastScroll, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Show additional data for myPlex sections"), config.plugins.dreamplex.showDetailsInList, _(" ")))
		if config.plugins.dreamplex.showDetailsInList.value:
			self.cfglist.append(getConfigListEntry(_("> Detail type for additional data"), config.plugins.dreamplex.showDetailsInListDetailType, _(" ")))

		# PATH SETTINGS
		self.cfglist.append(getConfigListEntry(_("Path Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		
		self.mediafolderpath = getConfigListEntry(_("> Media Folder Path"), config.plugins.dreamplex.mediafolderpath, _(" "))
		self.cfglist.append(self.mediafolderpath)
		
		self.configfolderpath = getConfigListEntry(_("> Config Folder Path"), config.plugins.dreamplex.configfolderpath, _(" "))
		self.cfglist.append(self.configfolderpath)
		
		self.cachefolderpath = getConfigListEntry(_("> Cache Folder Path"), config.plugins.dreamplex.cachefolderpath, _(" "))
		self.cfglist.append(self.cachefolderpath)

		self.playerTempPath =  getConfigListEntry(_("> Player Temp Path"), config.plugins.dreamplex.playerTempPath, _(" "))
		self.cfglist.append(self.playerTempPath)
		
		self.logfolderpath = getConfigListEntry(_("> Log Folder Path"), config.plugins.dreamplex.logfolderpath, _(" "))
		self.cfglist.append(self.logfolderpath)
		
		# MISC
		self.cfglist.append(getConfigListEntry(_("Misc Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Debug Mode"), config.plugins.dreamplex.debugMode, _(" ")))

		self["config"].list = self.cfglist
		self["config"].l.setList(self.cfglist)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def _changed(self):
		printl("", self, "S")
		
		self._hasChanged = True

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def updateHelp(self):
		printl("", self, "S")
		
		cur = self["config"].getCurrent()
		printl("cur: " + str(cur), self, "D")
		self["help"].text = cur and cur[2] or ""
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		printl("", self, "S")

		cur = self["config"].getCurrent()
		
		if cur == self.mediafolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.mediafolderpath[1].value, "media")
		
		elif cur == self.configfolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.configfolderpath[1].value, "config")
		
		elif cur == self.playerTempPath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.playerTempPath[1].value, "player")

		elif cur == self.logfolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.logfolderpath[1].value, "log")

		elif cur == self.cachefolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.cachefolderpath[1].value, "cache")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def savePathConfig(self, pathValue, myType):
		printl("", self, "S")
		
		printl("pathValue: " + str(pathValue), self, "D")
		printl("type: " + str(myType), self, "D")
		
		if pathValue is not None:

			if myType == "media":
				self.mediafolderpath[1].value = pathValue
			
			elif myType == "config":
				self.configfolderpath[1].value = pathValue
			
			elif myType == "player":
				self.playerTempPath[1].value = pathValue
	
			elif myType == "log":
				self.logfolderpath[1].value = pathValue
	
			elif myType == "cache":
				self.cachefolderpath[1].value = pathValue
			
		config.plugins.dreamplex.save()
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keySave(self):
		printl("", self, "S")

		self.saveAll()
		self.close(None)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyLeft(self):
		printl("", self, "S")
		
		ConfigListScreen.keyLeft(self)
		self.createSetup()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyRight(self):
		printl("", self, "S")
		
		ConfigListScreen.keyRight(self)
		self.createSetup()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyBouquetUp(self):
		printl("", self, "S")
		
		self["config"].instance.moveSelection(self["config"].instance.pageUp)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def keyBouquetDown(self):
		printl("", self, "S")
		
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPS_ServerEntriesListConfigScreen(Screen):

	def __init__(self, session, what = None):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.session = session
		
		self["state"] = StaticText(_("State"))
		self["name"] = StaticText(_("Name"))
		self["ip"] = StaticText(_("IP"))
		self["port"] = StaticText(_("Port"))
		
		self["key_red"] = StaticText(_("Discover"))
		self["key_green"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Delete"))
		self["entrylist"] = DPS_ServerEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyYellow,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "yellow":	self.keyYellow,
			 "green":	self.keyGreen,
			 "blue":	self.keyDelete,
			 }, -1)
		self.what = what
		self.updateList()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def updateList(self):
		printl("", self, "S")
		
		self["entrylist"].buildList()

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyClose(self):
		printl("", self, "S")
		
		self.close(self.session, self.what, None)

		printl("", self, "C")
	
	#=======================================================================
	# 
	#=======================================================================
	def keyGreen(self):
		printl("", self, "S")
		
		self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, None)
		
		printl("", self, "C")
		
	#=======================================================================
	# 
	#=======================================================================
	def keyRed(self):
		printl("", self, "S")

		client = PlexGdm(debug=3)
		version = str(getVersion())
		gBoxType = getBoxInformation()
		clientBox = gBoxType[1]
		printl("clientBox: " + str(gBoxType), self, "D")
		client.clientDetails(clientBox, "DreamPlex Client", "3003", "DreamPlex", version)

		client.start_discovery()
		while not client.discovery_complete:
			print "Waiting for results"
			time.sleep(1)
		
		client.stop_discovery()
		serverList = client.getServerList()
		printl("serverList: " + str(serverList),self, "D")
		
		menu = []
		for server in serverList:
			printl("server: " + str(server), self, "D")
			menu.append((str(server.get("serverName")) + " (" + str(server.get("server")) + ":" + str(server.get("port")) + ")", server,))
			
		printl("menu: " + str(menu), self, "D")
		self.session.openWithCallback(self.useSelectedServerData, ChoiceBox, title=_("Select server"), list=menu)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def useSelectedServerData(self, choice):
		printl("", self, "S")
		
		if choice is not None:
			serverData = choice[1]
			self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, None, serverData)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyOK(self): #not in use for now
		printl("", self, "S")
		
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except Exception, ex:
			printl("Exception: " + str(ex), self, "W")
			sel = None
		
		self.close(self.session, self.what, sel)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyYellow(self):
		printl("", self, "S")
		
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		
		except Exception, ex:
			printl("Exception: " + str(ex), self, "W")
			sel = None
		
		if sel is None:
			return
		
		printl("config selction: " +  str(sel), self, "D")
		self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, sel)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyDelete(self):
		printl("", self, "S")
		
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		
		except Exception, ex:
			printl("Exception: " + str(ex), self, "W")
			sel = None
		
		if sel is None:
			return
		
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Server Entry?"))
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def deleteConfirm(self, result):
		printl("", self, "S")
		
		if not result:
			return
		
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.dreamplex.entriescount.value -= 1
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.remove(sel)
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()
		self.updateList()
		
		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPS_ServerEntryConfigScreen(ConfigListScreen, Screen):
	
	useMappings = False

	def __init__(self, session, entry, data = None):
		printl("", self, "S")
		
		self.session = session
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel,
			"yellow": self.keyYellow,
			"left": self.keyLeft,
			"right": self.keyRight,
		}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Delete"))
		self["key_yellow"] = StaticText(_("mappings"))
		self["help"] = StaticText()
		
		if entry is None:
			self.newmode = 1
			self.current = initServerEntryConfig()
			if data is not None:
				ipBlocks = data.get("server").split(".")
				self.current.name.value = data.get("serverName")
				self.current.ip.value = [int(ipBlocks[0]),int(ipBlocks[1]),int(ipBlocks[2]),int(ipBlocks[3])]
				self.current.port.value = int(data.get("port"))
				self.keySave(True)

		else:
			self.newmode = 0
			self.current = entry
			self.currentId = self.current.id.value
			printl("currentId: " + str(self.currentId), self, "D")

		self.cfglist = []
		ConfigListScreen.__init__(self, self.cfglist, session)

		self.createSetup()
		
		self["config"].onSelectionChanged.append(self.updateHelp)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def createSetup(self):
		printl("", self, "S")
		
		separator = "".ljust(90,"_")
		
		self.cfglist = []
		##
		self.cfglist.append(getConfigListEntry(_("General Settings") + separator, config.plugins.dreamplex.about, _("-")))
		##
		self.cfglist.append(getConfigListEntry(_(" > State"), self.current.state, _("Toggle state to on/off to show this server in lost or not.")))
		self.cfglist.append(getConfigListEntry(_(" > Autostart"), self.current.autostart, _("Enter this server automatically on startup.")))
		self.cfglist.append(getConfigListEntry(_(" > Name"), self.current.name, _(" ")))
		
		##
		self.cfglist.append(getConfigListEntry(_("Connection Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		##
		self.cfglist.append(getConfigListEntry(_(" > Connection Type"), self.current.connectionType, _(" ")))
		
		if self.current.connectionType.value == "0": # IP
			self.cfglist.append(getConfigListEntry(_(" > Local Authentication"), self.current.localAuth, _("Toggle state to on/off")))
			self.addIpSettings()
			if self.current.localAuth.value:
				self.addMyPlexSettings()

		elif self.current.connectionType.value == "1": # DNS
			self.cfglist.append(getConfigListEntry(_(" >> DNS"), self.current.dns, _(" ")))
			self.cfglist.append(getConfigListEntry(_(" >> Port"), self.current.port, _(" ")))

		elif self.current.connectionType.value == "2": # MYPLEX
			self.addMyPlexSettings()

		##
		self.cfglist.append(getConfigListEntry(_("Playback Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		##
		
		self.cfglist.append(getConfigListEntry(_(" > Playback Type"), self.current.playbackType, _(" ")))
		if self.current.playbackType.value == "0":
			self.useMappings = False
			
		elif self.current.playbackType.value == "1":
			self.useMappings = False
			self.cfglist.append(getConfigListEntry(_(" >> Use universal Transcoder"), self.current.universalTranscoder, _("You need gstreamer_fragmented installed for this feature! Please check in System ... ")))
			if not self.current.universalTranscoder.value:
				self.cfglist.append(getConfigListEntry(_(" >> Transcoding quality"), self.current.quality, _("You need gstreamer_fragmented installed for this feature! Please check in System ... ")))
				self.cfglist.append(getConfigListEntry(_(" >> Segmentsize in seconds"), self.current.segments, _("You need gstreamer_fragmented installed for this feature! Please check in System ... ")))
			else:
				self.cfglist.append(getConfigListEntry(_(" >> Transcoding quality"), self.current.uniQuality, _("You need gstreamer_fragmented installed for this feature! Please check in System ... ")))
			
		elif self.current.playbackType.value == "2":
			printl("i am here", self, "D")
			self.useMappings = True
		
		elif self.current.playbackType.value == "3":
			self.useMappings = False
			#self.cfglist.append(getConfigListEntry(_(">> Username"), self.current.smbUser))
			#self.cfglist.append(getConfigListEntry(_(">> Password"), self.current.smbPassword))
			#self.cfglist.append(getConfigListEntry(_(">> Server override IP"), self.current.nasOverrideIp))
			#self.cfglist.append(getConfigListEntry(_(">> Servers root"), self.current.nasRoot))
		
		##
		self.cfglist.append(getConfigListEntry(_("Wake On Lan Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		##
		self.cfglist.append(getConfigListEntry(_(" > Use Wake on Lan (WoL)"), self.current.wol, _(" ")))

		if self.current.wol.value:
			self.cfglist.append(getConfigListEntry(_(" >> Mac address (Size: 12 alphanumeric no seperator) only for WoL"), self.current.wol_mac, _(" ")))
			self.cfglist.append(getConfigListEntry(_(" >> Wait for server delay (max 180 seconds) only for WoL"), self.current.wol_delay, _(" ")))
		
		#===================================================================
		# 
		# getConfigListEntry(_("Transcode Type (no function yet but soon ;-)"), self.current.transcodeType),
		# getConfigListEntry(_("Quality (no function yet but soon ;-)"), self.current.quality),
		# getConfigListEntry(_("Audio Output (no function yet but soon ;-)"), self.current.audioOutput),
		# getConfigListEntry(_("Stream Mode (no function yet but soon ;-)"), self.current.streamMode),
		#===================================================================

		self["config"].list = self.cfglist
		self["config"].l.setList(self.cfglist)
		
		self.setKeyNames()
			
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def addIpSettings(self):
		printl("", self, "S")

		self.cfglist.append(getConfigListEntry(_(" >> IP"), self.current.ip, _(" ")))
		self.cfglist.append(getConfigListEntry(_(" >> Port"), self.current.port, _(" ")))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def addMyPlexSettings(self):
		printl("", self, "S")

		#self.cfglist.append(getConfigListEntry(_(" >> myPLEX URL"), self.current.myplexUrl, _("You need curl installed for this feature! Please check in System ...")))
		self.cfglist.append(getConfigListEntry(_(" >> myPLEX Username"), self.current.myplexUsername, _("You need curl installed for this feature! Please check in System ...")))
		self.cfglist.append(getConfigListEntry(_(" >> myPLEX Password"), self.current.myplexPassword, _("You need curl installed for this feature! Please check in System ...")))
		self.cfglist.append(getConfigListEntry(_(" >> myPLEX renew myPlex token"), self.current.renewMyplexToken, _("You need curl installed for this feature! Please check in System ...")))

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def updateHelp(self):
		printl("", self, "S")
		
		cur = self["config"].getCurrent()
		printl("cur: " + str(cur), self, "D")
		self["help"].text = cur and cur[2] or ""
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def setKeyNames(self):
		printl("", self, "S")
		
		if self.useMappings:
			self["key_yellow"].setText(_("Mappings"))
		else:
			self["key_yellow"].setText(_("check myPlex Token"))
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyLeft(self):
		printl("", self, "S")
		
		ConfigListScreen.keyLeft(self)
		self.createSetup()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyRight(self):
		printl("", self, "S")
		
		ConfigListScreen.keyRight(self)
		self.createSetup()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def keySave(self, stayOpen = False):
		printl("", self, "S")
		
		if self.newmode == 1:
			config.plugins.dreamplex.entriescount.value += 1
			config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()

		if not stayOpen:
			self.close()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyCancel(self):
		printl("", self, "S")
		
		if self.newmode == 1:
			config.plugins.dreamplex.Entries.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyYellow(self):
		printl("", self, "S")
		
		
		if self.useMappings:
			serverID = self.currentId
			self.session.open(DPS_Mappings, serverID)
		else:
			self.session.open(MessageBox,(_("myPlex Token:") + "\n%s \n" + _("for the user:") + "\n%s") % (self.current.myplexToken.value, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyDelete(self):
		printl("", self, "S")
		
		if self.newmode == 1:
			self.keyCancel()
		else:		
			self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Server Entry?"))
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def deleteConfirm(self, result):
		printl("", self, "S")
		
		if not result:
			return

		config.plugins.dreamplex.entriescount.value -= 1
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.remove(self.current)
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()
		self.close()
		
		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPS_ServerEntryList(MenuList):
	
	def __init__(self, menuList, enableWrapAround = True):
		printl("", self, "S")
		
		MenuList.__init__(self, menuList, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def postWidgetCreate(self, instance):
		printl("", self, "S")
		
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def buildList(self):
		printl("", self, "S")
		
		self.list=[]

		
		for entry in config.plugins.dreamplex.Entries:
			res = [entry]
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(entry.name.value)))
			
			if entry.connectionType.value == "2":
				text1 = entry.myplexUrl.value
				text2 = entry.myplexUsername.value
			else:
				text1 = "%d.%d.%d.%d" % tuple(entry.ip.value)
				text2 = "%d"% entry.port.value
				
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(text1)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 450, 0, 80, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(text2)))
			self.list.append(res)
		
		
		self.l.setList(self.list)
		self.moveToIndex(0)
				
		printl("", self, "C")

#===============================================================================
# fictive setting for translation of returned strings from PlexServer
#===============================================================================
def _StringsForTransalation():
	a = _("All")
	a = _("All Movies")
	a = _("All Filmy")
	a = _("All Shows")
	a = _("All episodes")
	a = _("By Genre")
	a = _("By Folder")
	a = _("By First Letter")
	a = _("By Resolution")
	a = _("By Rating")
	a = _("By Country")
	a = _("By Director")
	a = _("By Decade")
	a = _("By Year")
	a = _("By Collection")
	a = _("By Content Rating")
	a = _("By Starring Actor")
	a = _("Recently Aired")
	a = _("Recently Added")
	a = _("Recently Released")
	a = _("Recently Viewed")
	a = _("Recently Viewed Episodes")
	a = _("Recently Viewed Shows")
	a = _("Unwatched")
	a = _("On Deck")
	a = _("Search...")
	a = _("Search Shows...")
	a = _("Search Episodes...")
	a = _("Movies")
	a = _("Shows")
	a = _("Series")
