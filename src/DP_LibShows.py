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
import cPickle as pickle

from Components.config import config

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
	def __init__(self, session, url=None, showEpisodesDirectly=False, uuid=None, source=None):
		'''
		we use showEpisodesDirectly for the onDeck functions that forces us to jump directly to episodes
		'''
		printl ("", self, "S")
		
		DP_LibMain.__init__(self, session, "tvshows")
		self.g_url = url
		self.showEpisodesDirectly = showEpisodesDirectly
		self.g_uuid = uuid
		self.g_source = source
		
		printl ("", self, "C")

	#===============================================================================
	# 
	#===============================================================================
	def loadLibrary(self, params):
		printl ("", self, "S")
		printl("params: " + str(params), self, "D")
		
		if self.showEpisodesDirectly == True:
			printl("show episodes in OnDeck ...", self, "I")
			
			url = self.g_url
			
			library = Singleton().getPlexInstance().getEpisodesOfSeason(url)

			sort = [("by title", None, False), ]
			
			filter = [("All", (None, False), ("", )), ]
			
			#filter.append(("Seen", ("Seen", False, 1), ("Seen", "Unseen", )))
			
			printl ("", self, "C")
			return (library, ("viewMode", "ratingKey", ), None, "None", sort, filter)
		else:
			# Diplay all TVShows
			if params["viewMode"] is None:
				printl("show TV shows ...", self, "I")
	
				url = self.g_url
				printl("url: " + str(url), self, "D")
				
				if config.plugins.dreamplex.useCache.value == True:
					self.tvShowPickle = "%s%s_%s.cache" % (config.plugins.dreamplex.cachefolderpath.value, "tvShowSection", self.g_uuid,)
					
					# params['cache'] is default None. if it is present and it is False we know that we triggered refresh
					# for this reason we have to set self.g_source = 'plex' because the if is with "or" and not with "and" which si not possible
					if "cache" in params:
						if params['cache'] == False:
							self.g_source = "plex"
					
					if self.g_source == "cache" or params['cache'] == True:
						try:
							fd = open(self.tvShowPickle, "rb")
							pickleData = pickle.load(fd)
							library = pickleData[0]
							tmpAbc = pickleData[1]
							tmpGenres = pickleData [2]
							fd.close()
							printl("from pickle", self, "D")
						except:
							printl("movie cache not found ... saving", self, "D")
							library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getShowsFromSection(url)
							reason = "cache file does not exists, recreating ..."
							self.generatingCacheForTvShowSection(reason,library, tmpAbc, tmpGenres)
							printl("fallback to: from server", self, "D")
					else:
						library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getShowsFromSection(url)
						reason = "generating cache first time, creating ..."
						self.generatingCacheForTvShowSection(reason, library, tmpAbc, tmpGenres)
				else:
					library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getShowsFromSection(url)
	
				# sort
				sort = [("by title", None, False), ("by year", "year", True), ("by rating", "rating", True), ]
				
				filter = [("All", (None, False), ("", )), ]
				
				#if len(tmpGenres) > 0:
					#tmpGenres.sort()
					#filter.append(("Genre", ("Genres", True), tmpGenres))
				
				printl ("", self, "C")
				return (library, ("viewMode", "ratingKey", ), None, None, sort, filter)
				# (libraryArray, onEnterPrimaryKeys, onLeavePrimaryKeys, onLeaveSelectEntry

			# Display the Seasons Menu
			elif params["viewMode"] == "ShowSeasons":
				printl("show seasons of TV show ...", self, "I")
				
				url = params["url"]
	
				library = Singleton().getPlexInstance().getSeasonsOfShow(url)
				
				sort = (("by season", "season", False), )
				
				filter = [("All", (None, False), ("", )), ]
				
				printl ("", self, "C")
				return (library, ("viewMode", "ratingKey", ), None, "backToShows", sort, filter)
				# (libraryArray, onEnterPrimaryKeys, onLeavePrimaryKeys, onLeaveSelectEntry
	
		
			# Display the Episodes Menu
			elif params["viewMode"] == "ShowEpisodes":
				printl("show episodes of season ...", self, "I")
				
				url = params["url"]
				
				library = Singleton().getPlexInstance().getEpisodesOfSeason(url)
	
				sort = [("by title", None, False), ]
				
				filter = [("All", (None, False), ("", )), ]

				#filter.append(("Seen", ("Seen", False, 1), ("Seen", "Unseen", )))
				
				printl ("", self, "C")
				return (library, ("viewMode", "ratingKey", ), None, "backToSeasons", sort, filter)
				# (libraryArray, onEnterPrimaryKeys, onLeavePrimaryKeys, onLeaveSelectEntry

		printl ("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def generatingCacheForTvShowSection(self, reason, library, tmpAbc, tmpGenres):
		printl ("", self, "S")
		
		printl ("reason: " + str(reason), self, "S")
		pickleData = library, tmpAbc, tmpGenres
		fd = open(self.tvShowPickle, "wb")
		pickle.dump(pickleData, fd, 2) #pickle.HIGHEST_PROTOCOL
		fd.close()
		
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
