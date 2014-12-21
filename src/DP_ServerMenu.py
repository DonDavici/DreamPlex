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
from Components.ActionMap import HelpableActionMap
from Components.Input import Input
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.Pixmap import Pixmap
from Components.Label import Label

from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox

from DPH_Singleton import Singleton
from DPH_MovingLabel import DPH_HorizontalMenu
from DP_HelperScreens import DPS_InputBox
from DP_Syncer import DPS_Syncer
from DPH_ScreenHelper import DPH_ScreenHelper, DPH_Screen
from DP_ViewFactory import getGuiElements
from DP_Users import DPS_Users

from __common__ import printl2 as printl, getLiveTv
from __plugin__ import Plugin
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
class DPS_ServerMenu(DPH_Screen, DPH_HorizontalMenu, DPH_ScreenHelper):

	g_horizontal_menu = False

	selectedEntry = None
	g_serverConfig = None

	g_serverDataMenu = None
	currentService = None
	plexInstance = None
	selectionOverride = None
	secondRun = False
	menuStep = 0 # vaule how many steps we made to restore navigation data
	currentMenuDataDict = {}
	currentIndexDict = {}
	isHomeUser = False

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, g_serverConfig ):
		printl("", self, "S")
		DPH_Screen.__init__(self, session)
		DPH_ScreenHelper.__init__(self)


		self.selectionOverride = None
		printl("selectionOverride:" +str(self.selectionOverride), self, "D")
		self.session = session

		self.g_serverConfig = g_serverConfig
		self.plexInstance = Singleton().getPlexInstance()
		self.guiElements = getGuiElements()

		self.initScreen("server_menu")
		self.initMenu()

		if self.g_horizontal_menu:
			self.setHorMenuElements(depth=2)
			self.translateNames()

		self["title"] = StaticText()

		self["menu"]= List(enableWrapAround=True)

		self["actions"] = HelpableActionMap(self, "DP_MainMenuActions",
			{
				"ok":		(self.okbuttonClick, ""),
				"left":		(self.left, ""),
				"right":	(self.right, ""),
				"up":		(self.up, ""),
				"down":		(self.down, ""),
				"cancel":	(self.cancel, ""),
			    "red":		(self.onKeyRed, ""),
			    "green":    (self.onKeyGreen, ""),
			}, -2)

		self["btn_green"]		= Pixmap()
		self["btn_green"].hide()
		self["btn_greenText"]   = Label()

		self["text_HomeUserLabel"]   = Label()
		self["text_HomeUser"]   = Label()

		self.onLayoutFinish.append(self.finishLayout)
		self.onLayoutFinish.append(self.getInitialData)
		self.onLayoutFinish.append(self.checkSelectionOverride)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle(_("Server Menu"))

		if self.miniTv:
			self.initMiniTv()

		if self.g_serverConfig.myplexHomeUsers.value:
			self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])
			self["btn_green"].show()
			self["btn_greenText"].setText(_("Switch User"))
			self["text_HomeUserLabel"].setText(_("Current User:"))
			currentHomeUser = self.g_serverConfig.myplexCurrentHomeUser.value
			if currentHomeUser != "":
				self["text_HomeUser"].setText(self.g_serverConfig.myplexCurrentHomeUser.value)
			else:
				self["text_HomeUser"].setText(self.g_serverConfig.myplexTokenUsername.value)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getInitialData(self):
		printl("", self, "S")

		self.getServerData()

		# save the mainMenuList for later usage
		self.menu_main_list = self["menu"].list

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
			self.okbuttonClick()

		printl("", self, "C")

#===============================================================================
# KEYSTROKES
#===============================================================================

	#===============================================================
	#
	#===============================================================
	def onKeyRed(self):
		printl("", self, "S")

		self.session.open(DPS_Syncer, "sync", self.g_serverConfig,)

		printl("", self, "C")

	#===============================================================
	#
	#===============================================================
	def onKeyGreen(self):
		printl("", self, "S")

		self.displayOptionsMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenu(self):
		printl("", self, "S")

		functionList = []

		# add myPlex User as first one
		functionList.append((self.g_serverConfig.myplexTokenUsername.value, self.g_serverConfig.myplexPin.value, self.g_serverConfig.myplexToken.value, False))

		# now add all home users
		homeUsersObject = DPS_Users(self.session, self.g_serverConfig.id.value, self.plexInstance)
		homeUsersFromServer = homeUsersObject["content"].getHomeUsersFromServer()

		for user in homeUsersFromServer.findall('user'):
			self.lastUserId = user.attrib.get("id")
			self.currentHomeUsername = user.attrib.get("username")
			self.currentPin = user.attrib.get("pin")
			self.currentHomeUserToken = user.attrib.get("token")

		functionList.append((self.currentHomeUsername, self.currentPin, self.currentHomeUserToken, True))

		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, title=_("Home Users"), list=functionList)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			printl("choice: None - we pressed exit", self, "D")
			return

		printl("choice: " + str(choice), self, "D")
		self.isHomeUser = choice[3]

		if choice[1] != "" and self.isHomeUser:
			printl(choice[1], self, "D")
			self.session.openWithCallback(self.askForPin, InputBox, title=_("Please enter the pincode!") ,type=Input.PIN)
		else:
			if self.g_serverConfig.myplexPinProtect.value:
				self.session.openWithCallback(self.askForPin, InputBox, title=_("Please enter the pincode!") , type=Input.PIN)
				self.currentPin = self.g_serverConfig.myplexPin.value
			else:
				self.switchToMyPlexUser()

		printl("", self, "C")

	#===============================================================
	#
	#===============================================================
	def switchToMyPlexUser(self):
		printl("", self, "S")

		self.g_serverConfig.myplexCurrentHomeUser.value = ""
		self.g_serverConfig.myplexCurrentHomeUserToken.value = ""
		self.g_serverConfig.save()

		self["text_HomeUser"].setText(self.g_serverConfig.myplexTokenUsername.value)

		printl("", self, "C")

	#===============================================================
	#
	#===============================================================
	def switchToHomeUser(self):
		printl("", self, "S")

		self.g_serverConfig.myplexCurrentHomeUser.value = self.currentHomeUsername
		self.g_serverConfig.myplexCurrentHomeUserToken.value = self.currentHomeUserToken
		self.g_serverConfig.save()

		self["text_HomeUser"].setText(self.g_serverConfig.myplexCurrentHomeUser.value)

		printl("", self, "C")

	#===============================================================
	#
	#===============================================================
	def askForPin(self, enteredPin):
		printl("", self, "S")
		print self.currentPin
		print enteredPin

		if enteredPin is None:
			pass
		else:
			if int(enteredPin) == int(self.currentPin):
				self.session.open(MessageBox,"The pin was correct! Switching user.", MessageBox.TYPE_INFO)
				if self.isHomeUser:
					self.switchToHomeUser()
				else:
					self.switchToMyPlexUser()
			else:
				self.session.open(MessageBox,"The pin was wrong! Abort user switiching.", MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===============================================================
	#
	#===============================================================
	def okbuttonClick(self):
		printl("", self, "S")

		self.currentMenuDataDict[self.menuStep] = self.g_serverDataMenu
		printl("currentMenuDataDict: " + str(self.currentMenuDataDict), self, "D")

		# first of all we save the data from the current step
		self.currentIndexDict[self.menuStep] = self["menu"].getIndex()

		# now we increase the step value because we go to the next step
		self.menuStep += 1
		printl("menuStep: " + str(self.menuStep), self, "D")

		# this is used to step in directly into a server when there is only one entry in the serverlist
		if self.selectionOverride is not None:
			selection = self.selectionOverride

			# because we change the screen we have to unset the information to be able to return to main menu
			self.selectionOverride = None
		else:
			selection = self["menu"].getCurrent()

		printl("selection = " + str(selection), self, "D")

		if selection is not None and selection:

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

				hasPromptTag = entryData.get('hasPromptTag', False)
				printl("hasPromptTag: " + str(hasPromptTag), self, "D")
				if hasPromptTag:
					self.session.openWithCallback(self.addSearchString, DPS_InputBox, entryData, title=_("Please enter your search string: "), text=" " * 55, maxSize=55, type=Input.TEXT )
				else:
					self.menuStep -= 1
					self.executeSelectedEntry(entryData)

			self.refreshMenu()
		else:
			printl("no data, leaving ...", self, "D")
			self.cancel()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def addSearchString(self, entryData, searchString = None):
		printl("", self, "S")
		printl("entryData: " + str(entryData), self, "D")

		if searchString is not None:
			if "origContentUrl" in entryData[0]:
				searchUrl = entryData[0]["origContentUrl"] + "&local=1&query=" + searchString
			else:
				searchUrl = entryData[0]["contentUrl"] + "&local=1&query=" + searchString
				entryData[0]["origContentUrl"] = entryData[0]["contentUrl"]

			printl("searchUrl: " + str(searchUrl), self, "D")

			entryData[0]["contentUrl"] = searchUrl

		self.executeSelectedEntry(entryData[0])

		printl("", self, "C")

	#===========================================================================
	# this function starts DP_Lib...
	#===========================================================================
	def executeSelectedEntry(self, entryData):
		printl("", self, "S")

		if self.selectedEntry.start is not None:
			printl("we are startable ...", self, "D")
			self.session.openWithCallback(self.myCallback, self.selectedEntry.start, entryData)

		elif self.selectedEntry.fnc is not None:
			printl("we are a function ...", self, "D")
			self.selectedEntry.fnc(self.session)

		if config.plugins.dreamplex.showFilter.value:
			self.selectedEntry = Plugin.MENU_FILTER # we overwrite this now to handle correct menu jumps with exit/cancel button

		printl("", self, "C")

	#==========================================================================
	#
	#==========================================================================
	def myCallback(self):
		printl("", self, "S")

		if not config.plugins.dreamplex.stopLiveTvOnStartup.value:
			self.session.nav.playService(getLiveTv(), forceRestart=True)

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
	def cancel(self):
		printl("", self, "S")
		self.menuStep -= 1
		printl("menuStep: " + str(self.menuStep), self, "D")

		if self.menuStep >= 0:
			self.g_serverDataMenu = self.currentMenuDataDict[self.menuStep]
			self["menu"].setList(self.g_serverDataMenu)
			self["menu"].setIndex(self.currentIndexDict[self.menuStep])
			self.refreshMenu()

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
	def getServerData(self, filterBy=None):
		printl("", self, "S")

		if config.plugins.dreamplex.summerizeSections.value and filterBy is None:
			serverData = self.plexInstance.getSectionTypes()
		else:
			serverData = self.plexInstance.getAllSections(filterBy)

		if not serverData:
			self.showNsoDataMessage()
		else:
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
			self.showNoDataMessage()
			self.menuStep -= 1
			printl("menuStep: " + str(self.menuStep), self, "D")

		else:
			self["menu"].setList(menuData)
			self.g_serverDataMenu = menuData #lets save the menu to call it when cancel is pressed
			self.refreshMenu()

		printl("", self, "S")

	#===========================================================================
	#
	#===========================================================================
	def showNoDataMessage(self):
		printl("", self, "S")

		text = self.plexInstance.getLastErrorMessage()
		self.session.open(MessageBox,_("\n%s") % text, MessageBox.TYPE_INFO)

		printl("", self, "C")
