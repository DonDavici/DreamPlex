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
import datetime
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
		printl("viewMode: " + str(self.details ["viewMode"]), self, "D")

		if self.details ["viewMode"] == "ShowAlbums":
			printl( "is ShowAlbums", self, "D")
			self.parentSeasonId = self.details ["ratingKey"]
			self.bname = self.details["ratingKey"]
			self.pname = self.details["ratingKey"]
			self.changeBackdrop = True
			self.changePoster = True
			self.resetPoster = True
			self.resetBackdrop = True

		elif self.details ["viewMode"] == "ShowTracks":
			printl( "is ShowTracks", self, "D")
			self.bname = self.parentSeasonId
			self.pname = self.details["ratingKey"]
			self.changeBackdrop = True
			self.changePoster = True
			self.resetPoster = False
			self.resetBackdrop = False

		else:
			printl( "is playable content",self, "D")
			self.bname = self.details["ratingKey"]

			if self.parentSeasonId is not None:
				self.pname = self.parentSeasonId
			else:
				self.pname = self.details["parentRatingKey"]
			# we dont want to have the same poster downloaded and used for each episode
			self.changePoster = False
			self.changeBackdrop = True

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
	def onEnter(self):
		printl("", self, "S")

		# first we call the the rest of the onEnter from super
		super(DPS_ViewMusic,self).onEnter()

		# this is the part we extend
		#if self.viewMode == "ShowAlbums" or self.viewMode == "ShowTracks":
		self.processGuiElements(self.viewMode)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first we call the the rest of the onEnter from super
		super(DPS_ViewMusic,self).onLeave()

		self.restoreElementsInViewStep()

		printl("", self, "C")
