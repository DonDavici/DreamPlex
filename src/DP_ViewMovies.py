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

from DP_View import DP_View

from DPH_Singleton import Singleton

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
# 
#===============================================================================
def getViewClass():
	printl("",__name__ , "S")
	
	printl("",__name__ , "C")
	return DPS_ViewMovies

#===============================================================================
# 
#===============================================================================
class DPS_ViewMovies(DP_View):

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
		printl("myParams: " + str(viewName[3]), self, "D")
		printl("libraryName: " + str(libraryName), self, "D")
		
		self.myParams = viewName[3]
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, myFilter, cache)
		printl("cache: " + str(cache), self, "D")
		# set navigation values
		#DP_View.setListViewElementsCount("DPS_ViewList")
		
		# set image names to use
		self.poster_postfix = self.myParams["poster_postfix"]
		self.backdrop_postfix = self.myParams["backdrop_postfix"]
		
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
		
		if self.myParams["showPoster"]:
			self["poster"] = Pixmap()
			self.posterHeight = self.myParams["posterHeight"]
			self.posterWidth = self.myParams["posterWidth"]
		
		if self.myParams["showBackdrop"]:
			self["mybackdrop"] = Pixmap()
			self.backdropHeight = self.myParams["backdropHeight"]
			self.backdropWidth = self.myParams["backdropWidth"]
			
		if self.myParams["audio"]:
			self["audio"] = MultiPixmap()
		
		if self.myParams["resolution"]:
			self["resolution"] = MultiPixmap()
		
		if self.myParams["aspect"]:
			self["aspect"] = MultiPixmap()
		
		if self.myParams["codec"]:
			self["codec"] = MultiPixmap()
		
		if self.myParams["rated"]:
			self["rated"] = MultiPixmap()
		
		if self.myParams["title"]:
			self["title"] = Label()
		
		if self.myParams["tag"]:
			self["tag"] = Label()
		
		if self.myParams["shortDescription"]:
			self["shortDescription"] = ScrollLabel()
		
		if self.myParams["subtitles"]:
			self["subtitles"] = Label()
		
		if self.myParams["selectedAudio"]:
			self["selectedAudio"] = Label()
		
		if self.myParams["genre"]:
			self["genre"] = Label()
		
		if self.myParams["year"]:
			self["year"] = Label()
		
		if self.myParams["runtime"]:
			self["runtime"] = Label()
		
		if self.myParams["total"]:
			self["total"] = Label()
		
		if self.myParams["current"]:
			self["current"] = Label()
		
		if self.myParams["backdroptext"]:
			self["backdroptext"] = Label()
		
		if self.myParams["postertext"]:
			self["postertext"] = Label()
		
		if self.myParams["rating_stars"]:
			self["rating_stars"] = ProgressBar()
		
		printl("skinName: " + str(self.skinName), self, "C")
		self.skinName = self.myParams["screen"]

		if self.myParams["showPoster"] == True or self.myParams["showBackdrop"] == True:
			self.EXscale = (AVSwitch().getFramebufferScale())

			if self.myParams["showPoster"]:
				self.EXpicloadPoster = ePicLoad()

			if self.myParams["showBackdrop"]:
				self.EXpicloadBackdrop = ePicLoad()

			self.onLayoutFinish.append(self.setPara)

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def _refresh(self, selection):
		printl("", self, "S")
		#printl("selection: " + str(selection), self, "D")
		
		printl("resetGuiElements: " + str(self.resetGuiElements), self, "D")
		
		if self.resetGuiElements:
			self.resetGuiElementsInFastScrollMode()
		
		if self.myParams["showBackdrop"] or self.myParams["showPoster"]:
			self.resetCurrentImages()
		
		printl("showMedia: " + str(self.showMedia), self, "D")
		
		printl("isDirectory: " + str(self.isDirectory), self, "D")
		
		if selection is not None:
			self.details 		= selection[1]
			self.extraData 		= selection[2]
			self.context		= selection[3]
		
			if self.isDirectory:
				pass
			else:
				# lets get all data we need to show the needed pictures
				# we also check if we want to play
				if self.myParams["showBackdrop"] == True or self.myParams["showPoster"] == True:
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
				
				if self.myParams["title"]:
					self.setText("title", self.details.get("title", " "))
				
				if self.myParams["tag"]:
					self.setText("tag", self.details.get("tagline", " ").encode('utf8'), True)
				
				if self.myParams["year"]:
					self.setText("year", str(self.details.get("year", " - ")))
				
				if self.myParams["genre"]:
					self.setText("genre", str(self.details.get("genre", " - ").encode('utf8')))
				
				if self.myParams["subtitles"]:
					self.setText("subtitles", str(self.extraData.get("selectedSub", " - ").encode('utf8')))
				
				if self.myParams["selectedAudio"]:
					self.setText("selectedAudio", str(self.extraData.get("selectedAudio", " - ").encode('utf8')))
				
				if self.myParams["runtime"]:
					self.setText("runtime", str(self.details.get("runtime", " - ")))
				
				if self.myParams["shortDescription"]:
					self["shortDescription"].setText(self.details.get("summary", " ").encode('utf8'))
				
				if self.fastScroll == False or self.showMedia == True:
					# handle all pixmaps
					if self.myParams["rating_stars"]:
						self.handlePopularityPixmaps()
					
					if self.myParams["codec"]:
						self.handleCodecPixmaps()
					
					if self.myParams["aspect"]:
						self.handleAspectPixmaps()
					
					if self.myParams["resolution"]:
						self.handleResolutionPixmaps()
					
					if self.myParams["rated"]:
						self.handleRatedPixmaps()
					
					if self.myParams["audio"]:
						self.handleSoundPixmaps()
				
				# navigation
				self.handleNavigationData()
				
				# now lets switch images
				if self.changePoster == True and self.myParams["showPoster"] == True:
					self.showPoster()
				
				if self.fastScroll == False or self.showMedia == True:
					if self.changeBackdrop == True and self.myParams["showBackdrop"] == True:
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

		printl( "is playable content",self, "D")
		bname = self.details["ratingKey"]
		self.startPlaybackNow = False

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
