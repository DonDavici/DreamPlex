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

from Components.ActionMap import HelpableActionMap
from Components.Input import Input
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.Label import Label

from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from __common__ import printl2 as printl, testPlexConnectivity, testInetConnectivity
from __plugin__ import Plugin
from __init__ import _ # _ is translation

from DPH_WOL import wake_on_lan
from DPH_Singleton import Singleton
from DPH_MovingLabel import DPH_HorizontalMenu
from DP_HelperScreens import DPS_InputBox

#===============================================================================
#
#===============================================================================
class DPS_ServerMenu(Screen, DPH_HorizontalMenu):

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
	currentService = None
	plexInstance = None
	selectionOverride = None
	secondRun = False

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, g_serverConfig ):
		printl("", self, "S")
		Screen.__init__(self, session)
		self.selectionOverride = None
		printl("selectionOverride:" +str(self.selectionOverride), self, "D")
		self.session = session

		self.g_serverConfig = g_serverConfig
		self.plexInstance = Singleton().getPlexInstance()

		self.setMenuType("server_menu")

		if self.g_horizontal_menu:
			self.setHorMenuElements()
			self.translateNames()

		self["title"] = StaticText()
		self["txt_exit"] = Label()
		self["txt_menu"] = Label()
		self["menu"]= List(enableWrapAround=True)

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

		self.onLayoutFinish.append(self.finishLayout)
		self.onShown.append(self.checkSelectionOverride)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle(_("Server Menu"))

		self["txt_exit"].setText(_("Exit"))
		self["txt_menu"].setText(_("Menu"))

		self.checkServerState()

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

		self.session.openWithCallback(self.setSeverMenu,MessageBox,_("Plexserver seems to be offline. Please check your your settings or connection!\n Retry?"), MessageBox.TYPE_YESNO)

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
			self.session.open(DPS_ServerMenu,allowOverride=False)

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

		if selection is not None:

			self.selectedEntry = selection[1]
			printl("selected entry " + str(self.selectedEntry), self, "D")

			if type(self.selectedEntry) is int:
				printl("selected entry is int", self, "D")

				if self.selectedEntry == Plugin.MENU_MOVIES:
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
					self.getFilterData(selection[3])

				# elif self.selectedEntry == Plugin.MENU_FILTER_VERT:
				# 	printl("found Plugin.MENU_FILTER_VERT", self, "D")
				# 	self.getFilterData(selection[3])
				#
				# 	self.session.open(DPS_ServerMenu, self.g_serverConfig)

			else:
				printl("selected entry is executable", self, "D")
				self.mediaType = selection[2]
				printl("mediaType: " + str(self.mediaType), self, "D")

				entryData = selection[3]
				printl("entryData: " + str(entryData), self, "D")

				# set additional data mediaType specific
				if self.mediaType == "musicEntry":
					if selection[0] == "All Artists":
						entryData["librarySteps"] = 3
					else:
						entryData["librarySteps"] = 2

				elif self.mediaType == "showEntry":
					self.showEpisodesDirectly = entryData.get('t_showEpisodesDirectly', False)

				elif self.mediaType == "movieEntry":
					pass

				hasPromptTag = entryData.get('hasPromptTag', False)
				printl("hasPromptTag: " + str(hasPromptTag), self, "D")
				if hasPromptTag:
					self.session.openWithCallback(self.addSearchString, DPS_InputBox, entryData, title=_("Please enter your search string!"), text="", maxSize=55, type=Input.TEXT )
				else:
					self.executeSelectedEntry(entryData)

			self.refreshMenu()
			printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def addSearchString(self, entryData, searchString = None):
		printl("", self, "S")
		printl("entryData: " + str(entryData), self, "D")
		if searchString is not None:
			searchUrl = entryData[0]["contentUrl"] + "&query=" + searchString
			printl("searchUrl: " + str(searchUrl), self, "D")

			entryData[0]["contentUrl"] = searchUrl

		self.executeSelectedEntry(entryData[0])

		printl("", self, "C")

	#===========================================================================
	# this function starts DP_Lib...
	#===========================================================================
	def executeSelectedEntry(self, entryData):
		printl("", self, "S")
		printl("self.s_url: " + str(self.s_url), self, "D")

		if self.selectedEntry.start is not None:
			printl("we are startable ...", self, "D")
			self.session.open(self.selectedEntry.start, entryData)

		elif self.selectedEntry.fnc is not None:
			printl("we are a function ...", self, "D")
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

		self.close((True,) )

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

			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(0)

		elif self.selectedEntry == Plugin.MENU_TVSHOWS or self.selectedEntry == Plugin.MENU_MOVIES:
			printl("coming from MENU_TVSHOWS or MENU_MOVIES", self, "D")
			self["menu"].setList(self.g_sectionDataMenu)
			self.selectedEntry = Plugin.MENU_SERVER

			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(0)

		else:
			self.exit()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def refreshMenu(self):
		printl("", self, "S")

		if self.g_horizontal_menu:
			self.refreshOrientationHorMenu(0)

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
			self.refreshMenu()

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

		if summerize and filterBy is None:
			serverData = self.getSectionTypes()
			self.g_sectionDataMenu = serverData
		else:
			serverData = self.plexInstance.getAllSections(filterBy)
			self.g_serverDataMenu = serverData #lets save the menu to call it when cancel is pressed

		self["menu"].setList(serverData)
		self.refreshMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getFilterData(self, entryData):
		printl("", self, "S")
		menuData = self.plexInstance.getSectionFilter(entryData)

		if not menuData:
			text = "You have no data in this section!"
			self.session.open(MessageBox,_("\n%s") % text, MessageBox.TYPE_INFO)
		else:
			self["menu"].setList(menuData)
			self.g_filterDataMenu = menuData #lets save the menu to call it when cancel is pressed
			self.refreshMenu()

		printl("", self, "S")

	#===========================================================================
	#
	#===========================================================================
	def getSectionTypes(self):
		printl("", self, "S")

		fullList = []
		entryData = {}
		fullList.append((_("Movies"), Plugin.MENU_MOVIES, "movieEntry", entryData))
		fullList.append((_("Tv Shows"), Plugin.MENU_TVSHOWS, "showEntry" ,entryData))
		fullList.append((_("Music"), Plugin.MENU_MUSIC, "musicEntry", entryData))
		#fullList.append((_("OnDeck"), Plugin.MENU_MOVIES, "movieEntry", entryData))

		extend = False # SWITCH

		if extend:
			fullList.append((_("Pictures"), Plugin.MENU_PICTURES, "pictureEntry", entryData))
			fullList.append((_("Channels"), Plugin.MENU_CHANNELS, "channelEntry", entryData))

		printl("mainMenuList: " + str(fullList), self, "D")
		printl("", self, "C")
		return fullList
