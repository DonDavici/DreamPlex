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

from enigma import ePicLoad, getDesktop
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap, MultiPixmap
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.AVSwitch import AVSwitch
from Components.ProgressBar import ProgressBar

from Tools.Directories import fileExists

from twisted.web.client import downloadPage

from DP_View import DP_View

from DPH_Arts import getPictureData
from enigma import eServiceReference
from urllib import urlencode, quote_plus

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
def getViewClass():
	'''
	'''
	printl("",__name__ , "S")
	
	printl("",__name__ , "C")
	return DPS_ViewMusic

#===============================================================================
# 
#===============================================================================
class DPS_ViewMusic(DP_View):
	'''
	'''
	backdrop_postfix 		= "_backdrop_1280x720.jpg"
	poster_postfix 			= "_poster.jpg"
	image_prefix 			= ""
	plexInstance 			= None
	details 				= None
	extraData 				= None
	context					= None
	parentSeasonId 			= None
	parentSeasonNr 			= None
	isTvShow 				= False
	playTheme 				= False
	startPlaybackNow 		= False
	itemsPerPage 			= 0
	whatPoster 				= None
	whatBackdrop 			= None
	changePoster 			= True
	changeBackdrop 			= True
	resetPoster				= True
	resetBackdrop			= True
	seenUrl 				= None
	unseenUrl 				= None
	deleteUrl 				= None
	refreshUrl 				= None
	resetGuiElements		= False
	fastScroll 				= False

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None, cache=None):
		printl("", self , "S")
		self.session = session
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, filter, cache)
		
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
		
		if self.fastScroll == True:
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
		
		if self.resetGuiElements == True:
			self.resetGuiElementsInFastScrollMode()
		
		self.resetCurrentImages()
		printl("showMedia: " + str(self.showMedia), self, "D")
		
		if selection != None:
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
					super(DP_ViewMusic, self).startThemePlayback()

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
			if self.changePoster == True:
				self.showPoster()
			
			if self.fastScroll == False or self.showMedia == True:
				if self.changeBackdrop == True:
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
		
		if self.fastScroll == True:
			self.fastScroll = False
			self["txt_yellow"].setText("fastScroll = Off")
		else:
			self.fastScroll = True
			self["txt_yellow"].setText("fastScroll = On")
		
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
		
		if found == True:
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
			self["audio"].setPixmapNum(0)
		
		elif audio == "AC3":
			found = True
			self["audio"].setPixmapNum(1)
		
		elif audio == "MP2":
			found = True
			self["audio"].setPixmapNum(2)
			
		elif audio == "MP3":
			found = True
			self["audio"].setPixmapNum(3)
		
		elif audio == "UNKNOWN" or audio == "":
			found = False;
		
		else:
			printl("we have a value but no match!! audio: " + str(audio), self, "I")
			found = False
		
		if found == True:
			self["audio"].show()
		else:
			self["audio"].hide()
		
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
			found = False;
		
		else:
			printl("we have a value but no match!! resolution: " + str(resolution), self, "I")
			found = False
		
		if found == True:
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
		
		if found == True:
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
			found = False;
		
		else:
			printl("we have a value but no match!! codec: " + str(codec), self, "I")
			found = False
		
		if found == True:
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
			popularity = float(self.details ["rating"])
		except Exception, e: 
			popularity = 0
			printl( "error in popularity " + str(e),self, "D")
			
		self["rating_stars"].setValue(int(popularity) * 10)
		self["rating_stars"].show()
		
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
	def resetCurrentImages(self):
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/all/picreset.png"
		
		if self.resetPoster == True:
			self["poster"].instance.setPixmapFromFile(ptr)
		
		if self.resetBackdrop == True:
			self["mybackdrop"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def showPoster(self):
		printl("", self, "S")
		
		dwl_poster = False
		
		if fileExists(getPictureData(self.details, self.image_prefix, self.poster_postfix)):
			
			if self.whatPoster is not None:
				self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
				ptr = self.EXpicloadPoster.getData()
				
				if ptr is not None:
					self["poster"].instance.setPixmap(ptr)

		else:
			self.downloadPoster()
			
		printl("", self, "C")
		return
			
	#===========================================================================
	# 
	#===========================================================================
	def showBackdrop(self):
		printl("", self, "S")
		
		dwl_backdrop = False
				
		if fileExists(getPictureData(self.details, self.image_prefix, self.backdrop_postfix)):
			
			if self.whatBackdrop is not None:
				self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
				ptr = self.EXpicloadBackdrop.getData()
				
				if ptr is not None:
					self["mybackdrop"].instance.setPixmap(ptr)

		else:
			self.downloadBackdrop()
			
		printl("", self, "C")
		return
			
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
			downloadPage(str(download_url), getPictureData(self.details, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showPoster())
		
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
		
		if download_url == "" or download_url == "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/resources/plex.png":
			printl("no pic data available", self, "D")
			
		else:
			printl("starting download", self, "D")	
			downloadPage(download_url, getPictureData(self.details, self.image_prefix, self.backdrop_postfix)).addCallback(lambda _: self.showBackdrop())
				
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
		
