# -*- coding: utf-8 -*-

import os

from enigma import ePicLoad
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.AVSwitch import AVSwitch

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

from DP_View import DP_View
from twisted.web.client import downloadPage
from DPH_Arts import getPictureData

from Tools.Directories import fileExists

#===============================================================================
# 
#===============================================================================
def getViewClass():
	'''
	'''
	printl("", __name__, "S")
	
	printl("", __name__, "C")
	return DPS_ViewPoster

#===============================================================================
# 
#===============================================================================
class DPS_ViewPoster(DP_View):
	'''
	'''
	
	poster_postfix = "_poster.png"
	image_prefix = ""
	loadNext = False
	currentIndex = ""
	
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None):
		'''
		'''
		printl("", self, "S")
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, filter)
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		self.image_prefix = plexInstance.getServerName().lower()
		
		self.posters = {}
		
		self.parentSeasonId = None
		self.parentSeasonNr = None
		self.isTvShow = False
		
		self.EXpicloadPoster_P0 = ePicLoad()
		self.EXpicloadPoster_P1 = ePicLoad()
		self.EXpicloadPoster_P2 = ePicLoad()
		self.EXpicloadPoster_P3 = ePicLoad()
		self.EXpicloadPoster_P4 = ePicLoad()
		self.EXpicloadPoster_P5 = ePicLoad()

		self.EXscale = (AVSwitch().getFramebufferScale())
		
		self["poster_0"] = Pixmap()
		self["poster_1"] = Pixmap()
		self["poster_2"] = Pixmap()
		self["poster_3"] = Pixmap()
		self["poster_4"] = Pixmap()
		self["poster_5"] = Pixmap()
		
		self["seen_0"] = Pixmap()
		self["seen_1"] = Pixmap()
		self["seen_2"] = Pixmap()
		self["seen_3"] = Pixmap()
		self["seen_4"] = Pixmap()
		self["seen_5"] = Pixmap()

		
		self["title"] = Label()

		self["shortDescriptionContainer"] = Label()
		self["shortDescription"] = Label()
		
		self["key_red"] = StaticText(_("Sort: ") + _("Default"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(self.viewName[0])
		
		self.skinName = self.viewName[2]

		self.EXpicloadPoster_P0.PictureData.get().append(self.DecodeActionPoster_P0)	
		self.EXpicloadPoster_P1.PictureData.get().append(self.DecodeActionPoster_P1)
		self.EXpicloadPoster_P2.PictureData.get().append(self.DecodeActionPoster_P2)
		self.EXpicloadPoster_P3.PictureData.get().append(self.DecodeActionPoster_P3)
		self.EXpicloadPoster_P4.PictureData.get().append(self.DecodeActionPoster_P4)
		self.EXpicloadPoster_P5.PictureData.get().append(self.DecodeActionPoster_P5)
		
		self.onLayoutFinish.append(self.setPara)
		self.loadNext = True
		
		printl("", self, "C")
		
	#==============================================================================
	# 
	#==============================================================================
	def setPara(self):
		'''
		'''
		printl("", self, "S")
		
		self.EXpicloadPoster_P0.setPara([self["poster_0"].instance.size().width(), self["poster_0"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_P1.setPara([self["poster_1"].instance.size().width(), self["poster_1"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_P2.setPara([self["poster_2"].instance.size().width(), self["poster_2"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_P3.setPara([self["poster_3"].instance.size().width(), self["poster_3"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_P4.setPara([self["poster_4"].instance.size().width(), self["poster_4"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_P5.setPara([self["poster_5"].instance.size().width(), self["poster_5"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])

		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def setCustomTitle(self):
		'''
		'''
		printl("", self, "S")
		
		self.showPlot(False)
		super(getViewClass(), self).setCustomTitle()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def showPlot(self, visible):
		'''
		'''
		printl("", self, "S")
		
		self.isPlotHidden = visible

		if visible:
			self["shortDescriptionContainer"].show()
			self["shortDescription"].show()
		else:
			self["shortDescriptionContainer"].hide()
			self["shortDescription"].hide()
			
		printl("", self, "C")


	#===========================================================================
	# 
	#===========================================================================
	def refresh(self, changeBackdrop=True):
		'''
		'''
		printl("", self, "S")
		
		selection = self["listview"].getCurrent()
		currentIndex = self["listview"].getIndex()
		
		if int(currentIndex) not in self.posters:
			printl("currentIndex: " + str(currentIndex), self, "D")
			printl("self.posters: " + str(self.posters), self, "D")
			self.loadNext = True
			
		self._refresh(selection)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def _refresh(self, selection):
		'''
		'''
		printl("", self, "S")
		printl("selection: " + str(selection), self, "S")
		
		if selection != None:
			
			self.selection = selection
			element = selection[1]
			
			currentIndex = self["listview"].getIndex()
			printl("currentIndex: " + str(currentIndex), self, "D")
			self.currentIndex = currentIndex
			
			listViewList = self["listview"].list
			count = int(len(listViewList))
			printl("count:" + str(count), self, "D")
			
			if self.loadNext == True:
				self.posters  = {}
				for i in range(0,6): # 1, 2, 3, ..
					self.loadNext = False
					tmpSelectionMinus = listViewList[currentIndex + i]
					pname = self.getFileNameFormSection(tmpSelectionMinus)
					self.posters[currentIndex + i] = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
				
				self.showImages(element)
			
			self.setText("title", selection[0])
			self.setText("shortDescription", element["Plot"].encode('utf8'), what=_("Overview"))
			printl("posters: " + str(self.posters), self, "D")
			
			
		else:
			self.setText("title", "no data retrieved")
			self.setText("shortDescription", "no data retrieved")
			
		printl("", self, "C")
		
	
	#===========================================================================
	# 
	#===========================================================================
	def getFileNameFormSection(self, selection):
		element = selection[1]
		printl("element: " + str(element), self, "D")
		#self.resetCurrentImages()
		
		if element ["viewMode"] == "ShowSeasons":
			#print "is ShowSeasons"
			self.parentSeasonId = element ["Id"]
			self.isTvShow = True
			bname = element["Id"]
			pname = element["Id"]
	
		elif element ["viewMode"] == "ShowEpisodes" and element["Id"] is None:
			#print "is ShowEpisodes all entry"
			bname = self.parentSeasonId
			pname = self.parentSeasonId
			
		elif element ["viewMode"] == "ShowEpisodes" and element["Id"] != "":
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
				
		return pname
	
	#===========================================================================
	# 
	#===========================================================================
	def showImages(self, selection):
		'''
		'''
		printl("", self, "S")
		
		listViewList = self["listview"].list
		currentIndex = self["listview"].getIndex()
				
		self.check_P0(listViewList, currentIndex + 0)
		self.check_P1(listViewList, currentIndex + 1)
		self.check_P2(listViewList, currentIndex + 2)
		self.check_P3(listViewList, currentIndex + 3)
		self.check_P4(listViewList, currentIndex + 4)
		self.check_P5(listViewList, currentIndex + 5)
		
		printl("", self, "C")

	
	def check_P0(self, listViewList, currentIndex):
		if fileExists(getPictureData(self.selection, self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.show_P0(currentIndex)
		else:
			#self.setText("postertext", "downloading ...")
			self.download_P0(listViewList[currentIndex], currentIndex)
			pass
		
		
		
	def check_P1(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.show_P1(currentIndex)
		else:
			#self.setText("postertext", "downloading ...")
			self.download_P1(listViewList[currentIndex], currentIndex)
			pass
		
	def check_P2(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.show_P2(currentIndex)
		else:
			#self.setText("postertext", "downloading ...")
			self.download_P2(listViewList[currentIndex], currentIndex)
			pass
	
	def check_P3(self, listViewList, currentIndex):	
		if fileExists(getPictureData(listViewList[currentIndex], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.show_P3(currentIndex)
		else:
			#self.setText("postertext", "downloading ...")
			self.download_P3(listViewList[currentIndex], currentIndex)
			pass
		
	def check_P4(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.show_P4(currentIndex)
		else:
			#self.setText("postertext", "downloading ...")
			self.download_P4(listViewList[currentIndex], currentIndex)
			pass
		
	def check_P5(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.show_P5(currentIndex)
		else:
			#self.setText("postertext", "downloading ...")
			self.download_P5(listViewList[currentIndex], currentIndex)
			pass
		
		
	def show_P0(self, currentIndex):
		#self.setText("postertext", "rendering ...")
		
		if currentIndex in self.posters:
			printl("show_P0: " + str(currentIndex), self, "D")	
			printl("show me: " + str(self.posters[currentIndex]), self, "D")
			self.EXpicloadPoster_P0.startDecode(self.posters[currentIndex])
		
		
		
	def show_P1(self, currentIndex):
			
		#self.setText("postertext", "rendering ...")
		
		if currentIndex in self.posters:
			printl("show_P0: " + str(currentIndex), self, "D")	
			printl("show me: " + str(self.posters[currentIndex]), self, "D")
			self.EXpicloadPoster_P1.startDecode(self.posters[currentIndex])

		
	def show_P2(self, currentIndex):
		#self.setText("postertext", "rendering ...")
		
		if currentIndex in self.posters:
			printl("show_P0: " + str(currentIndex), self, "D")	
			printl("show me: " + str(self.posters[currentIndex]), self, "D")
			self.EXpicloadPoster_P2.startDecode(self.posters[currentIndex])

	
	def show_P3(self, currentIndex):	
		#self.setText("postertext", "rendering ...")
		
		if currentIndex in self.posters:
			printl("show_P0: " + str(currentIndex), self, "D")	
			printl("show me: " + str(self.posters[currentIndex]), self, "D")
			self.EXpicloadPoster_P3.startDecode(self.posters[currentIndex])
		
	def show_P4(self, currentIndex):
		#self.setText("postertext", "rendering ...")
		
		if currentIndex in self.posters:
			printl("show_P0: " + str(currentIndex), self, "D")	
			printl("show me: " + str(self.posters[currentIndex]), self, "D")
			self.EXpicloadPoster_P4.startDecode(self.posters[currentIndex])
		
	def show_P5(self, currentIndex):
		#self.setText("postertext", "rendering ...")
		
		if currentIndex in self.posters:
			printl("show_P0: " + str(currentIndex), self, "D")	
			printl("show me: " + str(self.posters[currentIndex]), self, "D")
			self.EXpicloadPoster_P5.startDecode(self.posters[currentIndex])

	#===========================================================================
	# 
	#===========================================================================
	def download_P0(self, selection, currentIndex):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.show_P0(currentIndex))
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def download_P1(self, selection, currentIndex):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.show_P1(currentIndex))
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def download_P2(self, selection, currentIndex):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.show_P2(currentIndex))
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def download_P3(self, selection, currentIndex):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.show_P3(currentIndex))
		
		printl("", self, "C")
	
	
	#===========================================================================
	# 
	#===========================================================================
	def download_P4(self, selection, currentIndex):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.show_P4(currentIndex))
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def download_P5(self, selection, currentIndex):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.show_P5(currentIndex))
		
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
	def playEntry(self, entry, flags, callback):
		'''
		'''
		printl("", self, "S")
		
		super(getViewClass(), self).playEntry(entry, flags, callback)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def sort(self):
		'''
		'''
		printl("", self, "S")
		
		text = "%s" % (_(self.activeSort[0]))
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
	def onKeyLeft(self):
		'''
		'''
		printl("", self, "S")
		
		self.onPreviousEntry()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyLeftQuick(self):
		'''
		'''
		printl("", self, "S")
		
		self.onPreviousEntryQuick()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyRight(self):
		'''
		'''
		printl("", self, "S")
		
		self.onNextEntry()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyRightQuick(self):
		'''
		'''
		printl("", self, "S")
		
		self.onNextEntryQuick()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyUp(self):
		'''
		'''
		printl("", self, "S")
		
		self.onPreviousPage()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyUpQuick(self):
		'''
		'''
		printl("", self, "S")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyDown(self):
		'''
		'''
		printl("", self, "S")
		
		self.onNextPage()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onKeyDownQuick(self):
		'''
		'''
		printl("", self, "S")
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def onKeyInfo(self):
		'''
		'''
		printl("", self, "S")
		
		self.showPlot(not self.isPlotHidden)
		
		printl("", self, "C")
		
#===============================================================================
# DECODE SECTION
#===============================================================================

	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_P0(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.posters[self.currentIndex + 0] is not None:
			ptr = self.EXpicloadPoster_P0.getData()
			self["poster_0"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_P1(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.posters[self.currentIndex + 1] is not None:
			ptr = self.EXpicloadPoster_P1.getData()
			self["poster_1"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_P2(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.posters[self.currentIndex + 2] is not None:
			ptr = self.EXpicloadPoster_P2.getData()
			self["poster_2"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_P3(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.posters[self.currentIndex + 3] is not None:
			ptr = self.EXpicloadPoster_P3.getData()
			self["poster_3"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_P4(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.posters[self.currentIndex + 4] is not None:
			ptr = self.EXpicloadPoster_P4.getData()
			self["poster_4"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_P5(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.posters[self.currentIndex + 5] is not None:
			ptr = self.EXpicloadPoster_P5.getData()
			self["poster_5"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def resetCurrentImages(self):
		'''
		'''
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/all/picreset.png"
		self["poster_0"].instance.setPixmapFromFile(ptr)
		self["poster_1"].instance.setPixmapFromFile(ptr)
		self["poster_2"].instance.setPixmapFromFile(ptr)
		self["poster_3"].instance.setPixmapFromFile(ptr)
		self["poster_4"].instance.setPixmapFromFile(ptr)
		self["poster_5"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
