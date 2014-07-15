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
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry
from Components.Label import Label
from Components.Pixmap import Pixmap

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

from DP_PathSelector import DPS_PathSelector

#===============================================================================
#
#===============================================================================
class DPS_Settings(Screen, ConfigListScreen, HelpableScreen):

	_hasChanged = False
	_session = None
	skins = None
	
	def __init__(self, session):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self.cfglist = []
		ConfigListScreen.__init__(self, self.cfglist, session, on_change = self._changed)
		
		self._session = session
		self._hasChanged = False

		self["txt_green"] = Label()
		self["btn_green"] = Pixmap()

		self["help"] = StaticText()
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "DPS_Settings"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.ok,
			"left": self.keyLeft,
			"right": self.keyRight,
			"bouquet_up":	self.keyBouquetUp,
			"bouquet_down":	self.keyBouquetDown,
		}, -2)

		self.createSetup()
		
		self["config"].onSelectionChanged.append(self.updateHelp)
		self.onLayoutFinish.append(self.finishLayout)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		self["txt_green"].hide()
		self["btn_green"].hide()

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def createSetup(self):
		printl("", self, "S")
		
		separator = "".ljust(120,"_")
		
		self.cfglist = []
		
		# GENERAL SETTINGS
		self.cfglist.append(getConfigListEntry(_("General Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Used Skin"), config.plugins.dreamplex.skin, _("If you change the skin you have to restart at least the GUI!")))
		self.cfglist.append(getConfigListEntry(_("> Show Plugin in Main Menu"), config.plugins.dreamplex.showInMainMenu, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Use Cache for Sections"), config.plugins.dreamplex.useCache, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Use Picture Cache"), config.plugins.dreamplex.usePicCache, _("Use this if you do not have enough space on your box e.g. no hdd drive just flash.")))
		self.cfglist.append(getConfigListEntry(_("> Show Infobar when buffer drained"), config.plugins.dreamplex.showInfobarOnBuffer, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Show Backdrops as Videos"), config.plugins.dreamplex.useBackdropVideos, _("Use this if you have m1v videos as backdrops")))
		self.cfglist.append(getConfigListEntry(_("> Stop Live TV on startup"), config.plugins.dreamplex.stopLiveTvOnStartup, _(" ")))

		# playing themes stops live tv for this reason we enable this only if live stops on startup is set
		# also backdrops as video needs to turn of live tv
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			# if backdrop videos are active we have to turn off theme playback
			if config.plugins.dreamplex.useBackdropVideos.value:
				config.plugins.dreamplex.playTheme.value = False
			else:
				self.cfglist.append(getConfigListEntry(_(">> Play Themes in TV Shows"), config.plugins.dreamplex.playTheme, _(" ")))
		else:
			# if the live startup stops is not set we have to turn of playtheme automatically
			config.plugins.dreamplex.playTheme.value = False
			#config.plugins.dreamplex.useBackdropVideos.value = False

		if config.plugins.dreamplex.showUpdateFunction.value:
			self.cfglist.append(getConfigListEntry(_("> Check for updates on startup"), config.plugins.dreamplex.checkForUpdateOnStartup, _("If activated on each start we will check if there is a new version depending on your update type.")))
			self.cfglist.append(getConfigListEntry(_("> Updatetype"), config.plugins.dreamplex.updateType, _("Use Beta only if you really want to help with testing")))
		# USERINTERFACE SETTINGS
		self.cfglist.append(getConfigListEntry(_("Userinterface Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Summerize Sections"), config.plugins.dreamplex.summerizeSections, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Show Filter for Section"), config.plugins.dreamplex.showFilter, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Show Seen/Unseen count in TvShows"), config.plugins.dreamplex.showUnSeenCounts, _(" ")))

		if config.plugins.dreamplex.useBackdropVideos.value:
			config.plugins.dreamplex.fastScroll.value = False
		else:
			self.cfglist.append(getConfigListEntry(_("> Use fastScroll as default"), config.plugins.dreamplex.fastScroll, _(" ")))

		self.cfglist.append(getConfigListEntry(_("> Show additional data for myPlex sections"), config.plugins.dreamplex.showDetailsInList, _(" ")))
		if config.plugins.dreamplex.showDetailsInList.value:
			self.cfglist.append(getConfigListEntry(_("> Detail type for additional data"), config.plugins.dreamplex.showDetailsInListDetailType, _(" ")))

		# VIEW SETTINGS
		self.cfglist.append(getConfigListEntry(_("Path Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Default View for Movies"), config.plugins.dreamplex.defaultMovieView, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Default View for Shows"), config.plugins.dreamplex.defaultShowView, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Default View for Music"), config.plugins.dreamplex.defaultMusicView, _(" ")))

		# PATH SETTINGS
		self.cfglist.append(getConfigListEntry(_("Path Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		
		self.mediafolderpath = getConfigListEntry(_("> Media Folder Path"), config.plugins.dreamplex.mediafolderpath, _(" "))
		self.cfglist.append(self.mediafolderpath)
		
		self.configfolderpath = getConfigListEntry(_("> Config Folder Path"), config.plugins.dreamplex.configfolderpath, _(" "))
		self.cfglist.append(self.configfolderpath)
		
		self.cachefolderpath = getConfigListEntry(_("> Cache Folder Path"), config.plugins.dreamplex.cachefolderpath, _(" "))
		self.cfglist.append(self.cachefolderpath)

		self.playerTempPath =  getConfigListEntry(_("> Player Temp Path"), config.plugins.dreamplex.playerTempPath, _(" "))
		self.cfglist.append(self.playerTempPath)
		
		self.logfolderpath = getConfigListEntry(_("> Log Folder Path"), config.plugins.dreamplex.logfolderpath, _(" "))
		self.cfglist.append(self.logfolderpath)
		
		# MISC
		self.cfglist.append(getConfigListEntry(_("Misc Settings") + separator, config.plugins.dreamplex.about, _(" ")))
		self.cfglist.append(getConfigListEntry(_("> Debug Mode"), config.plugins.dreamplex.debugMode, _(" ")))

		self["config"].list = self.cfglist
		self["config"].l.setList(self.cfglist)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def _changed(self):
		printl("", self, "S")
		
		self._hasChanged = True

		self["txt_green"].show()
		self["txt_green"].setText(_("Save"))
		self["btn_green"].show()

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def updateHelp(self):
		printl("", self, "S")
		
		cur = self["config"].getCurrent()
		printl("cur: " + str(cur), self, "D")
		self["help"].text = cur and cur[2] or "empty"
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		printl("", self, "S")

		cur = self["config"].getCurrent()
		
		if cur == self.mediafolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.mediafolderpath[1].value, "media")
		
		elif cur == self.configfolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.configfolderpath[1].value, "config")
		
		elif cur == self.playerTempPath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.playerTempPath[1].value, "player")

		elif cur == self.logfolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.logfolderpath[1].value, "log")

		elif cur == self.cachefolderpath:
			self.session.openWithCallback(self.savePathConfig,DPS_PathSelector,self.cachefolderpath[1].value, "cache")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def savePathConfig(self, pathValue, myType):
		printl("", self, "S")
		
		printl("pathValue: " + str(pathValue), self, "D")
		printl("type: " + str(myType), self, "D")
		
		if pathValue is not None:

			if myType == "media":
				self.mediafolderpath[1].value = pathValue
			
			elif myType == "config":
				self.configfolderpath[1].value = pathValue
			
			elif myType == "player":
				self.playerTempPath[1].value = pathValue
	
			elif myType == "log":
				self.logfolderpath[1].value = pathValue
	
			elif myType == "cache":
				self.cachefolderpath[1].value = pathValue
			
		config.plugins.dreamplex.save()
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keySave(self):
		printl("", self, "S")

		self.saveAll()
		self.close(None)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def keyLeft(self):
		printl("", self, "S")
		
		ConfigListScreen.keyLeft(self)
		self.createSetup()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyRight(self):
		printl("", self, "S")
		
		ConfigListScreen.keyRight(self)
		self.createSetup()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def keyBouquetUp(self):
		printl("", self, "S")
		
		self["config"].instance.moveSelection(self["config"].instance.pageUp)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def keyBouquetDown(self):
		printl("", self, "S")
		
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

		printl("", self, "C")



#===============================================================================
#
#===============================================================================
class DPS_ServerEntryList(MenuList):
	
	def __init__(self, menuList, enableWrapAround = True):
		printl("", self, "S")
		
		MenuList.__init__(self, menuList, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def postWidgetCreate(self, instance):
		printl("", self, "S")
		
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def buildList(self):
		printl("", self, "S")
		
		self.list=[]

		
		for entry in config.plugins.dreamplex.Entries:
			res = [entry]
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(entry.name.value)))
			
			if entry.connectionType.value == "2":
				text1 = entry.myplexUrl.value
				text2 = entry.myplexUsername.value
			else:
				text1 = "%d.%d.%d.%d" % tuple(entry.ip.value)
				text2 = "%d"% entry.port.value
				
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(text1)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 450, 0, 80, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(text2)))
			self.list.append(res)
		
		
		self.l.setList(self.list)
		self.moveToIndex(0)
				
		printl("", self, "C")
