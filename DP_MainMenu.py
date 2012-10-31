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
#=================================
#IMPORT
#=================================
import sys
import time

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from os import system, popen

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Input import Input
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, testPlexConnectivity
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__init__ import initServerEntryConfig

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

#===============================================================================
# class
# DPS_MainMenu
#===============================================================================	
class DPS_MainMenu(Screen):
	
	g_wolon = False
	g_wakeserver = "00-11-32-12-C5-F9"
	g_woldelay = 10
	
	selectedEntry = None
	s_url = None
	
	g_serverDataMenu = None
	g_filterDataMenu = None
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session):
		'''
		'''
		printl("", self, "S")
		Screen.__init__(self, session)
		
		self["infoContainer"] = Label()
		self["infoText"] = Label()
		self["title"] = StaticText("")
		self["welcomemessage"] = StaticText("")
		self["key_blue"] = StaticText(_("Info"))
		self["key_red"] = StaticText(_("Exit"))
		
		self.setText("infoText", self.getInfoText())
		

		self.mainMenuList = []
		
		# add servers to list 
		for serverConfig in config.plugins.dreamplex.Entries:
			serverName = serverConfig.name.value
		
			self.mainMenuList.append((serverName, Plugin.MENU_SERVER, serverConfig, "50"))
	
		self.mainMenuList.append((_("System"), Plugin.MENU_SYSTEM, "50"))
		
		self["menu"]= List(self.mainMenuList, True)
		
		self.menu_main_list = self["menu"].list

		self["actions"] = HelpableActionMap(self, "DP_MainMenuActions", 
			{
				"ok":    (self.okbuttonClick, ""),
				"left":  (self.left, ""),
				"right": (self.right, ""),
				"up":    (self.up, ""),
				"down":  (self.down, ""),
				"blue": (self.blue, ""),
				"red":   (self.red, ""),
				"cancel":   (self.cancel, ""),
			}, -2)
		
		self.onFirstExecBegin.append(self.onExec)
		self.onFirstExecBegin.append(self.onExecRunDev)
		
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
	
		self.onLayoutFinish.append(self.setCustomTitle)
		printl("", self, "C")


#===============================================================================
# SCREEN FUNCTIONS
#===============================================================================
		
	#===============================================================================
	# 
	#===============================================================================
	def setCustomTitle(self):
		'''
		'''
		printl("", self, "S")
		
		self.setTitle(_("DreamPlex"))
		self.showInfo(False)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def showInfo(self, visible):
		'''
		'''
		printl("", self, "S")
		
		self.isInfoHidden = visible

		if visible:
			self["infoContainer"].show()
			self["infoText"].show()
		else:
			self["infoContainer"].hide()
			self["infoText"].hide()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getInfoText(self):
		'''
		'''
		printl("", self, "S")
		
		content = ""
		content += "Information\n\n"
		content += "Autors: \t DonDavici\n"
		content += "DreamPlex - a plex client for Enigma2" 
		content += "Your current version is " + config.plugins.dreamplex.version.value + " "
		
		printl("", self, "C")
		return content
	
	#===========================================================================
	# 
	#===========================================================================
	def setText(self, name, value, ignore=False, what=None):
		'''
		'''
		printl("", self, "S")
		
		try:
			if self[name]:
				if len(value) > 0:
					self[name].setText(value)
				elif ignore is False:
					if what is None:
						self[name].setText(_("Not available"))
					else:
						self[name].setText(what + ' ' + _("not available"))
				else:
					self[name].setText(" ")
		except Exception, ex:
			printl("Exception: " + str(ex), self, "E")
		
		printl("", self, "C")
	
	#=======================================================================
	# 
	#=======================================================================
	def getSettingsMenu (self):
		'''
		'''
		printl("", self, "S")
		
		mainMenuList = []

		mainMenuList.append((_("Settings"), "DPS_Settings", "menu_watch", "50"))
		mainMenuList.append((_("Server"), "DPS_ServerEntriesListConfigScreen", "menu_watch", "50"))
		mainMenuList.append((_("Systemcheck"), "DPS_SystemCheck", "menu_watch", "50"))
		
		printl("", self, "C")
		return mainMenuList

#===============================================================================
# KEYSTROKES
#===============================================================================

	#===============================================================
	# 
	#===============================================================
	def okbuttonClick(self):
		'''
		'''
		printl("", self, "S")

		selection = self["menu"].getCurrent()
		
		printl("selection = " + str(selection), self, "D")
		
		if selection is not None:
			self.selectedEntry = selection[1]
			printl("selected entry " + str(self.selectedEntry), self, "D")
			
			if type(self.selectedEntry) is list:
				printl("selected entry is list", self, "D")
				l = []
			
				for plugin in self.selectedEntry:
					l.append((plugin.desc, plugin, "", "50"))
					
				printl(str(l), self, "D")
				self["menu"].setList(l)
				self.refreshMenu(0)

			elif type(self.selectedEntry) is int:
				printl("selected entry is int", self, "D")
				
				if self.selectedEntry == Plugin.MENU_MAIN: #is 1 => __plugin__ line 77
					self["menu"].setList(self.menu_main_list)
			
				elif self.selectedEntry == Plugin.MENU_SERVER:
					self.g_serverConfig = selection[2]
					self.checkWakeOnLan()
				
				elif self.selectedEntry == Plugin.MENU_FILTER:
					self.s_url = selection[3]
					self.getFilterData()
			
				elif self.selectedEntry == Plugin.MENU_SYSTEM:
					self["menu"].setList(self.getSettingsMenu())
					self.refreshMenu(0)

				
			elif type(self.selectedEntry) is str:
				printl("selected entry is string", self, "D")
				
				if selection[1] == "InfoBar":
					self.Exit()
					
				elif selection[1] == "DPS_Settings":
					self.session.open(DPS_Settings)
					
				elif selection[1] == "DPS_ServerEntriesListConfigScreen":
					self.session.open(DPS_ServerEntriesListConfigScreen)
					
				elif selection[1] == "DPS_SystemCheck":
					self.session.open(DPS_SystemCheck)
				
			elif selection[1] == "Exit":
				printl("selected entry is exit", self, "D")
				self.Exit()
			
			else:
				printl("selected entry is executable", self, "D")
				self.s_url = selection[3]
				if selection[4] == True:
					self.session.openWithCallback(self.addSearchString, InputBox, title=_("Please enter your search string!"), text="", maxSize=55, type=Input.TEXT)
				else:
					self.executeSelectedEntry()
					
			printl("", self, "C")
					
	#===========================================================================
	# 
	#===========================================================================
	def addSearchString(self, searchString):
		'''
		'''
		printl("", self, "S")
		
		if searchString is not "" and not None:
			self.s_url = self.s_url + "&query" + searchString

		self.executeSelectedEntry()
		
		printl("", self, "C")	
	
	#===========================================================================
	# 
	#===========================================================================
	def executeSelectedEntry(self):
		'''
		'''
		printl("", self, "S")
		
		if self.selectedEntry.start is not None:
			kwargs = {"url": self.s_url}
			self.session.open(self.selectedEntry.start, **kwargs)
					
		elif self.selectedEntry.fnc is not None:
			self.selectedEntry.fnc(self.session)
		
		self.selectedEntry = Plugin.MENU_FILTER # we overwrite this now to handle correct menu jumps with exit/cancel button
		
		printl("", self, "C")
	
	#==========================================================================
	# 
	#==========================================================================
	def up(self):
		'''
		'''
		printl("", self, "S")
		
		self["menu"].selectPrevious()
		
		printl("", self, "C")	
		return
	
	#===========================================================================
	# 
	#===========================================================================
	def down(self):
		'''
		'''
		printl("", self, "S")
		
		self["menu"].selectNext()
		
		printl("", self, "C")
		return
	
	#===============================================================================
	# 
	#===============================================================================
	def right(self):
		'''
		'''
		printl("", self, "S")
				
		try:
			self["menu"].pageDown()
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")
			self["menu"].selectNext()
		
		printl("", self, "C")
		return

	#===========================================================================
	# 
	#===========================================================================
	def left(self):
		'''
		'''
		printl("", self, "S")
		
		try:
			self["menu"].pageUp()
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")
			self["menu"].selectPrevious()
		
		printl("", self, "C")
		return
	
	#===========================================================================
	# 
	#===========================================================================
	def blue(self):
		'''
		'''
		printl("", self, "S")
		
		self.showInfo(not self.isInfoHidden)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def red(self):
		'''
		'''
		printl("", self, "S")
		
		self.Exit()
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def cancel(self):
		'''
		'''
		printl("", self, "S")
		
		if self.selectedEntry == Plugin.MENU_FILTER:
			printl("coming from MENU_FILTER", self, "D")
			self["menu"].setList(self.g_serverDataMenu)
			self.selectedEntry = Plugin.MENU_SERVER
		
		else:
			printl("coming from ELSEWHERE", self, "D")
			printl("selectedEntry " +  str(self.selectedEntry), self, "D")
			self["menu"].setList(self.menu_main_list)

		printl("", self, "C")
		return
	
	#===========================================================================
	# 
	#===========================================================================
	def Exit(self):
		'''
		'''
		printl("", self, "S")
		
		self.session.nav.playService(self.currentService)
		self.close((True,) )
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def refreshMenu(self, value):
		'''
		'''
		printl("", self, "S")
		
		if value == 1:
			self["menu"].selectNext()
		elif value == -1:
			self["menu"].selectPrevious()	

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def checkWakeOnLan(self):
		'''
		'''
		printl("", self, "S")

		self.g_wolon = self.g_serverConfig.wol.value
		self.g_wakeserver = str(self.g_serverConfig.wol_mac.value)
		self.g_woldelay = int(self.g_serverConfig.wol_delay.value)

		if self.g_wolon == True:
			ip = "%d.%d.%d.%d" % tuple(self.g_serverConfig.ip.value)
			port =  int(self.g_serverConfig.port.value)
			state = testPlexConnectivity(ip, port)

			if state == False:

				self.session.openWithCallback(self.executeWakeOnLan, MessageBox, _("Plexserver seems to be offline. Start with Wake on Lan settings? \n\nPlease note: \nIf you press yes the spinner will run for " + str(self.g_woldelay) + " seconds. \nAccording to your settings."), MessageBox.TYPE_YESNO)
			else:

				self.getServerData()
		else:
			self.getServerData()
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def executeWakeOnLan(self, confirm):
		'''
		'''
		printl("", self, "S")
		
		if confirm:
			# User said 'yes'		
			printl("Wake On LAN: " + str(self.g_wolon), self, "I")
			
			for i in range(1,12):
				#===================================================================
				# self.g_wakeserver = __settings__.getSetting('wol'+str(i))
				#===================================================================
				if not self.g_wakeserver == "":
					try:
						printl("Waking server " + str(i) + " with MAC: " + self.g_wakeserver, self, "I")
						wake_on_lan(self.g_wakeserver)
					except ValueError:
						printl("Incorrect MAC address format for server " + str(i), self, "W")
					except:
						printl("Unknown wake on lan error", self, "E")
			self.sleepNow()
		else:
			# User said 'no'
			self.getServerData() 
	
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def sleepNow (self):
		'''
		'''
		printl("", self, "S")
			
		time.sleep(int(self.g_woldelay))
		self.getServerData()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def getServerData(self):
		'''
		'''
		printl("", self, "S")
		
		instance = Singleton()
		instance.getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))
		
		plexInstance = instance.getPlexInstance()
		serverData = plexInstance.getAllSections()
		
		self["menu"].setList(serverData)
		self.g_serverDataMenu = serverData #lets save the menu to call it when cancel is pressed
		self.refreshMenu(0)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def getFilterData(self):
		'''
		'''
		printl("", self, "S")
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		
		printl("self.s_url = " + self.s_url, self, "D")
		menuData = plexInstance.getSectionFilter(self.s_url)
		
		self["menu"].setList(menuData)
		self.g_filterDataMenu = menuData #lets save the menu to call it when cancel is pressed
		self.refreshMenu(0)

		printl("", self, "S")

#===============================================================================
# HELPER
#===============================================================================
		
	#===============================================================================
	# 
	#===============================================================================
	def Error(self, error):
		'''
		'''
		printl("", self, "S")
		
		self.session.open(MessageBox,_("UNEXPECTED ERROR:\n%s") % (error), MessageBox.TYPE_INFO)
		
		printl("", self, "C")
	
		
#===============================================================================
# ADDITIONAL STARTUPS
#===============================================================================
	
	#===============================================================================
	# 
	#===============================================================================
	def onExecRunDev(self):
		'''
		'''
		printl("", self, "S")
		
		printl("", self, "C")		
	
	#===========================================================================
	# 
	#===========================================================================
	def onExec(self):
		'''
		'''
		printl("", self, "S")

		printl(self["menu"], self, "D")
		i = 0
		for entry in self["menu"].list:
			if entry[2] == "menu_tv":
				self["menu"].setIndex(i)
				break
			i += 1
	
		printl("", self, "C")

#===============================================================================
# class
# Settings
#===============================================================================
class DPS_SystemCheck(Screen):
	oeVersion = None
	
	def __init__(self, session):
		'''
		'''
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.session = session
		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		"ok": self.checkLib,
		"cancel": self.cancel,
		"red": self.cancel,
		}, -1)
		
		vlist = []
		
		self.oeVersion = self.getBoxArch()
		
		if self.oeVersion == "mipsel":
			vlist.append((_("found mipsel (OE 1.6) => Check for 'gst-plugin-fragmented"), "oe16"))
		
		elif self.oeVersion == "mips32el":
			vlist.append((_("found mips32el (OE 2.0) => Check for 'gst-plugins-bad-fragmented"), "oe20"))
		
		else:
			printl("unknown oe version", self, "W")
			vlist.append((_("Check for 'gst-plugin-fragmented if you are using OE16."), "oe16"))
			vlist.append((_("Check for 'gst-plugins-bad-fragmented if you are using OE20."), "oe20"))
		
		self["content"] = MenuList(vlist)
		
		self["key_red"] = StaticText(_("Exit"))
		
		printl("", self, "C")
		
	#===============================================================================
	# 
	#===============================================================================	
	def checkLib(self):
		'''
		'''
		printl("", self, "S")
		
		if self.oeVersion == "mipsel":
			command = "opkg status gst-plugin-fragmented"
		
		elif self.oeVersion == "mips32el":
			command = "opkg status gst-plugins-bad-fragmented"
		
		else:
			pass
		
		pipe = popen(command, "r")
		
		if pipe:
			data = pipe.read(8192)
			pipe.close()
			if data is not None and data != "":
				# gst-plugins-bad is installed
				self.session.open(MessageBox, _("Information:\n") + data, MessageBox.TYPE_INFO)
			else:
				# gst-plugins-bad is not install
				self.session.openWithCallback(self.installStreamingLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)
		
		printl("", self, "C")
		
	#===============================================================================
	# 
	#===============================================================================
	def installStreamingLibs(self, confirm):
		'''
		'''
		printl("", self, "S")
		
		if confirm:
			# User said 'Yes'
			
			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install gst-plugin-fragmented"
		
			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install gst-plugins-bad-fragmented"
		
			else:
				pass
			if not system(command):
				# Successfully installed
				#defaultServer = plexServerConfig.getDefaultServer()
				#self.openSectionlist(defaultServer)
				pass
			else:
				# Fail, try again and report the output...
				pipe = popen(command, "r")
				if pipe is not None:
					data = pipe.read(8192)
					if data is None:
						data = "Unknown Error"
					pipe.close()
					self.session.open(MessageBox, _("Could not install "+ command + ":\n") + data, MessageBox.TYPE_ERROR)
				# Failed to install
				self.cancel()
		else:
			# User said 'no' 
			self.cancel()
		
		printl("", self, "C")

	#===================================================================
	# 
	#===================================================================
	def cancel(self):
		'''
		'''
		printl("", self, "S")

		self.close(False,self.session)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def getBoxArch(self):
		'''
		'''
		printl("", self, "S")
		
		ARCH = "unknown"
		
		if (sys.version_info < (2, 6, 8) and sys.version_info > (2, 6, 6)):
			ARCH = "mipsel"
				
		if (sys.version_info < (2, 7, 4) and sys.version_info > (2, 7, 0)):
			ARCH = "mips32el"
				
		printl("", self, "C")
		return ARCH

#===============================================================================
# class
# Settings
#===============================================================================		
class DPS_Settings(Screen, ConfigListScreen):
	_hasChanged = False
	_session = None
	
	def __init__(self, session):
		'''
		'''
		printl("", self, "S")
		
		Screen.__init__(self, session)
		
		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Debug Mode"), config.plugins.dreamplex.debugMode, _("fill me")),
				getConfigListEntry(_("Plugin Folder Path"), config.plugins.dreamplex.pluginfolderpath, _("fill me")),
				getConfigListEntry(_("Skin Folder Path"), config.plugins.dreamplex.skinfolderpath, _("fill me")),
				getConfigListEntry(_("Temp Folder Path"), config.plugins.dreamplex.tmpfolderpath, _("fill me")),
				getConfigListEntry(_("Config Folder Path"), config.plugins.dreamplex.configfolderpath, _("fill me")),
				getConfigListEntry(_("Media Folder Path"), config.plugins.dreamplex.mediafolderpath, _("fill me")),
			],
			session = self.session,
			on_change = self._changed
		)
		
		self._session = session
		self._hasChanged = False

			
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.ok,
		}, -2)
		self.onLayoutFinish.append(self.setCustomTitle)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def setCustomTitle(self):
		'''
		'''
		printl("", self, "S")
		
		self.setTitle(_("Settings"))

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def _changed(self):
		'''
		'''
		printl("", self, "S")
		
		self._hasChanged = True

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		'''
		'''
		printl("", self, "S")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keySave(self):
		'''
		'''
		printl("", self, "S")

		self.saveAll()
		self.close(None)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def restartGUI(self, answer):
		'''
		'''
		printl("", self, "S")
		if answer is True:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()
		
		printl("", self, "C")

#===============================================================================
# class
# DPS_ServerEntriesListConfigScreen
#===============================================================================
class DPS_ServerEntriesListConfigScreen(Screen):

	def __init__(self, session, what = None):
		'''
		'''
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.session = session
		
		self["state"] = StaticText(_("State"))
		self["name"] = StaticText(_("Name"))
		self["ip"] = StaticText(_("IP"))
		self["port"] = StaticText(_("Port"))
		
		self["key_red"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Delete"))
		self["entrylist"] = DPH_ServerEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self.what = what
		self.updateList()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def updateList(self):
		'''
		'''
		printl("", self, "S")
		
		self["entrylist"].buildList()

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyClose(self):
		'''
		'''
		printl("", self, "S")
		
		self.close(self.session, self.what, None)

		printl("", self, "C")
	
	#=======================================================================
	# 
	#=======================================================================
	def keyRed(self):
		'''
		'''
		printl("", self, "S")
		
		self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, None)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyOK(self):
		'''
		'''
		printl("", self, "S")
		
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except Exception, ex:
			printl("Exception: " + ex, self, "W")
			sel = None
		
		self.close(self.session, self.what, sel)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyYellow(self):
		'''
		'''
		printl("", self, "S")
		
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		
		except Exception, ex:
			printl("Exception: " + ex, self, "W")
			sel = None
		
		if sel is None:
			return
		
		self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, sel)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyDelete(self):
		'''
		'''
		printl("", self, "S")
		
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		
		except Exception, ex:
			printl("Exception: " + ex, self, "W")
			sel = None
		
		if sel is None:
			return
		
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Server Entry?"))
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def deleteConfirm(self, result):
		'''
		'''
		printl("", self, "S")
		
		if not result:
			return
		
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.dreamplex.entriescount.value = config.plugins.dreamplex.entriescount.value - 1
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.remove(sel)
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()
		self.updateList()
		
		printl("", self, "C")

#===============================================================================
# class
# DPS_ServerEntryConfigScreen
#===============================================================================
class DPS_ServerEntryConfigScreen(ConfigListScreen, Screen):

	def __init__(self, session, entry):
		printl("", self, "S")
		
		self.session = session
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Delete"))

		if entry is None:
			self.newmode = 1
			self.current = initServerEntryConfig()
		else:
			self.newmode = 0
			self.current = entry

		cfglist = [
			getConfigListEntry(_("State"), self.current.state),
			getConfigListEntry(_("Name"), self.current.name),
			getConfigListEntry(_("IP"), self.current.ip),
			getConfigListEntry(_("Use Wake on Lan (WoL)"), self.current.wol),
			getConfigListEntry(_("Mac address (Size: 12 alphanumeric no seperator) only for WoL"), self.current.wol_mac),
			getConfigListEntry(_("Wait for server delay (max 180 seconds)"), self.current.wol_delay),
			getConfigListEntry(_("Port"), self.current.port),
			getConfigListEntry(_("Plexserver ip differs due to VPN connect"), self.current.showForeign),

		]

			#===================================================================
			# getConfigListEntry(_("Transcode (no function yet but soon ;-)"), self.current.transcode),
			# getConfigListEntry(_("Transcode Type (no function yet but soon ;-)"), self.current.transcodeType),
			# getConfigListEntry(_("Quality (no function yet but soon ;-)"), self.current.quality),
			# getConfigListEntry(_("Audio Output (no function yet but soon ;-)"), self.current.audioOutput),
			# getConfigListEntry(_("Stream Mode (no function yet but soon ;-)"), self.current.streamMode),
			#===================================================================

		ConfigListScreen.__init__(self, cfglist, session)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keySave(self):
		'''
		'''
		printl("", self, "S")
		
		if self.newmode == 1:
			config.plugins.dreamplex.entriescount.value = config.plugins.dreamplex.entriescount.value + 1
			config.plugins.dreamplex.entriescount.save()
		ConfigListScreen.keySave(self)
		config.plugins.dreamplex.save()
		configfile.save()
		self.close()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyCancel(self):
		'''
		'''
		printl("", self, "S")
		
		if self.newmode == 1:
			config.plugins.dreamplex.Entries.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyDelete(self):
		'''
		'''
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
		'''
		'''
		printl("", self, "S")
		
		if not result:
			return
		
		config.plugins.dreamplex.entriescount.value = config.plugins.dreamplex.entriescount.value - 1
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.remove(self.current)
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()
		self.close()
		
		printl("", self, "C")

#===============================================================================
# class
# DPH_ServerEntryList
#===============================================================================
class DPH_ServerEntryList(MenuList):
	
	def __init__(self, menuList, enableWrapAround = True):
		'''
		'''
		printl("", self, "S")
		
		MenuList.__init__(self, menuList, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def postWidgetCreate(self, instance):
		'''
		'''
		printl("", self, "S")
		
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def buildList(self):
		'''
		'''
		printl("", self, "S")
		
		self.list=[]

		
		for c in config.plugins.dreamplex.Entries:
			res = [c]
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.state.value)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.name.value)))
			ip = "%d.%d.%d.%d" % tuple(c.ip.value)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 130, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(ip)))
			port = "%d"%(c.port.value)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 400, 0, 80, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(port)))
			self.list.append(res)
		
		
		self.l.setList(self.list)
		self.moveToIndex(0)
				
		printl("", self, "C")
