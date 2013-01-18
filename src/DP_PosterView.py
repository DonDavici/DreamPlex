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
	return DPS_PosterView

#===============================================================================
# 
#===============================================================================
class DPS_PosterView(DP_View):
	'''
	'''
	
	poster_postfix = "_poster.png"
	image_prefix = ""
	
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None):
		'''
		'''
		printl("", self, "S")
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, filter)
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		self.image_prefix = plexInstance.getServerName().lower()
		
		self.postersLeft = {}
		self.whatPoster_0_ = None
		self.postersRight = {}
		
		self.parentSeasonId = None
		self.parentSeasonNr = None
		self.isTvShow = False
		
		self.EXpicloadPoster_m3 = ePicLoad()
		self.EXpicloadPoster_m2 = ePicLoad()
		self.EXpicloadPoster_m1 = ePicLoad()
		self.EXpicloadPoster_0_ = ePicLoad()
		self.EXpicloadPoster_p1 = ePicLoad()
		self.EXpicloadPoster_p2 = ePicLoad()
		self.EXpicloadPoster_p3 = ePicLoad()
		
		
		self.EXscale = (AVSwitch().getFramebufferScale())
		
		self["poster_m3"] = Pixmap()
		self["poster_m2"] = Pixmap()
		self["poster_m1"] = Pixmap()
		self["poster_0_"] = Pixmap()
		self["poster_p1"] = Pixmap()
		self["poster_p2"] = Pixmap()
		self["poster_p3"] = Pixmap()
		
		self["seen_m3"] = Pixmap()
		self["seen_m2"] = Pixmap()
		self["seen_m1"] = Pixmap()
		self["seen_0_"] = Pixmap()
		self["seen_p1"] = Pixmap()
		self["seen_p2"] = Pixmap()
		self["seen_p3"] = Pixmap()
		
		self["title"] = Label()
		

		self["shortDescriptionContainer"] = Label()
		self["shortDescription"] = Label()
		
		self["key_red"] = StaticText(_("Sort: ") + _("Default"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(self.viewName[0])
		
		self.skinName = self.viewName[2]
		
		self.EXpicloadPoster_m3.PictureData.get().append(self.DecodeActionPoster_m3)
		self.EXpicloadPoster_m2.PictureData.get().append(self.DecodeActionPoster_m2)
		self.EXpicloadPoster_m1.PictureData.get().append(self.DecodeActionPoster_m1)
		self.EXpicloadPoster_0_.PictureData.get().append(self.DecodeActionPoster_0_)
		self.EXpicloadPoster_p1.PictureData.get().append(self.DecodeActionPoster_p1)
		self.EXpicloadPoster_p2.PictureData.get().append(self.DecodeActionPoster_p2)
		self.EXpicloadPoster_p3.PictureData.get().append(self.DecodeActionPoster_p3)
		
		self.onLayoutFinish.append(self.setPara)
		
		printl("", self, "C")
		
	#==============================================================================
	# 
	#==============================================================================
	def setPara(self):
		'''
		'''
		printl("", self, "S")
		
		self.EXpicloadPoster_m3.setPara([self["poster_m3"].instance.size().width(), self["poster_m3"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_m2.setPara([self["poster_m2"].instance.size().width(), self["poster_m2"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_m1.setPara([self["poster_m1"].instance.size().width(), self["poster_m1"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_0_.setPara([self["poster_0_"].instance.size().width(), self["poster_0_"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_p1.setPara([self["poster_p1"].instance.size().width(), self["poster_p1"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_p2.setPara([self["poster_p2"].instance.size().width(), self["poster_p2"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadPoster_p3.setPara([self["poster_p2"].instance.size().width(), self["poster_p2"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		
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
	def _refresh(self, selection):
		'''
		'''
		printl("", self, "S")
		printl("selection: " + str(selection), self, "S")
		
		if selection != None:
			self.postersLeft  = {}
			self.postersRight = {}
			self.selection = selection
			element = selection[1]
			pname = self.getFileNameFormSection(selection)
			self.whatPoster_0_ = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
			
			currentIndex = self["listview"].getIndex()
			printl("currentIndex: " + str(currentIndex), self, "D")
			listViewList = self["listview"].list
			count = int(len(listViewList))
			printl("count:" + str(count), self, "D")
			
			for i in range(1,4): # 1, 2, 3
				
				if currentIndex >= i:
					tmpSelectionMinus = listViewList[currentIndex - i]
					pname = self.getFileNameFormSection(tmpSelectionMinus)
					self.postersLeft[i] = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
					#self.whatPoster_m.i = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
					#self.setPoster("poster_m" + str(i), listViewList[currentIndex - i][1]["ArtPosterId"])
					
					#self.setPosterFromPixmap("seen_-" + str(i), listViewList[currentIndex - i][4])
				
				else:
					pass
					#self["poster_m" + str(i)].hide()
					#self["seen_-" + str(i)].hide()
				
				if (currentIndex + i) < count:
					printl("drinnen", self, "D")
					tmpSelectionPlus = listViewList[currentIndex + i]
					pname = self.getFileNameFormSection(tmpSelectionPlus)
					#self.whatPoster_p + i = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
					self.postersRight[i] = self.mediaPath + self.image_prefix + "_" + pname + self.poster_postfix
					printl("posterRIght an i " + str(self.postersRight[i]), self, "D")
					#self.setPoster("poster_p" + str(i), listViewList[currentIndex + i][1]["ArtPosterId"])
					#self.setPosterFromPixmap("seen_+" + str(i), listViewList[currentIndex + i][4])
				
				else:
					pass
					#self["poster_p" + str(i)].hide()
					#self["seen_+" + str(i)].hide()

			self.setText("title", selection[0])
			self.setText("shortDescription", element["Plot"].encode('utf8'), what=_("Overview"))
			
			self.showImages(element)
			
		else:
			self.setText("title", "no data retrieved")
			self.setText("shortDescription", "no data retrieved")
			
		printl("", self, "C")
		
	
	def getFileNameFormSection(self, selection):
		element = selection[1]
		#self.resetCurrentImages()
		
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
				
		self.checkL3(listViewList, currentIndex)
		self.checkL2(listViewList, currentIndex)
		self.checkL1(listViewList, currentIndex)
		self.checkP0(listViewList, currentIndex)
		self.checkR1(listViewList, currentIndex)
		self.checkR2(listViewList, currentIndex)
		self.checkR3(listViewList, currentIndex)
		
#===============================================================================
#		#self.setPoster("poster_0_", selection["ArtPoster"])
# 
#		currentIndex = self["listview"].getIndex()
#		listViewList = self["listview"].list
#		count = len(listViewList)
#		
#		for i in range(1,4): # 1, 2, 3
#			
#			if currentIndex >= i:
#				self.showPoster("poster" + str(i) + "__", listViewList[currentIndex - i][1]["ArtPosterId"])
#			
#			else:
#				self["poster" + str(i) + "__"].hide()
#			
#			if currentIndex + i < count:
#				self.showPoster("poster__" + str(i), listViewList[currentIndex + i][1]["ArtPosterId"])
#			
#			else:
#				self["poster__" + str(i)].hide()
#===============================================================================
		
		printl("", self, "C")
	
	
	
	def checkP0(self, listViewList, currentIndex):
		if fileExists(getPictureData(self.selection, self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showP0()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadP0(self.selection)
			pass
		
		
		
	def checkL1(self, listViewList, currentIndex):
			
		if fileExists(getPictureData(listViewList[currentIndex - 1], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showL1()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadL1(listViewList[currentIndex - 1])
			pass
		
	def checkL2(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex - 2], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showL2()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadL2(listViewList[currentIndex - 2])
			pass
	
	def checkL3(self, listViewList, currentIndex):	
		if fileExists(getPictureData(listViewList[currentIndex - 3], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showL3()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadL3(listViewList[currentIndex - 3])
			pass
		
	def checkR1(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex + 1], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showR1()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadR1(listViewList[currentIndex + 1])
			pass
		
	def checkR2(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex + 2], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showR2()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadR2(listViewList[currentIndex + 2])
			pass
		
		
	def checkR3(self, listViewList, currentIndex):
		if fileExists(getPictureData(listViewList[currentIndex + 3], self.image_prefix, self.poster_postfix)):
			#self.setText("postertext", "rendering ...")
			self.showR3()
		else:
			#self.setText("postertext", "downloading ...")
			self.downloadR3(listViewList[currentIndex + 3])
			pass
		
	
	def showP0(self):
		#self.setText("postertext", "rendering ...")
		
		if self.whatPoster_0_ is not None:
			self.EXpicloadPoster_0_.startDecode(self.whatPoster_0_)
		
		
		
	def showL1(self):
			
		#self.setText("postertext", "rendering ...")
		
		if self.postersLeft[1] is not None:
			printl("show me: " + str(self.postersLeft[1]), self, "D")
			test = self.EXpicloadPoster_m1.startDecode(self.postersLeft[1])

		
	def showL2(self):
		#self.setText("postertext", "rendering ...")
		
		if self.postersLeft[2] is not None:
			printl("show me: " + str(self.postersLeft[2]), self, "D")
			test = self.EXpicloadPoster_m2.startDecode(self.postersLeft[2])

	
	def showL3(self):	
		#self.setText("postertext", "rendering ...")
		
		if self.postersLeft[3] is not None:
			printl("show me: " + str(self.postersLeft[3]), self, "D")
			test = self.EXpicloadPoster_m3.startDecode(self.postersLeft[3])
		
	def showR1(self):
		#self.setText("postertext", "rendering ...")
		
		if self.postersRight[1] is not None:
			printl("show me: " + str(self.postersRight[1]), self, "D")
			test = self.EXpicloadPoster_p1.startDecode(self.postersRight[1])
		
	def showR2(self):

		#self.setText("postertext", "rendering ...")
		
		if self.postersRight[2] is not None:
			printl("show me: " + str(self.postersRight[2]), self, "D")
			test = self.EXpicloadPoster_p2.startDecode(self.postersRight[2])

		
		
	def showR3(self):

		#self.setText("postertext", "rendering ...")
		
		if self.postersRight[3] is not None:
			printl("show me: " + str(self.postersRight[3]), self, "D")
			test = self.EXpicloadPoster_p3.startDecode(self.postersRight[3])

	
	
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadL3(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showL3())
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadL2(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showL2())
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadL1(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showL1())
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadP0(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showP0())
		
		printl("", self, "C")
	
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadR1(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showR1())
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadR2(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showR2())
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def downloadR3(self, selection):
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
			downloadPage(str(download_url), getPictureData(self.selection, self.image_prefix, self.poster_postfix)).addCallback(lambda _: self.showR3())
		
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
	def DecodeActionPoster_m3(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.postersLeft[3] is not None:
			ptr = self.EXpicloadPoster_m3.getData()
			self["poster_m3"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_m2(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.postersLeft[2] is not None:
			ptr = self.EXpicloadPoster_m2.getData()
			self["poster_m2"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_m1(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.postersLeft[1] is not None:
			ptr = self.EXpicloadPoster_m1.getData()
			self["poster_m1"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_0_(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster_0_ is not None:
			ptr = self.EXpicloadPoster_0_.getData()
			self["poster_0_"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_p1(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.postersRight[1] is not None:
			ptr = self.EXpicloadPoster_p1.getData()
			self["poster_p1"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_p2(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.postersRight[2] is not None:
			ptr = self.EXpicloadPoster_p2.getData()
			self["poster_p2"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_p3(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.postersRight[3] is not None:
			ptr = self.EXpicloadPoster_p3.getData()
			self["poster_p3"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def resetCurrentImages(self):
		'''
		'''
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/all/picreset.png"
		self["poster_m3"].instance.setPixmapFromFile(ptr)
		self["poster_m2"].instance.setPixmapFromFile(ptr)
		self["poster_m1"].instance.setPixmapFromFile(ptr)
		self["poster_0_"].instance.setPixmapFromFile(ptr)
		self["poster_p1"].instance.setPixmapFromFile(ptr)
		self["poster_p2"].instance.setPixmapFromFile(ptr)
		self["poster_p3"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
