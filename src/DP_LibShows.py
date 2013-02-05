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
from Plugins.Extensions.DreamPlex.DP_LibMain import DP_LibMain

from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class DP_LibShows(DP_LibMain):
	'''
	'''
	
	g_url = None
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, url=None):
		'''
		'''
		printl ("", self, "S")
		
		DP_LibMain.__init__(self, session, "tv shows")
		self.g_url = url
		
		printl ("", self, "C")

	#===============================================================================
	# 
	#===============================================================================
	def loadLibrary(self, params):
		'''
		'''
		printl ("", self, "S")
		printl("params =" + str(params), self, "D")

		# Diplay all TVShows
		if params is None:
			printl("show TV shows ...", self, "I")
			parsedLibrary = []
			
			url = self.g_url
			
			instance = Singleton()
			plexInstance = instance.getPlexInstance()
			library = plexInstance.getShowsFromSection(url)
				
			tmpAbc = []
			tmpGenres = []
			for tvshow in library:

				#===============================================================
				# printl ("-> url = " + str(tvshow[0]), self, "D")
				# printl ("-> properties = " + str(tvshow[1]), self, "D")
				# printl ("-> arguments = " + str(tvshow[2]), self, "D")
				# printl ("-> context = " + str(tvshow[3]), self, "D")
				#===============================================================
				
				url = tvshow[0]
				properties = tvshow[1]
				arguments = tvshow[2]
				context = tvshow[3]
	
			
				d = {}
				d["Title"]          = properties.get('title', "")
				d["Year"]           = properties.get('year', "")
				d["Plot"]           = properties.get('plot', "")
				d["Runtime"]        = properties.get('duration', "")
				d["Genres"]         = properties.get('genre', "")
				d["Seen"]        	= properties.get('playcount', "")
				d["Studio"]     	= properties.get('studio', "")#
				d["Director"]     	= properties.get('director', "")#
				d["MPAA"]     		= properties.get('mpaa', "")#
				
				d["Id"]				= arguments.get('ratingKey') #we use this because there is the id as value without any need of manipulating
				d["Tag"]            = arguments.get('tagline', "")
				d["Path"]          	= arguments.get('key', "")
				d["Popularity"]     = arguments.get('rating', 0)
				d["Resolution"]    	= arguments.get('VideoResolution', "")
				d["Video"]    	   	= arguments.get('VideoCodec', "")
				d["Sound"]         	= arguments.get('AudioCodec', "")
				d["ArtBackdrop"] 	= arguments.get('fanart_image', "")
				d["ArtPoster"]   	= arguments.get('thumb', "")
				d["Seen"]        	= arguments.get('playcount', 0)
				d["Creation"]		= arguments.get('addedAt', 0)
				d["Banner"]			= arguments.get('banner', "")
				d["server"]			= arguments.get('server', "")
				d["theme"]			= arguments.get('theme', "")
				
				d["ViewMode"] = "ShowSeasons"
				d["ScreenTitle"] = d["Title"]

				if (d["Seen"] == 0):
					image = None
				else:
					image = None
				
				parsedLibrary.append((d["Title"], d, d["Title"].lower(), "50", image))
				
			sort = (("Title", None, False), ("Popularity", "Popularity", True), )
			
			filter = [("All", (None, False), ("", )), ]
			if len(tmpGenres) > 0:
				tmpGenres.sort()
				filter.append(("Genre", ("Genres", True), tmpGenres))
				
			if len(tmpAbc) > 0:
				tmpAbc.sort()
				filter.append(("Abc", ("Title", False, 1), tmpAbc))
			
			printl ("", self, "C")
			return (parsedLibrary, ("ViewMode", "Id", ), None, None, sort, filter)	

		
		# Display the Seasons Menu
		elif params["ViewMode"]=="ShowSeasons":
			printl("show seasons of TV show ...", self, "I")
			parsedLibrary = []
			
			url = params["url"]
			
			instance = Singleton()
			plexInstance = instance.getPlexInstance()
			library = plexInstance.getSeasonsOfShow(url)

			seasons = []
			for season in library:

				#===============================================================
				# printl ("-> url = " + str(season[0]), self, "D")
				# printl ("-> properties = " + str(season[1]), self, "D")
				# printl ("-> arguments = " + str(season[2]), self, "D")
				# printl ("-> context = " + str(season[3]), self, "D")
				#===============================================================
				
				url 		= season[0]
				properties 	= season[1]
				arguments 	= season[2]
				context 	= season[3]
				
				d = {}
				d["Title"]          = properties.get('title', "")
				d["Year"]           = properties.get('year', "")
				d["Plot"]           = properties.get('plot', "")
				d["Runtime"]        = properties.get('duration', "")
				d["Genres"]         = properties.get('genre', "")
				d["Seen"]        	= properties.get('playcount', "")
				
				d["Id"]				= arguments.get('ratingKey') #we use this because there is the id as value without any need of manipulating
				d["Tag"]            = arguments.get('tagline', "")
				d["Path"]          	= arguments.get('key', "")
				d["Popularity"]     = arguments.get('rating', 0)
				d["Resolution"]    	= arguments.get('VideoResolution', "")
				d["Video"]    	   	= arguments.get('VideoCodec', "")
				d["Sound"]         	= arguments.get('AudioCodec', "")
				d["ArtBackdrop"] 	= arguments.get('fanart_image', "")
				d["ArtPoster"]   	= arguments.get('thumb', "")
				d["Seen"]        	= arguments.get('playcount', 0)
				d["Creation"]		= arguments.get('addedAt', 0)
				d["Banner"]			= arguments.get('banner', "")
				d["server"]			= arguments.get('server', "")
				
				d["ViewMode"] = "ShowEpisodes"
				d["ScreenTitle"] = d["Title"]

				if (d["Seen"] == 0):
					image = None
				else:
					image = None

				printl( "appending title: " + str(d["Title"]), self, "I")
				parsedLibrary.append((d["Title"], d, d["Title"].lower(), "50", image))
			
			sort = (("Title", None, False), )
			
			filter = [("All", (None, False), ("", )), ]
			
			printl ("", self, "C")
			return (parsedLibrary, ("ViewMode", "Id", "Season", ), None, None, sort, filter)

	
		# Display the Episodes Menu
		elif params["ViewMode"]=="ShowEpisodes":
			printl("show episodes of season ...", self, "I")
			parsedLibrary = []
			
			url = params["url"]
			instance = Singleton()
			plexInstance = instance.getPlexInstance()
			library = plexInstance.getEpisodesOfSeason(url)

			for episode in library:

				#===============================================================
				# printl ("-> url = " + str(episode[0]), self, "D")
				# printl ("-> properties = " + str(episode[1]), self, "D")
				# printl ("-> arguments = " + str(episode[2]), self, "D")
				# printl ("-> context = " + str(episode[3]), self, "D")
				#===============================================================
				
				url = episode[0]
				properties = episode[1]
				arguments = episode[2]
				context = episode[3]
				
				d = {}
				d["Title"]          = properties.get('title', "")
				d["Year"]           = properties.get('year', "")
				d["Plot"]           = properties.get('plot', "")
				d["Runtime"]        = properties.get('duration', "")
				d["Genres"]         = properties.get('genre', "")
				d["Seen"]        	= properties.get('playcount', "")
				
				d["Id"]				= arguments.get('ratingKey') #we use this because there is the id as value without any need of manipulating
				d["Tag"]            = arguments.get('tagline', "")
				d["Path"]          	= arguments.get('key', "")
				d["Popularity"]     = arguments.get('rating', 0)
				d["Resolution"]    	= arguments.get('VideoResolution', "")
				d["Video"]    	   	= arguments.get('VideoCodec', "")
				d["Sound"]         	= arguments.get('AudioCodec', "")
				d["ArtBackdrop"] 	= arguments.get('thumb', "")
				d["ArtPoster"]   	= arguments.get('fanart_image', "")
				d["Seen"]        	= arguments.get('playcount', 0)
				d["Creation"]		= arguments.get('addedAt', 0)
				d["Banner"]			= arguments.get('banner', "")
				d["server"]			= arguments.get('server', "")
				
				d["ViewMode"] = "play"
				d["ScreenTitle"] = d["Title"]

				if (d["Seen"] == 0):
					image = None
				else:
					image = None	
					
				parsedLibrary.append((d["Title"], d, d["Title"].lower(), "50", image))	
			
			sort = [("Title", None, False), ("Popularity", "Popularity", True), ]
			
			filter = [("All", (None, False), ("", )), ]
			filter.append(("Seen", ("Seen", False, 1), ("Seen", "Unseen", )))
			
			printl ("", self, "C")
			return (parsedLibrary, ("ViewMode", "Id", "Episodes", ), None, None, sort, filter)

		printl ("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getPlaybackList(self, entry):
		'''
		'''
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
		'''
		'''
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
