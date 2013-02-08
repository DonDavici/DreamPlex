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

from Plugins.Extensions.DreamPlex.DP_SystemCheck import DPS_SystemCheck

from Plugins.Extensions.DreamPlex.DP_Settings import DPS_Settings
from Plugins.Extensions.DreamPlex.DP_Settings import DPS_ServerEntriesListConfigScreen
from Plugins.Extensions.DreamPlex.DP_Settings import DPS_ServerEntryConfigScreen

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

#===============================================================================
# class
# DPS_MainMenu
#===============================================================================	
class DPS_MainMenu(Screen):
	'''
	'''
	
	g_wolon = False
	g_wakeserver = "00-11-32-12-C5-F9"
	g_woldelay = 10
	
	selectedEntry = None
	s_url = None
	s_mode = None
	s_final = False
	
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
		
			self.mainMenuList.append((serverName, Plugin.MENU_SERVER, serverConfig))
	
		self.mainMenuList.append((_("System"), Plugin.MENU_SYSTEM))
		self.mainMenuList.append((_("Exit"), "DPS_Exit"))
		
		self["menu"]= List(self.mainMenuList, True)
		
		self.menu_main_list = self["menu"].list

		self["actions"] = HelpableActionMap(self, "DP_MainMenuActions", 
			{
				"ok":    (self.okbuttonClick, ""),
				"left":  (self.left, ""),
				"right": (self.right, ""),
				"up":    (self.up, ""),
				"down":  (self.down, ""),
				"cancel":   (self.cancel, ""),
				"info":   (self.info, ""),
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

		mainMenuList.append((_("Settings"), "DPS_Settings"))
		mainMenuList.append((_("Server"), "DPS_ServerEntriesListConfigScreen"))
		mainMenuList.append((_("Systemcheck"), "DPS_SystemCheck"))
		
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
			
			if type(self.selectedEntry) is int:
				printl("selected entry is int", self, "D")
				
				if self.selectedEntry == Plugin.MENU_MAIN:
					printl("found Plugin.MENU_MAIN", self, "D")
					self["menu"].setList(self.menu_main_list)
			
				elif self.selectedEntry == Plugin.MENU_SERVER:
					printl("found Plugin.MENU_SERVER", self, "D")
					self.g_serverConfig = selection[2]
					self.checkServerState()
				
				elif self.selectedEntry == Plugin.MENU_FILTER:
					printl("found Plugin.MENU_FILTER", self, "D")
					params = selection[2]
					printl("params: " + str(params), self, "D")
					
					t_url = params.get('t_url', "notSet")
					t_mode = params.get('t_mode', "notSet")
					t_final = params.get('t_final', "notSet")
					t_accessToken = params.get('t_accessToken', "notSet")

					self.s_url = t_url
					self.s_mode = t_mode
					self.s_final = t_final
					self.s_accessToken = t_accessToken
					
					self.getFilterData()
			
				elif self.selectedEntry == Plugin.MENU_SYSTEM:
					printl("found Plugin.MENU_SYSTEM", self, "D")
					self["menu"].setList(self.getSettingsMenu())
					self.refreshMenu(0)

				
			elif type(self.selectedEntry) is str:
				printl("selected entry is string", self, "D")
					
				if selection[1] == "DPS_Settings":
					self.session.open(DPS_Settings)
					
				elif selection[1] == "DPS_ServerEntriesListConfigScreen":
					self.session.open(DPS_ServerEntriesListConfigScreen)
					
				elif selection[1] == "DPS_SystemCheck":
					self.session.open(DPS_SystemCheck)
					
				elif selection[1] == "DPS_Exit":
					self.exit()
					
			else:
				printl("selected entry is executable", self, "D")
				params = selection[2]
				t_url = params.get('t_url', "notSet")
				self.s_url = t_url
				isSearchFilter = params.get('isSearchFilter', "notSet")
				
				if isSearchFilter == "True" or isSearchFilter == True:
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
		# sample: http://192.168.45.190:32400/search?type=1&query=fringe
		instance = Singleton()
		instance.getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))
		
		plexInstance = instance.getPlexInstance()
		serverUrl = plexInstance.getServerFromURL(self.s_url)
		
		if searchString is not "" and searchString is not None:
			self.s_url = serverUrl + "/search?type=1&query=" + searchString

		self.executeSelectedEntry()
		
		printl("", self, "C")	
	
	#===========================================================================
	# 
	#===========================================================================
	def executeSelectedEntry(self):
		'''
		'''
		printl("", self, "S")
		printl("self.s_url: " + str(self.s_url), self, "D")
		
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
	
	#===========================================================================
	# 
	#===========================================================================
	def down(self):
		'''
		'''
		printl("", self, "S")
		
		self["menu"].selectNext()
		
		printl("", self, "C")
	
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
	
	#===========================================================================
	# 
	#===========================================================================
	def info(self):
		'''
		'''
		printl("", self, "S")
		
		self.showInfo(not self.isInfoHidden)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def exit(self):
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
	def checkServerState(self):
		'''
		'''
		printl("", self, "S")

		self.g_wolon = self.g_serverConfig.wol.value
		self.g_wakeserver = str(self.g_serverConfig.wol_mac.value)
		self.g_woldelay = int(self.g_serverConfig.wol_delay.value)

		ip = "%d.%d.%d.%d" % tuple(self.g_serverConfig.ip.value)
		port =  int(self.g_serverConfig.port.value)
		state = testPlexConnectivity(ip, port)
		printl("state: " + str(state), self, "D")
		
		if state == False:
			if self.g_wolon == True:
				self.session.openWithCallback(self.executeWakeOnLan, MessageBox, _("Plexserver seems to be offline. Start with Wake on Lan settings? \n\nPlease note: \nIf you press yes the spinner will run for " + str(self.g_woldelay) + " seconds. \nAccording to your settings."), MessageBox.TYPE_YESNO)
			else:
				self.session.open(MessageBox,_("Plexserver seems to be offline. Please check your your settings or connection!"), MessageBox.TYPE_INFO)
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
		#serverData = plexInstance.getAllSections()
		serverData = plexInstance.displaySections()
		
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

		menuData = plexInstance.getSectionFilter(self.s_url, self.s_mode, self.s_final, self.s_accessToken)

		
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
	
		printl("", self, "C")
