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

from DPH_Singleton import Singleton

from __common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class DP_LibMusic(DP_LibMain):

	g_url = None
	
	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, entryData):
		printl ("", self, "S")

		DP_LibMain.__init__(self, session, "music")

		self.entryData = entryData

		printl ("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def loadLibrary(self, params):
		printl ("", self, "S")

		if self.g_librarySteps == 2:
			if params["viewMode"] is None:
				params["viewMode"] = "ShowAlbums"
		else:
			if params["viewMode"] is None:
				params["viewMode"] = "ShowArtists"

		library = self._loadLibrary(params)

		printl("libary:" + str(library[0]), self, "D")
		printl ("", self, "C")
		return library

	#===============================================================================
	#
	#===============================================================================
	def  _loadLibrary(self, params):
		printl ("", self, "S")
		printl("params: " + str(params), self, "D")

		returnTo = None

		if params["viewMode"] == "ShowArtists":
			printl("show artists ...", self, "D")

			library, mediaContainer = self.getLibraryData(params, self.g_url, params["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

		elif params["viewMode"] == "ShowAlbums":
			printl("show albums ...", self, "D")

			if self.g_librarySteps == 2:
				params["url"] = self.g_url

			library, mediaContainer = self.getLibraryData(params, params["url"], params["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

			if self.g_librarySteps == 2:
				returnTo = None
			else:
				returnTo = "backToArtists"

		elif params["viewMode"] == "ShowTracks":
			printl("show tracks ...", self, "I")

			library, mediaContainer = self.getLibraryData(params, params["url"], params["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

		printl ("", self, "C")
		return library, returnTo
