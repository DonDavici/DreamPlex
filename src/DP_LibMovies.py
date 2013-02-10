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
		
		DP_LibMain.__init__(self, session, "movies")
		
		self.g_url = url

		printl ("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def loadLibrary(self, params):
		'''
		'''
		printl ("", self, "S")
		printl("params =" + str(params), self, "D")
		
		url = self.g_url
		printl("url: " + str(url), self, "D")
		
		library, tmpAbc, tmpGenres = Singleton().getPlexInstance().getMoviesFromSection(url)

		# sort
		sort = [("by title", "title", False), ("by year", "year", True), ("by rating", "rating", True), ]
		
		filter = [("All", (None, False), ("", )), ]
		
		# filter seen unseen
		#filter.append(("Seen", ("viewState", "seen", ), ("", )))
		
		# filter genres
		#if len(tmpGenres) > 0:
			#tmpGenres.sort()
			#filter.append(("Genre", ("genre", True), tmpGenres))
		
		printl ("", self, "C")
		return (library, ("viewMode", "ratingKey", ), None, None, sort, filter)

	#===========================================================================
	# 
	#===========================================================================
	def buildInfoPlaybackArgs(self, entry):
		'''
		'''
		printl ("", self, "S")
		
		args = {}
		args["id"] 	= entry["ratingKey"]
		args["title"]   = entry["title"]
		args["year"]    = entry["year"]
		args["type"]    = "movie"
		
		printl ("args = " + args, self, "D")
		
		printl ("", self, "C")
		return args


