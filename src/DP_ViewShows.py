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
	return DPS_ViewShows

#===============================================================================
# 
#===============================================================================
class DPS_ViewShows(DP_View):

	parentSeasonId = None

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, viewClass, libraryName, loadLibraryFnc, viewParams):
		printl("", self , "S")

		DP_View.__init__(self, viewClass, libraryName, loadLibraryFnc, viewParams)

		self.setTitle(_("Shows"))

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getPictureInformationToLoad(self):
		printl("", self, "S")
		printl("currentViewMode: " + str(self.details ["currentViewMode"]), self, "D")

		if self.details ["currentViewMode"] == "ShowShows":
			printl( "is ShowShows", self, "D")
			self.parentSeasonId = self.details ["ratingKey"]
			self.isTvShow = True
			self.startPlaybackNow = True
			self.bname = self.details["ratingKey"]
			self.pname = self.details["ratingKey"]
			self.changeBackdrop = True
			self.changePoster = True
			self.resetPoster = True
			self.resetBackdrop = True

		elif self.details ["currentViewMode"] == "ShowSeasons":
			printl( "is ShowSeasons",self, "D")
			self.isTvShow = True
			self.parentSeasonNr = self.details["ratingKey"]
			self.bname = self.parentSeasonId
			self.pname = self.details["ratingKey"]
			self.startPlaybackNow = False
			self.changeBackdrop = False
			self.changePoster = True
			self.resetPoster = False
			self.resetBackdrop = False

		elif self.details ["currentViewMode"] == "ShowEpisodes":
			printl( "is ShowEpisodes specific season",self, "D")
			self.isTvShow = True
			self.bname = self.details["ratingKey"]
			self.pname = self.details["parentRatingKey"]
			self.startPlaybackNow = False
			self.changeBackdrop = False
			self.changePoster = True
			self.resetPoster = False
			self.resetBackdrop = False

		elif self.details ["currentViewMode"] == "ShowEpisodes" and self.details["ratingKey"] == "0":
			printl( "is ShowEpisodes all entry", self, "D")
			self.isTvShow = True
			self.bname = self.parentSeasonId
			self.pname = self.parentSeasonId
			self.startPlaybackNow = False
			self.changeBackdrop = True
			self.changePoster = True
			self.resetPoster = False
			self.resetBackdrop = False

		elif self.details["currentViewMode"] == "directMode":
			printl( "is directMode",self, "D")
			self.startPlaybackNow = True
			#self.isTvShow = True
			self.bname = self.details["ratingKey"]
			self.pname = self.details["grandparentRatingKey"]
			self.changeBackdrop = self.myParams["elements"]["backdrop"]["visible"]
			self.changePoster = self.myParams["elements"]["poster"]["visible"]
			self.resetPoster = True
			self.resetBackdrop = True

		else:
			printl( "is playable content",self, "D")
			self.bname = self.details["ratingKey"]
			self.startPlaybackNow = False

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
	def _refresh(self):
		printl("", self, "S")

		# first we call the the rest of the _refresh from super
		super(DPS_ViewShows,self)._refresh()

		if self.viewStep == 1 and not self.leaving and self.mediaContainer["title2"] != "By Folder":
			self.setTitle(self.mediaContainer.get("title2", " "))
			self["leafCount"].setText(self.details.get("leafCount", " "))
			self["viewedLeafCount"].setText(self.details.get("viewedLeafCount", " "))
			self["unviewedLeafCount"].setText(str(int(self.details.get("leafCount", " ")) - int(self.details.get("viewedLeafCount", " "))))

		if self.viewStep == 2:
			self["season"].setText(self.mediaContainer.get("title2", " "))
		else:
			self["season"].setText("")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onEnter(self):
		printl("", self, "S")

		self.lastTagType = None

		super(DPS_ViewShows,self).onEnter()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first we call the the rest of the onEnter from super
		super(DPS_ViewShows,self).onLeave()

		# first restore Elements
		self.restoreElementsInViewStep()

		self.lastTagType = None

		# we do the refresh here to be able to handle directory content
		self.refresh()

		printl("", self, "C")