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
#===============================================================================
# IMPORT
#===============================================================================
import math
import time

from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Label import Label
from Components.config import config
from Components.config import NumericalTextInput

from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from enigma import eServiceReference
from enigma import loadPNG

from Tools.Directories import fileExists

from urllib import urlencode, quote_plus

from twisted.web.client import downloadPage

from Plugins.Extensions.DreamPlex.DPH_Arts import getPictureData
from Plugins.Extensions.DreamPlex.DP_Player import DP_Player
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, getXmlContent, convertSize
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugins, Plugin

#===============================================================================
# 
#===============================================================================
def getViews(libraryName):
	'''
	@param: none 
	@return: availableViewList
	'''
	printl("", "DP_View::getViews", "S")
	
	availableViewList = []
	
	if libraryName == "movies" or libraryName == "tvshows":
		viewList = (
			(_("Short List"), "DP_ViewList", "DPS_ViewList"),
			(_("Long List"), "DP_ViewListLong", "DPS_ViewListLong"), 
			(_("Backdrop"), "DP_ViewBackdrop", "DPS_ViewBackdrop"), 
		)
	elif libraryName == "music":
		viewList = (
					(_("Music"), "DP_ViewMusic", "DPS_ViewMusic"), 
				)
	else:
		viewList = ()
	
	for view in viewList:
		try:
			availableViewList.append(view)
		except Exception, ex:
			printl("View %s not available in this skin" % view[1] + " exception: " + ex , __name__, "W")
	
	printl("", __name__, "C")
	return availableViewList

#===============================================================================
# 
#===============================================================================
def getViewClass():
	'''
	@param: none
	@return: DP_View Class 
	'''
	printl("", __name__, "S")
	
	printl("", __name__, "C")
	return DP_View

class DP_View(Screen, NumericalTextInput):
	'''
	'''

	ON_CLOSED_CAUSE_CHANGE_VIEW = 1
	ON_CLOSED_CAUSE_SAVE_DEFAULT = 2
	ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE = 3

	onNumberKeyLastChar				= "#"
	activeSort						= ("Default", None, False)
	activeFilter					= ("All", (None, False), "")
	onEnterPrimaryKeys				= None
	onLeavePrimaryKeyValuePair		= None
	onLeaveSelectKeyValuePair		= None
	currentKeyValuePair				= None
	
	currentShowIndex				= None
	currentSeasonIndex				= None
	currentMovieIndex				= None
	showMedia						= False
	showDetail						= False
	isDirectory						= False
	
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None, cache=None):
		printl("", self, "S")
		printl("cache: " + str(cache), self, "D")
		
		printl("viewName: "+ str(viewName), self, "I")
		self.skinName = viewName[2]
		Screen.__init__(self, session)
		NumericalTextInput.__init__(self)
		self.skinName = viewName[2]
		self.select = select
		self.cache = cache
		self.onFirstExecSort = sort
		self.onFirstExecFilter = filter
		
		self.libraryName = libraryName
		self.loadLibrary = loadLibrary
		self.viewName = viewName
		self._playEntry = playEntry
		
		self.playerData = None
		
		self.setListViewElementsCount(str(viewName[1]))
	
		self.usePicCache = config.plugins.dreamplex.usePicCache.value
		
		# Initialise library list
		list = []
		self["listview"] = List(list, True)
		
		self["number_key_popup"] = Label("")
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
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def setCustomTitle(self):
		printl("", self, "S")
		
		self.setTitle(_(self.libraryName))
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getGuiElements(self):
		printl("", self, "S")
		
		tree = getXmlContent("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value +"/params")
		
		self.guiElements = {}
		for guiElement in tree.findall('guiElement'):
			name = str(guiElement.get('name'))
			path = str(guiElement.get('path'))
			self.guiElements[name] = path
			
		printl("guiElements: " + str(self.guiElements))
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def setListViewElementsCount(self, viewName):
		printl("", self, "S")
		
		tree = getXmlContent("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value +"/params")
		for view in tree.findall('view'):
			if view.get('name') == viewName:
				self.itemsPerPage = int(view.get('itemsPerPage'))
		printl("self.itemsPerPage: " + str(self.itemsPerPage), self, "D")
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onFirstExec(self):
		printl("", self, "S")		
		
		if self.select is None: # Initial Start of View, select first entry in list
			sort = False
			if self.onFirstExecSort is not None:
				self.activeSort = self.onFirstExecSort
				sort = True
			filter = False
			if self.onFirstExecFilter is not None:
				self.activeFilter = self.onFirstExecFilter
				filter = True
			
			# lets override this
			filter = True
			sort = True
			
			self._load(ignoreSort=sort, ignoreFilter=filter)
			self.refresh()
		else: # changed views, reselect selected entry
			printl("self.select: " +  str(self.select), self, "D")
			sort = False
			if self.onFirstExecSort is not None:
				self.activeSort = self.onFirstExecSort
				sort = True
			filter = False
			if self.onFirstExecFilter is not None:
				self.activeFilter = self.onFirstExecFilter
				filter = True
			
			self._load(self.select[0], ignoreSort=sort, ignoreFilter=filter)
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
		'''
		onNumberKeyTimeout
		'''
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
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def onKeyRight(self):
		printl("", self, "S")
		
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
		
		self.onToggleView()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyBlueLong(self):
		printl("", self, "S")
		
		#self.onChooseView()
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
				subelements = self.onFilterKeyValuePair[i][2]
				for j in range(len(subelements)):
					if self.activeFilter[2] == subelements[j]:
						# Action == Action
						if (j+1) < len(subelements):
							y = subelements[j + 1]
							found = True
							break
				
				if found is True:
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
	def onChooseView(self):
		printl("", self, "S")
		
		menu = getViews()
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
			image		= selection[3]
			
			#details
			viewMode	= details['viewMode']
			server		= details['server']
			printl("viewMode: " +str(viewMode), self, "D")
			printl("server: " +str(server), self, "D")
			
			#extraData
			url_path	= extraData['key']
			printl("url_path: " +str(url_path), self, "D")
		
			if (viewMode == "ShowSeasons"):
				printl("viewMode -> ShowSeasons", self, "I")

				params = {}
				params["viewMode"] = viewMode
				params["url"] = "http://" + server + url_path
				
				self.currentSeasonsParams = params
				self.currentShowIndex = self["listview"].getIndex()

				self._load(params)

			elif (viewMode == "ShowEpisodes"):
				printl("viewMode -> ShowEpisodes", self, "I")

				params = {}
				params["viewMode"] = viewMode
				params["url"] = "http://" + server + url_path
				
				self.currentEpisodesParams = params
				self.currentSeasonIndex = self["listview"].getIndex()
				
				self._load(params)
			
			elif (viewMode == "play"):
				printl("viewMode -> play", self, "I")
				self.playEntry(selection)
			
			elif (viewMode == "directory"):
				printl("viewMode -> directory", self, "I")
				
				params = {}
				params["viewMode"] = viewMode
				params["url"] = "http://" + server + url_path
				
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
	def showMediaDetail(self, unused=None, unused2=None):
		printl("", self, "S")
		self.showDetail = True
		selection = self["listview"].getCurrent()
		
		if selection is not None:
			details			= selection[1]
			extraData		= selection[2]
			image			= selection[3]
			
			#details
			viewMode		= details['viewMode']
			server			= details['server']
			
			#extraData
			url_path		= extraData['key']
			
			if (viewMode == "play"):
				printl("viewMode -> play", self, "I")
				self.playEntry(selection)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")
		
		selectKeyValuePair = self.onLeaveSelectKeyValuePair
		printl("selectKeyValuePair: " + str(selectKeyValuePair), self, "D")
		
		if config.plugins.dreamplex.playTheme.value == True:
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
		'''
			e.g.
			params = {}
			params["viewMode"] = viewMode
			params["url"] = "http://" + server + url_path
			params["index"] = int
		'''
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
			seenVisu = loadPNG(listView[4])
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
		
		listViewList = []
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
		'''
		
		@todo: lets check this. seems to be some kind of too much
		
		'''
		#printl("", self, "S")
		#printl("setting text for " + str(name) + " with value " + str(value), self, "D")
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
		
		# update the list to sync list with content
		#self.updateList()
		
		# show content for selected list item
		selection = self["listview"].getCurrent()
		viewMode = selection[1]['viewMode']
		
		self.isDirectory = False
		if viewMode == "directory":
			self.isDirectory = True
		
		self._refresh(selection)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def _refresh(self, selection):
		printl("", self, "S")
		
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
		result=0
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

		if self.showDetail == True:
			currentFile = "Location:\n " + str(self.playerData['currentFile'])
			self.session.open(MessageBox,_("%s") % (currentFile), MessageBox.TYPE_INFO)
			self.showDetail = False
		else:
			if self.playerData['fallback'] == True:
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
		
		resume = False
		
		if confirm:
			resume = True
			self.session.open(DP_Player, self.playerData, resume)
		
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
	def setDefaultView(self, unused=None, unused2=None):
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
	def clearDefaultView(self, unused=None, unused2=None):
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
		
		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, \
			title=_("Media Functions"), list=functionList)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def refreshSection(self, unused=None, unused2=None):
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
		
		self.session.openWithCallback(self.displaySubtitleMenuCallback, ChoiceBox, \
			title=_("Subtitle Functions"), list=functionList,selection=selection)
		
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
		
		self.session.openWithCallback(self.displayAudioMenuCallback, ChoiceBox, \
			title=_("Audio Functions"), list=functionList,selection=selection)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def markUnwatched(self, unused=None, unused2=None):
		printl("", self, "S")

		Singleton().getPlexInstance().doRequest(self.unseenUrl)
		self.showMessage()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def markWatched(self, unused=None, unused2=None):
		printl("", self, "S")
		
		Singleton().getPlexInstance().doRequest(self.seenUrl)
		self.showMessage()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def initiateRefresh(self, unused=None, unused2=None):
		printl("", self, "S")
		
		Singleton().getPlexInstance().doRequest(self.refreshUrl)
		self.showMessage()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def deleteFromLibrary(self, unused=None, unused2=None):
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
		
		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, \
			title=_("Options"), list=pluginList)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
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
					if self.has_key("backdrop"):
						self["backdrop"].finishStillPicture()
					self.session.openWithCallback(self.pluginCallback, choice[1].start, selection[1])
					
			elif choice[1].fnc:
				if choice[1].supportStillPicture is False and self.has_key("backdrop"):
					self["backdrop"].finishStillPicture()
				choice[1].fnc(self.session, selection[1])
				if choice[1].supportStillPicture is False and self.has_key("backdrop"):
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
		
		#self.setText("subtitles", str(choice[0]).encode('utf8'))
		
		doRequest = Singleton().getPlexInstance().setAudioById(choice[4], choice[3], choice[2], choice[5])
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def displaySubtitleMenuCallback(self, choice):
		printl("", self, "S")
		
		if choice is None or choice[1] is None:
			return
		
		printl("choice" + str(choice), self, "D")
		
		#self.setText("audio", str(choice[0]).encode('utf8'))
		
		doRequest = Singleton().getPlexInstance().setSubtitleById(choice[4], choice[3], choice[2], choice[5])
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def startThemePlayback(self):
		'''
		'''
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
		
		if forceShow == True:
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
		
		if forceShow == True:
			if self.whatBackdrop is not None:
				self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
				ptr = self.EXpicloadBackdrop.getData()
				
				if ptr is not None:
					self["mybackdrop"].instance.setPixmap(ptr)
		
		elif self.usePicCache :
			if fileExists(getPictureData(self.details, self.image_prefix, self.backdrop_postfix, self.usePicCache)):
				
				if self.whatBackdrop is not None:
					self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
					ptr = self.EXpicloadBackdrop.getData()
					
					if ptr is not None:
						self["mybackdrop"].instance.setPixmap(ptr)
	
			else:
				self.downloadBackdrop()
		else:
			self.downloadBackdrop()
		
		printl("", self, "C")
		return

	#===========================================================================
	# 
	#===========================================================================
	def resetCurrentImages(self):
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value + "/all/picreset.png"
		
		if self.resetPoster == True:
			self["poster"].instance.setPixmapFromFile(ptr)
		
		if self.resetBackdrop == True:
			self["mybackdrop"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def downloadPoster(self):
		printl("", self, "S")
		
		download_url = self.extraData["thumb"]
		printl( "download url " + download_url, self, "D")
		
		if download_url == "" or download_url == "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/resources/plex.png":
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
		
		download_url = self.extraData["fanart_image"]
		printl( "download url " + download_url, self, "D")	
		
		if download_url == "" or download_url == "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/resources/plex.png":
			printl("no pic data available", self, "D")
			
		else:
			printl("starting download", self, "D")	
			downloadPage(download_url, getPictureData(self.details, self.image_prefix, self.backdrop_postfix, self.usePicCache)).addCallback(lambda _: self.showBackdrop(forceShow = True))
				
		printl("", self, "C")
		
	#==============================================================================
	# 
	#==============================================================================
	def setPara(self):
		printl("", self, "S")
		
		self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadBackdrop.setPara([self["mybackdrop"].instance.size().width(), self["mybackdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		
		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_blue"].instance.setPixmapFromFile(self.guiElements["key_blue"])
		self["btn_yellow"].instance.setPixmapFromFile(self.guiElements["key_yellow"])
		self["btn_zero"].instance.setPixmapFromFile(self.guiElements["key_zero"])
		self["btn_nine"].instance.setPixmapFromFile(self.guiElements["key_nine"])
		self["btn_pvr"].instance.setPixmapFromFile(self.guiElements["key_pvr"])
		self["btn_menu"].instance.setPixmapFromFile(self.guiElements["key_menu"])
		
		self.resetGuiElementsInFastScrollMode()
		
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
		self["audio"].hide()
		
		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/all/picreset.png"
		self["mybackdrop"].instance.setPixmapFromFile(ptr)
				
		printl("", self, "C")
