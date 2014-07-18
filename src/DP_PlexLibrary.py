# -*- coding: utf-8 -*-
"""
DreamPlex Plugin by DonDavici, 2012
 
https://github.com/DonDavici/DreamPlex

special thx to hippojay for his great work in plexbmc
which was the the base for this lib :-)

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
import urllib
import httplib
import socket
import sys
import os
import base64
import hmac
import uuid
import cPickle as pickle

from time import time
from urllib import quote_plus
from base64 import b64encode, b64decode
from Components.config import config
from hashlib import sha256
from urllib2 import urlopen, Request
from random import seed

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from __plugin__ import getPlugin, Plugin
from __common__ import printl2 as printl, getXmlContent, getPlexHeader
from __init__ import _ # _ is translation

#===============================================================================
# import cProfile
#===============================================================================
try:
# Python 2.5
	import xml.etree.cElementTree as etree
	#printl2("running with cElementTree on Python 2.5+", __name__, "D")
except ImportError:
	try:
		# Python 2.5
		import xml.etree.ElementTree as etree
		#printl2("running with ElementTree on Python 2.5+", __name__, "D")
	except ImportError:
		etree = None
		raise Exception
					
#===============================================================================
# 
#===============================================================================
#The method seed() sets the integer starting value used in generating random numbers. Call this function before calling any other random module function.
seed()

#===============================================================================
# 
#===============================================================================
DEFAULT_PORT="32400"
MYPLEX_SERVER="my.plexapp.com"

#===============================================================================
# PlexLibrary
#===============================================================================
class PlexLibrary(Screen):

	g_sessionID=None
	g_sections=[]
	serverConfig_Name = "Plexserver"
	g_host = "192.168.45.190"
	serverConfig_port = "32400"
	g_currentServer = None
	serverConfig_connectionType = None
	g_showForeign = True
	g_address = None # is later the combination of g_host : serverConfig_port
	serverConfig_playbackType = None
	g_stream = "0" # 0 = linux local mount override, 1 = Selecting stream, 2 = smb/unc override 3 = transcode!?!?!
	g_useFilterSections = "true" # show filter for media
	g_streamControl = "1" # 1 unknown, 2 = unknown, 3 = All subs disabled
	g_channelview = "false" # unknown
	g_flattenShow = False # False = show seasons, True = show all
	g_playtheme = "false"
	g_forcedvd = "false"
	g_skipmetadata = "false" # best understanding when looking getMoviesfromsection
	g_skipmediaflags = "false" # best understanding when looking getMoviesfromsection
	g_skipimages = "false"
	g_loc = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex" # homeverzeichnis
	g_myplex_username = ""
	g_myplex_password = ""
	serverConfig_myplexToken = ""
	g_myplex_accessToken = ""
	g_accessTokenDictHeader = ""
	g_accessTokenUrlHeader= ""
	g_transcode = "true"
	g_wolon = "true"
	g_wakeserver = "00-11-32-12-C5-F9"
	g_woldelay = 10
	g_nasoverride = "false"
	g_nasoverrideip = "192.168.45.190"
	g_nasuserid = "username"
	g_naspass = "password"
	g_nasroot = "Video"
	g_bonjour = "0" # 0 = OFF, 1= ON
	serverConfig_quality = None #
	g_capability = ""
	g_audioOutput = "2" #0 = "mp3,aac", 1 = "mp3,aac,ac3", 2 ="mp3,aac,ac3,dts"
	g_session = None
	g_serverConfig = None
	g_error = False
	g_showUnSeenCounts = False
	
	##################
	
	##################
	g_serverDict=[]
	g_serverVersion=None
	g_myplex_accessTokenDict = {}
	g_sectionCache = None
	g_multiUser = False # this is only true if we use myPlex Connection and we have a plexPlass Account active on the server
	g_currentError = ""
	seenPic = "seen-fs8.png"
	unseenPic = "unseen-fs8.png"
	startedPic = "started-fs8.png"
	
	#Create the standard header structure and load with a User Agent to ensure we get back a response.
	g_txheaders = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',}
	
	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, serverConfig=None):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.g_session = session
		self.g_error = False
		printl("running on " + str(sys.version_info), self, "I")
		
		# global serverConfig
		self.g_serverConfig = serverConfig
				
		# global settings
		self.g_useFilterSections = config.plugins.dreamplex.showFilter.value
		self.g_showUnSeenCounts = config.plugins.dreamplex.showUnSeenCounts.value
		self.g_sessionID = str(uuid.uuid4())
		
		# server settings
		self.serverConfig_Name = str(self.g_serverConfig.name.value)
		self.serverConfig_connectionType = str(self.g_serverConfig.connectionType.value)
		self.serverConfig_port = str(self.g_serverConfig.port.value)
		self.serverConfig_quality = str(self.g_serverConfig.quality.value)
		self.serverConfig_myplexToken = str(self.g_serverConfig.myplexToken.value)
		self.serverConfig_playbackType = self.g_serverConfig.playbackType.value
		self.serverConfig_localAuth = self.g_serverConfig.localAuth.value

		# PLAYBACK TYPES
		self.g_segments = self.g_serverConfig.segments.value # is needed here because of fallback

		if self.serverConfig_playbackType == "0": # STREAMED
			self.g_stream = "1"
			self.g_transcode = "false"

		elif self.serverConfig_playbackType == "1": # TRANSCODED
			self.g_stream = "1"
			self.g_transcode = "true"
			self.g_segments = self.g_serverConfig.segments.value

			printl("using transcode: " + str(self.g_transcode), self, "I")
			printl("using this transcoding quality: " +  str(self.serverConfig_quality), self, "I")
			printl("using this segments size: " +  str(self.g_segments), self, "I")

		elif self.serverConfig_playbackType == "2": # DIRECT LOCAL
			self.g_stream = "0"
			self.g_transcode = "false"

		elif self.serverConfig_playbackType == "3": # DIRECT REMOTE
			self.g_stream = "2"
			self.g_transcode = "false"
			self.g_nasoverride = "true"
			self.g_nasoverrideip = "%d.%d.%d.%d" % tuple(self.g_serverConfig.nasOverrideIp.value)
			self.g_nasuserid = str(self.g_serverConfig.smbUser.value)
			self.g_naspass = str(self.g_serverConfig.smbPassword.value)
			self.g_nasroot = str(self.g_serverConfig.nasRoot.value)

		printl("using this debugMode: " + str(config.plugins.dreamplex.debugMode.value), self, "D")
		printl("using this serverName: " +  self.serverConfig_Name, self, "I")
		printl("using this connectionType: " +  self.serverConfig_connectionType, self, "I")

		# CONNECTIONS TYPES
		if self.serverConfig_connectionType == "2": # MYPLEX
			self.setMyPlexData()

		elif self.serverConfig_connectionType == "0": # IP
			self.setIpData()

			if self.serverConfig_localAuth:
				self.setMyPlexData()

		else: # DNS
			try:
				self.g_host = str(socket.gethostbyname(self.g_serverConfig.dns.value))
				printl("using this FQDN: " +  self.g_serverConfig.dns.value, self, "I")
				printl("found this ip for fqdn: " + self.g_host, self, "I")
				printl("using this serverPort: " +  self.serverConfig_port, self, "I")
			except Exception, e:
				printl("socket error: " + str(e), self, "W")
				printl("trying fallback to ip", self, "I")
				self.g_host = "%d.%d.%d.%d" % tuple(self.g_serverConfig.ip.value)

		if self.g_error is True:
			self.leaveOnError()
		else:
			#Fill serverdata to global g_serverDict
			self.prepareServerDict()

		printl("", self, "C")

#===============================================================================
# LIBRARY ACCESS
#===============================================================================
	#============================================================================
	#
	#============================================================================
	def getAllSections(self, myFilter=None ):
		printl("", self, "S")
		printl("myFilter: " + str(myFilter), self, "D")

		fullList=[]

		self.sectionCacheLoaded = False
		if config.plugins.dreamplex.useCache.value:
			# load section cache
			self.loadSectionCache()

		# sections tree
		tree = self.getAllSectionsXmlTree()

		entries = tree.findall('Directory')

		for entry in entries:
			entryData = (dict(entry.items()))
			printl("entryData: " + str(entryData), self, "D")

			# set the source for the section data
			source = "plex"
			if config.plugins.dreamplex.useCache.value:
				source = self.updateSectionCache(entryData)

			entryData["source"] =source

			# add specific data to entryData if needed
			if self.serverConfig_connectionType == "2": # MYPLEX
				entryData["address"] = entryData['address'] + ":" + entryData['port']

				# we have to do this because via myPlex there could be diffrent servers with other tokens
				if str(entryData.get('address')) not in self.g_myplex_accessToken:
					printl("section address" + str(entryData.get('address')), self, "D")
					self.g_myplex_accessTokenDict[str(entryData.get('address'))] = str(entryData.get('accessToken', None))

				# finally we set AccessTokenHeader
				self.setAccessTokenHeader(str(entryData.get('serverVersion')))
			else:
				entryData["path"] = "/library/sections/" + entryData.get('key')
				entryData["address"] = str(self.g_host + ":" + self.serverConfig_port)

			if not self.g_useFilterSections and entryData.get('type') != 'artist':
				entryData["path"] += '/all'

			entryData["serverName"] = self.serverConfig_Name.encode()
			entryData["contentUrl"] = self.getContentUrl(entryData['address'], entryData['path']) # former t_url

			# if this is a myPlex connection we look if we should provide more information for better overview since myplex combines all servers and shares
			detail = ""
			if config.plugins.dreamplex.showDetailsInList.value and self.serverConfig_connectionType == "2":
				if config.plugins.dreamplex.showDetailsInListDetailType.value == "1":
					detail = " ( " + entryData['sourceTitle'] + ")"
				elif config.plugins.dreamplex.showDetailsInListDetailType.value == "2":
					detail = " (" + str(entryData['serverName']) + ")"

			entryName = _(entryData.get('title').encode('utf-8')) + detail

			if entryData.get('type') == 'show':
				printl( "_MODE_TVSHOWS detected", self, "D")
				if myFilter is not None and myFilter != "tvshow":
					continue

				if self.g_useFilterSections:
					fullList.append((entryName, Plugin.MENU_FILTER, "showEntry", entryData))
				else:
					fullList.append((_(entryData.get('title').encode('utf-8')), getPlugin("tvshows", Plugin.MENU_TVSHOWS), "showEntry", entryData))

			elif entryData.get('type') == 'movie':
				printl( "_MODE_MOVIES detected", self, "D")
				if (myFilter is not None) and (myFilter != "movies"):
					continue

				if self.g_useFilterSections:
					fullList.append((entryName, Plugin.MENU_FILTER, "movieEntry", entryData))
				else:
					fullList.append((_(entryData.get('title').encode('utf-8')), getPlugin("movies", Plugin.MENU_MOVIES), "movieEntry", entryData))

			elif entryData.get('type') == 'artist':
				printl( "_MODE_ARTISTS detected", self, "D")
				if (myFilter is not None) and (myFilter != "music"):
					continue

				# in case of music we use always filters
				fullList.append((entryName, Plugin.MENU_FILTER, "musicEntry", entryData))

			elif entryData.get('type') == 'photo':
				printl( "_MODE_PHOTOS detected but excluded", self, "D")
				# if (myFilter is not None) and (myFilter != "photos"):
				# 	continue
				# if self.g_useFilterSections:
				# 	fullList.append((entryName, Plugin.MENU_FILTER, "pictureEntry", entryData))
				# else:
				# 	fullList.append((_(entryData.get('title').encode('utf-8')), getPlugin("pictures", Plugin.MENU_PICTURES), "movieEntry", entryData))

			else:
				raise Exception("we should not be here")

		if config.plugins.dreamplex.useCache.value:
			self.saveSectionCache()

		printl("fullList: " + str(fullList), self, "D")
		printl("", self, "C")
		return fullList

	#=============================================================================
	#
	#=============================================================================
	def getSectionFilter(self, incomingEntryData):
		printl("", self, "S")
		printl("incomingEntryData: " + str(incomingEntryData), self, "D")

		# we need this for cache mechanism
		if incomingEntryData.has_key("uuid"):
			printl("we have a uuid ...", self, "D")
			self.currentUuid = incomingEntryData["uuid"]

		if incomingEntryData.has_key("type"):
			printl("we have a type ...", self, "D")
			self.type = incomingEntryData["type"]

		fullList = []
		# get xml from url
		tree = self.getXmlTreeFromUrl(incomingEntryData["contentUrl"])

		# find coressponding tags in xml
		entries = tree.findall('Directory')

		for entry in entries:
			entryData = (dict(entry.items()))

			entryData["hasSecondaryTag"] = entryData.get("secondary", False)
			entryData["hasPromptTag"] = entryData.get("prompt", False)
			entryData["type"] = incomingEntryData["type"]

			if entryData["hasSecondaryTag"]: #means that the next answer is a filter
				entryData["contentUrl"] = incomingEntryData["contentUrl"] + "/" + entryData["key"]

				fullList.append((_(entryData.get('title').encode('utf-8')), Plugin.MENU_FILTER, "showFilter", entryData))

			else:
				entryData["contentUrl"] = incomingEntryData["contentUrl"] + "/" + entryData["key"]

				if config.plugins.dreamplex.useCache.value:
					# we set this here now to have this information later
					if self.g_sectionCache.has_key(self.currentUuid):
						entryData["source"] = self.g_sectionCache[self.currentUuid]["source"]
					else:
						entryData["source"] = "plex"

					entryData["uuid"] = self.currentUuid
					entryData["type"] = self.type
					printl("entryData: " + str(entryData), self, "D")

				if incomingEntryData["type"] == 'show' or incomingEntryData["type"] == 'episode':
					fullList.append((_(entryData.get('title').encode('utf-8')), getPlugin("tvshows", Plugin.MENU_TVSHOWS), "showEntry", entryData))

				elif incomingEntryData["type"] == 'movie':
					fullList.append((_(entryData.get('title').encode('utf-8')), getPlugin("movies", Plugin.MENU_MOVIES), "movieEntry", entryData))

				elif incomingEntryData["type"] == 'artist':
					fullList.append((_(entryData.get('title').encode('utf-8')), getPlugin("music", Plugin.MENU_MUSIC), "musicEntry", entryData))

				# elif incomingEntryData["type"] == 'photo':
				# 	printl( "_MODE_PHOTOS detected", self, "D")

				else:
					raise Exception("we should not be here")

			printl("entryData: " + str(entryData), self, "D")

		printl("", self, "C")
		return fullList

	#===========================================================================
	#
	#===========================================================================
	def getMoviesFromSection(self, url):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		printl("", self, "C")
		return self.getMediaData(url, tagType = "Video", nextViewMode = "play", currentViewMode = "ShowMovies")

	#===============================================================================
	#
	#===============================================================================
	def getMusicByArtist(self, url):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		printl("", self, "C")
		return self.getDirectoryData(url, nextViewMode = "ShowAlbums", currentViewMode = "ShowArtists")

	#===============================================================================
	#
	#===============================================================================
	def getMusicByAlbum(self, url):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		printl("", self, "C")
		return self.getMediaData(url, tagType = "Track", nextViewMode = "ShowTracks", currentViewMode = "ShowAlbums")

	#=======================================================================
	#
	#=======================================================================
	def getShowsFromSection(self, url):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		fullList=[]

		# get xml from url
		tree = self.getXmlTreeFromUrl(url)
		server = str(self.getServerFromURL(url))
		# find coressponding tags in xml
		entries = tree.findall('Directory')

		# write global xml data to entryData
		mediaContainer  = (dict(tree.items()))
		printl("mediaContainer: " + str(mediaContainer), self, "D")

		for entry in entries:
			entryData = (dict(entry.items()))
			printl("entryData: " + str(entryData), self, "D")

			entryData["currentViewMode"]	= "ShowShows"
			entryData["nextViewMode"]		= "ShowSeasons"
			entryData['server']			    = server
			entryData['tagType']            = "Show"

			entryData['thumb']			    = self.getImage(entry, server, myType = "thumb")
			entryData['art']	            = self.getImage(entry, server, myType = "art")
			entryData['banner']             = self.getImage(entry, server, myType = "banner")
			entryData['token']			    = self.g_myplex_accessToken

			if mediaContainer["title2"] != "By Folder":
				viewState = self.getViewStateForShowEntry(entryData)
				printl("viewState: " + str(viewState), self, "D")

				if self.g_showUnSeenCounts:
					entryData['title'] = entryData['title'] + " ("+ str(entryData["leafCount"]) + "/" + str(entryData["viewedLeafCount"]) + ")"
			else:
				entryData['tagType']            = "Directory"
				viewState = None

			#Create URL based on whether we are going to flatten the season view
			if self.g_flattenShow:
				printl("Flattening all shows", self, "I")
				url = 'http://%s/%s'  % ( server, entryData['key'].replace("children","allLeaves"))
			else:
				url = 'http://%s/%s'  % ( server, entryData['key'])

			# add to fullList
			fullList.append(self.getFullListEntry(entryData, url, viewState, isDirectory=True))

		printl("", self, "C")
		return fullList, mediaContainer

	#===========================================================================
	#
	#===========================================================================
	def getSeasonsOfShow(self, url):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		fullList=[]

		# get xml from url
		tree = self.getXmlTreeFromUrl(url)
		server = str(self.getServerFromURL(url))

		# find coressponding tags in xml
		entries = tree.findall('Directory')
		printl("entries: " + str(entries), self, "D")

		# write global xml data to entryData
		mediaContainer  = (dict(tree.items()))
		printl("mediaContainer: " + str(mediaContainer), self, "D")

		for entry in entries:
			entryData = (dict(entry.items()))
			printl("entryData: " + str(entryData), self, "D")

			if self.g_flattenShow:
				url='http://' + server + entryData["key"]
				self.getEpisodesOfSeason(url)
				return

			entryData["currentViewMode"]	= "ShowSeasons"
			entryData["nextViewMode"]		= "ShowEpisodes"
			entryData['server']			    = server
			entryData['tagType']            = "Episodes"

			entryData['thumb']			    = self.getImage(entry, server, myType = "thumb")
			entryData['art']	            = self.getImage(entry, server, myType = "art")
			entryData['token']			    = self.g_myplex_accessToken

			# if we are "all episodes" we do not have ratingKey - for this reason we set "key" as "ratingKey" form parent Mediacontainer but only if we are not in ByFolder mode
			if "ratingKey" not in entryData and mediaContainer["title2"] != "By Folder":
				entryData["ratingKey"] = mediaContainer["key"]

			if mediaContainer["title2"] != "By Folder":
				viewState = self.getViewStateForShowEntry(entryData)
			else:
				entryData['tagType']            = "Directory"
				viewState = None

			url = 'http://%s/%s'  % ( server, entryData['key'])

			# add to fullList
			fullList.append(self.getFullListEntry(entryData, url, viewState, isDirectory=True))

		printl("fullList: " + str(fullList), self, "C")
		printl("", self, "C")
		return fullList, mediaContainer

	#===============================================================================
	#
	#===============================================================================
	def getEpisodesOfSeason(self, url, directMode=False):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")
		if not directMode:
			nextViewMode    = "play"
		else:
			nextViewMode	= "directMode"

		return self.getMediaData(url, tagType = "Video", nextViewMode = nextViewMode, currentViewMode="ShowEpisodes", switchMedias=True )

	#===========================================================================
	#
	#===========================================================================
	def getMusicTracks(self, url):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		printl("", self, "C")
		return self.getMediaData(url, tagType = "Track", nextViewMode = "play", currentViewMode="ShowTracks")

	#===========================================================================
	#
	#===========================================================================
	def getMediaData(self, url, tagType, nextViewMode, currentViewMode, switchMedias=False):
		printl("", self, "S")
		fullList=[]

		# get xml from url
		tree = self.getXmlTreeFromUrl(url)
		server = str(self.getServerFromURL(url))
		# find coressponding tags in xml
		entries = tree.findall(tagType)

		# write global xml data to entryData
		mediaContainer  = (dict(tree.items()))
		printl("mediaContainer: " + str(mediaContainer), self, "D")

		for entry in entries:
			entryData = (dict(entry.items()))
			printl("entryData: " + str(entryData), self, "D")

			entryData["currentViewMode"]	= currentViewMode
			entryData["nextViewMode"]		= nextViewMode
			entryData['server']			    = server
			entryData['tagType']            = tagType
			entryData['genre']			    = " / ".join(self.getListFromTag(entry, "Genre"))
			entryData['director']			= " / ".join(self.getListFromTag(entry, "Director"))
			entryData['cast']	            = " / ".join(self.getListFromTag(entry, "Role"))
			entryData['writer']             = " / ".join(self.getListFromTag(entry, "Writer"))
			entryData['country']            = " / ".join(self.getListFromTag(entry, "Country"))

			if switchMedias:
				# we need this for example for episodes
				entryData['thumb']			    = self.getImage(entry, server, myType = "art")
				entryData['art']	            = self.getImage(entry, server, myType = "thumb")
			else:
				entryData['thumb']			    = self.getImage(entry, server, myType = "thumb")
				entryData['art']	            = self.getImage(entry, server, myType = "art")

			entryData['token']			    = self.g_myplex_accessToken

			# add part and media data to main data element
			mediaDataArr= self.getPartAndMediaDataFromEntry(entry)

			entryData["mediaDataArr"] = mediaDataArr

			# set seen state for picture handling in view
			seenVisu = self.getViewStatefromViewCount(entryData)

			# add to fullList
			fullList.append(self.getFullListEntry(entryData, url, seenVisu))

		# find coressponding tags in xml
		entries = tree.findall('Directory')

		for entry in entries:
			entryData = (dict(entry.items()))
			printl("directoryData: " + str(entryData), self, "D")

			entryData['server'] 	        = str(server)
			entryData['tagType']            = "Directory"
			entryData["currentViewMode"]	= currentViewMode
			entryData["nextViewMode"]	    = "ShowDirectory"

			# add to fullList
			fullList.append(self.getFullListEntry(entryData, url, isDirectory = True))

		printl("", self, "C")
		return fullList, mediaContainer

	#===============================================================================
	#
	#===============================================================================
	def getDirectoryData(self, url, nextViewMode, currentViewMode):
		printl("", self, "S")
		fullList = []

		# get xml from url
		tree = self.getXmlTreeFromUrl(url)
		server = str(self.getServerFromURL(url))
		# find coressponding tags in xml
		entries = tree.findall("Directory")

		# write global xml data to entryData
		mediaContainer  = (dict(tree.items()))
		printl("mediaContainer: " + str(mediaContainer), self, "D")

		for entry in entries:
			entryData = (dict(entry.items()))
			printl("entryData: " + str(entryData), self, "D")

			entryData['server']				        = server
			entryData['tagType']                    = "Directory"
			entryData["currentViewMode"]		    = currentViewMode
			entryData["nextViewMode"]			    = nextViewMode

			entryData['thumb']			    = self.getImage(entry, server, myType = "thumb")
			entryData['art']	            = self.getImage(entry, server, myType = "art")

			# add to fullList
			fullList.append(self.getFullListEntry(entryData, url, isDirectory = True))

		printl("", self, "C")
		return fullList, mediaContainer

	#===========================================================================
	#
	#===========================================================================s
	def getPartAndMediaDataFromEntry(self, entry):
		printl("", self, "S")
		mediaDataArr = []

		for child in entry:
			isMedia = False
			if child.tag == "Media":
				isMedia = True
				mediaData = (dict(child.items()))
				printl("mediaData: " + str(mediaData), self, "D")
				mediaData["Parts"] = []

			for babies in child:
				if babies.tag == "Part":
					partData = (dict(babies.items()))
					printl( "partData:" + str(partData), self, "D")
					mediaData["Parts"].append(partData)

			if isMedia:
				mediaDataArr.append(mediaData)

		printl("", self, "C")
		return mediaDataArr

	#===========================================================================
	#
	#===========================================================================
	def setIpData(self):
		printl("", self, "S")

		self.g_host = "%d.%d.%d.%d" % tuple(self.g_serverConfig.ip.value)

		printl("using this serverIp: " +  self.g_host, self, "I")
		printl("using this serverPort: " +  self.serverConfig_port, self, "I")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setMyPlexData(self):
		printl("", self, "S")

		self.g_myplex_username = self.g_serverConfig.myplexUsername.value
		self.g_myplex_password = self.g_serverConfig.myplexPassword.value
		self.g_myplex_url	  = self.g_serverConfig.myplexUrl.value

		if self.serverConfig_myplexToken == "" or self.g_serverConfig.renewMyplexToken.value == True:
			printl("serverconfig: " + str(self.g_serverConfig), self, "D")
			self.serverConfig_myplexToken = self.getNewMyPlexToken()

			if self.serverConfig_myplexToken is False:
				self.g_error = True

			else:
				self.g_serverConfig.myplexTokenUsername.value = self.g_myplex_username
				self.g_serverConfig.myplexTokenUsername.save()
				self.g_serverConfig.myplexToken.value = self.serverConfig_myplexToken
				self.g_serverConfig.myplexToken.save()

		else:
			self.serverConfig_myplexToken = self.g_serverConfig.myplexToken.value

		printl("myplexUrl: " +  str(self.g_myplex_url), self, "D")
		printl("myplex_username: " +  str(self.g_myplex_username), self, "D", True, 10)
		printl("myplex_password: " +  str(self.g_myplex_password), self, "D", True, 6)
		printl("myplex_token: " +  str(self.serverConfig_myplexToken), self, "D", True, 6)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def prepareServerDict(self):
		printl("", self, "S")

		self.g_serverDict = {}

		if self.serverConfig_connectionType == "2": # MYPLEX
			printl( "Adding myplex as server location", self, "D")
			self.g_serverDict = {'serverName':'MYPLEX', 'address':"my.plex.app", 'discovery':'myplex', 'token':None, 'uuid':None, 'role':'master'}

		else:
			if not self.g_host or self.g_host == "<none>":
				self.g_host = None

			elif not self.serverConfig_port:
				printl( "No port defined. Using default of " + DEFAULT_PORT, self, "D")
				self.g_currentServer = self.g_host + ":" + DEFAULT_PORT

			else:
				self.g_currentServer = self.g_host + ":" + self.serverConfig_port
				printl( "Settings hostname and port: " + self.g_currentServer, self, "D")

			if self.g_currentServer is not None:
				printl("g_currentServer: " + str(self.g_currentServer), self, "D")
				self.g_serverDict = {'serverName':self.serverConfig_Name, 'address':self.g_currentServer, 'discovery':'local', 'token':None, 'uuid':None, 'role':'master'}
			else:
				raise Exception

			# we have to set self.g_myplex_accessTokenDict here
			# because none will trigger empty tokens that are needed when we do not use myPlex
			self.g_myplex_accessTokenDict = {}

			# just in case we use myPlex also in local Lan we have to set the token data
			if self.serverConfig_localAuth:
				self.g_myplex_accessTokenDict[str(self.g_currentServer)] = self.serverConfig_myplexToken
			else:
				self.g_myplex_accessTokenDict[str(self.g_currentServer)] = None

			# now we genereate and store all headers that are needed
			self.setAccessTokenHeader()

		printl("DreamPlex -> serverList is " + str(self.g_serverDict), self, "D")
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setAccessTokenHeader(self, serverVersion = None):
		printl("", self, "S")

		for key, value in self.g_myplex_accessTokenDict.iteritems():
			self.g_myplex_accessTokenDict[key] = {}

			uToken = self.getAuthDetails({'token':value})
			#printl("uToken: " +  str(uToken), self, "D", True, 6)
			self.g_myplex_accessTokenDict[key]["uToken"] = uToken

			hToken = self.getAuthDetails({'token':value}, False)
			#printl("hToken: " +  str(hToken), self, "D", True, 6)
			self.g_myplex_accessTokenDict[key]["hToken"] = hToken

			aToken = self.getAuthDetails({'token':value}, prefix="?")
			#printl("aToken: " +  str(aToken), self, "D", True, 6)
			self.g_myplex_accessTokenDict[key]["aToken"] = aToken

			if serverVersion is not None:
				self.g_myplex_accessTokenDict[key]["serverVersion"] = serverVersion

		printl("g_myplex_accessTokenDict: " + str(self.g_myplex_accessTokenDict), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def leaveOnError(self):
		printl("", self, "S")

		mainMenuList = []
		mainMenuList.append((_("Press exit to return"), "", "messageEntry"))
		mainMenuList.append((_("If you are using myPlex"), "", "messageEntry"))
		mainMenuList.append((_("please check if curl is installed."), "", "messageEntry"))
		mainMenuList.append((_("You can use Systemcheck in the menu."), "", "messageEntry"))

		printl("", self, "C")
		return mainMenuList

	#=============================================================================
	#
	#=============================================================================
	def loadSectionCache(self):
		printl("", self, "S")

		self.sectionCache = "%s%s.cache" % (config.plugins.dreamplex.cachefolderpath.value, "sections", )
		try:
			fd = open(self.sectionCache, "rb")
			self.g_sectionCache = pickle.load(fd)
			fd.close()
			printl("section chache data loaded", self, "D")
			self.sectionCacheLoaded = True
		except:
			printl("section chache data not loaded", self, "D")
			self.g_sectionCache = {}

		printl("", self, "C")

	#=============================================================================
	#
	#=============================================================================
	def saveSectionCache(self):
		printl("", self, "S")

		fd = open(self.sectionCache, "wb")
		pickle.dump(self.g_sectionCache, fd, 2) #pickle.HIGHEST_PROTOCOL
		fd.close()

		printl("", self, "C")

	#=============================================================================
	#
	#=============================================================================
	def updateSectionCache(self, entryData):
		printl("", self, "S")

		myUuid = entryData.get('uuid','Unknown')
		updatedAt = entryData.get('updatedAt', 'Unknown')
		printl("uuid: " + str(myUuid), self, "D")
		printl("updatedAt: " + str(updatedAt), self, "D")
		source = "plex"

		try:
			if not self.sectionCacheLoaded:
				printl("adding data to section cache  ...", self, "D")
				self.g_sectionCache[myUuid] = {'updatedAt': updatedAt}
				self.g_sectionCache[myUuid]["source"] = "plex"

			elif self.sectionCacheLoaded and myUuid != "Unknown" and updatedAt != "Unknown":
				printl("searching in cache ...", self, "D")

				# check if uuid is in dict
				if myUuid in self.g_sectionCache:
					if int(self.g_sectionCache[myUuid].get("updatedAt")) == int(updatedAt):
						printl("unchanged data, using cache data ...", self, "D")
						self.g_sectionCache[myUuid]["source"] = "cache"
					else:
						printl("updating existing uuid in cache ...", self, "D")
						self.g_sectionCache[myUuid] = {'updatedAt': updatedAt}
						self.g_sectionCache[myUuid]["source"] = "plex"
				else:
					printl("new uuid found, updating cache ...", self, "D")
					self.g_sectionCache[myUuid] = {'updatedAt': updatedAt}
					self.g_sectionCache[myUuid]["source"] = "plex"
			else:
				printl("uuid or updateAt are unknown", self, "D")
		except Exception, e:
			printl("something went wrong with section cache", self, "D")
			printl("error: " + str(e), self, "D")

		printl("", self, "C")
		return source

	#=============================================================================
	#
	#=============================================================================
	def getAllSectionsXmlTree(self):
		printl("", self, "S")

		# get xml as tree
		if self.serverConfig_connectionType == "2": # MYPLEX

			if self.serverConfig_myplexToken == "ERROR":
				tree = None
				self._showErrorOnTv(_("MyPlex Token error:\nCheck Username and Password.\n%s") % self.serverConfig_myplexToken)
			else:
				tree = self.getXmlTreeFromPlex('/pms/system/library/sections')

		else:
			tree = self.getXmlTreeFromUrl('http://' + self.g_serverDict['address'] + '/library/sections')

		printl("", self, "C")
		return tree

	#===============================================================================
	#
	#===============================================================================
	def getContentUrl(self, address, path):
		printl("", self, "S")

		contentUrl = 'http://%s%s' % ( address, path)

		printl("contentUrl = " + contentUrl, self, "D")
		printl("", self, "C")
		return contentUrl

	#====================================================================
	#
	#====================================================================
	def getAuthDetails(self, details, url_format=True, prefix="&" ):
		"""
		Takes the token and creates the required arguments to allow
		authentication.  This is really just a formatting tools
		@input: token as dict, style of output [opt] and prefix style [opt]
		@return: header string or header dict
		"""
		printl("", self, "S")

		token = details.get('token', None)
		printl("token: " + str(token), self, "D", True, 8)
		if url_format:
			if token is not None:
				printl("", self, "C")
				return prefix+"X-Plex-Token="+str(token)
			else:
				printl("", self, "C")
				return ""
		else:
			if token is not None:
				printl("", self, "C")
				return {'X-Plex-Token' : token }
			else:
				printl("", self, "C")
				return {}

	#=============================================================================
	#
	#=============================================================================
	def getMyPlexToken(self, renew=False ):
		"""
		Get the myplex token. If the user ID stored with the token
		does not match the current userid, then get new token.  This stops old token
		being used if plex ID is changed. If token is unavailable, then get a new one
		@input: whether to get new token
		@return: myplex token
		"""
		printl("", self, "S")

		try:
			token = self.serverConfig_myplexToken
		except:
			token=""

		if token == ""  or renew:
			token = self.getNewMyPlexToken()

		printl("Using token: " + str(token), self, "D", True, 8)
		printl("", self, "C")
		return token

	#============================================================================
	#
	#============================================================================
	def getNewMyPlexToken(self):
		"""
		Get a new myplex token from myplex API
		@input: nothing
		@return: myplex token
		"""
		printl("", self, "S")

		printl("Getting new token", self, "I")

		if ( self.g_myplex_username or self.g_myplex_password ) == "":
			printl("Missing myplex details in config...", self, "I")

			printl("", self, "C")
			return False

		base64string = base64.encodestring('%s:%s' % (self.g_myplex_username, self.g_myplex_password)).replace('\n', '')
		token = None

		myplex_header = getPlexHeader(self.g_sessionID, asString=False)
		myplex_header.append('Authorization: Basic ' + base64string)

		printl( "Starting auth request", self, "I")
		curl_string = 'curl -s -k -X POST "%s"' % ("https://" + MYPLEX_SERVER + "/users/sign_in.xml")

		for child in myplex_header:
			curl_string += ' -H "' + child + '"'

		printl("curl_string: " + str(curl_string), self, "D")
		response = os.popen(curl_string).read()

		try:
			token = etree.fromstring(response).findtext('authentication-token')
		except Exception:
			self._showErrorOnTv("no xml as response", response)

		if token is None:
			self._showErrorOnTv("", response)

			printl("", self, "C")
			return False
		else:
			self.serverConfig_myplexToken = token
			self.g_serverConfig.myplexTokenUsername.value = self.g_myplex_username
			self.g_serverConfig.myplexTokenUsername.save()
			self.g_serverConfig.myplexToken.value = self.serverConfig_myplexToken
			self.g_serverConfig.myplexToken.save()

		#lets change back renew token to false
		self.g_serverConfig.renewMyplexToken.value = False
		self.g_serverConfig.renewMyplexToken.save()

		printl ("token: " + token, self, "D", True, 8)
		printl("", self, "C")
		return token

	#============================================================================
	#
	#============================================================================
	def doRequest(self, url, myType="GET" ):
		printl("", self, "S")
		printl("url: " + str(url), self, "D")
		server = self.getServerFromURL(url)
		urlPath = self.getUrlPathFormURL(url)
		self.urlPath = urlPath

		try:
			conn = httplib.HTTPConnection(server)

			authHeader = self.get_hTokenForServer(server)
			printl("header: " + str(authHeader), self, "D")
			conn.request(myType, urlPath, headers=authHeader)

			data = conn.getresponse()

			if ( int(data.status) == 301 ) or ( int(data.status) == 302 ):
				printl("status 301 or 302 found", self, "I")

				data = data.getheader('Location')
				printl("data: " + str(data), self, "I")

				printl("", self, "C")
				return data

			elif int(data.status) >= 400:
				error = "HTTP response error: " + str(data.status) + " " + str(data.reason)
				printl( error, self, "I")
				printl("", self, "C")
				self.g_currentError = error
				return False

			else:
				link=data.read()

				#printl("====== XML returned =======", self, "D")
				#printl("data: " + link, self, "D")
				#printl("====== XML finished ======", self, "D")

				printl("", self, "C")
				return link

		except socket.gaierror :
			error = 'Unable to lookup host: ' + server + "\nCheck host name is correct"
			printl( error, self, "I")

			printl("", self, "C")
			return False

		except socket.error, msg :
			error="Unable to connect to " + server +"\nReason: " + str(msg)
			printl( error, self, "I")
			printl("", self, "C")
			return False

	#============================================================================
	#
	#============================================================================
	def getTimelineURL(self, server, container, myId, state, myTime=0, duration=0):
		printl("", self, "S")
		conn = None
		try:

			urlPath="/:/timeline?containerKey=" + container + "&key=/library/metadata/" + myId + "&ratingKey=" + myId

			if state == "buffering":
				urlPath += "&state=buffering&time=" + str(myTime)
			elif state == "playing":
				urlPath += "&state=playing&time=" + str(myTime) + "&duration=" + str(duration)
			elif state == "stopped":
				urlPath += "&state=stopped&time=" + str(myTime) + "&duration=" + str(duration)
			elif state == "paused":
				urlPath += "&state=paused&time=" + str(myTime) + "&duration=" + str(duration)
			else:
				printl("No valid state supplied for getTimelineURL. State: " + str(state), self, "D")
				return

			urlPath += self.get_uTokenForServer(server)

			if self.g_sessionID is None:
				self.g_sessionID=str(uuid.uuid4())

			plexHeader = getPlexHeader(self.g_sessionID)

			conn = httplib.HTTPConnection(server)#,timeout=5)
			conn.request("GET", urlPath, headers=plexHeader)
			data = conn.getresponse()

			if int(data.status) == 200:
				link=data.read()
				try: conn.close()
				except: pass
				printl("", self, "C")
				return link

			else:
				link=data.read()
				try: conn.close()
				except: pass
				printl("", self, "C")
				return link

		except socket.gaierror :
			error = "Unable to locate host [%s]\nCheck host name is correct" % server
			printl( error, self, "I")


		except socket.error, msg :
			error="Server[%s] is offline, or not responding\nReason: %s" % (server, str(msg))
			printl( error, self, "I")

		try:
			conn.close()
		except:
			pass

		printl("", self, "C")
		return False

	#========================================================================
	#
	#========================================================================
	def mediaType(self, partData, server):
		printl("", self, "S")
		stream = partData['key']
		myFile = partData['file']
		self.fallback = False
		self.locations = ""

		#First determine what sort of 'file' file is
		printl("physical file location: " + str(myFile), self, "I")
		try:
			if myFile[0:2] == "\\\\":
				printl("Looks like a UNC",self, "I")
				myType="UNC"
			elif myFile[0:1] == "/" or myFile[0:1] == "\\":
				printl("looks like a unix file", self, "I")
				myType="unixfile"
			elif myFile[1:3] == ":\\" or myFile[1:2] == ":/":
				printl("looks like a windows file", self, "I")
				myType="winfile"
			else:
				printl("uknown file type", self, "I")
				printl("file = " + str(myFile),self, "I")
				myType="notsure"
		except Exception:
				printl("uknown file type", self, "I")
				printl("file = " + str(myFile),self, "I")
				myType="notsure"

		self.currentFile = myFile
		self.currentType = myType
		self.fallback = ""

		# 0 is linux local mount override
		if self.g_stream == "0":
			#check if the file can be found locally
			if myType == "unixfile" or myType == "winfile" or myType == "UNC":

				tree = getXmlContent(config.plugins.dreamplex.configfolderpath.value + "mountMappings")

				self.serverID = str(self.g_serverConfig.id.value)
				printl("serverID: " + str(self.serverID), self, "D")

				for entry in tree.findall("server"):
					printl("servername: " + str(entry.get('id')), self, "D")
					if str(entry.get('id')) == str(self.serverID):

						for mapping in entry.findall('mapping'):
							self.lastMappingId = mapping.attrib.get("id")
							remotePathPart = mapping.attrib.get("remotePathPart")
							localPathPart = mapping.attrib.get("localPathPart")
							printl("self.lastMappingId: " + str(self.lastMappingId), self, "D")
							printl("remotePathPart: " + str(remotePathPart), self, "D")
							printl("localPathPart: " + str(localPathPart), self, "D")

							locationCheck = self.checkFileLocation(remotePathPart, localPathPart)

							# if we find the media within the provided location we leave
							if locationCheck:
								return locationCheck

				printl("Sorry I didn't find the file on the provided locations", self, "I")

			self.fallback = True
			printl("No local mount override possible ... switching to transcoded mode", self, "I")

			self.g_stream="1"

		# 1 is stream no matter what
		if self.g_stream == "1":
			printl( "Selecting stream", self, "I")
			printl("", self, "C")
			return "http://"+server+stream

		# 2 is use SMB or afp override
		elif self.g_stream == "2":
			if self.g_stream == "2":
				protocol="smb"
			else:
				protocol="afp"

			printl( "Selecting smb/unc")
			if myType=="UNC":
				filelocation=protocol+":"+myFile.replace("\\","/")
			else:
				#Might be OSX type, in which case, remove Volumes and replace with server
				server=server.split(':')[0]
				loginstring=""

				if self.g_nasoverride == "true":
					if not self.g_nasoverrideip == "":
						server=self.g_nasoverrideip
						printl("Overriding server with: " + server, self, "I")

					nasuser = self.g_nasuserid
					if not nasuser == "":
						loginstring = self.g_nasuserid +":"+ self.g_naspass + "@"
						printl("Adding AFP/SMB login info for user " + nasuser, self, "I")


				if myFile.find('Volumes') > 0:
					filelocation=protocol+":/"+myFile.replace("Volumes",loginstring+server)
				else:
					if myType == "winfile":
						filelocation=protocol+"://"+loginstring+server+"/"+myFile[3:]
					else:
						#else assume its a file local to server available over smb/samba (now we have linux PMS).  Add server name to file path.
						filelocation=protocol+"://"+loginstring+server+myFile

			if self.g_nasoverride == "true" and self.g_nasroot != "":
				#Re-root the file path
				printl("Altering path " + filelocation + " so root is: " +  self.g_nasroot, self, "I")
				if '/'+self.g_nasroot+'/' in filelocation:
					components = filelocation.split('/')
					index = components.index(self.g_nasroot)
					for i in range(3,index):
						components.pop(3)
					filelocation='/'.join(components)
		else:
			printl( "No option detected, streaming is safest to choose", self, "I" )
			filelocation="http://"+server+stream

		printl("Returning URL: " + filelocation, self, "I")
		printl("", self, "C")
		return filelocation


	#===========================================================================
	#
	#===========================================================================
	def checkFileLocation(self, remotePathPart, localPathPart):
		printl("", self, "S")

		printl("Checking for local file", self, "I")

		printl("untouched remotePathPart: " + str(remotePathPart), self, "D")

		if self.currentType == "winfile" or self.currentType == "UNC":
			# to prevent wrong configuration errors we change all slashes to backslahes
			# this is nessesarry if the users enters the path with slashes instead fo backslahes
			remotePathPart.replace("/", "\\")

		printl("remotePathPart: " + str(remotePathPart), self, "D")
		printl("localPathPart: " + str(localPathPart), self, "D")
		myFile = self.currentFile

		myFile = myFile.replace(remotePathPart, localPathPart)

		# now we change backslahes back to slahes
		if self.currentType == "winfile" or self.currentType == "UNC":
			myFile = myFile.replace("\\", "/")

		myFile = urllib.unquote(myFile)

		printl("altered file string: " + str(myFile), self, "I")
		try:
			exists = open(myFile)
			printl("Local file found, will use this", self, "I")
			exists.close()

			printl("", self, "C")
			return "file:"+myFile
		except:
			self.locations += str(myFile) + "\n"
			printl("", self, "C")
			return False

	#===========================================================================
	#
	#===========================================================================
	def getStreamDataById(self, server, myId):
		printl("", self, "S")

		printl("Gather media stream info", self, "I" )

		#get metadata for audio and subtitle
		suburl="http://"+server+"/library/metadata/"+myId

		self.g_currentServer = server
		printl("g_currentServer: " + str(self.g_currentServer), self, "D")

		html=self.doRequest(suburl)
		#printl("retrived html: " + str(html), self, "D")

		tree = None

		try:
			tree = etree.fromstring(html)
		except Exception, e:
			printl("Exception: " + str(e), self, "D")
			self._showErrorOnTv("no xml as response", html)

		printl("", self, "C")
		return tree

	#===========================================================================
	#
	#===========================================================================
	def getSelectedSubtitleDataById(self, server, myId):
		printl("",self, "S")
		printl("server +  myId: " + str(server) + " / " + str(myId), self, "D")

		tree = self.getStreamDataById(server, myId)

		fromParts = tree.getiterator('Part')
		partitem = None
		#Get the Parts info for media type and source selection
		for part in fromParts:
			try:
				partitem=part.get('id'), part.get('file')
			except:
				pass

		tags=tree.getiterator('Stream')

		printl("Part Item: " + str(partitem),self,"I")

		selectedSubtitle = {'id': -1,
							'index': 		-1,
							'language':	 	"Disabled",
							'languageCode': "NA",
							'format': 		"Disabled",
							'partid' : 	partitem[0]
							}
		for bits in tags:
			stream=dict(bits.items())
			selected = stream.get('selected', "")
			if stream['streamType'] == '3' and selected == '1': #subtitle
				try:
					selectedSubtitle = {		'id': stream['id'],
								'index': 		stream['index'],
								'language':	 	stream['language'],
								'languageCode': stream['languageCode'],
								'format' : 		stream['format'],
								'partid' : 	partitem[0]
						   }
					printl ("selectedSubtitle = " + str(selectedSubtitle), self, "D" )
				except:
					printl ("Unable to read subtitles due to XML parsing error", self, "E" )

		printl("", self, "C")
		return selectedSubtitle

	#===========================================================================
	#
	#===========================================================================
	def getSubtitlesById(self, server, myId):
		"""
		sample:
		<Stream id="25819" streamType="3" selected="1" default="1" index="4" language="Deutsch" languageCode="ger" format="srt"/>
		<Stream id="25820" streamType="3" index="5" language="English" languageCode="eng" format="srt"/>
		"""
		printl("", self, "S")

		subtitlesList = []

		tree = self.getStreamDataById(server, myId)

		fromParts = tree.getiterator('Part')
		partitem = None
		#Get the Parts info for media type and source selection
		for part in fromParts:
			try:
				partitem=part.get('id'), part.get('file')
			except:
				pass

		tags=tree.getiterator('Stream')


		subtitle = {	'id': -1,
						'index': 		-1,
						'language':	 	"None",
						'languageCode': "NA",
						'format': 		"None",
						'partid' : 	partitem[0]
					}

		subtitlesList.append(subtitle)
		for bits in tags:
			stream=dict(bits.items())
			if stream['streamType'] == '3': #subtitle
				try:
					subtitle = {		'id': stream.get('id',-1),
										'index': 		stream.get('index',-1),
										'language':	 	stream.get('language','Unknown'),
										'languageCode': stream.get('languageCode','Ukn'),
										'format' : 		stream.get('format', 'UKN'),
										'partid' : 	partitem[0],
										'selected' : stream.get('selected',0)
								}

					subtitlesList.append(subtitle)
				except:
					printl ("Unable to set subtitles due to XML parsing error", self, "E" )
					pass

		printl ("subtitlesList = " + str(subtitlesList), self, "D" )

		printl("", self, "C")
		return subtitlesList

	#===========================================================================
	#
	#===========================================================================
	def getAudioById(self, server, myId):
		"""
		sample:
		<Stream id="25819" streamType="3" selected="1" default="1" index="4" language="Deutsch" languageCode="ger" format="srt"/>
		<Stream id="25820" streamType="3" index="5" language="English" languageCode="eng" format="srt"/>
		"""
		printl("", self, "S")

		audioList = []

		tree = self.getStreamDataById(server, myId)

		fromParts = tree.getiterator('Part')
		partitem = None
		#Get the Parts info for media type and source selection
		for part in fromParts:
			try:
				partitem=part.get('id'), part.get('file')
			except:
				pass

		tags=tree.getiterator('Stream')

		for bits in tags:
			stream=dict(bits.items())
			if stream['streamType'] == '2': #audio
				try:
					audio = {		'id': stream.get('id',-1),
										'index': 		stream.get('index',-1),
										'language':	 	stream.get('language','Unknown'),
										'languageCode': stream.get('languageCode','Ukn'),
										'format' : 		stream.get('format', 'UKN'),
										'partid' : 	partitem[0],
										'selected' : stream.get('selected',0)
								}

					audioList.append(audio)
				except:
					printl ("Unable to set audio due to XML parsing error", self, "E" )
					pass

		printl ("audioList = " + str(audioList), self, "D" )

		printl("", self, "C")
		return audioList

	#===========================================================================
	#
	#===========================================================================
	def setSubtitleById(self, server, sub_id, part_id):
		printl("", self, "S")

		url = "http://"+str(server)+"/library/parts/"+str(part_id)+"?subtitleStreamID="+ str(sub_id)

		self.doRequest(url, myType="PUT")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setAudioById(self, server, audio_id, part_id):
		printl("", self, "S")

		url = "http://"+str(server)+"/library/parts/"+str(part_id)+"?audioStreamID="+ str(audio_id)

		self.doRequest(url, myType="PUT")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getAudioSubtitlesMedia(self, server, myId, myType ):
		"""
		Cycle through the Parts sections to find all "selected" audio and subtitle streams
		If a stream is marked as selected=1 then we will record it in the dict
		Any that are not, are ignored as we do not need to set them
		We also record the media locations for playback decision later on
		"""
		printl("", self, "S")

		tree = self.getStreamDataById(server, myId)

		parts=[]
		partsCount=0
		subtitle={}
		subCount=0
		audio={}
		audioCount=0
		external={}
		videoData={}
		mediaData={}
		subOffset=-1
		audioOffset=-1
		selectedSubOffset=-1
		selectedAudioOffset=-1

		fromVideo = tree.find(myType) # Track or Video

		videoData['title'] = fromVideo.get('title', "")
		videoData['tagline'] = fromVideo.get('tagline', "")
		videoData['summary'] = fromVideo.get('summary', "")
		videoData['year'] = fromVideo.get('year', "")
		videoData['studio'] = fromVideo.get('studio', "")
		videoData['viewOffset']=fromVideo.get('viewOffset',0)
		videoData['duration']=fromVideo.get('duration',0)
		videoData['contentRating'] = fromVideo.get('contentRating', "")

		mediaData['audioCodec'] = fromVideo.get('audioCodec', "")
		mediaData['videoCodec'] = fromVideo.get('videoCodec', "")
		mediaData['videoResolution'] = fromVideo.get('videoResolution', "")
		mediaData['videoFrameRate'] = fromVideo.get('videoFrameRate', "")

		fromParts = tree.getiterator('Part')

		contents="type"

		#Get the Parts info for media type and source selection
		for part in fromParts:
			printl("part.attrib: " + str(part.attrib), self, "D")

			try:
				bits=part.get('key'), part.get('file'), part.get('container'), part.get('size'), part.get('duration')
				parts.append(bits)
				partsCount += 1
			except: pass

		if myType == "Video":
			if self.g_streamControl == "1" or self.g_streamControl == "2":

				contents="all"
				fromStream = tree.getiterator('Stream')
				printl("fromStream: " + str(fromStream), self, "D")
				#streamType: The type of media stream/track it is (1 = video, 2 = audio, 3 = subtitle)

				for bits in fromStream:
					printl("bits.attrib: " + str(bits.attrib), self, "D")
					stream=dict(bits.items())
					printl("stream: " + str(stream), self, "D")
					if stream['streamType'] == '2': #audio
						audioCount += 1
						audioOffset += 1
						try:
							if stream['selected'] == "1":
								printl("Found preferred audio id: " + str(stream['id']), self, "I" )
								audio=stream
								selectedAudioOffset=audioOffset
						except: pass

					elif stream['streamType'] == '3': #subtitle
						subOffset += 1
						try:
							if stream['key']:
								printl( "Found external subtitles id : " + str(stream['id']),self, "I")
								external=stream
								external['key']='http://'+server+external['key']
						except:
							#Otherwise it's probably embedded
							try:
								if stream['selected'] == "1":
									printl( "Found preferred subtitles id : " + str(stream['id']), self, "I")
									subCount += 1
									subtitle=stream
									selectedSubOffset=subOffset
							except: pass

			else:
					printl( "Stream selection is set OFF", self, "I")


		streamData={'contents'   : contents,
					'audio'	  : audio,
					'audioCount' : audioCount,
					'subtitle'   : subtitle,
					'subCount'   : subCount,
					'external'   : external,
					'parts'	  : parts,
					'partsCount' : partsCount,
					'videoData'  : videoData,
					'mediaData'  : mediaData,
					'subOffset'  : selectedSubOffset ,
					'audioOffset': selectedAudioOffset }

		printl ("streamData = " + str(streamData), self, "D" )
		printl("", self, "C")
		return streamData

	#========================================================================
	#
	#========================================================================
	def getMediaOptionsToPlay(self, myId, vids, override=False, myType="Video" ):
		printl("", self, "S")

		self.getTranscodeSettings(override)
		self.server = self.getServerFromURL(vids)
		self.streams=self.getAudioSubtitlesMedia(self.server,myId, myType)

		printl("partsCount: " + str(self.streams['partsCount']), self, "D")
		printl("parts: " + str(self.streams['parts']), self, "D")
		printl("server: " + str(self.streams), self, "D")

		printl("", self, "C")
		return self.streams['partsCount'], self.streams['parts'], self.server

	#========================================================================
	#
	#========================================================================
	def playLibraryMedia(self, myId, url):
		printl("", self, "S")

		printl("playLibraryMediaUrl: " + str(url), self, "D")

		printl("server: " + str(self.server), self, "D")

		if url is None:
			return

		protocol=url.split(':',1)[0]

		# set standard playurl
		playurl=url

		token = self.get_aTokenForServer(self.server)

		#alter playurl if needed
		if protocol == "file":
			printl( "We are playing a local file", self, "I")
			playurl=url.split(':',1)[1]

		elif protocol == "http":
			printl( "We are playing a stream", self, "I")
			if self.g_transcode == "true":
				printl( "We will be transcoding the stream", self, "I")
				playurl = self.transcode(myId,url+token)
			else:
				printl( "We will be playing raw stream", self, "I")
				playurl = url+token

		try:
			resume=int(int(self.streams['videoData']['viewOffset']))
		except:
			resume=0

		printl("Resume has been set to " + str(resume),self, "I")

		result=1

		if resume > 0:

			if result == -1:
				printl("", self, "C")
				return

			if not (self.g_transcode == "true" ):
				self.setAudioSubtitles(self.streams)

		multiUserServer = False
		# multiuser works only if the server is compatible
		self.setServerDetails()
		if self.g_serverVersion >= "0.9.8.0" and self.g_multiUser:
			multiUserServer = True

		printl("multiUserServer (version): " + str(multiUserServer),self,"I")

		printl("PLAYURL => " + playurl, self, "I")
		printl("RESUME => " + str(resume), self, "I")
		printl("", self, "C")

		playerData = {}
		playerData["playUrl"] = playurl
		playerData["resumeStamp"] = resume
		playerData["server"] = self.server
		playerData["id"] = myId
		playerData["multiUserServer"] = multiUserServer
		playerData["playbackType"] = self.serverConfig_playbackType
		playerData["connectionType"] = self.serverConfig_connectionType
		playerData["localAuth"] = self.serverConfig_localAuth
		playerData["transcodingSession"] = self.g_sessionID
		playerData["videoData"] = self.streams['videoData']
		playerData["mediaData"] = self.streams['mediaData']
		playerData["fallback"] = self.fallback
		playerData["locations"] = self.locations
		playerData["currentFile"] = self.currentFile
		playerData["universalTranscoder"] = self.g_serverConfig.universalTranscoder.value
		
		return playerData
	
	#===========================================================================
	# 
	#===========================================================================
	def setAudioSubtitles(self, stream ): 
		printl("", self, "S")
			
		if stream['contents'] == "type":
			printl ("No streams to process.", self, "I")
			
			if self.g_streamControl == "3":
				printl ("All subs disabled", self, "I")
			
			printl("", self, "C")   
			return True
	
		if self.g_streamControl == "1" or  self.g_streamControl == "2":
			audio=stream['audio']
			printl("Attempting to set Audio Stream", self, "I")
			#Audio Stream first		
			if stream['audioCount'] == 1:
				printl ("Only one audio stream present - will leave as default", self, "I")
			elif stream['audioCount'] > 1:
				printl ("Multiple audio stream. Attempting to set to local language", self, "I")
				try:
					if audio['selected'] == "1":
						printl ("Found preferred language at index " + str(stream['audioOffset']), self, "I")
						printl ("Audio set", self, "I")
				except: pass

		#Try and set embedded subtitles
		if self.g_streamControl == "1":
			subtitle=stream['subtitle']
			printl("Attempting to set subtitle Stream", self, "I")
			try:
				if stream['subCount'] > 0 and subtitle['languageCode']:
					printl ("Found embedded subtitle for local language", self, "I" )
					printl ("Enabling embedded subtitles", self, "I")
					printl("", self, "C")
					return True
				else:
					printl ("No embedded subtitles to set", self, "I")
			except:
				printl("Unable to set subtitles", self, "I")

		if self.g_streamControl == "1" or self.g_streamControl == "2":
			external=stream['external']
			printl("Attempting to set external subtitle stream", self, "I")
		
			try:   
				if external:
					try:
						printl ("External of type ["+external['codec']+"]", self, "I")
						if external['codec'] == "idx" or external['codec'] =="sub":
							printl ("Skipping IDX/SUB pair - not supported yet", self, "I")
						else:	
							printl("", self, "C")
							return True
					except: pass					
				else:
					printl ("No external subtitles available. Will turn off subs", self, "I")
			except:
				printl ("No External subs to set", self, "I")

		printl("", self, "C")   
		return False

	#===============================================================================
	#
	#===============================================================================
	def getXmlTreeFromPlex(self, url):
		"""
		Connect to the my.plexapp.com service and get an XML pages
		A seperate function is required as interfacing into myplex
		is slightly different than getting a standard URL
		@input: url to get, whether we need a new token, whether to display on screen err
		@return: an xml page as string or false
		"""
		printl("", self, "S")
		printl("url = " + MYPLEX_SERVER + url, self, "D")

		tree = None

		printl( "Starting request", self, "D")
		curl_string = 'curl -s -k "%s"' % ("https://" + MYPLEX_SERVER + url + "?X-Plex-Token=" + str(self.serverConfig_myplexToken))

		printl("curl_string: " + str(curl_string), self, "D", True, 10)
		response = os.popen(curl_string).read()

		try:
			tree = etree.fromstring(response)
		except Exception:
			self._showErrorOnTv("no xml as response", response)

		printl("", self, "C")
		return tree

	#===============================================================================
	#
	#===============================================================================
	def getXmlTreeFromUrl(self, url):
		printl("", self, "S")
		#Get the URL and server name. Get the XML and parse

		tree = None

		html = self.doRequest(url)
		printl("html: " + str(html), self, "D")
		if html is False:
			printl("", self, "C")
			return

		try:
			tree = etree.fromstring(html)
		except Exception:
			self._showErrorOnTv("no xml as response", html)

		printl("", self, "C")
		return tree

	#===============================================================================
	#
	#===============================================================================
	def getListFromTag(self, entry, tagName):
		printl("", self, "S")
		tempList = []

		for child in entry:
			if child.tag == tagName:
				tempList.append(child.get('tag').encode("utf-8"))

		printl("", self, "C")
		return tempList
	
	#=============================================================================
	# 
	#=============================================================================
	def getImage(self, data, server, myType, transcode = True):
		"""
		Simply take a URL or path and determine how to format for images
		@ input: elementTree element, server name
		@ return formatted URL
		"""
		printl("", self, "S")
		printl("myType: " + str(myType), self, "D")

		image = data.get(myType,'').split('?t')[0]

		if image == '':
			printl("", self, "C")   
			return ""
			
		elif image[0:4] == "http" :
			printl("", self, "C")   
			return image
		
		elif image[0] == '/':
			if transcode:
				printl("", self, "C")   
				return self.photoTranscode(server,'http://localhost:32400'+image)
			else:
				printl("", self, "C")   
				return 'http://'+server+image
		
		else: 
			printl("", self, "C")   
			return ""

	#===========================================================================
	# 
	#===========================================================================
	def photoTranscode(self, server, url, width=999, height=999):
		printl("", self, "S")

		transcode_url = None

		if width is not None and height is not None:
			transcode_url = 'http://%s/photo/:/transcode?url=%s&width=%s&height=%s' % (server, urllib.quote_plus(url), width, height)
			printl("transcode_url: " + str(transcode_url), self, "D")
		else:
			printl("unspecified width and height", self, "D")
		
		printl("", self, "C")   
		return transcode_url

	#============================================================================
	# 
	#============================================================================
	def watched(self, url ): 
		printl("", self, "S")
	
		if url.find("unscrobble") > 0:
			printl ("Marking as unwatched with: " + url, self, "I")
		else:
			printl ("Marking as watched with: " + url, self, "I")
		
		self.doRequest(url)

		printl("", self, "C")   
		return

	#===============================================================================
	# 
	#===============================================================================
	def deleteMedia(self, url ): 
		printl("", self, "S")
		printl ("deleting media at: " + url, self, "I")
		
		return_value = True
		if return_value:
			printl("Deleting....")
			self.doRequest(url, myType="DELETE")
		
		printl("", self, "C")   
		return True
	
	#===============================================================================
	# 
	#===============================================================================
	def buildContextMenu(self, url, ratingKey, server):
		printl("", self, "S")

		context={}

		#Initiate Library refresh 
		refreshURL=url.replace("/all", "/refresh")
		libraryRefreshURL = refreshURL.split('?')[0] # + self.get_aTokenForServer(server)
		context['libraryRefreshURL'] = libraryRefreshURL

		#Mark media unwatched
		unwatchedURL="http://"+server+"/:/unscrobble?key="+ratingKey+"&identifier=com.plexapp.plugins.library"# + self.get_uTokenForServer(server)
		context['unwatchURL'] = unwatchedURL

		#Mark media watched
		watchedURL="http://"+server+"/:/scrobble?key="+ratingKey+"&identifier=com.plexapp.plugins.library"# + self.get_uTokenForServer(server)
		context['watchedURL'] = watchedURL
	
		#Delete media from Library
		deleteURL="http://"+server+"/library/metadata/"+ratingKey # + self.get_uTokenForServer(server)
		context['deleteURL'] = deleteURL
	
		printl("", self, "C")
		return context

#===============================================================================
# HELPER FUNCTIONS
#===============================================================================
	
	#===========================================================================
	# 
	#===========================================================================
	def _showErrorOnTv(self, text, content):
		printl("", self, "S")
		
		self.session.open(MessageBox,_("UNEXPECTED ERROR:") + "\n%s\n%s" % (text, content), MessageBox.TYPE_INFO)
		
		printl("", self, "C")   

	#===========================================================================
	# 
	#===========================================================================
	def getUrlPathFormURL(self, url ):
		printl("", self, "S")

		if url[0:4] == "http" or url[0:4] == "plex":
			printl("", self, "C")   
			return "/"+"/".join(url.split('/')[3:])
		else:
			printl("", self, "C")   
			return "/"+"/".join(url.split('/')[1:])

		#===========================================================================
	#
	#===========================================================================
	def getServerFromURL(self, url ):
		"""
		Simply split the URL up and get the server portion, sans port
		@ input: url, woth or without protocol
		@ return: the URL server
		"""
		printl("", self, "S")
		printl("url: " + str(url), self, "D")

		if url[0:4] == "http" or url[0:4] == "plex":
			printl("", self, "C")
			return url.split('/')[2]
		else:
			printl("", self, "C")
			return url.split('/')[0]
	
	#============================================================================
	# 
	#============================================================================
	def getLinkURL(self, url, pathData, server ): 
		"""
		Investigate the passed URL and determine what is required to
		turn it into a usable URL
		@ input: url, XML data and PM server address
		@ return: Usable http URL
		"""
		printl("", self, "S")

		path=pathData.get('key','')
		printl("Path is " + path, self, "I")
		
		if path == '':
			printl("Empty Path", self, "I")
			printl("", self, "C")   
			return
		
		#If key starts with http, then return it
		if path[0:4] == "http":
			printl("Detected http link", self, "I")
			printl("", self, "C")   
			return path
			
		#If key starts with a / then prefix with server address	
		elif path[0] == '/':
			printl("Detected base path link", self, "I")
			printl("", self, "C")   
			return 'http://%s%s' % ( server, path )
	
		#If key starts with plex:// then it requires transcoding 
		elif path[0:5] == "plex:":
			printl("Detected plex link", self, "I")	
			components=path.split('&')
			for i in components:
				if 'prefix=' in i:
					del components[components.index(i)]
					break
			if pathData.get('identifier',None):
				components.append('identifier='+pathData['identifier'])
			
			path='&'.join(components)
			printl("", self, "C")		   
			return 'plex://'+server+'/'+'/'.join(path.split('/')[3:])
			
		#Any thing else is assumed to be a relative path and is built on existing url		
		else:
			printl("Detected relative link", self, "I")
			printl("", self, "C")   
			return "%s/%s" % ( url, path )

#===============================================================================
# GETTER FUNCTIONS
#===============================================================================

	#===============================================================================
	# 
	#===============================================================================
	def getTranscodeSettings(self, override=False ):
		printl("", self, "S")

		if override is True:
			printl( "Transcode override.  Will play media with addon transcoding settings", self, "I")
			self.g_transcode="true"
	
		if self.g_transcode == "true":
			
			printl( "We are set to Transcode, overriding stream selection", self, "I")
		
			printl( "Transcode quality is " + self.serverConfig_quality, self, "I")
			protocols = "protocols=http-video;"
			videoDecoders = "videoDecoders=mpeg2video{profile:high&resolution:1080&level:51},mpeg4{profile:high&resolution:1080&level:51},mpeg1video{profile:high&resolution:1080&level:51},mp4{profile:high&resolution:1080&level:51},h264{profile:high&resolution:1080&level:51}"
			#dts is not running for some reason
			audioDecoders = "audioDecoders=mp3,aac"

			self.g_capability = urllib.quote_plus(protocols + ";" + videoDecoders + ";" + audioDecoders)

			printl("Plex Client Capability = " + self.g_capability, self, "I")
			
			printl("", self, "C")   

	#===========================================================================
	# 
	#===========================================================================
	def get_hTokenForServer(self, server):
		printl("", self, "S")

		printl("", self, "C")
		return self.g_myplex_accessTokenDict[server]["hToken"]

	#===========================================================================
	# 
	#===========================================================================
	def get_aTokenForServer(self, server):
		printl("", self, "S")

		printl("", self, "C")
		return self.g_myplex_accessTokenDict[server]["aToken"]

	#===========================================================================
	# 
	#===========================================================================
	def get_uTokenForServer(self, server):
		printl("", self, "S")

		printl("", self, "C")   
		return self.g_myplex_accessTokenDict[server]["uToken"]

	#===========================================================================
	# 
	#===========================================================================
	def getServerName(self):
		printl("", self, "S")
		
		printl("", self, "C")
		return self.serverConfig_Name
	
	#===========================================================================
	# 
	#===========================================================================
	def setServerDetails(self):
		printl("", self, "S")

		url = self.getServerFromURL(self.g_currentServer)
		xml = self.doRequest(url)

		printl("xml: " + str(xml), self, "D")

		tree = etree.fromstring(xml)
		self.g_serverVersion = str(tree.get("version").split('-')[0])
		if str(tree.get("multiuser")) == "1":
			self.g_multiUser = True
		else:
			self.g_multiUser = False
			
		printl("self.g_serverVersion: " + str(self.g_serverVersion), self, "D")
		printl("self.g_multiUser: " + str(self.g_multiUser), self, "D")

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getUniversalTranscoderSettings(self):
		printl("", self, "S")
		
		quality = int(self.g_serverConfig.uniQuality.value)
		
		if quality == 0:
			#420x240, 320kbps
			videoResolution="420x240"
			maxVideoBitrate="320"
			videoQuality="30"
		elif quality == 1:
			#576x320, 720 kbps
			videoResolution="576x320"
			maxVideoBitrate="720"
			videoQuality="40"
		elif quality == 2:
			#720x480, 1,5mbps
			videoResolution="720x480"
			maxVideoBitrate="1500"
			videoQuality="60"
		elif quality == 3:
			#1024x768, 2mbps
			videoResolution="1024x768"
			maxVideoBitrate="2000"
			videoQuality="60"
		elif quality == 4:
			#1280x720, 3mbps
			videoResolution="1280x720"
			maxVideoBitrate="3000"
			videoQuality="75"
		elif quality == 5:
			#1280x720, 4mbps
			videoResolution="1280x720"
			maxVideoBitrate="4000"
			videoQuality="100"
		elif quality == 6:
			#1920x1080, 8mbps
			videoResolution="1920x1080"
			maxVideoBitrate="8000"
			videoQuality="60"
		elif quality == 7:
			#1920x1080, 10mbps
			videoResolution="1920x1080"
			maxVideoBitrate="10000"
			videoQuality="75"
		elif quality == 8:
			#1920x1080, 12mbps
			videoResolution="1920x1080"
			maxVideoBitrate="12000"
			videoQuality="90"
		elif quality == 9:
			#1920x1080, 20mbps
			videoResolution="1920x1080"
			maxVideoBitrate="20000"
			videoQuality="100"
		else:
			#1920x1080, 20mbps
			videoResolution="no settings"
			maxVideoBitrate="no settings"
			videoQuality="no settings"
		
		printl("", self, "C")
		return videoQuality, videoResolution, maxVideoBitrate

	#===========================================================================
	#
	#===========================================================================
	def transcode(self, myID, url):
		printl("", self, "S")
		# todo try to add here header as well
		server=self.getServerFromURL(url)

		#Check for myplex user, which we need to alter to a master server
		if 'plexapp.com' in url:
			server=self.g_currentServer

		printl("Using preferred transcoding server: " + server, self, "I")

		filename= '/'.join(url.split('/')[3:])

		#These are the DEV API keys - may need to change them on release
		publicKey="KQMIY6GATPC63AIMC4R2" #self.pKey
		privateKey = "k3U6GLkZOoNIoSgjDshPErvqMIFdE0xMTx8kgsrhnC0="  #pac

		streamURL = ""
		transcode = []
		ts = int(time())
		if self.g_serverConfig.universalTranscoder.value:
			videoQuality, videoResolution, maxVideoBitrate = self.getUniversalTranscoderSettings()
			printl("Setting up HTTP Stream with universal transcoder", self, "I")
			streamPath = "video/:/transcode/universal"
			streamFile = 'start.m3u8'
			transcode.append("path=%s%s" % (quote_plus('http://127.0.0.1:32400'), quote_plus(self.urlPath)))
			transcode.append("session=%s" % self.g_sessionID)
			transcode.append("protocol=hls")
			transcode.append("offset=0")
			transcode.append("3g=0")
			transcode.append("directPlay=0")
			transcode.append("directStream=0")
			transcode.append("videoQuality=" + videoQuality)
			transcode.append("videoResolution=" + videoResolution)
			transcode.append("maxVideoBitrate=" + maxVideoBitrate)
			transcode.append("subtitleSize=100")
			transcode.append("audioBoost=100")
			transcode.append("waitForSegments=1")
			transcode.append("X-Plex-Device=iPhone")
			transcode.append("X-Plex-Client-Platform=iOS")
			transcode.append("X-Plex-Device-Name=DDiPhone")
			transcode.append("X-Plex-Model=5%2C2")
			transcode.append("X-Plex-Platform=iOS")
			transcode.append("X-Plex-Client-Identifier=%s" % self.g_sessionID)
			transcode.append("X-Plex-Product=Plex%2FiOS")
			transcode.append("X-Plex-Platform-Version=6.1.2")
			transcode.append("X-Plex-Version=3.1.3")
			timestamp = "@%d" % ts
			streamParams = "%s/%s?%s" % (streamPath, streamFile, "&".join(transcode))
			streamParams += self.get_uTokenForServer(server)
			pac = quote_plus(b64encode(hmac.new(b64decode(privateKey), '/' + streamParams + timestamp, digestmod=sha256).digest()).decode()).replace('+', '%20')
			streamURL += "http://%s/%s&X-Plex-Client-Capabilities=%s&X-Plex-Access-Key=%s&X-Plex-Access-Time=%d&X-Plex-Access-Code=%s" % (server, streamParams, self.g_capability, publicKey, ts, pac)
			printl("Encoded HTTP Stream URL: " + str(streamURL), self, "I")
		else:
			printl("Setting up HTTP Stream", self, "I")
			streamPath = "video/:/transcode/segmented"
			streamFile = 'start.m3u8'
			transcode.append("identifier=com.plexapp.plugins.library")
			transcode.append("ratingKey=%s" % myID)
			transcode.append("offset=0")
			transcode.append("quality=%d" % int(self.serverConfig_quality ))
			transcode.append("session=%s" % self.g_sessionID)
			transcode.append("secondsPerSegment=%d" % int(self.g_segments ))
			transcode.append("url=%s%s" % (quote_plus('http://127.0.0.1:32400/'), quote_plus(filename)))
			transcode.append("key=%s%s" % (quote_plus('http://127.0.0.1:32400/library/metadata/'), myID))
			transcode.append("3g=0")
			transcode.append("httpCookies=")
			transcode.append("userAgent=")
			timestamp = "@%d" % ts
			streamParams = "%s/%s?%s" % (streamPath, streamFile, "&".join(transcode))
			pac = quote_plus(b64encode(hmac.new(b64decode(privateKey), '/' + streamParams + timestamp, digestmod=sha256).digest()).decode()).replace('+', '%20')
			streamURL += "http://%s/%s&X-Plex-Client-Capabilities=%s&X-Plex-Access-Key=%s&X-Plex-Access-Time=%d&X-Plex-Access-Code=%s" % (server, streamParams, self.g_capability, publicKey, ts, pac)
			printl("Encoded HTTP Stream URL: " + str(streamURL), self, "I")

		req = Request(streamURL)
		#req.add_header('X-Plex-Client-Capabilities', self.g_capability)
		#printl ("Telling the server we can accept: " + str(self.g_capability), self, "I")
		resp = urlopen(req)
		if resp is None:
			raise IOError, "No response from Server"
		urls = []
		for line in resp:
			if line[0] != '#':
				urls.append("http://%s/%s/%s" % (server, streamPath, line[:-1]))
				printl( "Got: http://%s/%s/%s" % (str(server), str(streamPath), str(line[:-1])),self, "I")
		resp.close()

		indexURL = urls.pop()
		fullURL = indexURL

		#fullURL = streamURL

		printl("Transcoded media location URL " + fullURL, self, "I")

		printl("", self, "C")
		return fullURL

#===============================================================================
# HELPER
#===============================================================================

	#===============================================================================
	#
	#===============================================================================
	def getFullListEntry(self, entryData, url, viewState = None, isDirectory = False):
		printl("", self, "S")

		if not isDirectory:
			# build specific context menu entries
			contextMenu = self.buildContextMenu(url, entryData['ratingKey'], entryData['server'])
		else:
			# directories have no contextMenu
			contextMenu = None

		# build url for content
		nextUrl = 'http://%s%s'  % ( entryData['server'], entryData['key'])

		content = entryData.get('title','no Title').encode('utf-8'), entryData, contextMenu, viewState, nextUrl

		printl("", self, "C")
		return content

	#===========================================================================
	#
	#===========================================================================
	def getViewStateForShowEntry(self, entryData):
		printl("", self, "S")

		# lets add this for another filter
		if int(entryData["viewedLeafCount"]) == int(entryData["leafCount"]):
			viewState = "seen"

		elif int(entryData["viewedLeafCount"]) > 0:
			viewState = "started"

		else:
			viewState = "unseen"

		printl("", self, "C")
		return viewState

	#===============================================================================
	#
	#===============================================================================
	def getViewStatefromViewCount(self, entryData):
		printl("", self, "S")

		# because it could be that this tags are not existing we write them via get to set them to zero if they dont
		viewCount = int(entryData.get('viewCount', 0))
		viewOffset = int(entryData.get('viewOffset', 0))

		if viewCount > 0:
			viewState = "seen"

		elif viewCount >= 0 and viewOffset > 0:
			viewState = "started"

		else:
			viewState = "unseen"

		printl("", self, "C")
		return viewState

	#===============================================================================
	#
	#===============================================================================
	def getServerConfig(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.g_serverConfig