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
import copy

from Components.ActionMap import HelpableActionMap
from Components.Input import Input
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.Label import Label

from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox

from __common__ import printl2 as printl, testPlexConnectivity, testInetConnectivity
from __plugin__ import Plugin
from __init__ import _ # _ is translation

from DP_PlexLibrary import PlexLibrary
from DP_SystemCheck import DPS_SystemCheck
from DP_Settings import DPS_Settings
from DP_Server import DPS_Server
from DP_About import DPS_About

from DPH_WOL import wake_on_lan
from DPH_Singleton import Singleton
from DPH_MovingLabel import DPH_MovingLabel

#===============================================================================
#
#===============================================================================	
class DPS_MainMenu(Screen):

	g_horizontal_menu = False
	g_wolon = False
	g_wakeserver = "00-11-32-12-C5-F9"
	g_woldelay = 10
	
	selectedEntry = None
	s_url = None
	s_mode = None
	s_final = False
	g_serverConfig = None
	
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
	def __init__(self, session, allowOverride=True):
		printl("", self, "S")
		Screen.__init__(self, session)
		self.selectionOverride = None
		printl("selectionOverride:" +str(self.selectionOverride), self, "D")
		self.session = session


		tree = Singleton().getSkinParamsInstance()

		for orientation in tree.findall('orientation'):
			name = str(orientation.get('name'))
			if name == "main_menu":
				myType = str(orientation.get('type'))
				if myType == "horizontal":
					self.g_horizontal_menu = True
		
		self["title"] = StaticText()
		self["welcomemessage"] = StaticText()
		
		# get all our servers as list
		self.getServerList(allowOverride)
		
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
			    "menu":		(self.onKeyMenu, ""),
			}, -2)
		
		self.onFirstExecBegin.append(self.onExec)
		self.onFirstExecBegin.append(self.onExecRunDev)
		
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()

		self["-2"] = DPH_MovingLabel()
		self["-1"] = DPH_MovingLabel(self["-2"].getTimer())
		self["0"]  = DPH_MovingLabel(self["-2"].getTimer())
		self["+1"] = DPH_MovingLabel(self["-2"].getTimer())
		self["+2"] = DPH_MovingLabel(self["-2"].getTimer())

		self["-3"] = Label()
		self["+3"] = Label()

		if self.g_horizontal_menu:
			self.translateNames()

		self.onLayoutFinish.append(self.setCustomTitle)
		self.onShown.append(self.checkSelectionOverride)
		printl("", self, "C")

#===============================================================================
# SCREEN FUNCTIONS
#===============================================================================

	def translateNames(self):
		self.translatePositionToName(-2, "-2")
		self.translatePositionToName(-1, "-1")
		self.translatePositionToName( 0, "0")
		self.translatePositionToName(+1, "+1")
		self.translatePositionToName(+2, "+2")

	#===============================================================================
	# 
	#===============================================================================
	def setCustomTitle(self):
		printl("", self, "S")
		
		self.setTitle(_("Main Menu"))

		if self.g_horizontal_menu:
			# init horizontal menu
			self.refreshOrientationHorMenu(0)

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

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showOfflineMessage(self):
		printl("", self, "S")

		self.session.openWithCallback(self.setMainMenu,MessageBox,_("Plexserver seems to be offline. Please check your your settings or connection!\n Retry?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setMainMenu(self, answer):
		printl("", self, "S")
		printl("answer: " + str(answer), self, "D")

		if answer:
			self.checkServerState()
		else:
			self.session.open(DPS_MainMenu,allowOverride=False)

		printl("", self, "C")
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
					self.g_serverConfig = selection[3]
					
					# now that we know the server we establish global plexInstance
					self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))
					
					self.checkServerState()
					if self.g_horizontal_menu:
						self.refreshOrientationHorMenu(0)

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
					params = selection[3]
					printl("params: " + str(params), self, "D")
					
					self.s_url = params.get('t_url', "notSet")
					self.s_mode = params.get('t_mode', "notSet")
					self.s_final = params.get('t_final', "notSet")
					self.s_source = params.get('t_source', "notSet")
					self.s_uuid = params.get('t_uuid', "notSet")

					self.getFilterData()

					if self.g_horizontal_menu:
						self.refreshOrientationHorMenu(0)
				
				elif self.selectedEntry == Plugin.MENU_SYSTEM:
					printl("found Plugin.MENU_SYSTEM", self, "D")
					self["menu"].setList(self.getSettingsMenu())
					self.setTitle(_("System"))
					self.refreshMenu(0)

					if self.g_horizontal_menu:
						self.refreshOrientationHorMenu(0)
				
			elif type(self.selectedEntry) is str:
				printl("selected entry is string", self, "D")

				if selection[1] == "DPS_Settings":
					self.session.open(DPS_Settings)
					
				elif selection[1] == "DPS_Server":
					self.session.open(DPS_Server)
					
				elif selection[1] == "DPS_SystemCheck":
					self.session.open(DPS_SystemCheck)
				
				elif selection[1] == "DPS_About":
					self.session.open(DPS_About)

				elif selection[1] == "DPS_Exit":
					self.exit()
				
				elif selection[1] == "getMusicSections":
					self.getMusicSections(selection)
					
			else:
				printl("selected entry is executable", self, "D")
				params = selection[3]
				printl("params: " + str(params), self, "D")
				self.s_url = params.get('t_url', "notSet")
				self.showEpisodesDirectly = params.get('t_showEpisodesDirectly', "notSet")
				self.uuid = params.get('t_uuid', "notSet")
				self.source = params.get('t_source', "notSet")
				self.viewGroup = params.get('t_viewGroup', "notSet")

				isSearchFilter = params.get('isSearchFilter', "notSet")
				printl("isSearchFilter: " + str(isSearchFilter), self, "D")
				if isSearchFilter == "True" or isSearchFilter and isSearchFilter != "notSet":
						printl("i am here: " + str(isSearchFilter), self, "D")
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
		mainMenuList.append((_("by Artists"), plugin, "artistsEntry", params))
		printl("mainMenuList 1: " + str(mainMenuList), self, "D")
		
		#ALBUMS
		params = copy.deepcopy(selection[3])
		params['t_url'] = url + "?type=9"
		mainMenuList.append((_("by Albums"), plugin, "albumsEntry", params))
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
	# this function starts DP_Lib...
	#===========================================================================
	def executeSelectedEntry(self):
		printl("", self, "S")
		printl("self.s_url: " + str(self.s_url), self, "D")

		if self.selectedEntry.start is not None:
			kwargs = {"url": self.s_url, "uuid": self.uuid, "source": self.source , "viewGroup": self.viewGroup}
			
			if self.showEpisodesDirectly != "notSet":
				kwargs["showEpisodesDirectly"] = self.showEpisodesDirectly

			self.session.open(self.selectedEntry.start, **kwargs)
					
		elif self.selectedEntry.fnc is not None:
			self.selectedEntry.fnc(self.session)

		if config.plugins.dreamplex.showFilter.value:
			self.selectedEntry = Plugin.MENU_FILTER # we overwrite this now to handle correct menu jumps with exit/cancel button
		
		printl("", self, "C")
	
	#==========================================================================
	# 
	#==========================================================================
	def up(self):
		printl("", self, "S")

		if self.g_horizontal_menu:
			self.left()
		else:
			self["menu"].selectPrevious()
		
		printl("", self, "C")	
	
	#===========================================================================
	# 
	#===========================================================================
	def down(self):
		printl("", self, "S")

		if self.g_horizontal_menu:
			self.right()
		else:
			self["menu"].selectNext()
		
		printl("", self, "C")
	
	#===============================================================================
	# 
	#===============================================================================
	def right(self):
		printl("", self, "S")
				
		try:
			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(+1)
			else:
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
			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(-1)
			else:
				self["menu"].pageUp()
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")
			self["menu"].selectPrevious()
		
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
	def onKeyMenu(self):
		printl("", self, "S")

		if self.g_serverConfig:
			functionList = []

			functionList.append((_("Sync medias from this server."), "sync"))
			functionList.append((_("Render fullsize backdrops to m1v."), "render"))

			self.session.openWithCallback(self.onKeyMenuCallback, ChoiceBox, title=_("Server Functions"), list=functionList)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyMenuCallback(self, choice):
		printl("", self, "S")
		printl("choice: " +str(choice), self, "D")

		if choice:
			from DP_Syncer import DPS_Syncer

			self.session.open(DPS_Syncer, self.g_serverConfig, choice[1])

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
			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(0)
			
		elif self.selectedEntry == Plugin.MENU_TVSHOWS or self.selectedEntry == Plugin.MENU_MOVIES:
			printl("coming from MENU_TVSHOWS or MENU_MOVIES", self, "D")
			self["menu"].setList(self.g_sectionDataMenu)
			self.selectedEntry = Plugin.MENU_SERVER
			self.nextExitIsQuit = False
			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(0)
		
		elif self.nextExitIsQuit:
			self.exit()
		
		else:
			printl("coming from ELSEWHERE", self, "D")
			self.setTitle(_("Main Menu"))
			printl("selectedEntry " +  str(self.selectedEntry), self, "D")
			self.getServerList()
			self["menu"].setList(self.menu_main_list)
			self.nextExitIsQuit = True

			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(0)

		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def Exit(self):
		printl("", self, "S")
		
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			printl("restoring liveTv", self, "D")
			self.session.nav.playService(self.currentService)

		self.close((True,) )
		
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
				self.showWakeMessage()

			else:
				self.showOfflineMessage()
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
			self.refreshMenu(0)
	
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
		menuData = self.plexInstance.getSectionFilter(self.s_url, self.s_mode, self.s_final, self.s_source, self.s_uuid )
		
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
		mainMenuList.append((_("Movies"), Plugin.MENU_MOVIES, "movieEntry", params))
		mainMenuList.append((_("Tv Shows"), Plugin.MENU_TVSHOWS, "showEntry" ,params))
		
		extend = False # SWITCH
		
		if extend:
			mainMenuList.append((_("Music"), Plugin.MENU_MUSIC, "musicEntry", params))
			mainMenuList.append((_("Pictures"), Plugin.MENU_PICTURES, "pictureEntry", params))
			mainMenuList.append((_("Channels"), Plugin.MENU_CHANNELS, "channelEntry", params))
		
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
		
		self.session.open(MessageBox,_("UNEXPECTED ERROR:") + "\n%s" % error, MessageBox.TYPE_INFO)
		
		printl("", self, "C")
		
	#=======================================================================
	# 
	#=======================================================================
	def getSettingsMenu (self):
		printl("", self, "S")
		
		mainMenuList = []

		mainMenuList.append((_("Settings"), "DPS_Settings", "settingsEntry"))
		mainMenuList.append((_("Server"), "DPS_Server", "settingsEntry"))
		mainMenuList.append((_("Systemcheck"), "DPS_SystemCheck", "settingsEntry"))

		self.nextExitIsQuit = False
		
		printl("", self, "C")
		return mainMenuList
	
	#===============================================================================
	# 
	#===============================================================================
	def getServerList(self, allowOverride=True):
			printl("", self, "S")
			
			self.mainMenuList = []
			
			# add servers to list 
			for serverConfig in config.plugins.dreamplex.Entries:
				
				# only add the server if state is active
				if serverConfig.state.value:
					serverName = serverConfig.name.value
				
					self.mainMenuList.append((serverName, Plugin.MENU_SERVER, "serverEntry", serverConfig))
					
					# automatically enter the server if wanted
					if serverConfig.autostart.value and allowOverride:
						printl("here", self, "D")
						self.selectionOverride = [serverName, Plugin.MENU_SERVER, "serverEntry", serverConfig]
		
			self.mainMenuList.append((_("System"), Plugin.MENU_SYSTEM, "systemEntry"))
			self.mainMenuList.append((_("About"), "DPS_About", "aboutEntry"))
			
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

	_translatePositionToName = {}
	def translatePositionToName(self, name, value=None):

		printl("->", self, "S")
		if value is None:
			return self._translatePositionToName[name]
		else:
			self._translatePositionToName[name] = value

	def refreshOrientationHorMenu(self, value):
		printl("->", self, "S")
		if self["-2"].moving is True or self["+2"].moving is True:
				printl("returning", self, "D")
				return False

		self.refreshMenu(value)
		currentIndex = self["menu"].index
		content = self["menu"].list
		count = len(content)

		print currentIndex
		print count

		howManySteps = 1
		doStepEveryXMs = 100

		if value == 0:
			printl("so soll es sein", self, "D")
			self[self.translatePositionToName(0)].setText(content[currentIndex][0])
			for i in range(1,3): # 1, 2
				targetIndex = currentIndex + i
				if targetIndex < count:
					self[self.translatePositionToName(+i)].setText(content[targetIndex][0])
				else:
					self[self.translatePositionToName(+i)].setText(content[targetIndex - count][0])

				targetIndex = currentIndex - i
				if targetIndex >= 0:
					self[self.translatePositionToName(-i)].setText(content[targetIndex][0])
				else:
					self[self.translatePositionToName(-i)].setText(content[count + targetIndex][0])


		elif value == 1:
			self[self.translatePositionToName(-1)].moveTo(self[self.translatePositionToName(-2)].getPosition(), howManySteps)
			self[self.translatePositionToName( 0)].moveTo(self[self.translatePositionToName(-1)].getPosition(), howManySteps)
			self[self.translatePositionToName(+1)].moveTo(self[self.translatePositionToName( 0)].getPosition(), howManySteps)
			self[self.translatePositionToName(+2)].moveTo(self[self.translatePositionToName(+1)].getPosition(), howManySteps)

			# He has to jump | This works but leaves us with an ugly jump
			pos = self["+3"].getPosition()
			self[self.translatePositionToName(-2)].move(pos[0], pos[1])
			#self[self.translatePositionToName(-2)].moveTo(pos, 1)
			self[self.translatePositionToName(-2)].moveTo(self[self.translatePositionToName(+2)].getPosition(), howManySteps)

			# We have to change the conten of the most right
			i = 2
			targetIndex = currentIndex + i
			if targetIndex < count:
				self[self.translatePositionToName(-2)].setText(content[targetIndex][0])
			else:
				self[self.translatePositionToName(-2)].setText(content[targetIndex - count][0])

			rM2 = self.translatePositionToName(-2)
			self.translatePositionToName(-2, self.translatePositionToName(-1))
			self.translatePositionToName(-1, self.translatePositionToName( 0))
			self.translatePositionToName( 0, self.translatePositionToName(+1))
			self.translatePositionToName(+1, self.translatePositionToName(+2))
			self.translatePositionToName(+2, rM2)

			self["-1"].startMoving(doStepEveryXMs)
			self["0"].startMoving(doStepEveryXMs)
			self["+1"].startMoving(doStepEveryXMs)
			self["+2"].startMoving(doStepEveryXMs)

			# GroupTimer
			self["-2"].startMoving(doStepEveryXMs)

		elif value == -1:
			self[self.translatePositionToName(+1)].moveTo(self[self.translatePositionToName(+2)].getPosition(), howManySteps)
			self[self.translatePositionToName( 0)].moveTo(self[self.translatePositionToName(+1)].getPosition(), howManySteps)
			self[self.translatePositionToName(-1)].moveTo(self[self.translatePositionToName( 0)].getPosition(), howManySteps)
			self[self.translatePositionToName(-2)].moveTo(self[self.translatePositionToName(-1)].getPosition(), howManySteps)

			# He has to jump | This works but leaves us with an ugly jump
			pos = self["-3"].getPosition()
			self[self.translatePositionToName(+2)].move(pos[0], pos[1])
			#self[self.translatePositionToName(+2)].moveTo(pos, 1)
			self[self.translatePositionToName(+2)].moveTo(self[self.translatePositionToName(-2)].getPosition(), howManySteps)

			# We have to change the conten of the most left
			i = -2
			targetIndex = currentIndex + i
			if targetIndex >= 0:
				self[self.translatePositionToName(+2)].setText(content[targetIndex][0])
			else:
				self[self.translatePositionToName(+2)].setText(content[count + targetIndex][0])

			rP2 = self.translatePositionToName(+2)
			self.translatePositionToName(+2, self.translatePositionToName(+1))
			self.translatePositionToName(+1, self.translatePositionToName( 0))
			self.translatePositionToName( 0, self.translatePositionToName(-1))
			self.translatePositionToName(-1, self.translatePositionToName(-2))
			self.translatePositionToName(-2, rP2)

			self["-1"].startMoving(doStepEveryXMs)
			self["0"].startMoving(doStepEveryXMs)
			self["+1"].startMoving(doStepEveryXMs)
			self["+2"].startMoving(doStepEveryXMs)

			# GroupTimer
			self["-2"].startMoving(doStepEveryXMs)

		return True
