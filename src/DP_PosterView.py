# -*- coding: utf-8 -*-

import os

from enigma import ePicLoad
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.AVSwitch import AVSwitch

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

from DP_View import DP_View
from twisted.web.client import downloadPage
from DPH_Arts import getTranscodeUrl, getPictureData
from Tools.Directories import fileExists

#------------------------------------------------------------------------------------------

def getViewClass():
	return DPS_PosterView

class DPS_PosterView(DP_View):
	
	poster_postfix = "_poster.png"
	
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None):
		'''
		'''
		printl("", self, "S")
		
		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, sort, filter)
		
		self.EXpicloadPoster3__ = ePicLoad()
		self.EXpicloadPoster2__ = ePicLoad()
		self.EXpicloadPoster1__ = ePicLoad()
		self.EXpicloadPoster_0_ = ePicLoad()
		self.EXpicloadPoster__1 = ePicLoad()
		self.EXpicloadPoster__2 = ePicLoad()
		self.EXpicloadPoster__3 = ePicLoad()
		
		
		self.EXscale = (AVSwitch().getFramebufferScale())
		
		self["poster3__"] = Pixmap()
		self["poster2__"] = Pixmap()
		self["poster1__"] = Pixmap()
		self["poster_0_"] = Pixmap()
		self["poster__1"] = Pixmap()
		self["poster__2"] = Pixmap()
		self["poster__3"] = Pixmap()
		
		self["title"] = Label()
		

		self["shortDescriptionContainer"] = Label()
		self["shortDescription"] = Label()
		
		self["key_red"] = StaticText(_("Sort: ") + _("Default"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(self.viewName[0])
		
		self.skinName = self.viewName[2]
		
		self.EXpicloadPoster3__.PictureData.get().append(self.DecodeActionPoster3__)
		self.EXpicloadPoster2__.PictureData.get().append(self.DecodeActionPoster2__)
		self.EXpicloadPoster1__.PictureData.get().append(self.DecodeActionPoster1__)
		self.EXpicloadPoster_0_.PictureData.get().append(self.DecodeActionPoster_0_)
		self.EXpicloadPoster__1.PictureData.get().append(self.DecodeActionPoster__1)
		self.EXpicloadPoster__2.PictureData.get().append(self.DecodeActionPoster__2)
		self.EXpicloadPoster__3.PictureData.get().append(self.DecodeActionPoster__3)
		
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
		
		element = selection[1]
		self.resetCurrentImages()
		
		if selection != None:
			
			self.setText("title", selection[0])
			self.setText("shortDescription", element["Plot"], what=_("Overview"))	
			
			self.showImages(element)
			
		else:
			self.setText("title", "no data retrieved")
			self.setText("shortDescription", "no data retrieved")
			
		printl("", self, "C")
		
	
	def showImages(self, selection):
		'''
		'''
		printl("", self, "S")
		
		dwl_poster3__ = False
		dwl_poster2__ = False
		dwl_poster1__ = False
		dwl_poster_0_ = False
		dwl_poster__1 = False
		dwl_poster__2 = False
		dwl_poster__3 = False
		
		if fileExists(getPictureData(self.selection, self.poster_postfix)):
			self.showRealPoster()
		else:
			dwl_poster_0_ = True
		
		self.setPoster("poster_0_", selection[1]["ArtPosterId"])

		currentIndex = self["listview"].getIndex()
		listViewList = self["listview"].list
		count = len(listViewList)
		
		for i in range(1,4): # 1, 2, 3
			
			if currentIndex >= i:
				self.setPoster("poster" + str(i) + "__", listViewList[currentIndex - i][1]["ArtPosterId"])
			
			else:
				self["poster" + str(i) + "__"].hide()
			
			if currentIndex + i < count:
				self.setPoster("poster__" + str(i), listViewList[currentIndex + i][1]["ArtPosterId"])
			
			else:
				self["poster__" + str(i)].hide()
		
		printl("", self, "C")
	#===========================================================================
	# 
	#===========================================================================
	def setPoster(self, posterName, artId):
		'''
		'''
		printl("", self, "S")
		
		if self[posterName].instance is not None:
			self[posterName].show()
			poster = config.plugins.pvmc.mediafolderpath.value + artId + "_poster"
			
			if os.access(poster + self.postersize + ".png", os.F_OK):
				self[posterName].instance.setPixmapFromFile(poster + self.postersize + ".png")
			
			else:
				self[posterName].instance.setPixmapFromFile(config.plugins.pvmc.mediafolderpath.value + \
					"defaultposter" + self.postersize + ".png")
				
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
	def DecodeActionPoster3__(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster3__.getData()
			self["poster3__"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster2__(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster2__.getData()
			self["poster2__"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster1__(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster1__.getData()
			self["poster1__"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster_0_(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster_0_.getData()
			self["poster_0_"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster__1(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster__1.getData()
			self["poster__1"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster__2(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster__2.getData()
			self["poster__2"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def DecodeActionPoster__3(self, pictureInfo=""):
		'''
		'''
		printl("", self, "S")
		
		if self.whatPoster is not None:
			ptr = self.EXpicloadPoster__3.getData()
			self["poster__3"].instance.setPixmap(ptr)
			
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def resetCurrentImages(self):
		'''
		'''
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/all/picreset.png"
		self["poster3__"].instance.setPixmapFromFile(ptr)
		self["poster2__"].instance.setPixmapFromFile(ptr)
		self["poster1__"].instance.setPixmapFromFile(ptr)
		self["poster_0_"].instance.setPixmapFromFile(ptr)
		self["poster__1"].instance.setPixmapFromFile(ptr)
		self["poster__2"].instance.setPixmapFromFile(ptr)
		self["poster__3"].instance.setPixmapFromFile(ptr)
		
		printl("", self, "C")
