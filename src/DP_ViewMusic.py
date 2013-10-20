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
from enigma import ePicLoad

from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap, MultiPixmap
from Components.config import config
from Components.AVSwitch import AVSwitch
from Components.ProgressBar import ProgressBar

from twisted.web.client import downloadPage

from DP_View import DP_View

from DPH_Singleton import Singleton
from DPH_Arts import getPictureData

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
# 
#===============================================================================
def getViewClass():
	printl("",__name__ , "S")
	
	printl("",__name__ , "C")
	return DPS_ViewMusic

#===============================================================================
# 
#===============================================================================
class DPS_ViewMusic(DP_View):

	plexInstance 			= None
	parentSeasonId 			= None
	parentSeasonNr 			= None
	isTvShow 				= False
	playTheme 				= False
	startPlaybackNow 		= False
	itemsPerPage 			= 0
	changePoster 			= True
	changeBackdrop 			= True
	resetGuiElements		= False
	fastScroll 				= False

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, myFilter=None, cache=None):
		printl("", self , "S")
		self.session = session
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, myFilter, cache)
		
		# get needed config parameters
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		self.playTheme = config.plugins.dreamplex.playTheme.value
		self.fastScroll = config.plugins.dreamplex.fastScroll.value
		
		# get data from plex library
		self.image_prefix = Singleton().getPlexInstance().getServerName().lower()
		
		# init skin elements
		self["functionsContainer"]  = Label()
		
		self["btn_red"]  = Pixmap()
		self["btn_blue"] = Pixmap()
		self["btn_yellow"] = Pixmap()
		self["btn_zero"] = Pixmap()
		self["btn_nine"] = Pixmap()
		self["btn_pvr"] = Pixmap()
		self["btn_menu"] = Pixmap()
		
		self["txt_red"]     = Label()
		self["txt_filter"]  = Label()
		self["txt_blue"]    = Label()
		self["txt_blue"].setText(_("toogle View ") + _("(current 'Default')"))
		self["txt_yellow"]    = Label()
		
		if self.fastScroll:
			self["txt_yellow"].setText("fastScroll = On")
		else:
			self["txt_yellow"].setText("fastScroll = Off")
		
		self["txt_pvr"]    = Label()
		self["txt_pvr"].setText("load additional data")
		self["txt_menu"]    = Label()
		self["txt_menu"].setText("show media functions")
		
		self["poster"] 				= Pixmap()
		self["mybackdrop"] 			= Pixmap()

		self["audio"] 				= MultiPixmap()
		self["resolution"] 			= MultiPixmap()
		self["aspect"] 				= MultiPixmap()
		self["codec"] 				= MultiPixmap()
		self["rated"] 				= MultiPixmap()
	
		self["title"] 				= Label()
		self["tag"] 				= Label()
		self["shortDescription"] 	= ScrollLabel()
		self["genre"] 				= Label()
		self["year"] 				= Label()
		self["runtime"] 			= Label()
		self["total"] 				= Label()
		self["current"] 			= Label()
		self["backdroptext"]		= Label()
		self["postertext"]			= Label()
		
		self["rating_stars"] = ProgressBar()
		
		self.skinName = self.viewName[2]

		self.EXscale = (AVSwitch().getFramebufferScale())
		self.EXpicloadPoster 		= ePicLoad()
		self.EXpicloadBackdrop 		= ePicLoad()
		self.onLayoutFinish.append(self.setPara)
	
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def _refresh(self, selection):
		printl("", self, "S")
		printl("selection: " + str(selection), self, "D")
		
		printl("resetGuiElements: " + str(self.resetGuiElements), self, "D")
		
		if self.resetGuiElements:
			self.resetGuiElementsInFastScrollMode()
		
		self.resetCurrentImages()
		printl("showMedia: " + str(self.showMedia), self, "D")
		
		if selection is not None:
			self.details 		= selection[1]
			self.extraData 		= selection[2]
			self.context		= selection[3]
			
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
					super(getViewClass(), self).startThemePlayback()

			self.setText("title", self.details.get("title", " "))
			self.setText("tag", self.details.get("tagline", " ").encode('utf8'), True)
			self.setText("year", str(self.details.get("year", " - ")))
			self.setText("genre", str(self.details.get("genre", " - ").encode('utf8')))
			self.setText("runtime", str(self.details.get("runtime", " - ")))
			self["shortDescription"].setText(self.details.get("summary", " ").encode('utf8'))
			
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
			
			if self.fastScroll == False or self.showMedia == True:
				if self.changeBackdrop:
					self.showBackdrop()
			
			self.showFunctions(False)
			
			# we need those for fastScroll
			# this prevents backdrop load on next item
			self.showMedia = False
			
		else:
			self.setText("title", "no data retrieved")
			self.setText("shortDescription", "no data retrieved")
			
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
	def onKeyYellow(self):
		printl("", self, "S")
		
		if self.fastScroll:
			self.fastScroll = False
			self["txt_yellow"].setText("fastScroll = Off")
		else:
			self.fastScroll = True
			self["txt_yellow"].setText("fastScroll = On")
		
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
	def getPictureInformationToLoad(self):
		printl("", self, "S")

		if self.details ["viewMode"] == "ShowSeasons":
			printl( "is ShowSeasons", self, "D")
			self.parentSeasonId = self.details ["ratingKey"]
			self.isTvShow = True
			self.startPlaybackNow = True
			bname = self.details["ratingKey"]
			pname = self.details["ratingKey"]
			self.changeBackdrop = True
			self.changePoster = True
			self.resetPoster = True
			self.resetBackdrop = True
	
		elif self.details ["viewMode"] == "ShowEpisodes" and self.details["ratingKey"] == "0":
			printl( "is ShowEpisodes all entry", self, "D")
			self.isTvShow = True
			bname = self.parentSeasonId
			pname = self.parentSeasonId
			self.startPlaybackNow = False
			self.changeBackdrop = True
			self.changePoster = True
			self.resetPoster = False
			self.resetBackdrop = False
			
		elif self.details ["viewMode"] == "ShowEpisodes" and self.details["ratingKey"] != "":
			printl( "is ShowEpisodes special season",self, "D")
			self.isTvShow = True
			self.parentSeasonNr = self.details["ratingKey"]			
			bname = self.parentSeasonId
			pname = self.details["ratingKey"]
			self.startPlaybackNow = False
			self.changeBackdrop = False
			self.changePoster = True
			self.resetPoster = False
			self.resetBackdrop = False
		
		else:
			printl( "is playable content",self, "D")
			bname = self.details["ratingKey"]
			self.startPlaybackNow = False
			if self.isTvShow is True:
				printl( "is episode",self, "D")
				pname = self.parentSeasonId
				# we dont want to have the same poster downloaded and used for each episode
				self.changePoster = False
				self.changeBackdrop = True
			else:
				printl( "is movie",self, "D")
				self.changeBackdrop = True
				self.changePoster = True
				pname = self.details["ratingKey"]
				
		if not self.usePicCache:
			pname = "temp"
			bname = "temp"
			self.mediaPath = config.plugins.dreamplex.logfolderpath.value
		
		self.whatPoster = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
		self.whatBackdrop = self.mediaPath + self.image_prefix + "_" + bname + self.backdrop_postfix
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def close(self, arg=None):
		printl("", self, "S")
		
		super(getViewClass(), self).close(arg)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def playEntry(self, entry):
		printl("", self, "S")
		
		super(getViewClass(), self).playEntry(entry)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def sort(self):
		printl("", self, "S")
		
		text = "toogle Sorting (sorted %s)" % (_(self.activeSort[0]))
		self["txt_red"].setText(text)
		super(getViewClass(), self).sort()
		self.areFunctionsHidden = True
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def filter(self):
		printl("", self, "S")
		
		if len(self.activeFilter[2]) > 0:
			#text = "%s: %s" % (_("Filter"), _(self.activeFilter[2])) #To little space
			text = "set Filter (set to '%s')" % (_(self.activeFilter[2]))
		else:
			#text = "%s: %s" % (_("Filter"), _(self.activeFilter[0])) #To little space
			text = "set Filter (set to '%s')" % (_(self.activeFilter[0]))

		self["txt_filter"].setText(text)
		super(getViewClass(), self).filter()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def downloadBackdrop(self):
		printl("", self, "S")
		
		download_url = self.extraData["fanart_image"]
		download_url = download_url.replace('&width=560&height=315', '&width=1280&height=720')
		#http://192.168.45.190:32400/photo/:/transcode?url=http%3A%2F%2Flocalhost%3A32400%2Flibrary%2Fmetadata%2F6209%2Fart%2F1354571799&width=560&height=315'
		printl( "download url " + download_url, self, "D")	
		
		if download_url == "":
			printl("no pic data available", self, "D")
			
		else:
			printl("starting download", self, "D")	
			downloadPage(download_url, getPictureData(self.details, self.image_prefix, self.backdrop_postfix, self.usePicCache)).addCallback(lambda _: self.showBackdrop(forceShow = True))
				
		printl("", self, "C")

