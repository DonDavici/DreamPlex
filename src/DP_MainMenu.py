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
import sys
import time
import copy

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

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, testPlexConnectivity, testInetConnectivity
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__init__ import getVersion

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary

from Plugins.Extensions.DreamPlex.DP_SystemCheck import DPS_SystemCheck

from Plugins.Extensions.DreamPlex.DP_Settings import DPS_Settings
from Plugins.Extensions.DreamPlex.DP_Settings import DPS_ServerEntriesListConfigScreen
from Plugins.Extensions.DreamPlex.DP_Settings import DPS_ServerEntryConfigScreen

from Plugins.Extensions.DreamPlex.DP_Help import DPS_Help
from Plugins.Extensions.DreamPlex.DP_About import DPS_About

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from Plugins.Extensions.DreamPlex.DPH_RemoteListener import HttpDeamon

#===============================================================================
# class
# DPS_MainMenu
#===============================================================================	
class DPS_MainMenu(Screen):
	"""
	"""
	
	g_wolon = False
	g_wakeserver = "00-11-32-12-C5-F9"
	g_woldelay = 10
	
	selectedEntry = None
	s_url = None
	s_mode = None
	s_final = False
	
	g_serverDataMenu = None
	g_filterDataMenu = None
	nextExitIsQuit = True
	currentService = None
	plexInstance = None
	selectionOverride = None
	secondRun = False
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session):
		printl("", self, "S")
		Screen.__init__(self, session)
		
		self["title"] = StaticText()
		self["welcomemessage"] = StaticText()
		
		# get all our servers as list
		self.getServerList()
		
		self["menu"]= List(self.mainMenuList, True)
		
		self.menu_main_list = self["menu"].list

		self["actions"] = HelpableActionMap(self, "DP_MainMenuActions", 
			{
				"ok":		(self.okbuttonClick, ""),
				"left":		(self.left, ""),
				"right":	(self.right, ""),
				"up":		(self.up, ""),
				"down":		(self.down, ""),
				"cancel":	(self.cancel, ""),
			}, -2)
		
		self.onFirstExecBegin.append(self.onExec)
		self.onFirstExecBegin.append(self.onExecRunDev)
		
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()
		
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onShown.append(self.checkSelectionOverride)
		printl("", self, "C")

#===============================================================================
# SCREEN FUNCTIONS
#===============================================================================
		
	#===============================================================================
	# 
	#===============================================================================
	def setCustomTitle(self):
		printl("", self, "S")
		
		self.setTitle(_("DreamPlex"))

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def checkSelectionOverride(self):
		printl("", self, "S")
		printl("self.selectionOverride: " + str(self.selectionOverride), self, "D")
		if self.selectionOverride is not None:
			self.okbuttonClick(self.selectionOverride)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showWakeMessage(self):
		printl("", self, "S")

		self.session.openWithCallback(self.executeWakeOnLan, MessageBox, _("Plexserver seems to be offline. Start with Wake on Lan settings? \n\nPlease note: \nIf you press yes the spinner will run for " + str(self.g_woldelay) + " seconds. \nAccording to your settings."), MessageBox.TYPE_YESNO)

		if not self.secondRun:
			self.selectionOverride = None
			self.secondRun = True # now that the screen is shown the onShown will not trigger our message so we use this param to force it
			self.onShown.remove(self.showOfflineMessage)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showOfflineMessage(self):
		printl("", self, "S")

		self.session.openWithCallback(self.setMainMenu,MessageBox,_("Plexserver seems to be offline. Please check your your settings or connection!"), MessageBox.TYPE_INFO)

		if not self.secondRun:
			self.selectionOverride = None
			self.secondRun = True # now that the screen is shown the onShown will not trigger our message so we use this param to force it
			self.onShown.remove(self.showOfflineMessage)

		printl("", self, "C")

	def setMainMenu(self):
		self["menu"].setList(self.menu_main_list)

#===============================================================================
# KEYSTROKES
#===============================================================================

	#===============================================================
	# 
	#===============================================================
	def okbuttonClick(self, selectionOverride = None):
		printl("", self, "S")
		
		# this is used to step in directly into a server when there is only one entry in the serverlist
		if selectionOverride is not None:
			selection = selectionOverride
		else:
			selection = self["menu"].getCurrent()
		
		printl("selection = " + str(selection), self, "D")
		self.nextExitIsQuit = False
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
					
					# now that we know the server we establish global plexInstance
					self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))
					
					self.checkServerState()

				elif self.selectedEntry == Plugin.MENU_MOVIES:
					printl("found Plugin.MENU_MOVIES", self, "D")
					self.getServerData("movies")
					
				elif self.selectedEntry == Plugin.MENU_TVSHOWS:
					printl("found Plugin.MENU_TVSHOWS", self, "D")
					self.getServerData("tvshow")
				
				elif self.selectedEntry == Plugin.MENU_MUSIC:
					printl("found Plugin.MENU_MUSIC", self, "D")
					self.getServerData("music")
					
				elif self.selectedEntry == Plugin.MENU_FILTER:
					printl("found Plugin.MENU_FILTER", self, "D")
					params = selection[2]
					printl("params: " + str(params), self, "D")
					
					self.s_url = params.get('t_url', "notSet")
					self.s_mode = params.get('t_mode', "notSet")
					self.s_final = params.get('t_final', "notSet")
					
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
				
				elif selection[1] == "DPS_About":
					self.session.open(DPS_About)
					#self.info()
				
				elif selection[1] == "DPS_Help":
					self.session.open(DPS_Help)
				
				elif selection[1] == "DPS_Exit":
					self.exit()
				
				elif selection[1] == "getMusicSections":
					self.getMusicSections(selection)
					
			else:
				printl("selected entry is executable", self, "D")
				params = selection[2]
				printl("params: " + str(params), self, "D")
				self.s_url = params.get('t_url', "notSet")
				self.showEpisodesDirectly = params.get('t_showEpisodesDirectly', "notSet")
				self.uuid = params.get('t_uuid', "notSet")
				self.source = params.get('t_source', "notSet")
				
				isSearchFilter = params.get('isSearchFilter', "notSet")
				
				if isSearchFilter == "True" or isSearchFilter:
						self.session.openWithCallback(self.addSearchString, InputBox, title=_("Please enter your search string!"), text="", maxSize=55, type=Input.TEXT)
				else:
					self.executeSelectedEntry()
					
			printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def getMusicSections(self, selection):
		printl("", self, "S")
		
		mainMenuList = []
		plugin = selection[2] #e.g. Plugin.MENU_MOVIES
		
		# ARTISTS
		params = copy.deepcopy(selection[3])
		url = params['t_url']
		params['t_url'] = url + "?type=8"
		mainMenuList.append((_("by Artists"), plugin, params))
		printl("mainMenuList 1: " + str(mainMenuList), self, "D")
		
		#ALBUMS
		params = copy.deepcopy(selection[3])
		params['t_url'] = url + "?type=9"
		mainMenuList.append((_("by Albums"), plugin, params))
		printl("mainMenuList 2: " + str(mainMenuList), self, "D")
		
		self["menu"].setList(mainMenuList)
		self.refreshMenu(0)
		
		printl("mainMenuList: " + str(mainMenuList), self, "D")
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def getSettingsMenuList(self):
		printl("", self, "S")
		
		self.nextExitIsQuit = False
		self["menu"].setList(self.getSettingsMenu())
		self.refreshMenu(0)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def addSearchString(self, searchString):
		printl("", self, "S")
		# sample: http://192.168.45.190:32400/search?type=1&query=fringe
		serverUrl = self.plexInstance.getServerFromURL(self.s_url)
		
		if searchString is not "" and searchString is not None:
			self.s_url = serverUrl + "/search?type=1&query=" + searchString

		self.executeSelectedEntry()
		
		printl("", self, "C")	
	
	#===========================================================================
	# 
	#===========================================================================
	def executeSelectedEntry(self):
		printl("", self, "S")
		printl("self.s_url: " + str(self.s_url), self, "D")
		
		if self.selectedEntry.start is not None:
			kwargs = {"url": self.s_url, "uuid": self.uuid, "source": self.source}
			
			if self.showEpisodesDirectly != "notSet":
				kwargs["showEpisodesDirectly"] = self.showEpisodesDirectly

			self.session.open(self.selectedEntry.start, **kwargs)
					
		elif self.selectedEntry.fnc is not None:
			self.selectedEntry.fnc(self.session)
		
		self.selectedEntry = Plugin.MENU_FILTER # we overwrite this now to handle correct menu jumps with exit/cancel button
		
		printl("", self, "C")
	
	#==========================================================================
	# 
	#==========================================================================
	def up(self):
		printl("", self, "S")
		
		self["menu"].selectPrevious()
		
		printl("", self, "C")	
	
	#===========================================================================
	# 
	#===========================================================================
	def down(self):
		printl("", self, "S")
		
		self["menu"].selectNext()
		
		printl("", self, "C")
	
	#===============================================================================
	# 
	#===============================================================================
	def right(self):
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
		printl("", self, "S")
		
		self.showInfo(not self.isInfoHidden)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def exit(self):
		printl("", self, "S")
		
		self.Exit()
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def cancel(self):
		printl("", self, "S")
		
		if self.selectedEntry == Plugin.MENU_FILTER:
			printl("coming from MENU_FILTER", self, "D")
			self["menu"].setList(self.g_serverDataMenu)
			self.selectedEntry = Plugin.MENU_SERVER
			self.nextExitIsQuit = False
			
		elif self.selectedEntry == Plugin.MENU_TVSHOWS or self.selectedEntry == Plugin.MENU_MOVIES:
			printl("coming from MENU_TVSHOWS or MENU_MOVIES", self, "D")
			self["menu"].setList(self.g_sectionDataMenu)
			self.selectedEntry = Plugin.MENU_SERVER
			self.nextExitIsQuit = False
		
		elif self.nextExitIsQuit:
			self.exit()
		
		else:
			printl("coming from ELSEWHERE", self, "D")
			printl("selectedEntry " +  str(self.selectedEntry), self, "D")
			self.getServerList()
			self["menu"].setList(self.menu_main_list)
			self.nextExitIsQuit = True

		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def Exit(self):
		printl("", self, "S")
		
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
				self.session.nav.playService(self.currentService)
		self.close((True,) )	#===============================================================================
	# 
	#===============================================================================
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def refreshMenu(self, value):
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
		printl("", self, "S")

		self.g_wolon = self.g_serverConfig.wol.value
		self.g_wakeserver = str(self.g_serverConfig.wol_mac.value)
		self.g_woldelay = int(self.g_serverConfig.wol_delay.value)
		connectionType = str(self.g_serverConfig.connectionType.value)
		if connectionType == "0":
			ip = "%d.%d.%d.%d" % tuple(self.g_serverConfig.ip.value)
			port =  int(self.g_serverConfig.port.value)
			isOnline = testPlexConnectivity(ip, port)
			
		elif connectionType == "2":
			#state = testInetConnectivity("http://my.plexapp.com")
			isOnline = True
		else:
			isOnline = testInetConnectivity()
		
		if isOnline:
			stateText = "Online"
		else:
			stateText = "Offline"
		
		printl("Plexserver State: " + str(stateText), self, "I")
		if not isOnline:
			if self.g_wolon == True and connectionType == "0":
				if self.secondRun:
					self.showWakeMessage()
				else:
					self.onShown.append(self.showWakeMessage)
			else:
				if self.secondRun:
					self.showOfflineMessage()
				else:
					self.onShown.append(self.showOfflineMessage)
		else:
			self.getServerData()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def executeWakeOnLan(self, confirm):
		printl("", self, "S")
		
		if confirm:
			# User said 'yes'		
			printl("Wake On LAN: " + str(self.g_wolon), self, "I")
			
			for i in range(1,12):
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
		printl("", self, "S")
			
		time.sleep(int(self.g_woldelay))
		self.getServerData()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def getServerData(self, filterBy=None):
		printl("", self, "S")
		
		summerize = config.plugins.dreamplex.summerizeSections.value
		
		if summerize == True and filterBy is None:
			serverData = self.getSectionTypes()
			self.g_sectionDataMenu = serverData
		else:
			serverData = self.plexInstance.displaySections(filterBy)
			self.g_serverDataMenu = serverData #lets save the menu to call it when cancel is pressed
		
		self["menu"].setList(serverData)
		self.refreshMenu(0)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def getFilterData(self):
		printl("", self, "S")
		menuData = self.plexInstance.getSectionFilter(self.s_url, self.s_mode, self.s_final)
		
		self["menu"].setList(menuData)
		self.g_filterDataMenu = menuData #lets save the menu to call it when cancel is pressed
		self.refreshMenu(0)

		printl("", self, "S")


	#===========================================================================
	# 
	#===========================================================================
	def getSectionTypes(self):
		printl("", self, "S")
		
		mainMenuList = []
		params = {} 
		mainMenuList.append((_("Movies"), Plugin.MENU_MOVIES, params))
		mainMenuList.append((_("Tv Shows"), Plugin.MENU_TVSHOWS, params))
		
		extend = False # SWITCH
		
		if extend:
			mainMenuList.append((_("Music"), Plugin.MENU_MUSIC, params))
			mainMenuList.append((_("Pictures"), Plugin.MENU_PICTURES, params))
			mainMenuList.append((_("Channels"), Plugin.MENU_CHANNELS, params))
		
		printl("mainMenuList: " + str(mainMenuList), self, "D")
		printl("", self, "C")
		return mainMenuList
#===============================================================================
# HELPER
#===============================================================================
		
	#===============================================================================
	# 
	#===============================================================================
	def Error(self, error):
		printl("", self, "S")
		
		self.session.open(MessageBox,_("UNEXPECTED ERROR:\n%s") % error, MessageBox.TYPE_INFO)
		
		printl("", self, "C")
		
	#=======================================================================
	# 
	#=======================================================================
	def getSettingsMenu (self):
		printl("", self, "S")
		
		mainMenuList = []

		mainMenuList.append((_("Settings"), "DPS_Settings"))
		mainMenuList.append((_("Server"), "DPS_ServerEntriesListConfigScreen"))
		mainMenuList.append((_("Systemcheck"), "DPS_SystemCheck"))
		mainMenuList.append((_("Help"), "DPS_Help"))

		self.nextExitIsQuit = False
		
		printl("", self, "C")
		return mainMenuList
	
	#===============================================================================
	# 
	#===============================================================================
	def getServerList(self):
			"""
			"""
			printl("", self, "S")
			
			self.mainMenuList = []
			
			# add servers to list 
			for serverConfig in config.plugins.dreamplex.Entries:
				
				# only add the server if state is active
				if serverConfig.state.value:
					serverName = serverConfig.name.value
				
					self.mainMenuList.append((serverName, Plugin.MENU_SERVER, serverConfig))
					
					# automatically enter the server if wanted
					if serverConfig.autostart.value:
						self.selectionOverride = [serverName, Plugin.MENU_SERVER, serverConfig]
		
			self.mainMenuList.append((_("System"), Plugin.MENU_SYSTEM))
			self.mainMenuList.append((_("About"), "DPS_About"))
			
			printl("", self, "C")
		
#===============================================================================
# ADDITIONAL STARTUPS
#===============================================================================
	
	#===============================================================================
	# 
	#===============================================================================
	def onExecRunDev(self):
		printl("", self, "S")
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def onExec(self):
		printl("", self, "S")
		
		# activate this to develop plex player via ios or android app
		# state server is starting
		# test over: 127.0.0.1:8000/version
		# registration on plex server is working - player is showing up in handy app
		# next step is to find out what should happen if a button is pressed. 
		# for now we do not see any incoming traffic from the app :-(
		#HttpDeamon().startDeamon()
		
		if config.plugins.dreamplex.checkForUpdateOnStartup.value:
			DPS_SystemCheck(self.session).checkForUpdate()

		printl("", self, "C")
