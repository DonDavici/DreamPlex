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
import os
import cPickle as pickle

from Screens.Screen import Screen

from Components.config import config

from DP_ViewFactory import getViews
from DP_View import DP_View

from DPH_Singleton import Singleton

from __common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class DP_LibMain(Screen):

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, libraryName):
		printl("", self, "S")
		printl("libraryName: " + str(libraryName), self, "D")
		
		Screen.__init__(self, session)
		self._session = session
		self._libraryName = libraryName
		
		self._views = getViews(libraryName)

		if self._libraryName == "movies":
			self.currentViewIndex = int(config.plugins.dreamplex.defaultMovieView.value)

		elif self._libraryName == "shows":
			self.currentViewIndex = int(config.plugins.dreamplex.defaultShowView.value)

		elif self._libraryName == "music":
			self.currentViewIndex = int(config.plugins.dreamplex.defaultMusicView.value)

		else:
			self.currentViewIndex = 0
		
		self.onFirstExecBegin.append(self.showView)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def showView(self):
		printl("", self, "S")

		viewParams = self._views[self.currentViewIndex][2]
		m = __import__(self._views[self.currentViewIndex][1], globals(), locals(), [])
		self._session.openWithCallback(self.onViewClosed, m.getViewClass(), self._libraryName, self.loadLibrary, viewParams)
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def loadLibrary(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def onViewClosed(self, cause=None):
		"""
		Called if View has closed, react on cause for example change to different view
		"""
		printl("", self, "S")
		printl("cause: %s" % str(cause), self, "D")

		if cause is not None:
			if cause[0] == DP_View.ON_CLOSED_CAUSE_SAVE_DEFAULT:
				selection = None

				if len(cause) >= 2 and cause[1] is not None:
					selection = cause[1]
				self.setDefault(selection)
				self.close()

			elif cause[0] == DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW or cause[0] == DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE:
				self.currentViewIndex += 1
				if len(self._views) <= self.currentViewIndex:
					self.currentViewIndex = 0
				
				if len(cause) >= 5 and cause[4] is not None:
					for i in range(len(self._views)):
						if cause[4]== self._views[i][1]:
							self.currentViewIndex = i
							break
				
				self.showView()

			else:
				printl("", self, "C")
				self.close()

		else:
			printl("", self, "C")
			self.close()

	#===========================================================================
	#
	#===========================================================================
	def loadLibraryData(self, entryData, forceUpdate):
		printl("", self, "S")

		printl("entryData: " + str(entryData), self, "D")

		url = entryData["contentUrl"]

		if entryData.has_key("source"):
			source = entryData["source"]
			uuid = entryData["uuid"]
		else:
			source = "plex"
			uuid = None

		# in this case we do not use cache because there is no uuid and updated on information on this level
		# maybe we find a way later and implement it than
		if entryData.has_key("viewMode"):
			myType = entryData["viewMode"]
			source = "plex"
		else:
			myType = entryData["type"]

		# in this case we have to ask plex for sure too
		if str(entryData.get('key')) != "all":
			source = "plex"

		if forceUpdate:
			source = "plex"

		library, mediaContainer = self.getLibraryData(source, url, myType, uuid, forceUpdate)

		printl ("", self, "C")
		return library, mediaContainer

	#===========================================================================
	#
	#===========================================================================
	def getLibraryData(self, source, url, myType, uuid, forceUpdate=False):
		printl ("", self, "S")

		if config.plugins.dreamplex.useCache.value:
			pickleFileExists = False
			regeneratePickleFile = False
			#noinspection PyAttributeOutsideInit
			self.pickleName = "%s%s_%s.cache" % (config.plugins.dreamplex.cachefolderpath.value, uuid, myType)
			if os.path.exists(self.pickleName):
				pickleFileExists = True

			# params['cache'] is default None. if it is present and it is False we know that we triggered refresh
			# for this reason we have to set self.g_source = 'plex' because the if is with "or" and not with "and" which si not possible
			if source == "cache" and pickleFileExists:
				try:
					library = self.getLibraryDataFromPickle()
					printl("from pickle", self, "D")
				except:
					printl("cache file not found", self, "D")
					library = self.getLibraryDataFromPlex(url, myType)
					regeneratePickleFile = True
			else:
				library = self.getLibraryDataFromPlex(url, myType)

				if forceUpdate:
					regeneratePickleFile = True

			if not pickleFileExists or regeneratePickleFile:
				printl("pickleFileExists: " + str(pickleFileExists), self, "D")
				printl("regeneratePickleFile: " + str(regeneratePickleFile), self, "D")
				self.generateCacheForSection(library)
		else:
			library = self.getLibraryDataFromPlex(url, myType)

		printl ("", self, "C")
		return library

	#===========================================================================
	#
	#===========================================================================
	def getLibraryDataFromPickle(self):
		printl ("", self, "S")

		fd = open(self.pickleName, "rb")
		pickleData = pickle.load(fd)
		fd.close()

		printl ("", self, "C")
		return pickleData

	#===========================================================================
	#
	#===========================================================================
	def getLibraryDataFromPlex(self, url, myType):
		printl ("", self, "S")

		printl("myType: " + str(myType), self, "D")
		library = None
		mediaContainer = None

		# MUSIC
		if myType == "artist":
			library, mediaContainer = Singleton().getPlexInstance().getMusicByArtist(url)

		elif myType == "ShowAlbums":
			library, mediaContainer = Singleton().getPlexInstance().getMusicByAlbum(url)

		elif myType == "ShowTracks":
			library, mediaContainer = Singleton().getPlexInstance().getMusicTracks(url)

		# MOVIES
		elif myType == "movie":
			library, mediaContainer = Singleton().getPlexInstance().getMoviesFromSection(url)

		# SHOWS
		elif myType == "show":
			library, mediaContainer = Singleton().getPlexInstance().getShowsFromSection(url)

		elif myType == "ShowEpisodesDirect":
			library, mediaContainer = Singleton().getPlexInstance().getEpisodesOfSeason(url, directMode=True)

		elif myType == "ShowSeasons":
			library, mediaContainer = Singleton().getPlexInstance().getSeasonsOfShow(url)

		elif myType == "ShowEpisodes":
			library, mediaContainer = Singleton().getPlexInstance().getEpisodesOfSeason(url)


		printl ("", self, "C")
		return library, mediaContainer

	#===========================================================================
	#
	#===========================================================================
	def generateCacheForSection(self, library):
		printl ("", self, "S")

		pickleData = library
		fd = open(self.pickleName, "wb")
		pickle.dump(pickleData, fd, 2) #pickle.HIGHEST_PROTOCOL
		fd.close()

		printl ("", self, "C")
