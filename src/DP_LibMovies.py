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
import cPickle as pickle

from Components.config import config

from Plugins.Extensions.DreamPlex.DP_LibMain import DP_LibMain

from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class DP_LibMovies(DP_LibMain):
	"""
	"""
	
	g_url = None
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, url=None, uuid=None, source=None):
		printl ("", self, "S")
		
		DP_LibMain.__init__(self, session, "movies")
		
		self.g_url = url
		self.g_uuid = uuid
		self.g_source = source
		
		printl ("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def loadLibrary(self, params):
		printl ("", self, "S")
		printl("params for me: " + str(params), self, "D")

		url = self.g_url
		printl("url: " + str(url), self, "D")
		
		# sort
		sort = [("by title", None, False), ("by year", "year", True), ("by rating", "rating", True), ]
		
		filter = [("All", (None, False), ("", )), ]
		
		# filter seen unseen
		#filter.append(("Seen", ("viewState", "seen", ), ("", )))
		
		# filter genres
		#if len(tmpGenres) > 0:
			#tmpGenres.sort()
			#filter.append(("Genre", ("genre", True), tmpGenres))
		
		if params["viewMode"] is None:
			printl ("viewMode = None", self, "D")
			if config.plugins.dreamplex.useCache.value:
				self.moviePickle = "%s%s_%s.cache" % (config.plugins.dreamplex.cachefolderpath.value, "movieSection", self.g_uuid,)
				
				# params['cache'] is default None. if it is present and it is False we know that we triggered refresh
				# for this reason we have to set self.g_source = 'plex' because the if is with "or" and not with "and" which si not possible
				if "cache" in params:
					if not params['cache']:
						self.g_source = "plex"
	 
				if self.g_source == "cache" or params['cache'] == True:
					try:
						fd = open(self.moviePickle, "rb")
						pickleData = pickle.load(fd)
						library = pickleData[0]
						tmpAbc = pickleData[1]
						tmpGenres = pickleData [2]
						fd.close()
						printl("from pickle", self, "D")
					except:
						printl("movie cache not found ... saving", self, "D")
						library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getMoviesFromSection(url)
						reason = "cache file does not exists, recreating ..."
						self.generatingCacheForMovieSection(reason,library, tmpAbc, tmpGenres)
						printl("fallback to: from server", self, "D")
				else:
					library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getMoviesFromSection(url)
					reason = "generating cache first time, creating ..."
					self.generatingCacheForMovieSection(reason, library, tmpAbc, tmpGenres)
			else:
				library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getMoviesFromSection(url)
		else:
			printl ("viewMode is Directory", self, "D")
			url = params["url"]
			library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getMoviesFromSection(url)
			
			printl ("", self, "C")
			return library, ("viewMode", "ratingKey", ), None, "backToMovies", sort, filter
		
		printl ("", self, "C")
		return library, ("viewMode", "ratingKey", ), None, None, sort, filter

	#===========================================================================
	# 
	#===========================================================================
	def generatingCacheForMovieSection(self, reason, library, tmpAbc, tmpGenres):
		printl ("", self, "S")
		
		printl ("reason: " + str(reason), self, "S")
		pickleData = library, tmpAbc, tmpGenres
		fd = open(self.moviePickle, "wb")
		pickle.dump(pickleData, fd, 2) #pickle.HIGHEST_PROTOCOL
		fd.close()
		
		printl ("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def buildInfoPlaybackArgs(self, entry):
		printl ("", self, "S")
		
		args = {}
		args["id"]      = entry["ratingKey"]
		args["title"]   = entry["title"]
		args["year"]    = entry["year"]
		args["type"]    = "movie"
		
		printl ("args = " + args, self, "D")
		
		printl ("", self, "C")
		return args


