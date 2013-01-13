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

from enigma import ePicLoad
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.AVSwitch import AVSwitch

from Tools.Directories import fileExists

from twisted.web.client import downloadPage

from DP_View import DP_View

from DPH_Arts import getTranscodeUrl, getPictureData

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

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None):
		'''
		'''
		printl("", self , "S")
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, filter)
		
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		
		self.EXpicloadPoster = ePicLoad()
		self.EXpicloadBackdrop = ePicLoad()
		
		self.EXscale = (AVSwitch().getFramebufferScale())
		
		self.whatPoster = None
		self.whatBackdrop = None

		self.parentSeasonId = None
		self.parentSeasonNr = None
		self.isTvShow = False

		self["poster"] = Pixmap()
		self["mybackdrop"] = Pixmap()
		self["title"] = Label()
		self["tag"] = Label()
		self["shortDescription"] = Label()
		self["genre"] = Label()
		self["year"] = Label()
		self["runtime"] = Label()
		self["total"] = Label()
		self["current"] = Label()
		self["quality"] = Label()
		self["sound"] = Label()

		self["key_red"] = StaticText(_("Sort: ") + _("Default"))
		self["key_green"] = StaticText(_("Filter: ") + _("None"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(self.viewName[0])
		
		for i in range(10):
			stars = "star" + str(i)
			self[stars] = Pixmap()
			if self[stars].instance is not None:
				self[stars].instance.hide()
		
		for i in range(10):
			stars = "nostar" + str(i)
			self[stars] = Pixmap()
		
		self.skinName = self.viewName[2]

		self.EXpicloadPoster.PictureData.get().append(self.DecodeActionPoster)
		self.EXpicloadBackdrop.PictureData.get().append(self.DecodeActionBackdrop)
	
		printl("", self, "C")
		
	#==============================================================================
	# 
	#==============================================================================
	def DecodeActionPoster(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster.getData()
			self["poster"].instance.setPixmap(ptr)
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionBackdrop(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadBackdrop.getData()
			self["mybackdrop"].instance.setPixmap(ptr)

		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def _refresh(self, selection):
		'''
		'''
		printl("", self, "S")
		printl("selection: " + str(selection), self, "S")
		
		
		self.resetCurrentImages()
		if selection != None:
			self.selection = selection
			element = selection[1]
		
			psuffix = "_poster.jpg"	
			bsuffix = "_backdrop.jpg"
			
			if element ["ViewMode"] == "ShowSeasons":
				#print "is ShowSeasons"
				self.parentSeasonId = element ["Id"]
				self.isTvShow = True
				bname = element["Id"]
				pname = element["Id"]
	
		
			elif element ["ViewMode"] == "ShowEpisodes" and element["Id"] is None:
				#print "is ShowEpisodes all entry"
				bname = self.parentSeasonId
				pname = self.parentSeasonId
				
			elif element ["ViewMode"] == "ShowEpisodes" and element["Id"] != "":
				#print "is ShowEpisodes special season"
				self.parentSeasonNr = element["Id"]			
				bname = self.parentSeasonId
				pname = element["Id"]
			
			else:
				#print "is ELSE"
				bname = element["Id"]
				if self.isTvShow is True:
					pname = self.parentSeasonNr
				else:
					pname = element["Id"]
	
			self.whatPoster = self.mediaPath + pname + psuffix
			self.whatBackdrop = self.mediaPath + bname + bsuffix
					
			self.setText("title", element["ScreenTitle"])
			self.setText("tag", element["Tag"], True)
			self.setText("shortDescription", element["Plot"].encode('utf8'), what=_("Overview"))
			
	
			res = "576i"
			if element.has_key("Resolution"):
				res = element["Resolution"]
			if res != "576" and res != "576i":
				self["quality"].setText(res)
			else:
				self["quality"].setText(" ")
			
			snd = "STEREO"
			if element.has_key("Sound"):
				snd = element["Sound"].upper()
			if snd != "STEREO":
				self["sound"].setText(snd)
			else:
				self["sound"].setText(" ")
			
			genres = ""
			for genre in element["Genres"]:
				genres += genre + " "
			genres = genres.strip()
	
			self.setText("genre", genres, what=_("Genre"))
			
			self.setText("runtime", str(element["Runtime"]))
			

			try:
				popularity = int(round(float(element["Popularity"])))
			except Exception, e: 
				popularity = 0
				printl( "error in popularity " + str(e),self, "D")
				

					
			for i in range(popularity):
				if self["star" + str(i)].instance is not None:
					self["star" + str(i)].instance.show()
			
			for i in range(10 - popularity):
				if self["star" + str(9 - i)].instance is not None:
					self["star" + str(9 - i)].instance.hide()
			
			itemsPerPage = int(12)
			itemsTotal = self["listview"].count()
			correctionVal = 0.5
			if (itemsTotal%itemsPerPage) == 0:
				correctionVal = 0
			pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + correctionVal))
			pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))
			self.setText("total", _("Total:") + ' ' + str(itemsTotal))
			self.setText("current", _("Pages:") + ' ' + str(pageCurrent) + "/" + str(pageTotal))
			
			self.showImages()
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
	def onKeyUpQuick(self):
		'''
		'''
		printl("", self, "S")
		
		self.onPreviousEntryQuick()
		
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
	def onKeyDownQuick(self):
		'''
		'''
		printl("", self, "S")
		
		self.onNextEntryQuick()
		
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

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/all/picreset.png"
		self["poster"].instance.setPixmapFromFile(ptr)
		self["mybackdrop"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def showImages(self):
		'''
		'''
		printl("", self, "S")
		
		dwl_poster = False
		dwl_backdrop = False
		
		if fileExists(getPictureData(self.selection, self.poster_postfix)):
			self.showRealPoster()
		else:
			dwl_poster = True
			
		
		if fileExists(getPictureData(self.selection, self.backdrop_postfix)):
			self.showRealBackdrop()
		else:
			dwl_backdrop = True

	
		if dwl_poster == True:
			self.downloadPoster()
			
			printl("", self, "C")
			return
		
		if dwl_backdrop == True:
			self.downloadBackdrop()
			
			printl("", self, "C")
			return
		
	#===========================================================================
	# 
	#===========================================================================
	def showRealPoster(self):
		'''
		'''
		printl("", self, "S")
		printl("show_poster " + self.whatPoster, self, "I")

		if self.whatPoster is not None:
			self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
			self.EXpicloadPoster.startDecode(self.whatPoster)
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def showRealBackdrop(self):
		'''
		'''
		printl("", self, "S")
		printl( "show_backdrop " + self.whatBackdrop, self, "I")

		if self.whatBackdrop is not None:
			self.EXpicloadBackdrop.setPara([self["mybackdrop"].instance.size().width(), self["mybackdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
			self.EXpicloadBackdrop.startDecode(self.whatBackdrop)
		
		printl("", self, "C")
			
	#===========================================================================
	# 
	#===========================================================================
	def downloadPoster(self):
		'''
		'''
		printl("", self, "S")
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		token = plexInstance.getAccessToken()
		
		download_url = getTranscodeUrl("ArtPoster", self.selection, str(182), str(268))
		if token != None:
			download_url += token

		printl( "download url " + download_url, self, "D")
		downloadPage(str(download_url), getPictureData(self.selection, self.poster_postfix)).addCallback(lambda _: self.downloadCallback())
		
		printl("", self, "C")


	#===========================================================================
	# 
	#===========================================================================
	def downloadBackdrop(self):
		'''
		'''
		printl("", self, "S")
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		token = plexInstance.getAccessToken()
		
		download_url = getTranscodeUrl("ArtBackdrop", self.selection, str(450), str(260))
		
		if token != None:
			download_url += token
		printl( "download url " + download_url, self, "D")
		
		downloadPage(download_url, getPictureData(self.selection, self.backdrop_postfix)).addCallback(lambda _: self.downloadCallback())
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadCallback(self):
		'''
		'''
		printl("", self, "S")
		
		self.showImages() 
		
		printl("", self, "C")
