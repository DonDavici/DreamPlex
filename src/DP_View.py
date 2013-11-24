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
import time
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

from DP_ViewFactory import getViews
from DP_Player import DP_Player

from DPH_Singleton import Singleton
from DPH_Arts import getPictureData

from __common__ import printl2 as printl, convertSize, loadPicture
from __plugin__ import getPlugins, Plugin
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
def getViewClass():
	"""
	@param: none
	@return: DP_View Class
	"""
	printl("", __name__, "S")

	printl("", __name__, "C")
	return DP_View

#===========================================================================
#
#===========================================================================
class DP_View(Screen, NumericalTextInput):

	ON_CLOSED_CAUSE_CHANGE_VIEW = 1
	ON_CLOSED_CAUSE_SAVE_DEFAULT = 2
	ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE = 3

	onNumberKeyLastChar             = "#"
	activeSort                      = ("Default", None, False)
	activeFilter                    = ("All", (None, False), "")
	onEnterPrimaryKeys              = None
	onLeavePrimaryKeyValuePair      = None
	onLeaveSelectKeyValuePair       = None
	currentKeyValuePair             = None

	currentShowIndex                = None
	currentSeasonIndex              = None
	currentMovieIndex               = None
	showMedia                       = False
	showDetail                      = False
	isDirectory                     = False

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

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, myFilter=None, cache=None):
		printl("", self, "S")
		Screen.__init__(self, session)
		self.myParams = viewName[3]
		NumericalTextInput.__init__(self)

		printl("cache: " + str(cache), self, "D")
		printl("viewName: "+ str(viewName), self, "I")
		printl("myParams: " + str(viewName[3]), self, "D")
		printl("libraryName: " + str(libraryName), self, "D")

		self.skinName = self.myParams["settings"]["screen"]
		printl("self.skinName: " + str(self.skinName), self, "D")
		self.useBackdropVideos = self.myParams["settings"]["backdropVideos"]
		self.select = select
		self.cache = cache
		self.onFirstExecSort = sort
		self.onFirstExecFilter = myFilter

		self.libraryName = libraryName
		self.loadLibrary = loadLibrary
		self.viewName = viewName
		self._playEntry = playEntry

		self.playerData = None

		self.setListViewElementsCount(viewName)

		self.usePicCache = config.plugins.dreamplex.usePicCache.value

		# Initialise library list
		myList = []
		self["listview"] = List(myList, True)

		self["number_key_popup"] = Label()
		self["number_key_popup"].hide()

		self.seenPng = None
		self.unseenPng = None

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
			"green":	  	(self.onKeyGreen, ""),
			"yellow":		(self.onKeyYellow, ""),
			"blue":			(self.onKeyBlue, ""),
			"text":			(self.onKeyText, ""),
			"red_long":		(self.onKeyRedLong, ""),
			#"green_long":	(self.onKeyGreenLong, ""),
			#"yellow_long":	(self.onKeyYellowLong, ""),
			"blue_long":	(self.onKeyBlueLong, ""),

			"bouquet_up":	(self.bouquetUp, ""),
			"bouquet_down":	(self.bouquetDown, ""),

			"1":			(self.onKey1, ""),
			"2":			(self.onKey2, ""),
			"3":			(self.onKey3, ""),
			"4":			(self.onKey4, ""),
			"5":			(self.onKey5, ""),
			"6":			(self.onKey6, ""),
			"7":			(self.onKey7, ""),
			"8":			(self.onKey8, ""),
			"9":			(self.onKey9, ""),
			"0":			(self.onKey0, ""),

		}, -2)

		# For number key input
		self.setUseableChars(u' 1234567890abcdefghijklmnopqrstuvwxyz')

		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.onFirstExec)

		self.getGuiElements()

		# set navigation values
		#DP_View.setListViewElementsCount("DPS_ViewList")

		# get needed config parameters
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		self.playTheme = config.plugins.dreamplex.playTheme.value
		self.fastScroll = config.plugins.dreamplex.fastScroll.value

		# get data from plex library
		self.image_prefix = Singleton().getPlexInstance().getServerName().lower()

		# init skin elements
		self["functionsContainer"]  = Label()

		self["btn_red"]			= Pixmap()
		self["btn_blue"]		= Pixmap()
		self["btn_yellow"]		= Pixmap()
		self["btn_zero"]		= Pixmap()
		self["btn_nine"]		= Pixmap()
		self["btn_pvr"]			= Pixmap()
		self["btn_menu"]		= Pixmap()

		self["txt_red"]			= Label()
		self["txt_filter"]		= Label()
		self["txt_yellow"]		= Label()
		self["txt_blue"]		= Label()
		self["txt_blue"].setText(_("toogle View ") + _("(current 'Default')"))


		if self.fastScroll:
			self["txt_yellow"].setText("fastScroll = On")
		else:
			self["txt_yellow"].setText("fastScroll = Off")

		self["txt_pvr"] = Label()
		self["txt_pvr"].setText("load additional data")

		self["txt_menu"] = Label()
		self["txt_menu"].setText("show media functions")

		self["sound"] = MultiPixmap()

		self["resolution"] = MultiPixmap()

		self["aspect"] = MultiPixmap()

		self["codec"] = MultiPixmap()

		self["rated"] = MultiPixmap()

		self["title"] = Label()
		self["grandparentTitle"] = Label()
		self["grandparentTitle"].setText("huraa")

		self["tag"] = Label()

		self["shortDescription"] = ScrollLabel()

		self["subtitles"] = Label()
		self["subtitlesLabel"] = Label()
		self["subtitlesLabel"].setText("Subtitles:")

		self["audio"] = Label()
		self["audioLabel"] = Label()
		self["audioLabel"].setText("Audio:")

		self["genre"] = Label()
		self["genreLabel"] = Label()
		self["genreLabel"].setText("Genre:")

		self["year"] = Label()
		self["yearLabel"] = Label()
		self["yearLabel"].setText("Year:")

		self["runtime"] = Label()
		self["runtimeLabel"] = Label()
		self["runtimeLabel"].setText("Runtime:")

		self["total"] = Label()

		self["current"] = Label()

		self["backdrop"] = Pixmap()
		self["backdropVideo"] = Pixmap() # this is just to avoid greenscreen, maybe we find a better way
		self["backdroptext"] = Label()

		self["poster"] = Pixmap()
		self["postertext"] = Label()

		self["rating_stars"] = ProgressBar()

		# Poster
		self.EXpicloadPoster = ePicLoad()
		self.poster_postfix = self.myParams["elements"]["poster"]["postfix"]
		self.posterHeight = self.myParams["elements"]["poster"]["height"]
		self.posterWidth = self.myParams["elements"]["poster"]["width"]

		# Backdrops
		self.EXpicloadBackdrop = ePicLoad()
		self.backdrop_postfix = self.myParams["elements"]["backdrop"]["postfix"]
		self.backdropHeight = self.myParams["elements"]["backdrop"]["height"]
		self.backdropWidth = self.myParams["elements"]["backdrop"]["width"]

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
		self.onLayoutFinish.append(self.finishLayout)
		self.onLayoutFinish.append(self.processGuiElements)

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
	def getGuiElements(self):
		printl("", self, "S")

		tree = Singleton().getSkinParamsInstance()

		self.guiElements = {}
		for guiElement in tree.findall('guiElement'):
			name = str(guiElement.get('name'))
			path = str(guiElement.get('path'))
			self.guiElements[name] = path

		printl("guiElements: " + str(self.guiElements), self, "D")
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setListViewElementsCount(self, viewName):
		printl("", self, "S")

		multiView = True

		if multiView:
			params = viewName[3]
			self.itemsPerPage = int(params["settings"]['itemsPerPage'])
		else:
			tree = Singleton().getSkinParamsInstance()
			for view in tree.findall('view'):
				if view.get('name') == str(viewName[1]):
					self.itemsPerPage = int(view.get('itemsPerPage'))

		printl("self.itemsPerPage: " + str(self.itemsPerPage), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onFirstExec(self):
		printl("", self, "S")

		if self.select is None: # Initial Start of View, select first entry in list
			#sort = False
			#if self.onFirstExecSort is not None:
			#	self.activeSort = self.onFirstExecSort
			#	sort = True
			#myFilter = False
			#if self.onFirstExecFilter is not None:
			#	self.activeFilter = self.onFirstExecFilter
			#	myFilter = True
			# lets override this
			myFilter = True
			sort = True

			self._load(ignoreSort=sort, ignoreFilter=myFilter)
			self.refresh()
		else: # changed views, reselect selected entry
			printl("self.select: " +  str(self.select), self, "D")
			sort = False
			if self.onFirstExecSort is not None:
				self.activeSort = self.onFirstExecSort
				sort = True
			myFilter = False
			if self.onFirstExecFilter is not None:
				self.activeFilter = self.onFirstExecFilter
				myFilter = True

			self._load(self.select[0], ignoreSort=sort, ignoreFilter=myFilter)
			keys = self.select[1].keys()
			listViewList = self["listview"].list
			for i in range(len(listViewList)):
				entry = listViewList[i]
				found = True
				for key in keys:
					if entry[1][key] != self.select[1][key]:
						found = False
						break
				if found:
					self["listview"].setIndex(i)
					break
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
	def onKey1(self):
		printl("", self, "S")

		self.onNumberKey(1)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey2(self):
		printl("", self, "S")

		self.onNumberKey(2)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey3(self):
		printl("", self, "S")

		self.onNumberKey(3)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey4(self):
		printl("", self, "S")

		self.onNumberKey(4)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey5(self):
		printl("", self, "S")

		self.onNumberKey(5)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey6(self):
		printl("", self, "S")

		self.onNumberKey(6)

		printl("", self, "C")


	#===========================================================================
	#
	#===========================================================================
	def onKey7(self):
		printl("", self, "S")

		self.onNumberKey(7)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey8(self):
		printl("", self, "S")

		self.onNumberKey(8)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey9(self):
		printl("", self, "S")

		self.onNumberKey(9)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey0(self):
		printl("", self, "S")

		self.onNumberKey(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNumberKey(self, number):
		printl("", self, "S")

		printl(str(number), self, "I")

		key = self.getKey(number)
		if key is not None:
			keyvalue = key.encode("utf-8")
			if len(keyvalue) == 1:
				self.onNumberKeyLastChar = keyvalue[0].upper()
				self.onNumberKeyPopup(self.onNumberKeyLastChar, True)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNumberKeyPopup(self, value, visible):
		printl("", self, "S")

		if visible:
			self["number_key_popup"].setText(value)
			self["number_key_popup"].show()
		else:
			self["number_key_popup"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def timeout(self):
		"""
		onNumberKeyTimeout
		"""
		printl("", self, "S")

		printl(self.onNumberKeyLastChar, self, "I")
		if self.onNumberKeyLastChar != ' ':
			self.activeFilter = ('Abc', ('title', False, 1), self.onNumberKeyLastChar)
		else:
			self.activeFilter = ("All", (None, False), ("All", ))
		self.sort()
		self.filter()

		self.refresh()

		self.onNumberKeyPopup(self.onNumberKeyLastChar, False)
		NumericalTextInput.timeout(self)

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

		self.showFunctions(not self.areFunctionsHidden)

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

		self.showMedia = True
		self.resetGuiElements = True
		self.refresh()

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

		self.onToggleSort()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRedLong(self):
		printl("", self, "S")

		self.onChooseSort()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyGreen(self):
		printl("", self, "S")

		self.onToggleFilter()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyGreenLong(self):
		printl("", self, "S")

		self.onChooseFilter()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyYellow(self):
		printl("", self, "S")

		if self.fastScroll:
			self.fastScroll = False
			self["txt_yellow"].setText("fastScroll = Off")
		else:
			self.fastScroll = True
			self["txt_yellow"].setText("fastScroll = On")
			self.resetGuiElements = True

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyBlue(self):
		printl("", self, "S")

		self.onToggleView()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyBlueLong(self):
		printl("", self, "S")

		self.displayViewMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onToggleSort(self):
		printl("", self, "S")

		for i in range(len(self.onSortKeyValuePair)):
			if self.activeSort[1] == self.onSortKeyValuePair[i][1]:
				if (i+1) < len(self.onSortKeyValuePair):
					self.activeSort = self.onSortKeyValuePair[i + 1]
				else:
					self.activeSort = self.onSortKeyValuePair[0]
				break

		self.sort()
		self.filter()
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onChooseSortCallback(self, choice):
		printl("", self, "S")

		if choice is not None:
			self.activeSort = choice[1]
			self.sort()
			self.filter()
			self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onChooseSort(self):
		printl("", self, "S")

		menu = []
		for e in self.onSortKeyValuePair:
			menu.append((_(e[0]), e, ))
		selection = 0
		for i in range(len(self.onSortKeyValuePair)):
			if self.activeSort[1] == self.onSortKeyValuePair[i][1]:
				selection = i
				break
		self.session.openWithCallback(self.onChooseSortCallback, ChoiceBox, title=_("Select sort"), list=menu, selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onToggleFilter(self):
		printl("", self, "S")

		for i in range(len(self.onFilterKeyValuePair)):
			if self.activeFilter[1][0] == self.onFilterKeyValuePair[i][1][0]:
				# Genres == Genres

				# Try to select the next genres subelement
				found = False
				y = None
				subelements = self.onFilterKeyValuePair[i][2]
				for j in range(len(subelements)):
					if self.activeFilter[2] == subelements[j]:
						# Action == Action
						if (j+1) < len(subelements):
							y = subelements[j + 1]
							found = True
							break

				if found:
					x = self.onFilterKeyValuePair[i]
					self.activeFilter = (x[0], x[1], y, )
				else:
					# If we are at the end of all genres subelements select the next one
					if (i+1) < len(self.onFilterKeyValuePair):
						x = self.onFilterKeyValuePair[i + 1]
					else:
						x = self.onFilterKeyValuePair[0]
					self.activeFilter = (x[0], x[1], x[2][0], )

				break

		self.sort()
		self.filter()
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onChooseFilterCallback(self, choice):
		printl("", self, "S")

		if choice is not None:
			self.activeFilter = choice[1]
			self.sort()
			self.filter()
			self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onChooseFilter(self):
		printl("", self, "S")

		menu = []

		selection = 0
		counter = 0

		for i in range(len(self.onFilterKeyValuePair)):
			x = self.onFilterKeyValuePair[i]
			subelements = self.onFilterKeyValuePair[i][2]
			for j in range(len(subelements)):
				y = subelements[j]
				text = "%s: %s" % (_(x[0]), _(y))
				menu.append((text, (x[0], x[1], y, )))
				if self.activeFilter[1][0] == self.onFilterKeyValuePair[i][1][0]:
					if self.activeFilter[2] == subelements[j]:
						selection = counter
				counter += 1

		self.session.openWithCallback(self.onChooseFilterCallback, ChoiceBox, title=_("Select filter"), list=menu, selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onToggleView(self, forceUpdate=False):
		printl("", self, "S")

		select = None
		selection = self["listview"].getCurrent()
		if selection is not None:
			params = {}
			printl( "self.onEnterPrimaryKeys:" + str(self.onEnterPrimaryKeys), self, "D")
			for key in self.onEnterPrimaryKeys:
				if key != "play":
					params[key] = selection[1][key]
			select = (self.currentKeyValuePair, params)

		if forceUpdate:
			self.close((DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE, select, self.activeSort, self.activeFilter))
		else:
			self.close((DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW, select, self.activeSort, self.activeFilter))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onChooseView(self):
		printl("", self, "S")

		menu = getViews(self.libraryName)
		selection = 0
		for i in range(len(menu)):
			if self.viewName[1] == menu[i][1]:
				selection = i
				break
		self.session.openWithCallback(self.onChooseViewCallback, ChoiceBox, title=_("Select view"), list=menu, selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onChooseViewCallback(self, choice):
		printl("", self, "S")

		if choice is not None:
			select = None
			selection = self["listview"].getCurrent()
			if selection is not None:
				params = {}
				printl( "self.onEnterPrimaryKeys:" + str(self.onEnterPrimaryKeys), self, "D")
				for key in self.onEnterPrimaryKeys:
					if key != "play":
						params[key] = selection[1][key]
				select = (self.currentKeyValuePair, params)
			self.close((DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW, select, self.activeSort, self.activeFilter, choice[1]))

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
			details		= selection[1]
			extraData	= selection[2]
			#image		= selection[3]

			#details
			viewMode	= details['viewMode']
			self.viewMode = self.details ["viewMode"]

			server		= details['server']
			printl("currentViewMode: " +str(viewMode), self, "D")
			printl("server: " +str(server), self, "D")

			#extraData
			url_path	= extraData['key']
			printl("url_path: " +str(url_path), self, "D")

			if viewMode == "ShowSeasons":
				self.viewStep += 1
				printl("viewMode -> ShowSeasons", self, "I")

				params = {"viewMode": viewMode, "url": "http://" + server + url_path}

				self.currentSeasonsParams = params
				self.currentShowIndex = self["listview"].getIndex()

				self._load(params)

			elif viewMode == "ShowEpisodes":
				self.viewStep += 1
				printl("viewMode -> ShowEpisodes", self, "I")

				params = {"viewMode": viewMode, "url": "http://" + server + url_path}

				self.currentEpisodesParams = params
				self.currentSeasonIndex = self["listview"].getIndex()

				self._load(params)

			elif viewMode == "play":
				printl("viewMode -> play", self, "I")
				self.playEntry(selection)

			elif viewMode == "directory":
				printl("viewMode -> directory", self, "I")

				params = {"viewMode": viewMode, "id": url_path}

				self.currentMovieParams = params
				self.currentMovieIndex = self["listview"].getIndex()

				self._load(params)

			else:
				printl("SOMETHING WENT WRONG", self, "W")

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showMediaDetail(self):
		printl("", self, "S")
		self.showDetail = True
		selection = self["listview"].getCurrent()

		if selection is not None:
			details			= selection[1]

			#details
			viewMode		= details['viewMode']

			if viewMode == "play":
				printl("viewMode -> play", self, "I")
				self.playEntry(selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		self.viewStep -= 1

		selectKeyValuePair = self.onLeaveSelectKeyValuePair
		printl("selectKeyValuePair: " + str(selectKeyValuePair), self, "D")

		if config.plugins.dreamplex.playTheme.value:
			printl("stoping theme playback", self, "D")
			self.session.nav.stopService()

		if selectKeyValuePair == "backToSeasons":
			self._load(self.currentSeasonsParams)
			self["listview"].setIndex(self.currentSeasonIndex)

		elif selectKeyValuePair == "backToShows":
			self._load()
			self["listview"].setIndex(self.currentShowIndex)

		elif selectKeyValuePair == "backToMovies":
			self._load()
			self["listview"].setIndex(self.currentMovieIndex)

		else:
			self.close()
			printl("", self, "C")
			return

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _load(self, params=None, ignoreSort=False, ignoreFilter=False):
		"""
			e.g.
			params = {}
			params["viewMode"] = viewMode
			params["url"] = "http://" + server + url_path
			params["index"] = int
		"""
		printl("", self, "S")
		printl("params: " + str(params), self, "D")
		printl("cache: " + str(self.cache), self, "D")

		if params is None:
			params = {}
			params["viewMode"] = None

		params["cache"] = self.cache

		library = self.loadLibrary(params)
		#library for e.g. = return (library, ("viewMode", "ratingKey", ), None, "backToShows", sort, filter)
		# (libraryArray, onEnterPrimaryKeys, onLeavePrimaryKeys, onLeaveSelectEntry

		self.listViewList = library[0]

		# we need to do this because since we save cache via pickle the seen pic object cant be saved anymore
		# so we implement it here
		self.newList = []
		for listView in self.listViewList:
			#printl("seenVisu location: " + str(listView[4]), self, "D")
			if listView is not None:
				seenVisu = loadPicture(listView[4])
				#printl("loading seenVisu ... (" + str(seenVisu) + ")" , self, "D")
				content = (listView[0], listView[1], listView[2], listView[3], seenVisu ,listView[5])
				self.newList.append(content)

		self.listViewList = self.newList
		self.origListViewList = self.newList

		self.onEnterPrimaryKeys = library[1]
		printl("onEnterPrimaryKeys: " + str(library[1]), self, "D")

		self.onLeavePrimaryKeyValuePair = library[2]
		printl("onLeavePrimaryKeyValuePair: " + str(library[2]), self, "D")

		self.onLeaveSelectKeyValuePair = library[3]
		printl("onLeaveSelectKeyValuePair: " + str(library[3]), self, "D")

		self.onSortKeyValuePair = library[4]
		printl("onSortKeyValuePair: " + str(library[4]), self, "D")

		self.onFilterKeyValuePair = library[5]
		printl("onFilterKeyValuePair: " + str(library[5]), self, "D")

		if len(library) >= 7:
			self.libraryFlags = library[6]
		else:
			self.libraryFlags = {}

		if ignoreSort is False:
			# After changing the lsit always return to the default sort
			self.activeSort = self.onSortKeyValuePair[0]
			self.sort()

		if ignoreFilter is False:
			# After changing the lsit always return to the default filter
			x = self.onFilterKeyValuePair[0]
			self.activeFilter = (x[0], x[1], x[2][0], )
			#self.listViewList = self.filter()

		self.updateList()
		printl("", self, "C")

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
	def resetList(self):
		printl("", self, "S")

		self.listViewList = self.origListViewList

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def sort(self):
		printl("", self, "S")
		#printl("listViewList: " + str(self.listViewList), self, "D")

		text = "toogle Sorting (sorted %s)" % (_(self.activeSort[0]))
		self["txt_red"].setText(text)
		self.areFunctionsHidden = True

		try:
			if self.activeSort[1] is None:
				printl("sorting by default", self, "D")
				self.listViewList.sort(key=lambda x: x[0], reverse=self.activeSort[2])
				self.resetList()
				self.updateList()
			else:
				printl("sorting by value in selection: " + str(self.activeSort[1]), self, "D")
				self.listViewList.sort(key=lambda x: x[1][self.activeSort[1]], reverse=self.activeSort[2])
		except Exception, ex:
			printl("Exception(" + str(ex) + ")", self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def filter(self):
		printl("", self, "S")

		printl( "self.activeFilter: " + str(self.activeFilter), self, "D")

		if len(self.activeFilter[2]) > 0:
			text = "set Filter (set to '%s')" % (_(self.activeFilter[2]))
		else:
			text = "set Filter (set to '%s')" % (_(self.activeFilter[0]))

		self["txt_filter"].setText(text)

		if self.activeFilter[1][0] is None:
			listViewList = self.origListViewList
		else:

			testLength = None
			if len(self.activeFilter[1]) >= 3:
				testLength = self.activeFilter[1][2]

			if self.activeFilter[1][1]:
				listViewList = [x for x in self.origListViewList if self.activeFilter[2] in x[1][self.activeFilter[1][0]]]
			else:
				if testLength is None:
					listViewList = [x for x in self.origListViewList if x[1][self.activeFilter[1][0]] == self.activeFilter[2]]
				else:
					listViewList = [x for x in self.origListViewList if x[1][self.activeFilter[1][0]].strip()[:testLength] == self.activeFilter[2].strip()[:testLength]]
		self.listViewList = listViewList
		self.updateList()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setText(self, name, value, ignore=False, what=None):
		#printl("", self, "S")
		#printl("setting text for " + str(name) + " with value " + str(value), self, "D")
		# todo lets check this. seems to be some kind of too much
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
			viewMode = self.selection[1]['viewMode']
			self.selection = self.selection

			self.isDirectory = False
			if viewMode == "directory":
				self.isDirectory = True

		self._refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _refresh(self):
		printl("", self, "S")

		printl("resetGuiElements: " + str(self.resetGuiElements), self, "D")
		printl("self.myParams: " + str(self.myParams), self, "D")

		if self.resetGuiElements:
			self.resetGuiElementsInFastScrollMode()

		self.resetCurrentImages()

		printl("showMedia: " + str(self.showMedia), self, "D")

		printl("isDirectory: " + str(self.isDirectory), self, "D")

		if self.selection is not None:
			self.details 		= self.selection[1]
			self.extraData 		= self.selection[2]
			self.context		= self.selection[3]

			if self.isDirectory:
				pass
			else:
				# lets get all data we need to show the needed pictures
				# we also check if we want to play
				self.getPictureInformationToLoad()

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
					if self.startPlaybackNow:
						self.startThemePlayback()

				self.setText("title", self.details.get("title", " "))
				self.setText("grandparentTitle", self.details.get("grandparentTitle", " "))
				self.setText("tag", self.details.get("tagline", " ").encode('utf8'), True)
				self.setText("year", str(self.details.get("year", " - ")))
				self.setText("genre", str(self.details.get("genre", " - ").encode('utf8')))
				self.setText("subtitles", str(self.extraData.get("selectedSub", " - ").encode('utf8')))
				self.setText("audio", str(self.extraData.get("selectedAudio", " - ").encode('utf8')))
				self.setText("runtime", str(self.details.get("runtime", " - ")))
				self.setText("shortDescription", str(self.details.get("summary", " ").encode('utf8')))

				if self.fastScroll == False or self.showMedia == True:
					# handle all pixmaps
					self.handlePopularityPixmaps()
					self.handleCodecPixmaps()
					self.handleAspectPixmaps()
					self.handleResolutionPixmaps()
					self.handleRatedPixmaps()
					self.handleSoundPixmaps()

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

				# toggle visible state of function box
				self.showFunctions(False)

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
	def playEntry(self, selection):
		printl("", self, "S")

		self.media_id = selection[1]['ratingKey']
		server = selection[1]['server']

		self.count, self.options, self.server = Singleton().getPlexInstance().getMediaOptionsToPlay(self.media_id, server, False)

		self.selectMedia(self.count, self.options, self.server)

		printl("", self, "C")

	#===========================================================
	#
	#===========================================================
	def selectMedia(self, count, options, server ):
		printl("", self, "S")

		#if we have two or more files for the same movie, then present a screen
		self.options = options
		self.server = server
		self.dvdplayback=False

		if count > 1:
			printl("we have more than one playable part ...", self, "I")
			indexCount=0
			functionList = []

			for items in self.options:
				printl("item: " + str(items), self, "D")
				if items[1] is not None:
					name=items[1].split('/')[-1]
				else:
					size = convertSize(int(items[3]))
					duration = time.strftime('%H:%M:%S', time.gmtime(int(items[4])))
					# this is the case when there is no information of the real file name
					name = items[0] + " (" + items[2] + " / " + size + " / " + duration + ")"

				printl("name " + str(name), self, "D")
				functionList.append((name ,indexCount, ))
				indexCount+=1

			self.session.openWithCallback(self.setSelectedMedia, ChoiceBox, title=_("Select media to play"), list=functionList)

		else:
			self.setSelectedMedia()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setSelectedMedia(self, choice=None):
		printl("", self, "S")
		result = 0
		printl("choice: " + str(choice), self, "D")

		if choice is not None:
			result = int(choice[1])

		printl("result: " + str(result), self, "D")

		self.mediaFileUrl = Singleton().getPlexInstance().mediaType({'key': self.options[result][0], 'file' : self.options[result][1]}, self.server)

		self.playSelectedMedia()

		printl("We have selected media at " + self.mediaFileUrl, self, "I")
		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def playSelectedMedia(self):
		printl("", self, "S")

		self.playerData = Singleton().getPlexInstance().playLibraryMedia(self.media_id, self.mediaFileUrl)

		resumeStamp = self.playerData['resumeStamp']
		printl("resumeStamp: " + str(resumeStamp), self, "I")

		if self.showDetail:
			currentFile = "Location:\n " + str(self.playerData['currentFile'])
			self.session.open(MessageBox,_("%s") % currentFile, MessageBox.TYPE_INFO)
			self.showDetail = False
		else:
			if self.playerData['fallback']:
				message = "Sorry I didn't find the file on the provided locations"
				locations = "Location:\n " + self.playerData['locations']
				suggestion = "Please verify you direct local settings"
				fallback = "I will now try to play the file via transcode."
				self.session.openWithCallback(self.checkResume, MessageBox,_("Warning:\n%s\n\n%s\n\n%s\n\n%s") % (message, locations, suggestion, fallback), MessageBox.TYPE_ERROR)
			else:
				self.checkResume(resumeStamp)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkResume(self, resumeStamp):
		printl("", self, "S")

		if resumeStamp > 0:
			self.session.openWithCallback(self.handleResume, MessageBox, _(" This file was partially played.\n\n Do you want to resume?"), MessageBox.TYPE_YESNO)

		else:
			self.session.open(DP_Player, self.playerData)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleResume(self, confirm):
		printl("", self, "S")

		if confirm:
			self.session.open(DP_Player, self.playerData, True)

		else:
			self.session.open(DP_Player, self.playerData)

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

		self.setText("total", _("Total:") + ' ' + str(itemsTotal))
		self.setText("current", _("Pages:") + ' ' + str(pageCurrent) + "/" + str(pageTotal))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setDefaultView(self):
		printl("", self, "S")

		select = None
		selection = self["listview"].getCurrent()
		if selection is not None:
			primaryKeyValuePair = {}
			printl( "self.onEnterPrimaryKeys: " + str(self.onEnterPrimaryKeys), self, "D")
			for key in self.onEnterPrimaryKeys:
				if key != "play":
					primaryKeyValuePair[key] = selection[1][key]
			select = (self.currentKeyValuePair, primaryKeyValuePair)
		self.close((DP_View.ON_CLOSED_CAUSE_SAVE_DEFAULT, select, self.activeSort, self.activeFilter))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def clearDefaultView(self):
		printl("", self, "S")

		self.close((DP_View.ON_CLOSED_CAUSE_SAVE_DEFAULT, ))

		printl("", self, "C")


	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenu(self):
		printl("", self, "S")

		functionList = []

		functionList.append((_("Mark media unwatched"), Plugin("View", fnc=self.markUnwatched), ))
		functionList.append((_("Mark media watched"), Plugin("View", fnc=self.markWatched), ))
		functionList.append((_("Initiate Library refresh"), Plugin("View", fnc=self.initiateRefresh), ))
		functionList.append((_("Show media details"), Plugin("View", fnc=self.showMediaDetail), ))
		functionList.append((_("Refresh this section"), Plugin("View", fnc=self.refreshSection), ))
		#functionList.append((_("Delete media from Library"), Plugin("View", fnc=self.deleteFromLibrary), ))

		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, title=_("Media Functions"), list=functionList)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def refreshSection(self):
		printl("", self, "S")

		self.onToggleView(forceUpdate=True)

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

			sub_id = item.get('id', "")
			languageCode = item.get('languageCode', "")
			part_id = item.get('partid', "")

			functionList.append((name, media_id, languageCode, sub_id, server, part_id, selected))

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

		Singleton().getPlexInstance().doRequest(self.unseenUrl)
		self.showMessage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def markWatched(self):
		printl("", self, "S")

		Singleton().getPlexInstance().doRequest(self.seenUrl)
		self.showMessage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initiateRefresh(self):
		printl("", self, "S")

		Singleton().getPlexInstance().doRequest(self.refreshUrl)
		self.showMessage()

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
			self.showMessage()
		else:
			self.session.open(MessageBox,_("Deleting aborted!"), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showMessage(self):
		printl("", self, "S")

		self.session.open(MessageBox,_("You have to reenter the section to see the changes!"), MessageBox.TYPE_INFO, timeout = 5)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayViewMenu(self):
		printl("", self, "S")

		pluginList = []

		pluginList.append((_("Set view as default"), Plugin("View", fnc=self.setDefaultView), ))
		pluginList.append((_("Clear default view"), Plugin("View", fnc=self.clearDefaultView), ))

		plugins = getPlugins(where=Plugin.MENU_MOVIES_PLUGINS)
		for plugin in plugins:
			pluginList.append((plugin.name, plugin, ))

		if len(pluginList) == 0:
			pluginList.append((_("No plugins available"), None, ))

		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, title=_("Options"), list=pluginList)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	#noinspection PyUnusedLocal
	def pluginCallback(self, args=None):
		printl("", self, "S")

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		selection = self["listview"].getCurrent()
		if selection is not None:
			if choice[1].start:
				if choice[1].supportStillPicture:
					self.session.open(choice[1].start, selection[1])
				else:
					self.session.openWithCallback(self.pluginCallback, choice[1].start, selection[1])

			elif choice[1].fnc:
				printl("here", self, "D")
				choice[1].fnc()
				if choice[1].supportStillPicture is False and self.has_key("backdrop"):
					printl("there", self, "D")
					self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayAudioMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		printl("choice" + str(choice), self, "D")

		Singleton().getPlexInstance().setAudioById(choice[4], choice[3], choice[2], choice[5])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displaySubtitleMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		printl("choice" + str(choice), self, "D")

		Singleton().getPlexInstance().setSubtitleById(choice[4], choice[3], choice[2], choice[5])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startThemePlayback(self):
		printl("", self, "S")

		printl("start pĺaying theme", self, "I")
		accessToken = Singleton().getPlexInstance().get_aTokenForServer()#g_myplex_accessToken
		theme = self.extraData["theme"]
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
			if fileExists(getPictureData(self.details, self.image_prefix, self.poster_postfix, self.usePicCache)):

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
			if fileExists(getPictureData(self.details, self.image_prefix, self.backdrop_postfix, self.usePicCache)):

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

		if self.myParams["elements"]["poster"]["visible"]:
			if self.resetPoster:
				self["poster"].instance.setPixmapFromFile(ptr)

		if self.myParams["elements"]["backdrop"]["visible"] and not self.usedStillPicture:
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

		download_url = self.extraData["thumb"]
		if download_url:
			download_url = download_url.replace('&width=999&height=999', '&width=' + self.posterWidth + '&height=' + self.posterHeight)
			printl( "download url " + download_url, self, "D")

		if not download_url:
			printl("no pic data available", self, "D")
		else:
			printl("starting download", self, "D")
			downloadPage(str(download_url), getPictureData(self.details, self.image_prefix, self.poster_postfix, self.usePicCache)).addCallback(lambda _: self.showPoster(forceShow = True))

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

		download_url = self.extraData["fanart_image"]
		if download_url:
			download_url = download_url.replace('&width=999&height=999', '&width=' + self.backdropWidth + '&height=' + self.backdropHeight)
			printl( "download url " + download_url, self, "D")

		if not download_url:
			printl("no pic data available", self, "D")
		else:
			printl("starting download", self, "D")
			downloadPage(download_url, getPictureData(self.details, self.image_prefix, self.backdrop_postfix, self.usePicCache)).addCallback(lambda _: self.showBackdrop(forceShow = True))

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def finishLayout(self):
		"""
		adds buttons pics from xml and handles fastScrollMode function
		"""
		printl("", self, "S")

		# first we set the pics for buttons
		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_blue"].instance.setPixmapFromFile(self.guiElements["key_blue"])
		self["btn_yellow"].instance.setPixmapFromFile(self.guiElements["key_yellow"])
		self["btn_zero"].instance.setPixmapFromFile(self.guiElements["key_zero"])
		self["btn_nine"].instance.setPixmapFromFile(self.guiElements["key_nine"])
		self["btn_pvr"].instance.setPixmapFromFile(self.guiElements["key_pvr"])
		self["btn_menu"].instance.setPixmapFromFile(self.guiElements["key_menu"])

		# if we are in fastScrollMode we remove some gui elements
		self.resetGuiElementsInFastScrollMode()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def processGuiElements(self, myType=None):
		printl("", self, "S")

		# this is always the case when the view starts the first time
		# in this case no need for look for subviews
		if myType is None:
			for element in self.myParams["elements"]:
				printl("element:" + str(element), self, "D")
				visibility = self.myParams["elements"][element]["visible"]

				self.alterGuiElementVisibility(element, visibility)

				# we do not alter positions here because this should be done in the skin.xml because we are the first view

		# now we check if we are in a special subView with its own params
		elif "subViews" in self.myParams:
			if myType in self.myParams["subViews"]:
				subViewParams = self.myParams["subViews"][myType]
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
		else:
			self[element].hide()
			try:
				self[element+"Label"].hide()

				# additional changes
				if element == "backdrop":
					self[element+"Video"].hide()
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

		mpaa = self.extraData.get("contentRating", "unknown").upper()
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

		audio = self.extraData.get("audioCodec", "unknown").upper()
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

		resolution = self.extraData.get("videoResolution", "unknown").upper()
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

		aspect = self.extraData.get("aspectRatio", "unknown").upper()
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

		codec = self.extraData.get("videoCodec", "unknown").upper()
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

		if visible:
			self["functionsContainer"].show()
			self["btn_red"].show()
			self["btn_blue"].show()
			self["btn_yellow"].show()
			self["txt_red"].show()
			self["txt_filter"].show()
			self["txt_blue"].show()
			self["txt_yellow"].show()
			self["btn_zero"].show()
			self["btn_nine"].show()
			self["btn_pvr"].show()
			self["txt_pvr"].show()
			self["btn_menu"].show()
			self["txt_menu"].show()
		else:
			self["functionsContainer"].hide()
			self["btn_red"].hide()
			self["btn_blue"].hide()
			self["btn_yellow"].hide()
			self["txt_red"].hide()
			self["txt_filter"].hide()
			self["txt_blue"].hide()
			self["txt_yellow"].hide()
			self["btn_zero"].hide()
			self["btn_nine"].hide()
			self["btn_pvr"].hide()
			self["txt_pvr"].hide()
			self["btn_menu"].hide()
			self["txt_menu"].hide()

		printl("", self, "C")
