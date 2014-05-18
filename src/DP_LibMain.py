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
from DP_Player import DP_Player
from DP_View import DP_View

from DPH_Singleton import Singleton

from __common__ import printl2 as printl
from __plugin__ import getPlugins, Plugin

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
		self.currentViewIndex = 0
		
		self.defaultPickle = "%s%s_view_%s.bin" % (config.plugins.dreamplex.playerTempPath.value, config.plugins.dreamplex.skins.value, libraryName, )
		self.onFirstExecBegin.append(self.showDefaultView)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getDefault(self):
		printl("", self, "S")
		
		try:
			fd = open(self.defaultPickle, "rb")
			default = pickle.load(fd)
			fd.close()
		except:
			default = {
			"view": self.currentViewIndex, 
			"selection": None, 
		}
		
		printl("", self, "C")
		return default

	#===========================================================================
	# 
	#===========================================================================
	def setDefault(self, selection):
		printl("", self, "S")
		
		if selection is None:
			try:
				os.remove(self.defaultPickle)
			except:
				printl("Could not remove " + str(self.defaultPickle), self, "E")
			
			printl("", self, "C")
			return
		
		default = {
			"view": self.currentViewIndex, 
			"selection": selection,
		}
		
		fd = open(self.defaultPickle, "wb")
		pickle.dump(default, fd, 2) #pickle.HIGHEST_PROTOCOL)
		fd.close()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def showDefaultView(self):
		printl("", self, "S")
		
		default = self.getDefault()
		self.currentViewIndex = default["view"]
		self.showView(default["selection"])
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def showView(self, selection=None, cache=None):
		"""
		Displays the selected View
		"""
		printl("", self, "S")
		m = __import__(self._views[self.currentViewIndex][1], globals(), locals(), [])
		self._session.openWithCallback(self.onViewClosed, m.getViewClass(), self._libraryName, self.loadLibrary, self.playEntry, self._views[self.currentViewIndex], select=selection, cache=cache)
		
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
					#self.currentViewIndex = cause[1]
					selection = cause[1]
				self.setDefault(selection)
				self.close()

			elif cause[0] == DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW or cause[0] == DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE:
				selection = None
				self.currentViewIndex += 1
				if len(self._views) <= self.currentViewIndex:
					self.currentViewIndex = 0
				
				if len(cause) >= 2 and cause[1] is not None:
					#self.currentViewIndex = cause[1]
					selection = cause[1]

				if len(cause) >= 5 and cause[4] is not None:
					for i in range(len(self._views)):
						if cause[4]== self._views[i][1]:
							self.currentViewIndex = i
							break
				
				if cause[0] == DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW:
					self.showView(selection, cache=True)
				else:
					self.showView(selection, cache=False)

			else:
				printl("", self, "C")
				self.close()

		else:
			printl("", self, "C")
			self.close()

	#===========================================================================
	# 
	#===========================================================================
	def loadLibrary(self, entryData):
		printl("", self, "S")

		printl("", self, "C")
		return []

	#===========================================================================
	# 
	#===========================================================================
	def playEntry(self, entry, flags=None):
		"""
		starts playback, is called by the view
		"""
		printl("", self, "S")
		if not flags:
			flags = {}

		playbackPath = entry["Path"]
		
		if playbackPath[0] == "/" and os.path.isfile(playbackPath) is False:
			
			printl("", self, "C")
			return False
		else:
			self.notifyEntryPlaying(entry, flags)
			
			isDVD, dvdFilelist, dvdDevice = self.checkIfDVD(playbackPath)
			
			if isDVD:
				self.playDVD(dvdDevice, dvdFilelist)
			else:
				self.playFile(entry, flags)
			
			printl("", self, "C")
			return True

	#===========================================================================
	# 
	#===========================================================================
	def checkIfDVD(self, playbackPath):
		"""
		tries to determin if media entry is a dvd
		"""
		printl("", self, "S")

		isDVD = False
		dvdFilelist = [ ]
		dvdDevice = None
		
		if playbackPath.lower().endswith(u"ifo"): # DVD
			isDVD = True
			dvdFilelist.append(str(playbackPath.replace(u"/VIDEO_TS.IFO", "").strip()))
		
		elif playbackPath.lower().endswith(u"iso"): # DVD
			isDVD = True
			dvdFilelist.append(str(playbackPath))
		
		printl("", self, "C")
		return isDVD, dvdFilelist, dvdDevice

	#===========================================================================
	# 
	#===========================================================================
	#noinspection PyUnresolvedReferences
	def playDVD(self, dvdDevice, dvdFilelist):
		"""
		playbacks a dvd by callinf dvdplayer plugin
		"""
		printl("", self, "S")
		
		try:
			from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
			# when iso -> filelist, when folder -> device
			self.session.openWithCallback(self.leaveMoviePlayer, DVDPlayer, dvd_device = dvdDevice, dvd_filelist = dvdFilelist)
		except Exception, ex:
			printl("Exception: " + str(ex), self, "E")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def playFile(self, entry, flags):
		"""
		playbacks a file by calling DP_player
		"""
		printl("", self, "S")
		
		playbackList = self.getPlaybackList(entry)
		printl("playbackList: " + str(playbackList), self, "D")
		
		if len(playbackList) == 1:
			self.session.openWithCallback(self.leaveMoviePlayer, DP_Player, playbackList, flags=flags)
		
		elif len(playbackList) >= 2:
			self.session.openWithCallback(self.leaveMoviePlayer, DP_Player, playbackList, self.notifyNextEntry, flags=flags)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def leaveMoviePlayer(self, flags=None):
		"""
		After calling this the view should auto reappear
		"""
		printl("", self, "S")

		if not flags:
			flags = {}

		self.notifyEntryStopped(flags)
		
		self.session.nav.playService(None) 
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getPlaybackList(self, entry):
		"""
		prototype fore playbacklist creation
		"""
		printl("", self, "S")
		

		playbackList = []
		playbackList.append( (entry["Path"], entry["title"], entry, ))
		
		printl("", self, "C")
		return playbackList

	#===========================================================================
	# 
	#===========================================================================
	def buildInfoPlaybackArgs(self, entry):
		printl("", self, "S")

		args = {}
		args["entry"] = entry

		printl("", self, "C")
		return args

	#===========================================================================
	# 
	#===========================================================================
	def notifyEntryPlaying(self, entry, flags):
		"""
		called on start of playback
		"""
		printl("", self, "S")
		
		args = self.buildInfoPlaybackArgs(entry)
		args["status"]  = "playing"
		plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
		
		for plugin in plugins:
			printl("plugin.name=" + str(plugin.name), self, "D")
			plugin.fnc(args, flags)
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def notifyEntryStopped(self, flags):
		"""
		called on end of playback
		"""
		printl("", self, "S")
		
		args = {}
		args["status"] = "stopped"
		plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
		
		for plugin in plugins:
			printl("plugin.name=" + str(plugin.name), self, "D")
			plugin.fnc(args, flags)
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def notifyNextEntry(self, entry, flags):
		"""
		called if the next entry in the playbacklist is being playbacked
		"""
		printl("", self, "S")
		
		self.notifyEntryStopped(flags)
		self.notifyEntryPlaying(entry, flags)
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getLibraryData(self, params, url, myType, uuid, viewGroup, source):
		printl ("", self, "S")

		if config.plugins.dreamplex.useCache.value:
			#noinspection PyAttributeOutsideInit
			self.pickleName = "%s%s_%s.cache" % (config.plugins.dreamplex.cachefolderpath.value, uuid, viewGroup)

			# params['cache'] is default None. if it is present and it is False we know that we triggered refresh
			# for this reason we have to set self.g_source = 'plex' because the if is with "or" and not with "and" which si not possible
			if "cache" in params:
				if not params['cache']:
					source = "plex"

			if source == "cache" or params['cache'] == True:
				try:
					library = self.getLibraryDataFromPickle()
					printl("from pickle", self, "D")
				except:
					printl("music cache not found ... saving", self, "D")
					library = self.getLibraryDataFromPlex(url, myType)
					reason = "cache file does not exists, recreating ..."
					self.generateCacheForSection(reason, library)
					printl("fallback to: from server", self, "D")
			else:
				library = self.getLibraryDataFromPlex(url, myType)
				reason = "generating cache first time, creating ..."
				self.generateCacheForSection(reason, library)
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

		if myType == "ShowAlbums":
			library, mediaContainer = Singleton().getPlexInstance().getMusicByAlbum(url)

		elif myType == "ShowArtists":
			library, mediaContainer = Singleton().getPlexInstance().getMusicByArtist(url)

		elif myType == "ShowTracks":
			library, mediaContainer = Singleton().getPlexInstance().getMusicTracks(url)

		printl ("", self, "C")
		return library, mediaContainer

	#===========================================================================
	#
	#===========================================================================
	def generateCacheForSection(self, reason, library):
		printl ("", self, "S")

		printl ("reason: " + str(reason), self, "S")
		pickleData = library
		fd = open(self.pickleName, "wb")
		pickle.dump(pickleData, fd, 2) #pickle.HIGHEST_PROTOCOL
		fd.close()

		printl ("", self, "C")
