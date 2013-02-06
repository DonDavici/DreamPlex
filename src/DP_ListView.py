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
	playTheme = False
	plexInstance = None
	
	itemsPerPage = 0

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
		
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		self.playTheme = config.plugins.dreamplex.playTheme.value
		
		self.EXscale = (AVSwitch().getFramebufferScale())
		
		self.whatPoster = None
		self.whatBackdrop = None
		
		instance = Singleton()
		self.plexInstance = instance.getPlexInstance()
		self.image_prefix = self.plexInstance.getServerName().lower()

		self.parentSeasonId = None
		self.parentSeasonNr = None
		self.isTvShow = False

		#self.EXpicloadPoster 		= ePicLoad()
		#self.EXpicloadBackdrop 	= ePicLoad()
		
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

		#self.onLayoutFinish.append(self.setPara)
	
		printl("", self, "C")
	
	#==============================================================================
	# 
	#==============================================================================
	def setPara(self):
		'''
		'''
		printl("", self, "S")
		
		self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadBackdrop.setPara([self["mybackdrop"].instance.size().width(), self["mybackdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def _refresh(self, selection):
		'''
		'''
		printl("", self, "S")
		printl("selection: " + str(selection), self, "S")
		
		changePoster = True
		changeBackdrop = True
		
		self.resetCurrentImages()
		if selection != None:
			self.selection = selection
			element = selection[1]
					
			self.setText("backdroptext", "searching ...")
			self.setText("postertext", "searching ...")
			
			if element ["ViewMode"] == "ShowSeasons":
				#print "is ShowSeasons"
				self.parentSeasonId = element ["Id"]
				self.isTvShow = True
				bname = element["Id"]
				pname = element["Id"]
				
				# @TODO lets put this in a seperate play class
				if self.playTheme == True:
					printl("start pĺaying theme", self, "I")
					accessToken = self.plexInstance.g_myplex_accessToken
					theme = element["theme"]
					server = element["server"]
					printl("theme: " + str(theme), self, "D")
					url = "http://" + str(server) + str(theme) + "?X-Plex-Token=" + str(accessToken)
					sref = "4097:0:0:0:0:0:0:0:0:0:%s" % quote_plus(url)
					printl("sref: " + str(sref), self, "D")
					self.session.nav.stopService()
	 				self.session.nav.playService(eServiceReference(sref))
		
			elif element ["ViewMode"] == "ShowEpisodes" and element["Id"] is None:
				print "is ShowEpisodes all entry"
				bname = self.parentSeasonId
				pname = self.parentSeasonId
				
			elif element ["ViewMode"] == "ShowEpisodes" and element["Id"] != "":
				print "is ShowEpisodes special season"
				self.parentSeasonNr = element["Id"]			
				bname = self.parentSeasonId
				pname = element["Id"]
			
			else:
				#print "is ELSE"
				bname = element["Id"]
				if self.isTvShow is True:
					pname = self.parentSeasonNr
					# we dont want to have the same poster downloaded and used for each episode
					changePoster = False
				else:
					pname = element["Id"]
				
			self.whatPoster = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
			self.whatBackdrop = self.mediaPath + self.image_prefix + "_" + bname + self.backdrop_postfix
			
			self.setText("title", element.get("ScreenTitle", " "))
			self.setText("tag", element.get("Tag", " ").encode('utf8'), True)
			self.setText("shortDescription", element.get("Plot", " ").encode('utf8'), what=_("Overview"))
			self.setText("studio", element.get("Studio", " "))
			self.setText("year", str(element.get("Year", " ")))
			self.setText("mpaa", str(element.get("MPAA", " ")))
			self.setText("director", str(element.get("Director", " ").encode('utf8')))
			self.setText("genre", str(element.get("Genres", " t").encode('utf8')))
			self.setText("runtime", str(element.get("Runtime", " ")))
			
			try:
				popularity = float(element["Popularity"])
			except Exception, e: 
				popularity = 0
				printl( "error in popularity " + str(e),self, "D")
				
			self["rating_stars"].setValue(int(popularity) * 10)
			self["rating_stars"].show()
			
			
			#CODEC
			codec = element.get("Video", "unknown").upper()
			if codec == "1.78":
				found = True
				self["codec"].setPixmapNum(0)
			elif codec == "2.35":
				found = True
				self["codec"].setPixmapNum(1)
			elif codec == "unknown":
				found = False;
			else:
				printl("we have a value but no match!!", self, "D")
				found = False
			
			if found == True:
				self["codec"].show()
			else:
				self["codec"].hide()
			
			#ASPECT
			aspect = element.get("Aspect", "unknown").upper()
			if aspect == "1.78":
				found = True
				self["aspect"].setPixmapNum(0)
			elif aspect == "2.35":
				found = True
				self["aspect"].setPixmapNum(1)
			elif aspect == "unknown":
				found = False;
			else:
				printl("we have a value but no match!!", self, "D")
				found = False
			
			if found == True:
				self["aspect"].show()
			else:
				self["aspect"].hide()
			
			# RESOLUTION
			resolution = element.get("Resolution", "unknown").upper()
			if resolution == "1080":
				found = True
				self["resolution"].setPixmapNum(0)
			elif resolution == "720":
				found = True
				self["resolution"].setPixmapNum(1)
			elif resolution == "unknown":
				found = False;
			else:
				printl("we have a value but no match!!", self, "D")
				found = False
			
			if found == True:
				self["resolution"].show()
			else:
				self["resolution"].hide()
			
			
			# SOUND
			audio = element.get("Sound", "unknown").upper()
			if audio == "DTS":
				found = True
				self["audio"].setPixmapNum(0)
			elif audio == "AC3":
				found = True
				self["audio"].setPixmapNum(1)
			elif audio == "STEREO":
				found = True
				self["audio_"].setPixmapNum(2)
			elif audio == "unknown":
				found = False;
			else:
				printl("we have a value but no match!!", self, "D")
				found = False
			
			if found == True:
				self["audio"].show()
			else:
				self["audio"].hide()

				
			# MPAA
			mpaa = element.get("MPAA", "unknown").upper()
			printl("MPAA: " + str(mpaa), self, "D")
			
			if mpaa == "RATED PG-13":
				found = True
				self["rated"].setPixmapNum(0)
			elif mpaa == "RATED PG":
				found = True
				self["rated"].setPixmapNum(1)
			elif mpaa == "RATED R":
				found = True
				self["rated"].setPixmapNum(2)
			elif mpaa == "NC-17":
				found = True
				self["rated"].setPixmapNum(3)
			elif mpaa == "unknown":
				found = False
			else:
				printl("we have a value but no match!!", self, "D")
				found = False
			
			if found == True:
				self["rated"].show()
			else:
				self["rated"].hide()

				
			itemsPerPage = self.itemsPerPage
			itemsTotal = self["listview"].count()
			correctionVal = 0.5
			
			if (itemsTotal%itemsPerPage) == 0:
				correctionVal = 0
			
			pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + correctionVal))
			pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))
			
			self.setText("total", _("Total:") + ' ' + str(itemsTotal))
			self.setText("current", _("Pages:") + ' ' + str(pageCurrent) + "/" + str(pageTotal))
			
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
		#print text
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
				#self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
				#ptr = self.EXpicloadPoster.getData()
				ptr = loadJPG(self.whatPoster)
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
				#self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
				#ptr = self.EXpicloadBackdrop.getData()
				ptr = loadJPG(self.whatBackdrop)
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
		
		download_url = self.selection[1]["ArtPoster"]
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
		
		download_url = self.selection[1]["ArtBackdrop"]
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
			self.itemsPerPage = int(15)
		elif desktop == 1024:
			self.itemsPerPage = int(15)
		elif desktop == 1280:
			self.itemsPerPage = int(8)
			
		printl("", self, "C")