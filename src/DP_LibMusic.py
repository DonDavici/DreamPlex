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
	def __init__(self, session, url=None, uuid=None, source=None, viewGroup=None, librarySteps=None):
		printl ("", self, "S")

		DP_LibMain.__init__(self, session, "music")

		self.g_url = url
		self.g_uuid = uuid
		self.g_source = source
		self.g_viewGroup = viewGroup
		self.g_librarySteps = librarySteps

		printl ("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def loadLibrary(self, params):
		printl ("", self, "S")

		if self.g_librarySteps == 2:
			if params["viewMode"] is None:
				params["viewMode"] = "ShowAlbums"
			library = self.loadTwoStepLibrary(params)
		else:
			if params["viewMode"] is None:
				params["viewMode"] = "ShowArtists"
			library = self.loadThreeStepLibrary(params)

		printl("libary:" + str(library[0]), self, "D")
		printl ("", self, "C")
		return library

	#===============================================================================
	#
	#===============================================================================
	def loadTwoStepLibrary(self, params):
		printl ("", self, "S")
		printl("params: " + str(params), self, "D")

		if params["viewMode"] == "ShowAlbums":
			printl("show albums ...", self, "D")

			library = self.getLibraryData(params, self.g_url, params["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

			sort = (("by albums", True, False), )

			myFilter = [("All", (None, False), ("", )), ]
			printl("library: " + str(library),self, "D")
			printl ("", self, "C")
			return library, ("viewMode", "ratingKey", ), None, "backToShows", sort, myFilter

		elif params["viewMode"] == "ShowTracks":
			printl("show tracks ...", self, "I")

			url = params["url"]

			library = Singleton().getPlexInstance().getMusicTracks(url)

			sort = [("by title", None, False), ]

			myFilter = [("All", (None, False), ("", )), ]

			printl ("", self, "C")
			printl("library: " + str(library),self, "D")
			return library, ("viewMode", "ratingKey", ), None, "backToSeasons", sort, myFilter

		printl ("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def loadThreeStepLibrary(self, params):
		printl ("", self, "S")
		printl("params: " + str(params), self, "D")

		if params["viewMode"] == "ShowArtists":
			printl("show artists ...", self, "D")

			library = self.getLibraryData(params, self.g_url, params["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

			sort = (("by artists", True, False), )

			myFilter = [("All", (None, False), ("", )), ]

			printl ("", self, "C")
			return library, ("viewMode", "ratingKey", ), None, "backToShows", sort, myFilter

		elif params["viewMode"] == "ShowAlbums":
			printl("show albums ...", self, "D")

			# workaroudn
			params["url"] = self.g_url
			params["viewMode"] = "ShowAlbums"
			# end
			library = self.getLibraryData(params, params["url"], params["viewMode"], self.g_uuid, self.g_viewGroup, self.g_source)

			sort = (("by albums", True, False), )

			myFilter = [("All", (None, False), ("", )), ]
			printl("library: " + str(library),self, "D")
			printl ("", self, "C")
			return library, ("viewMode", "ratingKey", ), None, "backToShows", sort, myFilter

		elif params["viewMode"] == "ShowTracks":
			printl("show tracks ...", self, "I")

			url = params["url"]

			library = Singleton().getPlexInstance().getMusicTracks(url)

			sort = [("by title", None, False), ]

			myFilter = [("All", (None, False), ("", )), ]

			printl ("", self, "C")
			printl("library: " + str(library),self, "D")
			return library, ("viewMode", "ratingKey", ), None, "backToSeasons", sort, myFilter

		printl ("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getPlaybackList(self, entry):
		printl ("", self, "S")
		
		playbackList = []
		
		params = {}
		params["Id"] = entry["TVShowId"]
		params["Season"] = entry["Season"]
		params["ViewMode"] = "ShowEpisodes"
		library = self.loadLibrary(params)[0]
		
		playbackList.append( (entry["Path"], entry["Title"], entry, ))
		if entry["Episode"] is None:
			nextEpisode = 0
		else:	
			nextEpisode = entry["Episode"] + 1
		
		found = True
		while found is True:
			found = False
			for episode in library:
				episodeDict = episode[1]
				if episodeDict["Episode"] == nextEpisode:
					playbackList.append( (episodeDict["Path"], episodeDict["Title"], episodeDict, ))
					nextEpisode += 1
					found = True
					break
		
		printl ("playbacklist = " + str(playbackList), self, "D")
		
		printl ("", self, "C")
		return playbackList

	#===========================================================================
	# 
	#===========================================================================
	def buildInfoPlaybackArgs(self, entry):
		printl ("", self, "S")
		
		args = {}
		args["id"] 	= entry["Id"]
		args["title"]   = entry["Title"]
		args["year"]    = entry["Year"]
		args["thetvdb"] = entry["TheTvDbId"]
		args["season"]  = entry["Season"]
		args["episode"] = entry["Episode"]
		args["type"]    = "tvshow"
		
		printl ("args = " + str(args), self, "D")
		
		printl ("", self, "C")
		return args