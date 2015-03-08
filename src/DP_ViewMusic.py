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
from Components.config import config

from DP_View import DP_View

from __common__ import printl2 as printl, encodeThat
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
def getViewClass():
	printl("",__name__ , "S")

	printl("",__name__ , "C")
	return DPS_ViewMusic

#===============================================================================
#
#===============================================================================
class DPS_ViewMusic(DP_View):

	parentSeasonId = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, viewClass, libraryName, loadLibraryFnc, viewParams):
		printl("", self , "S")

		DP_View.__init__(self, viewClass, libraryName, loadLibraryFnc, viewParams)

		self.setTitle(_("Music"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _refresh(self):
		printl("", self, "S")

		# we use this for filtermode at startup
		self.filterableContent = True

		self.setMediaFunctions()

		if "type" in self.details:
			if self.details["type"] == "folder":
				self.fromDirectory = True
			else:
				self.fromDirectory = False

			# looks like we are just a directory
			if self.details["type"] == "folder":
				self.pname = "temp"
				self.bname = "temp"
				self.resetBackdrop = True
				self.resetPoster = True
				self.changePoster = False
				self.changeBackdrop = False
				self.fromDirectory = True
			elif self.details["type"] == "album" or self.details["type"] == "artist":
				if self.details["type"] == "album":
					self["title"].setText(encodeThat(self.details.get("title", " ")))
					self["leafCount"].setText(encodeThat(self.details.get("leafCount", " ")))

					self["shortDescription"].setText(encodeThat(self.details.get("summary", " ")))
					self["year"].setText(str(self.details.get("year", " - ")))

					self.toggleElementVisibilityWithLabel("year")
					self.toggleElementVisibilityWithLabel("genre")
					self["shortDescription"].show()

					self.hideMediaFunctions()
					self.hideMediaPixmaps()
				else:
					self["title"].setText(encodeThat(self.details.get("title", " ")))
					self["shortDescription"].setText(encodeThat(self.details.get("summary", " ")))
					self["genre"].setText(encodeThat(self.details.get("genre", " - ")))

					self.toggleElementVisibilityWithLabel("genre")
					self["shortDescription"].show()

				self.changePoster = True
				self.changeBackdrop = True
				self.resetBackdrop = True
				self.resetPoster = True
				self.hideMediaFunctions()
				self.hideMediaPixmaps()

				if "ratingKey" in self.details:
					self.pname = self.details["ratingKey"]
					self.bname = self.details["ratingKey"]
				else:
					if "parentRatingKey" in self.details:
						self.pname = self.details["parentRatingKey"]
						self.bname = self.details["parentRatingKey"]
					else:
						self.pname = "temp"
						self.bname = "temp"

			elif self.details["type"] == "track":
				self.resetBackdrop = False
				self.resetPoster = False
				self.setDuration()

				# technical details
				self.mediaDataArr = self.details["mediaDataArr"][0]
				self.parts = self.mediaDataArr["Parts"][0]

				self["bitrate"].setText(self.mediaDataArr.get("bitrate", " - "))
				self["audioChannels"].setText(self.mediaDataArr.get("audioChannels", " - "))
				self["audioCodec"].setText(self.mediaDataArr.get("audioCodec", " - "))
				self["file"].setText(encodeThat(self.parts.get("file", " - ")))

				# this is when we are coming from directory
				if self.fromDirectory:
					if "parentRatingKey" in self.details:
						self.pname = self.details["parentRatingKey"]
						self.bname = self.details["parentRatingKey"]
					else:
						self.pname = "temp"
						self.bname = "temp"

					self.changePoster = True
					self.changeBackdrop = True
				else:
					self.pname = "temp"
					self.bname = "temp"
					self.changePoster = False
					self.changeBackdrop = False

		else:
			raise Exception

		# now gather information for pictures
		self.getPictureInformationToLoad()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first we have to turn off filtermode or the keypress that is needed to refresh function names will be interpreted as filter action
		self.toggleFilterMode(quit=True)

		# first we call the the rest of the onEnter from super
		super(DPS_ViewMusic,self).onLeave()

		# first restore Elements
		self.restoreElementsInViewStep()

		self.initFilterMode()

		# we do the refresh here to be able to handle directory content
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onEnter(self):
		printl("", self, "S")

		# first we have to turn off filtermode or the keypress that is needed to refresh function names will be interpreted as filter action
		self.toggleFilterMode(quit=True)

		# first we call the the rest of the onEnter from super
		super(DPS_ViewMusic,self).onEnter()

		printl("", self, "C")

