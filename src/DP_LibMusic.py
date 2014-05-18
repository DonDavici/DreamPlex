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
class DP_LibMusic(DP_LibMain):

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, initalEntryData):
		printl ("", self, "S")

		DP_LibMain.__init__(self, session, "music")

		self.initalEntryData = initalEntryData
		printl("initalEntryData: " + str(self.initalEntryData))

		printl ("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def loadLibrary(self, entryData = None):
		printl ("", self, "S")
		printl("entryData: " + str(entryData), self, "D")

		if entryData is None:
			entryData = self.initalEntryData

		returnTo = None

		if self.g_librarySteps == 2:
			if entryData["viewMode"] is None:
				entryData["viewMode"] = "ShowAlbums"
		else:
			if entryData["viewMode"] is None:
				entryData["viewMode"] = "ShowArtists"

		library = self._loadLibrary(entryData)

		printl("libary:" + str(library[0]), self, "D")
		printl ("", self, "C")
		return library

	#===============================================================================
	#
	#===============================================================================
	def  _loadLibrary(self, entryData):
		printl ("", self, "S")
		printl("entryData: " + str(entryData), self, "D")

		returnTo = None

		if entryData["viewMode"] == "ShowArtists":
			printl("show artists ...", self, "D")

			library, mediaContainer = self.getLibraryData(entryData, self.g_url, entryData["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

		elif entryData["viewMode"] == "ShowAlbums":
			printl("show albums ...", self, "D")

			if self.g_librarySteps == 2:
				entryData["url"] = self.g_url

			library, mediaContainer = self.getLibraryData(entryData, entryData["url"], entryData["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

			if self.g_librarySteps == 2:
				returnTo = None
			else:
				returnTo = "backToArtists"

		elif entryData["viewMode"] == "ShowTracks":
			printl("show tracks ...", self, "I")

			library, mediaContainer = self.getLibraryData(entryData, entryData["url"], entryData["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

		printl ("", self, "C")
		return library, returnTo, mediaContainer
