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
from DP_LibMain import DP_LibMain

from __common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class DP_LibShows(DP_LibMain):

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, initalEntryData):
		printl ("", self, "S")

		self.initalEntryData = initalEntryData
		printl("initalEntryData: " + str(self.initalEntryData), self, "D")

		libraryName = "shows"
		DP_LibMain.__init__(self, session, libraryName)

		printl ("", self, "C")

	#===============================================================================
	# 
	#===============================================================================
	def loadLibrary(self, entryData = None, forceUpdate=False):
		printl ("", self, "S")
		printl("entryData: " + str(entryData), self, "D")

		if entryData is None:
			entryData = self.initalEntryData

		if str(entryData.get('key')) == "onDeck" or str(entryData.get('key')) == "recentlyViewed" or str(entryData.get('key')) == "newest" or str(entryData.get('key')) == "recentlyAdded":
			entryData["currentViewMode"] = "ShowEpisodesDirect"

		printl ("", self, "C")
		return self.loadLibraryData(entryData, forceUpdate)

