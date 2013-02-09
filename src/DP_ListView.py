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
from enigma import loadPNG, loadJPG
from Components.Label import Label
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
	return DPS_ListView

#===============================================================================
# 
#===============================================================================
class DPS_ListView(DP_View):
	'''
	'''
	backdrop_postfix = "_backdrop.jpg"
	poster_postfix = "_poster.jpg"
	image_prefix = ""
	plexInstance = None
	element = None
	parentSeasonId = None
	parentSeasonNr = None
	isTvShow = False
	playTheme = False
	startPlaybackNow = False
	itemsPerPage = 0
	whatPoster = None
	whatBackdrop = None

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None):
		'''
		'''
		printl("", self , "S")
		self.session = session
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, filter)
		
		self.setListViewElementsCount()
		
		# get needed config parameters
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		self.playTheme = config.plugins.dreamplex.playTheme.value
		
		# get data from plex library
		self.image_prefix = Singleton().getPlexInstance().getServerName().lower()
		
		# init skin elements
		self["poster"] 				= Pixmap()
		self["mybackdrop"] 			= Pixmap()

		self["audio"] 				= MultiPixmap()
		self["resolution"] 			= MultiPixmap()
		self["aspect"] 				= MultiPixmap()
		self["codec"] 				= MultiPixmap()
		self["rated"] 				= MultiPixmap()
	
		self["title"] 				= Label()
		self["tag"] 				= Label()
		self["shortDescription"] 	= Label()
		self["genre"] 				= Label()
		self["year"] 				= Label()
		self["runtime"] 			= Label()
		self["studio"] 				= Label()
		self["director"] 			= Label()
		self["mpaa"] 				= Label()
		self["total"] 				= Label()
		self["current"] 			= Label()
		self["backdroptext"]		= Label()
		self["postertext"]			= Label()
		
		self["key_red"] 			= StaticText(_("Sort: ") + _("Default"))
		self["key_green"] 			= StaticText(_("Filter: ") + _("None"))
		self["key_yellow"] 			= StaticText("")
		self["key_blue"] 			= StaticText(self.viewName[0])
		
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
		'''
		'''
		printl("", self, "S")
		printl("selection: " + str(selection), self, "D")
		
		# starting values
		changePoster = True
		changeBackdrop = True
		
		self.resetCurrentImages()
		
		if selection != None:
			self.selection = selection
			self.element = selection[1]
			
			self.details 		= selection[1]
			self.extraData 		= selection[2]
			self.context		= selection[3]
			
			# lets get all data we need to show the needed pictures
			# we also check if we want to play
			self.getPictureInformationToLoad()
			
			# if we are a show an if playtheme is enabled we start playback here
			if self.playTheme: 
				if self.startPlaybackNow:
					self.startThemePlayback()
			
			# lets set the new text information
			self.setText("backdroptext", "searching ...")
			self.setText("postertext", "searching ...")

			self.setText("title", 				self.details.get("title", " "))
			self.setText("tag", 				self.details.get("tagline", " ").encode('utf8'), True)
			self.setText("shortDescription", 	self.details.get("summary", " ").encode('utf8'), what=_("Overview"))
			self.setText("studio", 				self.details.get("studio", " - "))
			self.setText("year", 				str(self.details.get("year", " - ")))
			self.setText("mpaa", 				str(self.extraData.get("contentRating", " - ")))
			self.setText("director", 			str(self.details.get("director", " - ").encode('utf8')))
			self.setText("genre", 				str(self.details.get("genre", " - ").encode('utf8')))
			self.setText("runtime", 			str(self.details.get("runtime", " - ")))
			
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
			if changePoster == True:
				self.showPoster()
			
			if changeBackdrop == True:
				self.showBackdrop()
			
		else:
			self.setText("title", "no data retrieved")
			self.setText("shortDescription", "no data retrieved")
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def handleNavigationData(self):
		'''
		'''
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
	def handleRatedPixmaps(self):
		'''
		'''
		printl("", self, "S")

		mpaa = self.element.get("MPAA", "unknown").upper()
		printl("MPAA: " + str(mpaa), self, "D")
		
		if mpaa == "RATED PG-13" or "TV-14":
			found = True
			self["rated"].setPixmapNum(0)
		
		elif mpaa == "RATED PG" or "TV-PG":
			found = True
			self["rated"].setPixmapNum(1)
		
		elif mpaa == "RATED R":
			found = True
			self["rated"].setPixmapNum(2)
		
		elif mpaa == "NC-17" or "TV-MA":
			found = True
			self["rated"].setPixmapNum(3)
		
		elif mpaa == "NOT RATED" or mpaa == "RATED DE/0":
			found = True
			self["rated"].setPixmapNum(4)
		
		elif mpaa == "UNKNOWN" or mpaa == "RATED UNKNOWN" or mpaa == "":
			found = False
		
		else:
			printl("we have a value but no match!! mpaa: " + str(mpaa), self, "I")
			found = False
		
		if found == True:
			self["rated"].show()
		else:
			self["rated"].hide()
		#, TV-MA, 
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def handleSoundPixmaps(self):
		'''
		'''
		printl("", self, "S")
		
		audio = self.element.get("Sound", "unknown").upper()
		
		if audio == "DCA":
			found = True
			self["audio"].setPixmapNum(0)
		
		elif audio == "AC3":
			found = True
			self["audio"].setPixmapNum(1)
		
		elif audio == "STEREO":
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
		'''
		'''
		printl("", self, "S")

		resolution = self.element.get("Resolution", "unknown").upper()
		
		if resolution == "1080":
			found = True
			self["resolution"].setPixmapNum(0)
		
		elif resolution == "720":
			found = True
			self["resolution"].setPixmapNum(1)
		
		elif resolution == "480" or resolution == "576":
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
		'''
		'''
		printl("", self, "S")

		aspect = self.element.get("Aspect", "unknown").upper()
		
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
		'''
		'''
		printl("", self, "S")
		
		codec = self.element.get("Video", "unknown").upper()
		
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
		'''
		'''
		printl("", self, "S")
		
		try:
			popularity = float(self.element["Popularity"])
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
		'''
		'''
		printl("", self, "S")
		
		if self.element ["viewMode"] == "ShowSeasons":
			printl( "is ShowSeasons", self, "D")
			self.parentSeasonId = self.element ["ratingKey"]
			self.isTvShow = True
			self.startPlaybackNow = True
			bname = self.element["ratingKey"]
			pname = self.element["ratingKey"]
	
		elif self.element ["viewMode"] == "ShowEpisodes" and self.element["Id"] is None:
			printl( "is ShowEpisodes all entry", self, "D")
			bname = self.parentSeasonId
			pname = self.parentSeasonId
			self.startPlaybackNow = False
			
		elif self.element ["viewMode"] == "ShowEpisodes" and self.element["ratingKey"] != "":
			printl( "is ShowEpisodes special season",self, "D")
			self.parentSeasonNr = self.element["ratingKey"]			
			bname = self.parentSeasonId
			pname = self.element["ratingKey"]
			self.startPlaybackNow = False
		
		else:
			bname = self.element["ratingKey"]
			self.startPlaybackNow = False
			if self.isTvShow is True:
				pname = self.parentSeasonNr
				# we dont want to have the same poster downloaded and used for each episode
				changePoster = False
			else:
				pname = self.element["ratingKey"]
			
		self.whatPoster = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
		self.whatBackdrop = self.mediaPath + self.image_prefix + "_" + bname + self.backdrop_postfix
		
		printl("", self, "C")
	#===========================================================================
	# 
	#===========================================================================
	def close(self, arg=None):
		'''
		'''
		printl("", self, "S")
		
		self.session.nav.stopService()
		super(getViewClass(), self).close(arg)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def playEntry(self, entry):
		'''
		'''
		printl("", self, "S")
		
		super(getViewClass(), self).playEntry(entry)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def sort(self):
		'''
		'''
		printl("", self, "S")
		
		text = "Sorted by: %s" % (_(self.activeSort[0]))
		self["key_red"].setText(text)
		super(getViewClass(), self).sort()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def filter(self):
		'''
		'''
		printl("", self, "S")
		
		if len(self.activeFilter[2]) > 0:
			#text = "%s: %s" % (_("Filter"), _(self.activeFilter[2])) #To little space
			text = "%s" % (_(self.activeFilter[2]))
		else:
			#text = "%s: %s" % (_("Filter"), _(self.activeFilter[0])) #To little space
			text = "%s" % (_(self.activeFilter[0]))

		self["key_green"].setText(text)
		super(getViewClass(), self).filter()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyUp(self):
		'''
		'''
		printl("", self, "S")
		
		self.onPreviousEntry()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyDown(self):
		'''
		'''
		printl("", self, "S")
		
		self.onNextEntry()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyLeft(self):
		'''
		'''
		printl("", self, "S")
		
		self.onPreviousPage()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyRight(self):
		'''
		'''
		printl("", self, "S")
		
		self.onNextPage()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def resetCurrentImages(self):
		'''
		'''
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/all/picreset.png"
		#self["poster"].instance.setPixmapFromFile(ptr)
		self["mybackdrop"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def showPoster(self):
		'''
		'''
		printl("", self, "S")
		
		dwl_poster = False
		
		if fileExists(getPictureData(self.selection, self.image_prefix, self.poster_postfix)):
			self.setText("postertext", "rendering ...")
			
			if self.whatPoster is not None:
				self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
				ptr = self.EXpicloadPoster.getData()
				self["poster"].instance.setPixmap(ptr.__deref__())
		else:
			self.setText("postertext", "downloading ...")
			self.downloadPoster()
			
		printl("", self, "C")
		return
			
	#===========================================================================
	# 
	#===========================================================================
	def showBackdrop(self):
		'''
		'''
		printl("", self, "S")
		
		dwl_backdrop = False
				
		if fileExists(getPictureData(self.selection, self.image_prefix, self.backdrop_postfix)):
			self.setText("backdroptext", "rendering ...")
			
			if self.whatBackdrop is not None:
				self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
				ptr = self.EXpicloadBackdrop.getData()
				self["mybackdrop"].instance.setPixmap(ptr.__deref__())
		else:
			self.setText("backdroptext", "downloading ...")
			self.downloadBackdrop()
			
		printl("", self, "C")
		return
			
	#===========================================================================
	# 
	#===========================================================================
	def downloadPoster(self):
		'''
		'''
		printl("", self, "S")
		
		download_url = self.selection[1]["thumb"]
		printl( "download url " + download_url, self, "D")
		
		if download_url == "" or download_url == "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/resources/plex.png":
			printl("no pic data available", self, "D")
			self.setText("postertext", "not existing ...")
		
		else:
			printl("starting download", self, "D")
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showPoster())
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def downloadBackdrop(self):
		'''
		'''
		printl("", self, "S")
		
		download_url = self.selection[1]["fanart_image"]
		printl( "download url " + download_url, self, "D")	
		
		if download_url == "" or download_url == "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/resources/plex.png":
			printl("no pic data available", self, "D")
			self.setText("backdroptext", "not existing ...")
			
		else:
			printl("starting download", self, "D")	
			downloadPage(download_url, getPictureData(self.selection, self.image_prefix, self.backdrop_postfix)).addCallback(lambda _: self.showBackdrop())
				
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def setListViewElementsCount(self):
		'''
		'''
		printl("", self, "S")
		
		desktop = getDesktop(0).size().width()
		if desktop == 720:
			self.itemsPerPage = int(12)
		elif desktop == 1024:
			self.itemsPerPage = int(12)
		elif desktop == 1280:
			self.itemsPerPage = int(6)
			
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def startThemePlayback(self):
		'''
		'''
		printl("", self, "S")
		
		printl("start pĺaying theme", self, "I")
		accessToken = Singleton().getPlexInstance().g_myplex_accessToken
		theme = self.element["theme"]
		server = self.element["server"]
		printl("theme: " + str(theme), self, "D")
		url = "http://" + str(server) + str(theme) + "?X-Plex-Token=" + str(accessToken)
		sref = "4097:0:0:0:0:0:0:0:0:0:%s" % quote_plus(url)
		printl("sref: " + str(sref), self, "D")
		self.session.nav.stopService()
		self.session.nav.playService(eServiceReference(sref))
		
		printl("", self, "C")
		
	#==============================================================================
	# 
	#==============================================================================
	def setPara(self):
		'''
		deprecaded for now because we have only jpg
		'''
		printl("", self, "S")
		
		self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadBackdrop.setPara([self["mybackdrop"].instance.size().width(), self["mybackdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		
		printl("", self, "C")