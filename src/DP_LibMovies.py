# -*- coding: utf-8 -*-
'''
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
'''
#===============================================================================
# IMPORT
#===============================================================================
from DP_LibMain import DP_LibMain

from DPH_Singleton import Singleton

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class DP_LibMovies(DP_LibMain):
	
	g_url = None
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, url=None):
		printl ("", self, "S")
		
		DP_LibMain.__init__(self, session, "movies")
		
		self.g_url = url

		printl ("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def loadLibrary(self, params):
		printl ("", self, "S")
		printl("params =" + str(params), self, "D")
		
		url = self.g_url
		printl("url: " + str(url), self, "D")
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		library = plexInstance.getMoviesFromSection(url)

		parsedLibrary = []
		tmpAbc = []
		tmpGenres = []
		for movie in library:
			
			#===============================================================
			# printl ("-> url = " + str(movie[0]), self, "D")
			# printl ("-> properties = " + str(movie[1]), self, "D")
			# printl ("-> arguments = " + str(movie[2]), self, "D")
			# printl ("-> context = " + str(movie[3]), self, "D")
			#===============================================================
			
			url = movie[0]
			properties = movie[1]
			arguments = movie[2]
			context = movie[3]
			
			d = {}
			d["Title"]          = properties.get('title', "")#
			d["Year"]           = properties.get('year', "")#
			d["Plot"]           = properties.get('plot', "") #
			d["Runtime"]        = properties.get('duration', "")#
			d["Genres"]         = properties.get('genre', "")
			d["Seen"]        	= properties.get('playcount', "")#
			d["Popularity"]     = properties.get('rating', 0)#
			d["Studio"]     	= properties.get('studio', 0)#
			d["MPAA"]     		= properties.get('mpaa', 0)#
			d["Tag"]            = properties.get('tagline', "")#
			d["server"]			= properties.get('server', "")
			
			d["Id"]				= arguments.get('ratingKey') #we use this because there is the id as value without any need of manipulating
			d["Path"]          	= arguments.get('key', "")
			d["Resolution"]    	= arguments.get('VideoResolution', "")
			d["Video"]    	   	= arguments.get('VideoCodec', "")
			d["Sound"]         	= arguments.get('AudioCodec', "")
			d["ArtBackdrop"] 	= arguments.get('fanart_image', "")
			d["ArtPoster"]   	= arguments.get('thumb', "")
			d["Creation"]		= arguments.get('addedAt', 0)
			d["Key"]			= arguments.get('key', "")

			
			d["ViewMode"]      = "play"
			d["ScreenTitle"]   = d["Title"]
			
			if d["Title"].upper() not in tmpAbc:
				tmpAbc.append(d["Title"].upper())
			
			for genre in d["Genres"]:
				if genre not in tmpGenres:
					tmpGenres.append(genre)
			
			if (d["Seen"] == 0):
				image = None
			else:
				image = None

			parsedLibrary.append((d["Title"], d, d["Title"].lower(), "50", image))
		sort = [("Title", None, False), ("Popularity", "Popularity", True), ]
		if self.checkFileCreationDate:
			sort.append(("File Creation", "Creation", True))
		
		sort.append(("Filename", "Filename", False))
		
		filter = [("All", (None, False), ("", )), ]
		filter.append(("Seen", ("Seen", False, 1), ("Seen", "Unseen", )))
		
		if len(tmpGenres) > 0:
			tmpGenres.sort()
			filter.append(("Genre", ("Genres", True), tmpGenres))
			
		if len(tmpAbc) > 0:
			tmpAbc.sort()
			filter.append(("Abc", ("Title", False, 1), tmpAbc))
		
		printl ("", self, "C")
		return (parsedLibrary, ("ViewMode", "Id", ), None, None, sort, filter)

	#===========================================================================
	# 
	#===========================================================================
	def buildInfoPlaybackArgs(self, entry):
		'''
		'''
		printl ("", self, "S")
		
		args = {}
		args["id"] 	= entry["Id"]
		args["title"]   = entry["Title"]
		args["year"]    = entry["Year"]
		args["imdbid"]  = entry["ImdbId"]
		args["type"]    = "movie"
		
		printl ("args = " + args, self, "D")
		printl ("", self, "C")
		return args


