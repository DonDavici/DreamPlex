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

from __common__ import printl2 as printl
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
	def getPictureInformationToLoad(self):
		printl("", self, "S")
		printl("currentViewMode: " + str(self.details ["currentViewMode"]), self, "D")

		self.lastPosterName = None
		self.lastBackdropName = None

		if "type" in self.details:
			if self.details["type"] == "album" or self.details["type"] == "artist":
				self.changePoster = True
				self.changeBackdrop = True
				self.resetBackdrop = True
				self.resetPoster = True
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

				self.lastPosterName = self.pname
				self.lastBackdropName = self.bname

			elif self.details["type"] == "track":
				self.resetBackdrop = False
				self.resetPoster = False

				# this is when we are coming from directory
				if self.lastPosterName is  None and self.lastBackdropName is  None:
					if "parentRatingKey" in self.details:
						self.pname = self.details["parentRatingKey"]
						self.bname = self.details["parentRatingKey"]
					else:
						self.pname = "temp"
						self.bname = "temp"

					self.changePoster = True
					self.changeBackdrop = True
				else:
					self.pname = self.lastPosterName
					self.bname = self.lastBackdropName
					self.changePoster = False
					self.changeBackdrop = False

		# looks like we are just a directory
		else:
			self.pname = "temp"
			self.bname = "temp"
			self.resetBackdrop = True
			self.resetPoster = True
			self.changePoster = False
			self.changeBackdrop = False

		if not self.usePicCache:
			self.pname = "temp"
			self.bname = "temp"
			self.mediaPath = config.plugins.dreamplex.logfolderpath.value

		printl("bname: " + str(self.bname), self, "D")
		printl("pname: " + str(self.pname), self, "D")
		self.whatPoster = self.mediaPath + self.image_prefix + "_" + self.pname + self.poster_postfix
		self.whatBackdrop = self.mediaPath + self.image_prefix + "_" + self.bname + self.backdrop_postfix

		printl("self.whatPoster : " + str(self.whatPoster ), self, "D")
		printl("self.whatBackdrop: " + str(self.whatBackdrop), self, "D")

		printl("", self, "C")

#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first we call the the rest of the onEnter from super
		super(DPS_ViewMusic,self).onLeave()

		# first restore Elements
		self.restoreElementsInViewStep()

		# we do the refresh here to be able to handle directory content
		self.refresh()

		printl("", self, "C")
