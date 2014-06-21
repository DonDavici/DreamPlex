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
from Components.Label import Label
from Components.Pixmap import Pixmap

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from DPH_Singleton import Singleton
from DPH_MovingLabel import DPH_HorizontalMenu
from DP_HelperScreens import DPS_InputBox
from DP_Syncer import DPS_Syncer
from DP_ViewFactory import getGuiElements
from DPH_ScreenHelper import DPH_ScreenHelper

from __common__ import printl2 as printl
from __plugin__ import Plugin
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
class DPS_ServerMenu(Screen, DPH_HorizontalMenu, DPH_ScreenHelper):

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

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, g_serverConfig ):
		printl("", self, "S")
		Screen.__init__(self, session)
		DPH_ScreenHelper.__init__(self)

		self.selectionOverride = None
		printl("selectionOverride:" +str(self.selectionOverride), self, "D")
		self.session = session

		self.g_serverConfig = g_serverConfig
		self.plexInstance = Singleton().getPlexInstance()

		self.guiElements = getGuiElements()

		self.setMenuType("server_menu")

		if self.g_horizontal_menu:
			self.setHorMenuElements()
			self.translateNames()

		self["btn_red"]			= Pixmap()
		self["btn_green"]		= Pixmap()

		self["title"] = StaticText()
		self["txt_exit"] = Label()
		self["btn_redText"] = Label()
		self["btn_redText"].setText("sync Medias")

		self["btn_greenText"] = Label()
		self["btn_greenText"].setText("render Backdrops")

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
			    "red":		(self.onKeyRed, ""),
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

		self.initMiniTv()

		# first we set the pics for buttons
		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])

		self.getServerData()

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
	def okbuttonClick(self, selectionOverride = None):
		printl("", self, "S")

		self.currentMenuDataDict[self.menuStep] = self.g_serverDataMenu
		printl("currentMenuDataDict: " + str(self.currentMenuDataDict), self, "D")

		# first of all we save the data from the current step
		self.currentIndexDict[self.menuStep] = self["menu"].getIndex()

		# now we increase the step value because we go to the next step
		self.menuStep += 1
		printl("menuStep: " + str(self.menuStep), self, "D")

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

				hasPromptTag = entryData.get('hasPromptTag', False)
				printl("hasPromptTag: " + str(hasPromptTag), self, "D")
				if hasPromptTag:
					self.session.openWithCallback(self.addSearchString, DPS_InputBox, entryData, title=_("Please enter your search string: "), text=" " * 55, maxSize=55, type=Input.TEXT )
				else:
					self.menuStep -= 1
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

		summerize = config.plugins.dreamplex.summerizeSections.value

		if summerize and filterBy is None:
			serverData = self.getSectionTypes()
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
