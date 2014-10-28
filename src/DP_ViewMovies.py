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
from DP_View import DP_View

from __common__ import printl2 as printl, encodeThat
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

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, viewClass, libraryName, loadLibraryFnc, viewParams):
		printl("", self , "S")

		DP_View.__init__(self, viewClass, libraryName, loadLibraryFnc, viewParams)

		self.setTitle(_("Movies"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _refresh(self):
		printl("", self, "S")

		# we use this for filtermode at startup
		self.filterableContent = True

		# handle pictures
		self.changeBackdrop = True
		self.changePoster = True

		if "ratingKey" in self.details:
			self.pname = self.details["ratingKey"]
			self.bname = self.details["ratingKey"]
		else:
			self.pname = "temp"
			self.bname = "temp"

		# handle content
		self["title"].setText(encodeThat(self.details.get("title", " ")))
		self["tag"].setText(encodeThat(self.details.get("tagline", " ")))
		self["shortDescription"].setText(encodeThat(self.details.get("summary", " ")))
		self["cast"].setText(encodeThat(self.details.get("cast", " ")))
		self["writer"].setText(encodeThat(self.details.get("writer", " ")))
		self["director"].setText(encodeThat(self.details.get("director", " ")))
		self["studio"].setText(encodeThat(self.details.get("studio", " ")))
		self["genre"].setText(encodeThat(self.details.get("genre", " - ")))
		self["year"].setText(str(self.details.get("year", " - ")))

		# technical details
		self.mediaDataArr = self.details["mediaDataArr"][0]
		self.parts = self.mediaDataArr["Parts"][0]

		self["videoCodec"].setText(self.mediaDataArr.get("videoCodec", " - "))
		self["bitrate"].setText(self.mediaDataArr.get("bitrate", " - "))
		self["videoFrameRate"].setText(self.mediaDataArr.get("videoFrameRate", " - "))
		self["audioChannels"].setText(self.mediaDataArr.get("audioChannels", " - "))
		self["aspectRatio"].setText(self.mediaDataArr.get("aspectRatio", " - "))
		self["videoResolution"].setText(self.mediaDataArr.get("videoResolution", " - "))
		self["audioCodec"].setText(self.mediaDataArr.get("audioCodec", " - "))
		self["file"].setText(encodeThat(self.parts.get("file", " - ")))

		if self.fastScroll == False or self.showMedia == True:
			# handle all pixmaps
			self.handlePopularityPixmaps()
			self.handleCodecPixmaps()
			self.handleAspectPixmaps()
			self.handleResolutionPixmaps()
			self.handleRatedPixmaps()
			self.handleSoundPixmaps()

		# final sets
		self.setDuration()
		self.setMediaFunctions()

		# now gather information for pictures
		self.getPictureInformationToLoad()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first we call the the rest of the onEnter from super
		super(DPS_ViewMovies,self).onLeave()

		# we do the refresh here to be able to handle directory content
		self.refresh()

		printl("", self, "C")