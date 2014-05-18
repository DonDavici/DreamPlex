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
class DP_LibMovies(DP_LibMain):

	g_url = None
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, entryData):
		printl ("", self, "S")
		
		DP_LibMain.__init__(self, session, "movies")

		self.entryData = entryData

		printl ("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def loadLibrary(self, entryData = None):
		printl ("", self, "S")

		if entryData is None:
			entryData = self.entryData

		# coming from DP_View _load()
		printl("entryData: " + str(entryData), self, "D")
		returnTo = None

		url = entryData["contentUrl"]
		printl("url: " + str(url), self, "D")


		if "viewMode" in entryData:
			printl ("viewMode: " + str(entryData["viewMode"]), self, "D")

			if entryData["viewMode"] == "ShowDirectory":
				returnTo = "backToMovies"

		movies, mediaContainer = Singleton().getPlexInstance().getMoviesFromSection(url)

		printl ("", self, "C")
		return movies, returnTo, mediaContainer


