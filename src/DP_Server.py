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

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen

from __common__ import printl2 as printl, getBoxInformation
from __init__ import initServerEntryConfig, getVersion, _ # _ is translation

from DP_PlexLibrary import PlexLibrary
from DP_Mappings import DPS_Mappings
from DP_Syncer import DPS_Syncer
from DPH_PlexGdm import PlexGdm
from DPH_ScreenHelper import DPH_PlexScreen
from DP_ViewFactory import getGuiElements
from DPH_Singleton import Singleton
#===============================================================================
#
#===============================================================================
class DPS_Server(Screen, DPH_PlexScreen):

	def __init__(self, session, what = None):
		printl("", self, "S")

		Screen.__init__(self, session)
		DPH_PlexScreen.__init__(self)
		self.session = session
		from Components.Sources.List import List

		self.guiElements = getGuiElements()

		self["entryList"]= List(self.builEntryList(), True)
		self["header"] = Label()
		self["columnHeader"] = Label()

		self["btn_redText"] = Label()
		self["btn_red"] = Pixmap()

		self["btn_greenText"] = Label()
		self["btn_green"] = Pixmap()

		self["btn_yellowText"] = Label()
		self["btn_yellow"] = Pixmap()

		self["btn_blueText"] = Label()
		self["btn_blue"] = Pixmap()

		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOk,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "yellow":	self.keyYellow,
			 "green":	self.keyGreen,
			 "blue":	self.keyBlue,
			 }, -1)
		self.what = what

		self.onLayoutFinish.append(self.finishLayout)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		# first we set the pics for buttons
		self.setColorFunctionIcons()

		self["header"].setText(_("Server List:"))

		if self.skinResolution == "FHD": # FHD is used for FULL HD Boxes with new framebuffer
			self["columnHeader"].setText(_("Name                                         IP/myPlex                                             Port/Email                                        Active"))
		else:
			self["columnHeader"].setText(_("Name                                         IP/myPlex                                  Port/Email                                  Active"))

		self["btn_redText"].setText(_("Delete"))
		self["btn_greenText"].setText(_("Add"))
		self["btn_yellowText"].setText(_("Sync Media"))
		self["btn_blueText"].setText(_("Discover"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def builEntryList(self):
		printl("", self, "S")

		self.myEntryList = []

		for serverConfig in config.plugins.dreamplex.Entries:

			name = serverConfig.name.value

			if serverConfig.connectionType.value == "2":
				text1 = serverConfig.myplexUrl.value
				text2 = serverConfig.myplexUsername.value
			else:
				text1 = "%d.%d.%d.%d" % tuple(serverConfig.ip.value)
				text2 = "%d"% serverConfig.port.value

			active = str(serverConfig.state.value)

			self.myEntryList.append((name, text1, text2, active, serverConfig))

		printl("", self, "C")
		return self.myEntryList

	#===========================================================================
	#
	#===========================================================================
	def updateList(self):
		printl("", self, "S")

		self["entryList"].setList(self.builEntryList())

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

		self.session.openWithCallback(self.updateList, DPS_ServerConfig, None)

		printl("", self, "C")

	#=======================================================================
	#
	#=======================================================================
	def keyRed(self):
		printl("", self, "S")

		try:
			sel = self["entryList"].getCurrent()[4]

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
	def useSelectedServerData(self, choice):
		printl("", self, "S")

		if choice is not None:
			serverData = choice[1]
			self.session.openWithCallback(self.updateList, DPS_ServerConfig, None, serverData)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyOk(self):
		printl("", self, "S")

		try:
			sel = self["entryList"].getCurrent()[4]

		except Exception, ex:
			printl("Exception: " + str(ex), self, "W")
			sel = None

		if sel is None:
			return

		printl("config selction: " +  str(sel), self, "D")
		self.session.openWithCallback(self.updateList, DPS_ServerConfig, sel)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyYellow(self):
		printl("", self, "S")

		try:
			serverConfig = self["entryList"].getCurrent()[4]

		except Exception, ex:
			printl("Exception: " + str(ex), self, "W")
			serverConfig = None

		if serverConfig is None:
			return

		printl("config selction: " +  str(serverConfig), self, "D")
		self.session.open(DPS_Syncer, "sync", serverConfig)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBlue(self):
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
	def deleteConfirm(self, result):
		printl("", self, "S")

		if not result:
			return

		sel = self["entryList"].getCurrent()[4]
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
class DPS_ServerConfig(ConfigListScreen, Screen, DPH_PlexScreen):

	useMappings = False

	def __init__(self, session, entry, data = None):
		printl("", self, "S")

		self.session = session
		Screen.__init__(self, session)

		self.guiElements = getGuiElements()

		self["actions"] = ActionMap(["DPS_ServerConfig", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyCancel,
		    "exit": self.keyCancel,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"red": self.keyRed,
			"left": self.keyLeft,
			"right": self.keyRight,
		}, -2)

		self["help"] = StaticText()

		self["btn_redText"] = Label()
		self["btn_red"] = Pixmap()

		self["btn_greenText"] = Label()
		self["btn_green"] = Pixmap()

		self["btn_yellowText"] = Label()
		self["btn_yellow"] = Pixmap()

		self["btn_blueText"] = Label()
		self["btn_blue"] = Pixmap()

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

		self.onLayoutFinish.append(self.finishLayout)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		# first we set the pics for buttons
		self.setColorFunctionIcons()

		self.setKeyNames()

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

		if self.current.connectionType.value == "0" or self.current.connectionType.value == "1": # IP or DNS
			self.cfglist.append(getConfigListEntry(_(" > Local Authentication"), self.current.localAuth, _("For currentlyRunning feature just activate.\nFor section management you have to connect your server successfully to myPlex once.\nAfter that just disable your Portforwarding policy.")))
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

		##
		self.cfglist.append(getConfigListEntry(_("Sync Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		##
		self.cfglist.append(getConfigListEntry(_(" > Sync Movies Medias"), self.current.syncMovies, _(" ")))
		self.cfglist.append(getConfigListEntry(_(" > Sync Shows Medias"), self.current.syncShows, _(" ")))
		self.cfglist.append(getConfigListEntry(_(" > Sync Music Medias"), self.current.syncMusic, _(" ")))

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

		self.cfglist.append(getConfigListEntry(_(" >> myPLEX URL"), self.current.myplexUrl, _("You need openSSL installed for this feature! Please check in System ...")))
		self.cfglist.append(getConfigListEntry(_(" >> myPLEX Username"), self.current.myplexUsername, _("You need openSSL installed for this feature! Please check in System ...")))
		self.cfglist.append(getConfigListEntry(_(" >> myPLEX Password"), self.current.myplexPassword, _("You need openSSL installed for this feature! Please check in System ...")))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def updateHelp(self):
		printl("", self, "S")

		cur = self["config"].getCurrent()
		printl("cur: " + str(cur), self, "D")
		self["help"].setText(cur[2])# = cur and cur[2] or ""

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setKeyNames(self):
		printl("", self, "S")

		self["btn_greenText"].setText(_("Save"))

		if self.useMappings and self.newmode == 0:
			self["btn_yellowText"].setText(_("Mappings"))
			self["btn_yellowText"].show()
			self["btn_yellow"].show()
		elif self.current.localAuth.value:
			self["btn_yellowText"].setText(_("get local auth Token"))
			self["btn_yellowText"].show()
			self["btn_yellow"].show()
		else:
			self["btn_yellowText"].hide()
			self["btn_yellow"].hide()

		if (self.current.localAuth.value or self.current.connectionType.value == "2") and self.newmode == 0:
			self["btn_redText"].setText(_("check myPlex Token"))
			self["btn_blueText"].setText(_("(re)create myPlex Token"))
			self["btn_redText"].show()
			self["btn_red"].show()
			self["btn_blueText"].show()
			self["btn_blue"].show()
		else:
			self["btn_redText"].hide()
			self["btn_red"].hide()
			self["btn_blueText"].hide()
			self["btn_blue"].hide()

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

		#if self.current.machineIdentifier.value == "":
		from DP_PlexLibrary import PlexLibrary
		self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.current))

		if self.current.connectionType.value == "2":
			xmlResponse = self.plexInstance.getSharedServerForPlexUser()
			self.current.machineIdentifier.value = xmlResponse.get("machineIdentifier")

		else:
			xmlResponse = self.plexInstance.getXmlTreeFromUrl("http://" + self.plexInstance.g_currentServer)
			self.current.machineIdentifier.value = xmlResponse.get("machineIdentifier")

		printl("machineIdentifier: " + str(self.current.machineIdentifier.value), self, "D")

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

		elif self.current.localAuth.value:
			# now that we know the server we establish global plexInstance
			self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.current))

			ipInConfig = "%d.%d.%d.%d" % tuple(self.current.ip.value)
			token = self.plexInstance.getPlexUserTokenForLocalServerAuthentication(ipInConfig)

			if token:
				self.current.myplexLocalToken.value = token
				self.current.myplexLocalToken.save()
				self.session.open(MessageBox,(_("Local Token:") + "\n%s \n" + _("for the user:") + "\n%s") % (token, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)
			else:
				response = self.plexInstance.getLastResponse()
				self.session.open(MessageBox,(_("Error:") + "\n%s \n" + _("for the user:") + "\n%s") % (response, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBlue(self):
		printl("", self, "S")

		# now that we know the server we establish global plexInstance
		self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.current))

		token = self.plexInstance.getNewMyPlexToken()

		if token:
			self.session.open(MessageBox,(_("myPlex Token:") + "\n%s \n" + _("for the user:") + "\n%s") % (token, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)
		else:
			response = self.plexInstance.getLastResponse()
			self.session.open(MessageBox,(_("Error:") + "\n%s \n" + _("for the user:") + "\n%s") % (response, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyRed(self):
		printl("", self, "S")

		self.session.open(MessageBox,(_("myPlex Token:") + "\n%s \n" + _("myPlex Localtoken:") + "\n%s \n"+ _("for the user:") + "\n%s") % (self.current.myplexToken.value, self.current.myplexLocalToken.value, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)

		printl("", self, "C")

