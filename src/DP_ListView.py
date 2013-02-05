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
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.AVSwitch import AVSwitch

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

		self["poster"] = Pixmap()
		self["mybackdrop"] = Pixmap()

		self["audio_unknown"] = Pixmap()
		self["audio_dts"] = Pixmap()
		self["audio_ac3"] = Pixmap()
		self["audio_stereo"] = Pixmap()
		
		self["resolution_unknown"] = Pixmap()
		self["resolution_1080"] = Pixmap()
		self["resolution_720"] = Pixmap()
		self["resolution_sd"] = Pixmap()
		
		self["aspect_unknown"] = Pixmap()
		self["aspect_wide"] = Pixmap()
		self["aspect_43"] = Pixmap()
		
		self["codec_unknown"] = Pixmap()
		self["codec_h264"] = Pixmap()
		self["codec_ts"] = Pixmap()
		
		self["rated_unknown"] = Pixmap()
		self["rated_nc17"] = Pixmap()
		self["rated_g"] = Pixmap()
		self["rated_pg"] = Pixmap()
		self["rated_pg13"] = Pixmap()
		self["rated_r"] = Pixmap()
		
		self["title"] = Label()
		self["tag"] = Label()
		self["shortDescription"] = Label()
		self["genre"] = Label()
		self["year"] = Label()
		self["runtime"] = Label()
		self["studio"] = Label()
		self["director"] = Label()
		self["mpaa"] = Label()
		self["total"] = Label()
		self["current"] = Label()
		self["quality"] = Label()
		self["sound"] = Label()
		self["backdroptext"]= Label()
		self["postertext"]= Label()
		
		self["key_red"] = StaticText(_("Sort: ") + _("Default"))
		self["key_green"] = StaticText(_("Filter: ") + _("None"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(self.viewName[0])
		
		self.EXpicloadPoster = ePicLoad()
		self.EXpicloadBackdrop = ePicLoad()
		
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
		
		self.onLayoutFinish.append(self.setPara)
	
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
			
			codec = "unknown"
			if element.has_key("Video"):
				codec = element["Video"]
				printl("Video: " + str(codec), self, "D")
				
				if codec == "h264":
					self["codec_unknown"].instance.hide()
					self["codec_h264"].instance.show()
					self["codec_ts"].instance.hide()
				
				elif codec == "ts":
					self["codec_unknown"].instance.hide()
					self["codec_h264"].instance.hide()
					self["codec_ts"].instance.show()
				else:
					self["codec_unknown"].instance.show()
					self["codec_h264"].instance.hide()
					self["codec_ts"].instance.hide()
			else:
				self["codec_unknown"].instance.show()
				self["codec_h264"].instance.hide()
				self["codec_ts"].instance.hide()
				
				
			aspect = "unknown"
			if element.has_key("Aspect"):
				aspect = element["Aspect"]
				printl("Aspect: " + str(aspect), self, "D")
				
				if aspect == "1.78":
					self["aspect_unknown"].instance.hide()
					self["aspect_wide"].instance.hide()
					self["aspect_43"].instance.show()
				elif aspect == "2.35":
					self["aspect_unknown"].instance.hide()
					self["aspect_wide"].instance.show()
					self["aspect_43"].instance.hide()
				else:
					self["aspect_unknown"].instance.show()
					self["aspect_wide"].instance.hide()
					self["aspect_43"].instance.hide()
			
			else:
				self["aspect_unknown"].instance.show()
				self["aspect_wide"].instance.hide()
				self["aspect_43"].instance.hide()
			
			
			
			res = "unknown"
			if element.has_key("Resolution"):
				res = element["Resolution"]
				printl("Resolution: " + str(res), self, "D")
				
				if res == "1080":
					self["resolution_unknown"].instance.hide()
					self["resolution_1080"].instance.show()
					self["resolution_720"].instance.hide()
					self["resolution_sd"].instance.hide()
				elif res == "720":
					self["resolution_unknown"].instance.hide()
					self["resolution_1080"].instance.hide()
					self["resolution_720"].instance.show()
					self["resolution_sd"].instance.hide()
				else:
					self["resolution_unknown"].instance.hide()
					self["resolution_1080"].instance.hide()
					self["resolution_720"].instance.hide()
					self["resolution_sd"].instance.show()
			else:
				self["resolution_unknown"].instance.show()
				self["resolution_1080"].instance.hide()
				self["resolution_720"].instance.hide()
				self["resolution_sd"].instance.hide()
			
			snd = "unknown"
			if element.has_key("Sound"):
				snd = element["Sound"].upper()
				printl("sound: " + str(snd), self, "D")
			
				if snd == "DCA" or snd == "DTS":
					self["audio_unknown"].instance.hide()
					self["audio_dts"].instance.show()
					self["audio_ac3"].instance.hide()
					self["audio_stereo"].instance.hide()
					
				elif snd == "AC3":
					self["audio_unknown"].instance.hide()
					self["audio_dts"].instance.hide()
					self["audio_ac3"].instance.show()
					self["audio_stereo"].instance.hide()
					
				elif snd == "STEREO":
					self["audio_unknown"].instance.hide()
					self["audio_dts"].instance.hide()
					self["audio_ac3"].instance.hide()
					self["audio_stereo"].instance.show()
				
			else:
				self["audio_unknown"].instance.show()
				self["audio_dts"].instance.hide()
				self["audio_ac3"].instance.hide()
				self["audio_stereo"].instance.hide()
			
			mpaa = "unknown"
			if element.has_key("MPAA"):
				mpaa = element["MPAA"].upper()
				printl("MPAA: " + str(mpaa), self, "D")
				
				if mpaa == "RATED PG-13":
					self["rated_unknown"].instance.hide()
					self["rated_nc17"].instance.hide()
					self["rated_g"].instance.hide()
					self["rated_pg"].instance.hide()
					self["rated_pg13"].instance.show()
					self["rated_r"].instance.hide()
					
				elif mpaa == "RATED PG":
					self["rated_unknown"].instance.hide()
					self["rated_nc17"].instance.hide()
					self["rated_g"].instance.hide()
					self["rated_pg"].instance.show()
					self["rated_pg13"].instance.hide()
					self["rated_r"].instance.hide()
				
				elif mpaa == "RATED R":
					self["rated_unknown"].instance.hide()
					self["rated_nc17"].instance.hide()
					self["rated_g"].instance.hide()
					self["rated_pg"].instance.hide()
					self["rated_pg13"].instance.hide()
					self["rated_r"].instance.show()
				
				elif mpaa == "NC-17":
					self["rated_unknown"].instance.hide()
					self["rated_nc17"].instance.show()
					self["rated_g"].instance.hide()
					self["rated_pg"].instance.hide()
					self["rated_pg13"].instance.hide()
					self["rated_r"].instance.hide()
				
				else:
					self["rated_unknown"].instance.show()
					self["rated_nc17"].instance.hide()
					self["rated_g"].instance.hide()
					self["rated_pg"].instance.hide()
					self["rated_pg13"].instance.hide()
					self["rated_r"].instance.hide()
			
			else:
				self["rated_unknown"].instance.show()
				self["rated_nc17"].instance.hide()
				self["rated_g"].instance.hide()
				self["rated_pg"].instance.hide()
				self["rated_pg13"].instance.hide()
				self["rated_r"].instance.hide()
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
			
			itemsPerPage = self.itemsPerPage
			itemsTotal = self["listview"].count()
			correctionVal = 0.5
			
			if (itemsTotal%itemsPerPage) == 0:
				correctionVal = 0
			
			pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + correctionVal))
			pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))
			
			self.setText("total", _("Total:") + ' ' + str(itemsTotal))
			self.setText("current", _("Pages:") + ' ' + str(pageCurrent) + "/" + str(pageTotal))
			
			self.showPoster() # start decoding image
			self.showBackdrop() # start decoding image
			
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

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/all/picreset.png"
		self["poster"].instance.setPixmapFromFile(ptr)
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
				self.EXpicloadPoster.startDecode(self.whatPoster)
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
				self.EXpicloadBackdrop.startDecode(self.whatBackdrop)
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