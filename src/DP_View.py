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
import math
import os

#noinspection PyUnresolvedReferences
from enigma import eTimer

from Components.ActionMap import HelpableActionMap
from Components.Sources.List import List
from Components.Label import Label
from Components.config import config
from Components.config import NumericalTextInput
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.AVSwitch import AVSwitch

from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Tools.Directories import fileExists

from enigma import eServiceReference
from enigma import ePicLoad

from urllib import quote_plus
from twisted.web.client import downloadPage

from DP_ViewFactory import getGuiElements
from DP_Player import DP_Player

from DPH_Singleton import Singleton

from __common__ import printl2 as printl, loadPicture
from __plugin__ import getPlugins, Plugin
from __init__ import _ # _ is translation

#===========================================================================
#
#===========================================================================
class DP_View(Screen, NumericalTextInput):

	ON_CLOSED_CAUSE_CHANGE_VIEW = 1
	ON_CLOSED_CAUSE_SAVE_DEFAULT = 2
	ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE = 3

	returnTo                        = None
	currentEntryDataDict            = {}
	currentIndexDict                = {}
	showMedia                       = False
	showDetail                      = False
	isDirectory                     = False
	forceUpdate                     = False

	backdrop_postfix                = ""
	poster_postfix                  = ""
	image_prefix                    = ""
	whatPoster                      = None
	whatBackdrop                    = None
	myParams                        = None
	seenUrl                         = None
	unseenUrl                       = None
	deleteUrl                       = None
	refreshUrl                      = None
	details                         = None
	extraData                       = None
	context                         = None
	resetPoster                     = True
	resetBackdrop                   = True
	posterHeight                    = None
	posterWidth                     = None
	backdropHeight                  = None
	backdropWidth                   = None
	EXpicloadPoster                 = None
	EXpicloadBackdrop               = None
	EXscale                         = None
	playTheme                       = False
	startPlaybackNow                = False
	changePoster                    = True
	changeBackdrop                  = True
	resetGuiElements                = False
	viewStep                        = 0 # we use this to know the steps we did to store the changes form subviews
	viewChangeStorage               = {} # we use this to save changed value if we have subViews
	loadedStillPictureLib           = False # until we do not know if we can load the libs it will be false
	usedStillPicture                = False
	refreshTimer                    = None # initial value to stay agile in list of media
	selection                       = None # this stores the current list entry of list

	playerData                      = {} # inital playerData dict
	currentQueuePosition            = 0 # this is the current selection id
	detailsPaneVisible              = True # is shortDescription or details visible

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, viewClass, libraryName, loadLibraryFnc, viewParams):
		"""
		@param viewClass: is the screen session (eg DP_ViewShows)
		@param libraryName: movie, show, music
		@type loadLibraryFnc: is loadLibrary Function from Lib_class (eg DP_LibShows)
		@param viewParams: are the params for dynamic screen handling from skin params
		@param select: unknown
		@return:
		"""
		printl("", self, "S")
		Screen.__init__(self, viewClass)
		self.viewParams = viewParams
		NumericalTextInput.__init__(self)

		printl("viewParams: " + str(self.viewParams), self, "D")
		printl("libraryName: " + str(libraryName), self, "D")

		self.skinName = self.viewParams["settings"]["screen"]
		printl("self.skinName: " + str(self.skinName), self, "D")

		self.currentViewName = str(self.viewParams["settings"]["name"])

		self.useBackdropVideos = self.viewParams["settings"]["backdropVideos"]

		self.plexInstance = Singleton().getPlexInstance()

		self.libraryName = libraryName
		self.loadLibrary = loadLibraryFnc

		self.setListViewElementsCount()

		self.usePicCache = config.plugins.dreamplex.usePicCache.value

		# Initialise library list
		myList = []
		self["listview"] = List(myList, True)

		self.seenPng = None
		self.unseenPng = None
		self.startedPng = None

		self["actions"] = HelpableActionMap(self, "DP_View",
		{
			"ok":			(self.onKeyOk, ""),
			"cancel":		(self.onKeyCancel, ""),
			"left":			(self.onKeyLeft, ""),
			"right":		(self.onKeyRight, ""),
			"up":			(self.onKeyUp, ""),
			"down":			(self.onKeyDown, ""),
			"info":			(self.onKeyInfo, ""),
			"menu":			(self.onKeyMenu, ""),
			"video":		(self.onKeyVideo, ""),
			"audio":		(self.onKeyAudio, ""),
			"red":			(self.onKeyRed, ""),
			"yellow":		(self.onKeyYellow, ""),
			"blue":			(self.onKeyBlue, ""),
			"green":		(self.onKeyGreen, ""),
			"text":			(self.onKeyText, ""),
			"red_long":		(self.onKeyRedLong, ""),
			"yellow_long":	(self.onKeyYellowLong, ""),
			"blue_long":	(self.onKeyBlueLong, ""),

			"bouquet_up":	(self.bouquetUp, ""),
			"bouquet_down":	(self.bouquetDown, ""),
		}, -2)

		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.getViewListData)

		self.guiElements = getGuiElements()

		# set navigation values
		#DP_View.setListViewElementsCount("DPS_ViewList")

		# get needed config parameters
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		self.playTheme = config.plugins.dreamplex.playTheme.value
		self.fastScroll = config.plugins.dreamplex.fastScroll.value

		# get data from plex library
		self.image_prefix = Singleton().getPlexInstance().getServerName().lower()

		# get server config
		self.serverConfig = Singleton().getPlexInstance().getServerConfig()

		# init skin elements
		self["txt_functions"] = Label()
		self["txt_exit"] = Label()

		self["totalLabel"] = Label()
		self["totalLabel"].setText(_("Total:"))
		self["total"] = Label()

		self["paginationLabel"] = Label()
		self["paginationLabel"].setText(_("Pages:"))
		self["pagination"] = Label()

		self["filterLabel"] = Label()
		self["filterLabel"].setText(_("Filter:"))
		self["filter"]		= Label()
		self["filter"].setText(_("press '0-9'"))

		self["btn_red"]			= Pixmap()
		self["btn_yellow"]		= Pixmap()
		self["btn_blue"]		= Pixmap()
		self["btn_green"]		= Pixmap()

		self["btn_redText"]			= Label()
		self["btn_yellowText"]		= Label()
		self["btn_blueText"]		= Label()
		self["btn_greenText"]		= Label()

		self["btn_redText"].setText(_("View '") + str(self.currentViewName) + "'")

		self["btn_yellowText"].setText(_("show 'Details'"))

		self["sound"] = MultiPixmap()

		self["resolution"] = MultiPixmap()

		self["aspect"] = MultiPixmap()

		self["codec"] = MultiPixmap()

		self["rated"] = MultiPixmap()

		self["title"] = Label()
		self["grandparentTitle"] = Label()
		self["season"] = Label()

		self["tag"] = Label()

		self["cast"] = Label()
		self["castLabel"] = Label()
		self["castLabel"].setText(_("Cast:"))

		self["shortDescription"] = ScrollLabel()

		self["subtitles"] = Label()
		self["subtitles"].setText(_("press 'Text'"))
		self["subtitlesLabel"] = Label()
		self["subtitlesLabel"].setText(_("Subtitles:"))

		self["audio"] = Label()
		self["audio"].setText(_("press 'Audio'"))
		self["audioLabel"] = Label()
		self["audioLabel"].setText(_("Audio:"))

		self["info"] = Label()
		self["info"].setText(_("press 'Info'"))
		self["infoLabel"] = Label()
		self["infoLabel"].setText(_("Info:"))

		self["director"] = Label()
		self["directorLabel"] = Label()
		self["directorLabel"].setText(_("Director:"))

		self["writer"] = Label()
		self["writerLabel"] = Label()
		self["writerLabel"].setText(_("Writer:"))

		self["genre"] = Label()
		self["genreLabel"] = Label()
		self["genreLabel"].setText(_("Genre:"))

		self["year"] = Label()
		self["yearLabel"] = Label()
		self["yearLabel"].setText(_("Year:"))

		self["runtime"] = Label()
		self["runtimeLabel"] = Label()
		self["runtimeLabel"].setText(_("Runtime:"))

		self["backdrop"] = Pixmap()
		self["backdropVideo"] = Pixmap() # this is just to avoid greenscreen, maybe we find a better way
		self["backdroptext"] = Label()

		self["poster"] = Pixmap()
		self["postertext"] = Label()

		self["rating_stars"] = ProgressBar()

		# Poster
		self.EXpicloadPoster = ePicLoad()
		self.poster_postfix = self.viewParams["elements"]["poster"]["postfix"]
		self.posterHeight = self.viewParams["elements"]["poster"]["height"]
		self.posterWidth = self.viewParams["elements"]["poster"]["width"]

		# Backdrops
		self.EXpicloadBackdrop = ePicLoad()
		self.backdrop_postfix = self.viewParams["elements"]["backdrop"]["postfix"]
		self.backdropHeight = self.viewParams["elements"]["backdrop"]["height"]
		self.backdropWidth = self.viewParams["elements"]["backdrop"]["width"]

		# now we try to enable stillPictureSupport
		if config.plugins.dreamplex.useBackdropVideos.value and self.useBackdropVideos:
			try:
				from DPH_StillPicture import StillPicture
				self["backdropVideo"] = StillPicture(session)
				self.loadedStillPictureLib = True
			except Exception, ex:
				printl("Exception: " + str(ex), self, "D")
				printl("was not able to import lib for stillpictures", self, "D")

		# on layout finish we have to do some stuff
		self.onLayoutFinish.append(self.setPara)
		self.onLayoutFinish.append(self.processGuiElements)
		self.onLayoutFinish.append(self.finishLayout)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setCustomTitle(self):
		printl("", self, "S")

		self.setTitle(_(self.libraryName))

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def setPara(self):
		"""
		set params for poster and backdrop via ePicLoad object
		"""
		printl("", self, "S")

		self.EXscale = (AVSwitch().getFramebufferScale())

		self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadBackdrop.setPara([self["backdrop"].instance.size().width(), self["backdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setListViewElementsCount(self):
		printl("", self, "S")

		self.itemsPerPage = int(self.viewParams["settings"]['itemsPerPage'])

		printl("self.itemsPerPage: " + str(self.itemsPerPage), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getViewListData(self):
		printl("", self, "S")

		self.viewStep = 0
		self.currentEntryDataDict = {}
		self.currentIndexDict = {}

		self._load()
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def bouquetUp(self):
		printl("", self, "S")

		self["shortDescription"].pageUp()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def bouquetDown(self):
		printl("", self, "S")

		self["shortDescription"].pageDown()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyOk(self):
		printl("", self, "S")

		self.onEnter()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyCancel(self):
		printl("", self, "S")

		self.onLeave()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyInfo(self):
		printl("", self, "S")

		self.showMedia = True
		self.resetGuiElements = True
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyMenu(self):
		printl("", self, "S")

		self.displayOptionsMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyVideo(self):
		printl("", self, "S")

		pass
		#self.showFunctions(not self.areFunctionsHidden)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyAudio(self):
		printl("", self, "S")

		self.displayAudioMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyText(self):
		printl("", self, "S")

		self.displaySubtitleMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyLeft(self):
		printl("", self, "S")

		self.onPreviousPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRight(self):
		printl("", self, "S")

		self.onNextPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyUp(self):
		printl("", self, "S")

		self.onPreviousEntry()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyDown(self):
		printl("", self, "S")

		self.onNextEntry()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRed(self):
		printl("", self, "S")

		self.onToggleView()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRedLong(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyYellow(self):
		printl("", self, "S")

		self.toggleDetails()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyYellowLong(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyBlue(self):
		printl("", self, "S")

		self.toggleFastScroll()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyGreen(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleFastScroll(self):
		printl("", self, "S")

		if self.viewParams["elements"]["info"]["visible"]:
			if self.fastScroll:
				self.fastScroll = False
				self["btn_blueText"].setText("fastScroll 'Off'")
				self["info"].hide()
				self["infoLabel"].hide()
			else:
				self.fastScroll = True
				self["btn_blueText"].setText("fastScroll 'On'")
				self.resetGuiElements = True
				self["info"].show()
				self["infoLabel"].show()

		self.setFunctionsText()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setFunctionsText(self):
		printl("", self, "S")

		self["txt_functions"].setText("Menu")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyBlueLong(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onToggleView(self):
		printl("", self, "S")

		if config.plugins.dreamplex.useBackdropVideos.value:
			self.stopBackdropVideo()

		self.close((DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW, ))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNextEntry(self):
		printl("", self, "S")

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onPreviousEntry(self):
		printl("", self, "S")

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNextPage(self):
		printl("", self, "S")
		itemsTotal = self["listview"].count()
		index = self["listview"].getIndex()

		if index >= itemsTotal:
			index = itemsTotal - 1
		self["listview"].setIndex(index)
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onPreviousPage(self):
		printl("", self, "S")
		index = self["listview"].getIndex()

		if index < 0:
			index = 0
		self["listview"].setIndex(index)

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onEnter(self):
		printl("", self, "S")
		selection = self["listview"].getCurrent()

		if selection is not None:
			entryData		= selection[1]
			#context		= selection[2]
			nextContentUrl = selection[4]

			# we extend details for provide the next data location
			entryData["contentUrl"] = nextContentUrl
			printl("entryData: " + str(entryData), self, "D")

			viewMode	= entryData['viewMode']
			printl("viewMode: " +str(viewMode), self, "D")

			# we need this for onEnter-func in child lib
			self.viewMode = viewMode

			if viewMode == "play" or viewMode == "directMode":
				printl("viewMode -> play", self, "D")

				if config.plugins.dreamplex.useBackdropVideos.value:
					self.stopBackdropVideo()

				currentIndex = self["listview"].getIndex()
				self.session.open(DP_Player, self.listViewList, currentIndex, self.viewParams)

			else:
				# save index here because user moved around for sure
				self.currentIndexDict[self.viewStep] = self["listview"].getIndex()

				self.viewStep += 1
				self._load(entryData)

				self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleDetails(self):
		printl("", self, "S")

		if self.detailsPaneVisible:
			self.detailsPaneVisible = False
			self["shortDescription"].hide()
			self["btn_yellowText"].setText(_("show 'Description'"))
			self.toggleElementVisibilityWithLabel("writer")
			self.toggleElementVisibilityWithLabel("director")
			self.toggleElementVisibilityWithLabel("cast")
		else:
			self.detailsPaneVisible = True
			self["shortDescription"].show()
			self["btn_yellowText"].setText(_("show 'Details'"))
			self.toggleElementVisibilityWithLabel("writer", "hide")
			self.toggleElementVisibilityWithLabel("director", "hide")
			self.toggleElementVisibilityWithLabel("cast", "hide")

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def toggleElementVisibilityWithLabel(self, elementName, action="show"):

		if action == "show":
			self[elementName].show()
			self[elementName+ "Label"].show()
		elif action == "hide":
			self[elementName].hide()
			self[elementName+ "Label"].hide()

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first decrease by one
		self.viewStep -= 1

		printl("returnTo: " + str(self.returnTo), self, "D")

		if config.plugins.dreamplex.useBackdropVideos.value:
			self.stopBackdropVideo()

		if config.plugins.dreamplex.playTheme.value:
			printl("stoping theme playback", self, "D")
			self.session.nav.stopService()

		if self.viewStep >= 0:
			self["listview"].setList(self.currentEntryDataDict[self.viewStep])
			self["listview"].setIndex(self.currentIndexDict[self.viewStep])
		else:
			printl("", self, "C")
			self.close()

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _load(self, entryData = None):
		printl("", self, "S")
		printl("entryData: " + str(entryData), self, "D")

		# loadLibrary is a function in each class that inherits from DP_LibMain (DP_LibMovies, DP_LibSHows, DP_LibMusic)
		libraryDataArr = self.loadLibrary(entryData, self.forceUpdate)
		self.forceUpdate=False

		# this is the content for the list (must be tuple no dict)
		self.libraryData = libraryDataArr[0]
		printl("libraryData: " + str(self.libraryData), self, "D")

		# we need to do this because since we save cache via pickle the seen pic object cant be saved anymore
		self.listViewList = self.alterViewStateInList(self.libraryData)

		# mediaContainer on top of xml
		self.mediaContainer = libraryDataArr[1]
		printl("mediaContainer: " + str(self.mediaContainer), self, "D")

		# we save the list to be able to restore
		self.currentEntryDataDict[self.viewStep] = self.listViewList

		# now just refresh list
		self.updateList()
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def alterViewStateInList(self, listViewList):
		printl("", self, "S")
		printl("listViewList: " + str(listViewList), self, "S")
		newList = []
		undefinedIcon = loadPicture('/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/default/all/picreset.png')

		for listViewEntry in listViewList:
			viewState = str(listViewEntry[3])
			printl("seenVisu location: " + str(listViewEntry[3]), self, "D")

			if listViewEntry is not None:
				if viewState == 'seen':
					viewState = self.seenPic

				elif viewState == 'started':
					viewState = self.startedPic

				elif viewState == 'unseen':
					viewState = self.unseenPic

				else:
					viewState = undefinedIcon

			content = (listViewEntry[0], listViewEntry[1], listViewEntry[2], viewState ,listViewEntry[4])
			newList.append(content)

		printl("", self, "C")
		return newList

	#===========================================================================
	#
	#===========================================================================
	def updateList(self):
		printl("", self, "S")

		self["listview"].setList(self.listViewList)
		self["listview"].setIndex(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setText(self, name, value, ignore=False, what=None):
		#printl("", self, "S")

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
			printl("Exception: " + str(ex), self)

		#printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def refresh(self):
		printl("", self, "S")

		# we kill a former timer to start a new one
		if self.refreshTimer is not None:
			self.refreshTimer.stop()

		# show content for selected list item
		self.selection = self["listview"].getCurrent()

		if self.selection is not None:
			printl("selection: " + str(self.selection), self, "D")
			tagType = self.selection[1]['tagType']

			self.isDirectory = False
			if tagType == "Directory":
				self.isDirectory = True

		self._refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _refresh(self):
		printl("", self, "S")

		printl("resetGuiElements: " + str(self.resetGuiElements), self, "D")
		printl("self.viewParams: " + str(self.viewParams), self, "D")

		if self.resetGuiElements:
			self.resetGuiElementsInFastScrollMode()

		self.resetCurrentImages()

		printl("showMedia: " + str(self.showMedia), self, "D")

		printl("isDirectory: " + str(self.isDirectory), self, "D")

		if self.selection is not None:
			self.details 	= self.selection[1]
			self.context	= self.selection[2]

			if self.isDirectory:
				# because we are a dirctory we have to do nothing here
				# processing the normal way would lead to greenscreen
				pass
			else:
				# lets get all data we need to show the needed pictures
				# we also check if we want to play
				self.getPictureInformationToLoad()

				if self.context is not None:
					# lets set the urls for context functions of the selected entry
					self.seenUrl = self.context.get("watchedURL", None)
					self.unseenUrl = self.context.get("unwatchURL", None)
					self.deleteUrl = self.context.get("deleteURL", None)
					self.refreshUrl = self.context.get("libraryRefreshURL", None)
					printl("seenUrl: " + str(self.seenUrl),self, "D")
					printl("unseenUrl: " + str(self.unseenUrl),self, "D")
					printl("deleteUrl: " + str(self.deleteUrl),self, "D")
					printl("refreshUrl: " + str(self.refreshUrl),self, "D")

				# if we are a show an if playtheme is enabled we start playback here
				if self.playTheme:
					if self.startPlaybackNow: # only if we are a show
						self.startThemePlayback()

				self.setText("title", self.details.get("title", " ").encode('utf-8'))
				self.setText("grandparentTitle", self.details.get("grandparentTitle", " "))
				self.setText("season", "Season " + self.details.get("season", " "))
				self.setText("tag", self.details.get("tagline", " ").encode('utf8'), True)
				self.setText("year", str(self.details.get("year", " - ")))
				self.setText("genre", str(self.details.get("genre", " - ").encode('utf8')))
				self.setText("runtime", str(self.details.get("runtime", " - ")))
				self.setText("shortDescription", str(self.details.get("summary", " ").encode('utf8')))
				self.setText("cast", str(self.details.get("cast", " ")))
				self.setText("writer", str(self.details.get("writer", " ").encode('utf8')))
				self.setText("director", str(self.details.get("director", " ").encode('utf8')))

				if self.fastScroll == False or self.showMedia == True and self.details ["viewMode"] == "play":
					# handle all pixmaps
					self.handlePopularityPixmaps()
					#self.handleCodecPixmaps()
					#self.handleAspectPixmaps()
					#self.handleResolutionPixmaps()
					#self.handleRatedPixmaps()
					#self.handleSoundPixmaps()

				# navigation
				self.handleNavigationData()

				# now lets switch images
				if self.changePoster:
					self.showPoster()

				if not self.fastScroll or self.showMedia:
					if self.changeBackdrop:
						# check if showiframe lib loaded ...
						if self.loadedStillPictureLib:
							printl("self.loadedStillPictureLib: " + str(self.loadedStillPictureLib), self, "D")
							backdrop = config.plugins.dreamplex.mediafolderpath.value + str(self.image_prefix) + "_" + str(self.details["ratingKey"]) + "_backdrop_" + self.backdropWidth + "x" + self.backdropHeight + ".m1v"
							printl("backdrop: " + str(backdrop), self, "D")

							# check if the backdrop file exists
							if os.access(backdrop, os.F_OK):
								printl("yes", self, "D")
								self["backdropVideo"].setStillPicture(backdrop)
								self["backdrop"].hide()
								self.usedStillPicture = True
							else:
								printl("no", self, "D")
								self["backdropVideo"].hide()
								self["backdrop"].show()
								# if not handle as normal backdrop
								self.handleBackdrop()

						else:
							# if not handle as normal backdrop
							self.handleBackdrop()

				# we need those for fastScroll
				# this prevents backdrop load on next item
				self.showMedia = False

		else:
			self.setText("title", "no data retrieved")
			self.setText("shortDescription", "no data retrieved")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def handleBackdrop(self):
		printl("", self, "S")

		self.usedStillPicture = False

		printl("showing backdrop with timeout ...", self, "D")
		# we use this to give enough time to jump through the list before we start encoding pics and reading all the data that have to be switched = SPEEDUP :-)
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.showBackdrop)
		self.refreshTimer.start(1000, True)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def stopBackdropVideo(self):
		printl("", self, "S")

		if self.loadedStillPictureLib and self.usedStillPicture:
			# stop the m1v playback to avoid blocking the playback of the movie
			self["backdropVideo"].finishStillPicture()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleNavigationData(self):
		printl("", self, "S")

		itemsPerPage = self.itemsPerPage
		itemsTotal = self["listview"].count()
		correctionVal = 0.5

		if (itemsTotal%itemsPerPage) == 0:
			correctionVal = 0

		pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + correctionVal))
		pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))

		self.setText("total", _(str(itemsTotal)))
		self.setText("pagination", _(str(pageCurrent) + "/" + str(pageTotal)))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenu(self):
		printl("", self, "S")

		functionList = []

		functionList.append((_("Mark media unwatched"), Plugin("View", fnc = self.markUnwatched), ))
		functionList.append((_("Mark media watched"), Plugin("View", fnc = self.markWatched), ))
		functionList.append((_("Initiate Library refresh"), Plugin("View", fnc = self.initiateRefresh), ))
		#functionList.append((_("Delete media from Library"), Plugin("View", fnc=self.deleteFromLibrary), ))

		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, title=_("Media Functions"), list=functionList)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displaySubtitleMenu(self):
		printl("", self, "S")

		selection = self["listview"].getCurrent()

		media_id = selection[1]['ratingKey']
		server = selection[1]['server']

		functionList = []

		subtitlesList = Singleton().getPlexInstance().getSubtitlesById(server, media_id)

		for item in subtitlesList:

			selected = item.get('selected', "")
			if selected == "1":
				name = item.get('language').encode("utf-8", "") + " [Currently Enabled]"
			else:
				name = item.get('language').encode("utf-8", "")

			sub_id = item.get('id', "")
			languageCode = item.get('languageCode', "")
			part_id = item.get('partid', "")

			functionList.append((name, media_id, languageCode, sub_id, server, part_id, selected))

		selection = 0
		for i in range(len(functionList)):
			if functionList[i][6] == "1":
				selection = i
				break

		self.session.openWithCallback(self.displaySubtitleMenuCallback, ChoiceBox, title=_("Subtitle Functions"), list=functionList,selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayAudioMenu(self):
		printl("", self, "S")

		selection = self["listview"].getCurrent()

		media_id = selection[1]['ratingKey']
		server = selection[1]['server']

		functionList = []

		audioList = Singleton().getPlexInstance().getAudioById(server, media_id)

		for item in audioList:

			selected = item.get('selected', "")
			if selected == "1":
				name = item.get('language').encode("utf-8", "") + " [Currently Enabled]"
			else:
				name = item.get('language').encode("utf-8", "")

			stream_id = item.get('id', "")
			languageCode = item.get('languageCode', "")
			part_id = item.get('partid', "")

			functionList.append((name, media_id, languageCode, stream_id, server, part_id, selected))

		selection = 0
		for i in range(len(functionList)):
			if functionList[i][6] == "1":
				selection = i
				break

		self.session.openWithCallback(self.displayAudioMenuCallback, ChoiceBox, title=_("Audio Functions"), list=functionList,selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def markUnwatched(self):
		printl("", self, "S")
		self.forceUpdate = True

		Singleton().getPlexInstance().doRequest(self.unseenUrl)
		self.getViewListData()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def markWatched(self):
		printl("", self, "S")
		self.forceUpdate = True

		Singleton().getPlexInstance().doRequest(self.seenUrl)
		self.getViewListData()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initiateRefresh(self):
		printl("", self, "S")
		self.forceUpdate = True

		Singleton().getPlexInstance().doRequest(self.refreshUrl)
		self.getViewListData()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def deleteFromLibrary(self):
		printl("", self, "S")

		self.session.openWithCallback(self.executeLibraryDelete, MessageBox, _("Are you sure?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def executeLibraryDelete(self, confirm):
		printl("", self, "S")

		if confirm:
			Singleton().getPlexInstance().doRequest(self.deleteUrl)
			self.getViewListData()
		else:
			self.session.open(MessageBox,_("Deleting aborted!"), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	# choice = name, media_id, languageCode, stream_id, server, part_id, selected
	#===========================================================================
	def displayAudioMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		printl("choice" + str(choice), self, "D")

		Singleton().getPlexInstance().setAudioById(choice[4], choice[3], choice[5])

		printl("", self, "C")

	#===========================================================================
	# choice = name, media_id, languageCode, stream_id, server, part_id, selected
	#===========================================================================
	def displaySubtitleMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		printl("choice" + str(choice), self, "D")

		Singleton().getPlexInstance().setSubtitleById(choice[4], choice[3], choice[5])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startThemePlayback(self):
		printl("", self, "S")

		printl("start pĺaying theme", self, "I")
		accessToken = Singleton().getPlexInstance().get_aTokenForServer()#g_myplex_accessToken
		theme = self.details["theme"]
		server = self.details["server"]
		printl("theme: " + str(theme), self, "D")
		url = "http://" + str(server) + str(theme) + str(accessToken) #"?X-Plex-Token=" + str(accessToken)
		sref = "4097:0:0:0:0:0:0:0:0:0:%s" % quote_plus(url)
		printl("sref: " + str(sref), self, "D")
		self.session.nav.stopService()
		self.session.nav.playService(eServiceReference(sref))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showPoster(self, forceShow = False):
		printl("", self, "S")

		#try:
		#	del self.EXpicloadPoster
		#except Exception:
		#	pass
		#finally:
		#	self.EXpicloadPoster = ePicLoad()
		#	self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])

		if forceShow:
			if self.whatPoster is not None:
				self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
				ptr = self.EXpicloadPoster.getData()

				if ptr is not None:
					self["poster"].instance.setPixmap(ptr)

		elif self.usePicCache:
			if fileExists(self.whatPoster):

				if self.whatPoster is not None:
					self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
					ptr = self.EXpicloadPoster.getData()

					if ptr is not None:
						self["poster"].instance.setPixmap(ptr)

			else:
				self.downloadPoster()
		else:
			self.downloadPoster()

		printl("", self, "C")
		return

	#===========================================================================
	#
	#===========================================================================
	def showBackdrop(self, forceShow = False):
		printl("", self, "S")

		#try:
		#	del self.EXpicloadBackdrop
		#except Exception:
		#	pass
		#finally:
		#	self.EXpicloadBackdrop = ePicLoad()
		#	self.EXpicloadBackdrop.setPara([self["backdrop"].instance.size().width(), self["backdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])

		if forceShow:
			if self.whatBackdrop is not None:
				self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
				ptr = self.EXpicloadBackdrop.getData()

				if ptr is not None:
					self["backdrop"].instance.setPixmap(ptr)

		elif self.usePicCache :
			if fileExists(self.whatBackdrop):

				if self.whatBackdrop is not None:
					self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
					ptr = self.EXpicloadBackdrop.getData()

					if ptr is not None:
						self["backdrop"].instance.setPixmap(ptr)

			else:
				self.downloadBackdrop()
		else:
			self.downloadBackdrop()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def resetCurrentImages(self):
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value + "/all/picreset.png"

		if self.viewParams["elements"]["poster"]["visible"]:
			if self.resetPoster:
				self["poster"].instance.setPixmapFromFile(ptr)

		if self.viewParams["elements"]["backdrop"]["visible"] and not self.usedStillPicture:
			if self.resetBackdrop:
				self.resetBackdropImage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadPoster(self):
		printl("", self, "S")
		printl("self.posterWidth:" + str(self.posterWidth), self, "D")
		printl("self.posterHeight:" + str(self.posterHeight), self, "D")
		printl("self.poster_postfix:" + str(self.poster_postfix), self, "D")
		printl("self.image_prefix:" + str(self.image_prefix), self, "D")

		download_url = self.details["thumb"]
		if download_url:
			download_url = download_url.replace('&width=999&height=999', '&width=' + self.posterWidth + '&height=' + self.posterHeight)
			printl( "download url " + download_url, self, "D")

		if not download_url:
			printl("no pic data available", self, "D")
		else:
			printl("starting download", self, "D")
			server = self.plexInstance.getServerFromURL(download_url)
			authHeader = self.plexInstance.get_hTokenForServer(server)
			printl("header: " + str(authHeader), self, "D")
			downloadPage(str(download_url), self.whatPoster, headers=authHeader).addCallback(lambda _: self.showPoster(forceShow = True))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadBackdrop(self):
		printl("", self, "S")
		printl("self.backdropWidth:" + str(self.backdropWidth), self, "D")
		printl("self.backdropHeight:" + str(self.backdropHeight), self, "D")
		printl("self.backdrop_postfix:" + str(self.backdrop_postfix), self, "D")
		printl("self.image_prefix:" + str(self.image_prefix), self, "D")

		download_url = self.details["fanart_image"]
		if download_url:
			download_url = download_url.replace('&width=999&height=999', '&width=' + self.backdropWidth + '&height=' + self.backdropHeight)
			printl( "download url " + download_url, self, "D")

		if not download_url:
			printl("no pic data available", self, "D")
		else:
			printl("starting download", self, "D")
			server = self.plexInstance.getServerFromURL(download_url)
			authHeader = self.plexInstance.get_hTokenForServer(server)
			printl("header: " + str(authHeader), self, "D")
			downloadPage(download_url, self.whatBackdrop, headers=authHeader).addCallback(lambda _: self.showBackdrop(forceShow = True))

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def finishLayout(self):
		"""
		adds buttons pics from xml and handles fastScrollMode function
		"""
		printl("", self, "S")

		printl("guiElements_key_red" +self.guiElements["key_red"], self, "D")

		# first we set the pics for buttons
		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])
		self["btn_yellow"].instance.setPixmapFromFile(self.guiElements["key_yellow"])
		self["btn_blue"].instance.setPixmapFromFile(self.guiElements["key_blue"])

		self.toggleFastScroll()

		self["txt_exit"].setText("Exit")

		# if we are in fastScrollMode we remove some gui elements
		self.resetGuiElementsInFastScrollMode()

		# now we set seen/unseen pictures
		self.getSeenVisus()

		# enable audio and subtitles information if we have transcoding active
		if self.serverConfig.playbackType.value == "1":
			printl("audio: " + str(self.viewParams["elements"]["audio"]),self, "D")
			if self.viewParams["elements"]["audio"]["visible"]:
				self.toggleElementVisibilityWithLabel("audio")
			else:
				self.toggleElementVisibilityWithLabel("audio", "hide")

			if self.viewParams["elements"]["subtitles"]["visible"]:
				self.toggleElementVisibilityWithLabel("subtitles")
			else:
				self.toggleElementVisibilityWithLabel("subtitles", "hide")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getSeenVisus(self):
		printl("", self, "S")

		self.seenPic = loadPicture(str(self.guiElements["seenPic"]))
		printl("self.seenPic: " + str(self.seenPic), self, "D")

		self.startedPic = loadPicture(str(self.guiElements["startedPic"]))
		printl("self.startedPic: " + str(self.startedPic), self, "D")

		self.unseenPic = loadPicture(str(self.guiElements["unseenPic"]))
		printl("self.unseenPic: " + str(self.unseenPic), self, "D")

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def processGuiElements(self, myType=None):
		printl("", self, "S")

		printl("myType: " +  str(myType), self, "D")

		# this is always the case when the view starts the first time
		# in this case no need for look for subviews
		if myType is None:
			for element in self.viewParams["elements"]:
				printl("element:" + str(element), self, "D")
				visibility = self.viewParams["elements"][element]["visible"]

				self.alterGuiElementVisibility(element, visibility)

				# we do not alter positions here because this should be done in the skin.xml because we are the first view except ...
				if str(self.libraryName) == "episodes":
					params = self.viewParams["elements"][element]
					if "xCoord" in params and "yCoord" in params:
						xCoord = params.get("xCoord")
						yCoord = params.get("yCoord")
						self.alterGuiElementPosition(element,xCoord, yCoord)

		# now we check if we are in a special subView with its own params
		elif "subViews" in self.viewParams:
			if myType in self.viewParams["subViews"]:
				subViewParams = self.viewParams["subViews"][myType]
				printl("subViewParams: " + str(subViewParams), self, "D")

				self.viewChangeStorage[self.viewStep] = {}
				for element in subViewParams:
					printl("element: " + str(element), self, "D")
					self.viewChangeStorage[self.viewStep][element] = {}
					params = subViewParams[element]
					if "visible" in params:
						visibility = params.get("visible")
						self.viewChangeStorage[self.viewStep][element]["visible"] = not visibility
						self.alterGuiElementVisibility(element, visibility)

					if "xCoord" in params and "yCoord" in params:
						xCoord = params.get("xCoord")
						yCoord = params.get("yCoord")
						position = self[element].getPosition()
						self.viewChangeStorage[self.viewStep][element]["xCoord"] = position[0]
						self.viewChangeStorage[self.viewStep][element]["yCoord"] = position[1]
						self.alterGuiElementPosition(element,xCoord, yCoord)

				printl("viewChangeStorage:" + str(self.viewChangeStorage), self, "D")
		# it not we use the params form the main view
		else:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def restoreElementsInViewStep (self):
		"""
		restores gui elements according to the self.viewChangeStorage dict and self.viewStep
		"""
		printl("", self, "S")
		printl("viewChangeStorage:" + str(self.viewChangeStorage), self, "D")

		# +1 is the correction for viewStep
		key = int(self.viewStep)+1
		printl("key:" + str(key), self, "D")

		# key 0 is when we leave the view there will never be data to change ;-)
		if key != 0 and key in self.viewChangeStorage:
			subViewParams = self.viewChangeStorage[key]
			for element in subViewParams:
				printl("element: " + str(element), self, "D")
				params = subViewParams[element]
				if "visible" in params:
					visibility = params.get("visible")
					self.alterGuiElementVisibility(element, visibility)

				if "xCoord" in params and "yCoord" in params:
					xCoord = params.get("xCoord")
					yCoord = params.get("yCoord")

					self.alterGuiElementPosition(element,xCoord, yCoord)
		else:
			printl("key is 0 or not in storage ...", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def alterGuiElementVisibility(self, element, visibility):
		printl("", self, "C")
		printl("element: " + str(element), self, "D")
		printl("visibility: " + str(visibility), self, "D")
		if visibility:
			self[element].show()
			try:
				self[element+"Label"].show()

				# additional changes
				if element == "backdrop":
					self[element+"Video"].show()

			except Exception, e:
				printl("Exception: " + str(e), self, "D")

			try:
				if element == "btn_red" or element == "green" or element == "btn_yellow" or element == "btn_blue":
					self[element + "Text"].show()
			except Exception, e:
				printl("Exception: " + str(e), self, "D")

		else:
			self[element].hide()
			try:
				self[element+"Label"].hide()

				# additional changes
				if element == "backdrop":
					self[element+"Video"].hide()
			except Exception, e:
				printl("Exception: " + str(e), self, "D")

			try:
				if element == "btn_red" or element == "green" or element == "btn_yellow" or element == "btn_blue":
					self[element + "Text"].hide()
			except Exception, e:
				printl("Exception: " + str(e), self, "D")

		printl("", self, "C")

#===========================================================================
	#
	#===========================================================================
	def alterGuiElementPosition(self, element, xCoord, yCoord):
		printl("", self, "C")

		elementPostion = self[element].getPosition()
		xElement = elementPostion[0]
		yElement = elementPostion[1]

		try:
			labelPosition = self[element+"Label"].getPosition()
			xLabel = labelPosition[0]
			yLabel = labelPosition[1]
			xDiff = int(xLabel) - int(xElement)
			yDiff = int(yLabel) - int(yElement)
			printl("xDiff: " + str(xDiff), self, "D")
			printl("yDiff: " + str(yDiff), self, "D")
			newX = int(xCoord) - (int(xDiff)*-1)
			newY = int(yCoord) - (int(yDiff)*-1)
			printl("newX: " + str(newX), self, "D")
			printl("newY: " + str(newY), self, "D")
			self[element+"Label"].setPosition(newX, newY)
		except Exception, e:
			printl("error: " + str(e), self, "D")

		printl("element: " + str(element), self, "D")
		printl("xCoord: " + str(xCoord), self, "D")
		printl("yCoord: " + str(yCoord), self, "D")

		self[element].setPosition(xCoord, yCoord)

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def resetGuiElementsInFastScrollMode(self):
		printl("", self, "S")

		# lets hide them so that fastScroll does not show up old information
		self["rating_stars"].hide()
		self["codec"].hide()
		self["aspect"].hide()
		self["resolution"].hide()
		self["rated"].hide()
		self["sound"].hide()

		if not self.usedStillPicture:
			self.resetBackdropImage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def resetBackdropImage(self):
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value + "/all/picreset.png"
		self["backdrop"].instance.setPixmapFromFile(ptr)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleRatedPixmaps(self):
		printl("", self, "S")

		mpaa = self.details.get("contentRating", "unknown").upper()
		printl("contentRating: " + str(mpaa), self, "D")

		if mpaa == "PG-13" or mpaa == "TV-14":
			found = True
			self["rated"].setPixmapNum(0)

		elif mpaa == "PG" or mpaa == "TV-PG":
			found = True
			self["rated"].setPixmapNum(1)

		elif mpaa == "R" or mpaa == "14A":
			found = True
			self["rated"].setPixmapNum(2)

		elif mpaa == "NC-17" or mpaa == "TV-MA":
			found = True
			self["rated"].setPixmapNum(3)

		elif mpaa == "DE/0" or mpaa == "G":
			found = True
			self["rated"].setPixmapNum(4)

		elif mpaa == "NOT RATED" or mpaa == "DE/0" or mpaa == "G" or mpaa == "NR":
			found = True
			self["rated"].setPixmapNum(5)

		elif mpaa == "UNKNOWN" or mpaa == "UNKNOWN" or mpaa == "":
			found = False

		else:
			printl("we have a value but no match!! mpaa: " + str(mpaa), self, "I")
			found = False

		if found:
			self["rated"].show()
		else:
			self["rated"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleSoundPixmaps(self):
		printl("", self, "S")

		audio = self.details.get("audioCodec", "unknown").upper()
		printl("audioCodec: " + str(audio), self, "D")

		if audio == "DCA":
			found = True
			self["sound"].setPixmapNum(0)

		elif audio == "AC3":
			found = True
			self["sound"].setPixmapNum(1)

		elif audio == "MP2":
			found = True
			self["sound"].setPixmapNum(2)

		elif audio == "MP3":
			found = True
			self["sound"].setPixmapNum(3)

		elif audio == "UNKNOWN" or audio == "":
			found = False

		else:
			printl("we have a value but no match!! audio: " + str(audio), self, "I")
			found = False

		if found:
			self["sound"].show()
		else:
			self["sound"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleResolutionPixmaps(self):
		printl("", self, "S")

		resolution = self.details.get("videoResolution", "unknown").upper()
		printl("videoResolution: " + str(resolution), self, "D")

		if resolution == "1080":
			found = True
			self["resolution"].setPixmapNum(0)

		elif resolution == "720":
			found = True
			self["resolution"].setPixmapNum(1)

		elif resolution == "480" or resolution == "576" or resolution == "SD":
			found = True
			self["resolution"].setPixmapNum(2)

		elif resolution == "UNKNOWN" or resolution == "":
			found = False

		else:
			printl("we have a value but no match!! resolution: " + str(resolution), self, "I")
			found = False

		if found:
			self["resolution"].show()
		else:
			self["resolution"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleAspectPixmaps(self):
		printl("", self, "S")

		aspect = self.details.get("aspectRatio", "unknown").upper()
		printl("aspectRatio: " + str(aspect), self, "D")

		if aspect == "1.33":
			found = True
			self["aspect"].setPixmapNum(0)

		elif aspect == "1.66" or aspect == "1.78" or aspect == "1.85":
			found = True
			self["aspect"].setPixmapNum(1)

		elif aspect == "2.35": # 21:9
			found = True
			self["aspect"].setPixmapNum(1)

		elif aspect == "UNKNOWN" or aspect == "":
			found = False

		else:
			printl("we have a value but no match!! aspect: " + str(aspect), self, "I")
			found = False

		if found:
			self["aspect"].show()
		else:
			self["aspect"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleCodecPixmaps(self):
		printl("", self, "S")

		codec = self.details.get("videoCodec", "unknown").upper()
		printl("videoCodec: " + str(codec), self, "D")

		if codec == "VC1":
			found = True
			self["codec"].setPixmapNum(0)

		elif codec == "H264":
			found = True
			self["codec"].setPixmapNum(1)

		elif codec == "MPEG4":
			found = True
			self["codec"].setPixmapNum(2)

		elif codec == "MPEG2VIDEO":
			found = True
			self["codec"].setPixmapNum(3)

		elif codec == "UNKNOWN" or codec == "":
			found = False

		else:
			printl("we have a value but no match!! codec: " + str(codec), self, "I")
			found = False

		if found:
			self["codec"].show()
		else:
			self["codec"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handlePopularityPixmaps(self):
		printl("", self, "S")

		try:
			popularity = float(self.details["rating"])
		except Exception, e:
			popularity = 0
			printl("error in popularity " + str(e), self, "D")

		self["rating_stars"].setValue(int(popularity) * 10)
		self["rating_stars"].show()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getPictureInformationToLoad(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showFunctions(self, visible):
		printl("", self, "S")

		self.areFunctionsHidden = visible

		printl("", self, "C")
