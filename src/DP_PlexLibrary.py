# -*- coding: utf-8 -*-
'''
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
'''
#===============================================================================
# IMPORT
#===============================================================================
import urllib
import re
import httplib
import socket
import sys
import os
import datetime 
import time
import base64 
import hashlib
import random
import hmac
import uuid
import string

#===============================================================================
# 
#===============================================================================
from time import time
from urllib import urlencode, quote_plus
from base64 import b64encode, b64decode
from Components.config import config
from hashlib import sha256
from urllib2 import urlopen, Request
from random import randint, seed
from threading import Thread
from Queue import Queue
from enigma import loadPNG

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox

from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, getXmlContent
from re import findall
#from DPH_bonjourFind import *

#===============================================================================
# import cProfile
#===============================================================================
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
		printl2("something went wrong during etree import" + str(e), self, "E")
					
#===============================================================================
# 
#===============================================================================
#The method seed() sets the integer starting value used in generating random numbers. Call this function before calling any other random module function.
seed()

#===============================================================================
# 
#===============================================================================
#DEBUG ON/OFF
DEBUG = "true"

#Get the setting from the appropriate file.
DEFAULT_PORT="32400"
MYPLEX_SERVER="my.plexapp.com"

_MODE_GETCONTENT=0
_MODE_TVSHOWS=1
_MODE_MOVIES=2
_MODE_ARTISTS=3
_MODE_getSeasonsOfShow=4
_MODE_PLAYLIBRARY=5
_MODE_TVEPISODES=6
_MODE_PLEXPLUGINS=7
_MODE_PROCESSXML=8
_MODE_BASICPLAY=12
_MODE_ALBUMS=14
_MODE_TRACKS=15
_MODE_PHOTOS=16
_MODE_MUSIC=17
_MODE_VIDEOPLUGINPLAY=18
_MODE_PLEXONLINE=19
_MODE_CHANNELINSTALL=20
_MODE_CHANNELVIEW=21
_MODE_DISPLAYSERVERS=22
_MODE_PLAYLIBRARY_TRANSCODE=23
_MODE_MYPLEXQUEUE=24

_OVERLAY_XBMC_UNWATCHED=6  #Blank
_OVERLAY_XBMC_WATCHED=7	#Tick
_OVERLAY_PLEX_UNWATCHED=4  #Dot
_OVERLAY_PLEX_WATCHED=0	#Blank
_OVERLAY_PLEX_PARTIAL=5	#half - Reusing XBMC overlaytrained

#===============================================================================
# PlexLibrary
#===============================================================================
class PlexLibrary(Screen):
	'''
	'''
	g_sessionID=None
	g_sections=[]
	g_name = "Plexserver"
	g_host = "192.168.45.190"
	g_port = "32400"
	g_currentServer = None
	g_connectionType = None
	g_showForeign = True
	g_address = None # is later the combination of g_host : g_port
	g_playbackType = None
	g_stream = "0" # 0 = linux local mount override, 1 = Selecting stream, 2 = smb/unc override 3 = transcode!?!?!
	g_secondary = "true" # show filter for media
	g_streamControl = "1" # 1 unknown, 2 = unknown, 3 = All subs disabled
	g_channelview = "false" # unknown
	g_flatten = "0" # 0 = show seasons, 1 = show all
	g_playtheme = "false"
	g_forcedvd = "false"
	g_skipcontext = "false" # best understanding when looking getMoviesfromsection
	g_skipmetadata = "false" # best understanding when looking getMoviesfromsection
	g_skipmediaflags = "false" # best understanding when looking getMoviesfromsection
	g_skipimages = "false"
	g_loc = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex" # homeverzeichnis
	g_myplex_username = ""
	g_myplex_password = ""
	g_myplex_token = ""
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
	g_quality = None #
	g_capability = ""
	g_audioOutput = "2" #0 = "mp3,aac", 1 = "mp3,aac,ac3", 2 ="mp3,aac,ac3,dts"
	g_session = None
	global g_serverConfig
	g_serverConfig = None
	g_error = False
	g_showUnSeenCounts = False
	
	##################
	# CHECKED
	##################
	g_serverDict=[]
	g_serverVersion=None
	g_myplex_accessTokenDict = {}
	
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
		doIt = False
		# global serverConfig
		self.g_serverConfig = serverConfig
				
		# global settings
		self.g_secondary = str(config.plugins.dreamplex.showFilter.value).lower()
		self.g_showUnSeenCounts = config.plugins.dreamplex.showUnSeenCounts.value
		self.g_sessionID = str(uuid.uuid4())
		
		# server settings
		self.g_name = str(serverConfig.name.value)
		self.g_connectionType = str(serverConfig.connectionType.value)
		self.g_port = str(serverConfig.port.value)
		self.g_quality = str(serverConfig.quality.value)
		self.g_myplex_token = str(serverConfig.myplexToken.value)
		self.g_playbackType = serverConfig.playbackType.value
		
		# PLAYBACK TYPES
		self.g_segments = serverConfig.segments.value # is needed here because of fallback
		
		if self.g_playbackType == "0": # STREAMED
			self.g_stream = "1"
			self.g_transcode = "false"
		
		elif self.g_playbackType == "1": # TRANSCODED
			self.g_stream = "1"
			self.g_transcode = "true"
			self.g_segments = serverConfig.segments.value
			
			printl("using transcode: " + str(self.g_transcode), self, "I")
			printl("using this transcoding quality: " +  str(self.g_quality), self, "I")
			printl("using this segments size: " +  str(self.g_segments), self, "I")
		
		elif self.g_playbackType == "2": # DIRECT LOCAL
			self.g_stream = "0"
			self.g_transcode = "false"
		
		elif self.g_playbackType == "3": # DIRECT REMOTE
			self.g_stream = "2"
			self.g_transcode = "false"
			self.g_nasoverride = "true"
			self.g_nasoverrideip = "%d.%d.%d.%d" % tuple(serverConfig.nasOverrideIp.value)
			self.g_nasuserid = str(serverConfig.smbUser.value)
			self.g_naspass = str(serverConfig.smbPassword.value)
			self.g_nasroot = str(serverConfig.nasRoot.value)

		printl("using this debugMode: " + str(config.plugins.dreamplex.debugMode.value), self, "D")
		printl("using this serverName: " +  self.g_name, self, "I") 
		printl("using this connectionType: " +  self.g_connectionType, self, "I")
		
		# CONNECTIONS TYPES
		if self.g_connectionType == "2": # MYPLEX
			self.g_myplex_username = serverConfig.myplexUsername.value
			self.g_myplex_password = serverConfig.myplexPassword.value
			self.g_myplex_url	  = serverConfig.myplexUrl.value
			
			if self.g_myplex_token == "" or serverConfig.renewMyplexToken.value == True:
				printl("serverconfig: " + str(serverConfig), self, "D")
				self.g_myplex_token = self.getNewMyPlexToken()
				
				if self.g_myplex_token is False:
					self.g_error = True
					
				else:
					serverConfig.myplexTokenUsername.value = self.g_myplex_username
					serverConfig.myplexTokenUsername.save()
					serverConfig.myplexToken.value = self.g_myplex_token
					serverConfig.myplexToken.save()
					
			else:
				self.g_myplex_token = serverConfig.myplexToken.value
			
			printl("myplexUrl: " +  str(self.g_myplex_url), self, "I")	
			printl("myplex_username: " +  str(self.g_myplex_username), self, "I", True, 10)
			printl("myplex_password: " +  str(self.g_myplex_password), self, "I", True, 6)
			printl("myplex_token: " +  str(self.g_myplex_token), self, "I", True, 6)
			
		elif self.g_connectionType == "0": # IP
			self.g_host = "%d.%d.%d.%d" % tuple(serverConfig.ip.value)
			
			printl("using this serverIp: " +  self.g_host, self, "I")
			printl("using this serverPort: " +  self.g_port, self, "I")
		else: # DNS
			try:
				self.g_host = str(socket.gethostbyname(serverConfig.dns.value))
				printl("using this FQDN: " +  serverConfig.dns.value, self, "I")
				printl("found this ip for fqdn: " + self.g_host, self, "I")
				printl("using this serverPort: " +  self.g_port, self, "I")
			except Exception, e:
				printl("socket error: " + str(e), self, "W")
				printl("trying fallback to ip", self, "I")
				self.g_host = "%d.%d.%d.%d" % tuple(serverConfig.ip.value) 
		
		if self.g_error is True:
			self.leaveOnError()
		else:
			#Fill serverdata to global g_serverDict
			self.prepareServerDict()
			
		self.g_serverVersion = self.getServerVersion()
		printl("PMS Version: " +  self.g_serverVersion, self, "I") 
			
		self.seenPic	= loadPNG("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/icons/seen-fs8.png")
		self.startedPic = loadPNG("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/icons/started-fs8.png")
		self.unseenPic  = loadPNG("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/icons/unseen-fs8.png")
								   
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def leaveOnError(self):
		printl("", self, "S")
		
		mainMenuList = []
		mainMenuList.append((_("Press exit to return"), ""))
		mainMenuList.append((_("If you are using myPlex"), ""))
		mainMenuList.append((_("please check if curl is installed."), ""))
		mainMenuList.append((_("You can use Systemcheck in the menu."), ""))
		
		printl("", self, "C")
		return mainMenuList
	
	#============================================================================
	# 
	#============================================================================
	def displaySections(self, filter=None ): # CHECKED
		printl("", self, "S")
		printl("filter: " + str(filter), self, "D")
		
		if self.g_error is True:
			mainMenuList = self.leaveOnError()
			return mainMenuList
		
		#===>
		mainMenuList = []
		self.g_sections = []
		#===>
		
		numOfServers=len(self.g_serverDict)
		printl( "Using list of "+str(numOfServers)+" servers: " +  str(self.g_serverDict), self, "I")
		self.getAllSections()
		
		for section in self.g_sections:
				
			details={'title' : section.get('title', 'Unknown') }
			
			if len(self.g_serverDict) > 1:
				details['title']=section.get('serverName')+": "+details['title']
			
			extraData={ 'fanart_image' : self.getFanart(section, section.get('address')) ,
						'type'		 : "Video" ,
						'thumb'		: self.getFanart(section, section.get('address'), False) ,
						'token'		: str(section['token']) }

			if self.g_connectionType == "2": # MYPLEX
				# we have to do this because via myPlex there could be diffrent servers with other tokens
				if str(section.get('address')) not in self.g_myplex_accessToken:
					printl("section address" + section.get('address'), self, "D")
					self.g_myplex_accessTokenDict[str(section.get('address'))] = str(section.get('token', None))
			
			#Determine what we are going to do process after a link is selected by the user, based on the content we find
			path = section['path']
			address =  section['address']
			
			if self.g_secondary == "true":
				printl( "_MODE_GETCONTENT detected", self, "D")
				mode=_MODE_GETCONTENT
			else:
				path=path+'/all'	
			
			params = {} 
			params['t_url'] = self.getSectionUrl(address, path)
			params['t_mode'] = str(section.get('type'))
			
			if self.g_secondary == "true":	  
				if section.get('type') == 'show':
					printl( "_MODE_TVSHOWS detected", self, "D")
					if (filter is not None) and (filter != "tvshow"):
						continue
					mainMenuList.append((_(section.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))
						
				elif section.get('type') == 'movie':
					
					printl( "_MODE_MOVIES detected", self, "D")
					if (filter is not None) and (filter != "movies"):
						continue
					mainMenuList.append((_(section.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))
	
				elif section.get('type') == 'artist':
					printl( "_MODE_ARTISTS detected", self, "D")
					if (filter is not None) and (filter != "music"):
						continue
					extend = False # SWITCH
					if extend == True:
						mainMenuList.append((_(section.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))
						
				elif section.get('type') == 'photo':
					printl( "_MODE_PHOTOS detected", self, "D")
					if (filter is not None) and (filter != "photos"):
						continue

				else:
					printl("Ignoring section "+details['title']+" of type " + section.get('type') + " as unable to process")
					continue
			
			else: # lets start here we configured no filters		  
				if section.get('type') == 'show':
					printl( "_MODE_TVSHOWS detected", self, "D")
					if (filter is not None) and (filter != "tvshow"):
						continue
					mainMenuList.append((_(section.get('title').encode('utf-8')), getPlugin("tvshows", Plugin.MENU_TVSHOWS), params))
						
				elif section.get('type') == 'movie':
					printl( "_MODE_MOVIES detected", self, "D")
					if (filter is not None) and (filter != "movies"):
						continue
					mainMenuList.append((_(section.get('title').encode('utf-8')), getPlugin("movies", Plugin.MENU_MOVIES), params))
	
				elif section.get('type') == 'artist':
					printl( "_MODE_ARTISTS detected", self, "D")
					if (filter is not None) and (filter != "music"):
						continue
					#mainMenuList.append((_(section.get('title').encode('utf-8')), getPlugin("music", Plugin.MENU_MUSIC), params))
					mainMenuList.append((_(section.get('title').encode('utf-8')), "getMusicSections", getPlugin("music", Plugin.MENU_MUSIC), params))
						
				elif section.get('type') == 'photo':
					printl( "_MODE_PHOTOS detected", self, "D")
					if (filter is not None) and (filter != "photos"):
						continue
				else:
					printl("Ignoring section "+details['title']+" of type " + section.get('type') + " as unable to process")
					continue
		
		if self.g_connectionType == "2": # MYPLEX
			self.setAccessTokenHeader()
		
		printl("mainMenuList: " + str(mainMenuList), self, "D")
		printl("", self, "C")
		return mainMenuList  

	#=============================================================================
	# 
	#=============================================================================
	def getAllSections(self): # CHECKED
		'''
			from self.g_serverDict, get a list of all the available sections
			and deduplicate the sections list
			@input: None
			@return: MainMenu for DP_MainMenu and alters the global value g_sectionList for other functions
		'''
		printl("", self, "S")
		  
		multiple = False
		multiple_list = []
		for server in self.g_serverDict:
																			
			if server['discovery'] == "local" or server['discovery'] == "bonjour":
				html = self.doRequest('http://'+server['address']+'/library/sections')
			elif server['discovery'] == "myplex":
				
				if self.g_myplex_token == "ERROR":
					self.session.open(MessageBox,_("MyPlex Token error:\nCheck Username and Password.\n%s") % (self.g_myplex_token), MessageBox.TYPE_INFO)
					continue
				else:
					html = self.getMyPlexURL('/pms/system/library/sections')
				
			if html is False or html is None:
				self.session.open(MessageBox,_("UNEXPECTED ERROR:\nThis is the answer from the request ...\n%s") % (html), MessageBox.TYPE_INFO)
				continue
					
			try:
				tree = etree.fromstring(html).getiterator("Directory")
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
			
			for sections in tree:
				
				#we need this until we do not support music and photos
				type = sections.get('type', 'unknown')
				if type == "movie" or type == "show" or type == "artist": #or type == "artist" or type == "photo"
					self.appendEntry(sections, server)
				else:
					printl("type: " + str(type), self, "D")
					printl("excluded unsupported section: " + str(sections.get('title','Unknown').encode('utf-8')),self, "I")
				
		if multiple == True:
			printl("there are other plex servers in the network => " + str(multiple_list), self, "I")
			
		'''
		If we have more than one server source, then
		we need to ensure uniqueness amonst the
		seperate sections.
		
		If we have only one server source, then the assumption
		is that Plex will deal with this for us
		'''
		if len(self.g_serverDict) > 1:	
			oneCount=0
			for onedevice in self.g_sections:
			
				twoCount=0
				for twodevice in self.g_sections:
	
					printl( "["+str(oneCount)+":"+str(twoCount)+"] Checking " + str(onedevice['title']) + " and " + str(twodevice['title']))
					printl( "and "+ onedevice['uuid'] + " is equal " + twodevice['uuid'])
	
					if oneCount == twoCount:
						printl( "skip" )
						twoCount+=1
						continue
						
					if ( str(onedevice['title']) == str(twodevice['title']) ) and ( onedevice['uuid'] == twodevice['uuid'] ):
						printl( "match")
						if onedevice['local'] == "1":
							printl ( "popping 2 " + str(self.g_sections.pop(twoCount)))
						else:
							printl ( "popping 1 " + str(self.g_sections.pop(oneCount)))
					else:
						printl( "no match")
					
					twoCount+=1

				oneCount+=1
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def appendEntry(self, sections, server):
		#printl("", self, "S")
		
		if self.g_connectionType != "2": # is not myPlex		
			self.g_sections.append({'title':sections.get('title','Unknown').encode('utf-8'), 
								   'address': self.g_host + ":" + self.g_port,
								   'serverName' : self.g_name.encode('utf-8'),
                                   'serverVersion' : sections.get('serverVersion','Unknown') ,
								   'uuid' : sections.get('machineIdentifier','Unknown') ,
								   'path' : '/library/sections/' + sections.get('key') ,
								   'token' : sections.get('accessToken',None) ,
								   'location' : server['discovery'] ,
								   'art' : sections.get('art') ,
								   #'local' : sections.get('local') ,
								   'type' : sections.get('type','Unknown') }) 
			
		else:
			self.g_sections.append({'title':sections.get('title','Unknown').encode('utf-8'), 
								   'address': sections.get('address') + ":" + sections.get('port'),
								   'serverName' : self.g_name.encode('utf-8'),
                                   'serverVersion' : sections.get('serverVersion','Unknown') ,
								   'uuid' : sections.get('machineIdentifier','Unknown') ,
								   'path' : sections.get('path') ,
								   'token' : sections.get('accessToken',None) ,
								   'location' : server['discovery'] ,
								   'art' : sections.get('art') ,
								   #'local' : sections.get('local') ,
								   'type' : sections.get('type','Unknown') }) 

		#printl("accessToken: " + str(sections.get('accessToken',None)), self, "D")
		#printl("", self, "C")

	#=============================================================================
	# 
	#=============================================================================
	def getSectionFilter(self, p_url, p_mode, p_final): # CHECKED
		printl("", self, "S")
		printl("p_url: " + str(p_url), self, "I")
		printl("p_mode: " + str(p_mode), self, "I")
		printl("p_final: " + str(p_final), self, "I")
		
		#===>
		mainMenuList = []
		#===>
		server=self.getServerFromURL(p_url)
		self.g_currentServer = server
		
		html = self.doRequest(p_url)  
				
		try:
			tree = etree.fromstring(html)
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)
		
		directories = tree.getiterator("Directory")
		viewGroup = str(tree.get("viewGroup"))
		
		printl("directories: " + str(directories), self, "D")
		printl("viewGroup: " + str(viewGroup),self, "D")

		viewGroupTypes = { "all":p_mode,
						 "unwatched":p_mode,
						 "newest":p_mode,
						 "recentlyAdded":p_mode,
						 "recentlyViewed":p_mode,
						 "onDeck":p_mode,
						 "folder":p_mode,
						 "recentlyViewedShows":p_mode,
						 "collection": "secondary",
						 "genre":"secondary",
						 "year":"secondary",
						 "decade":"secondary",
						 "director":"secondary",
						 "actor":"secondary",
						 "country":"secondary",
						 "contentRating":"secondary",
						 "rating":"secondary",
						 "resolution":"secondary",
						 "firstCharacter":"secondary"
					  }		

		for sections in directories:   
			
			isSearchFilter = False
			#sample = <Directory prompt="Search Movies - Teens" search="1" key="search?type=1" title="Search..." />
			prompt = str(sections.get('prompt', 'noSearch')) 
			
			if prompt != "noSearch": # prompt for search string
				isSearchFilter = True
				t_url = p_url
				t_mode = str(p_mode)
			
			elif p_final == True:
				printl("final", self, "D" )
				t_mode = p_mode
			
			else:
				t_mode = viewGroupTypes[sections.get('key')]
			
			t_url = p_url + "/" + str(sections.get('key'))
			
			printl("t_url: " + str(t_url), self, "D")
			printl("t_mode: " + str(t_mode),self, "D")
			printl("isSearchFilter: " + str(isSearchFilter), self, "D")  
			
			params = {}
			params["t_url"] = t_url
			params["t_mode"] = str(p_mode)
			params["isSearchFilter"] =isSearchFilter
			
			if t_mode != "secondary": #means that the next answer is again a filter cirteria
				
				if t_mode == 'show' or t_mode == 'episode':
					printl( "_MODE_TVSHOWS detected", self, "X")
					if str(sections.get('key')) == "onDeck" or str(sections.get('key')) == "recentlyViewed" or str(sections.get('key')) == "newest" or str(sections.get('key')) == "recentlyAdded":
						params["t_showEpisodesDirectly"] = True
					mainMenuList.append((_(sections.get('title').encode('utf-8')), getPlugin("tvshows", Plugin.MENU_TVSHOWS), params))
						
				elif t_mode == 'movie':
					printl( "_MODE_MOVIES detected", self, "X")
					mainMenuList.append((_(sections.get('title').encode('utf-8')), getPlugin("movies", Plugin.MENU_MOVIES), params))
	
				elif t_mode == 'artist':
					printl( "_MODE_ARTISTS detected", self, "X")
						
				elif t_mode == 'photo':
					printl( "_MODE_PHOTOS detected", self, "X")
				
				else:
					printl("Ignoring section " + str(sections.get('title').encode('utf-8')) + " of type " + str(sections.get('type')) + " as unable to process", self, "I")
					continue
			else:
				params["t_final"] = True
				mainMenuList.append((_(sections.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))

			t_url = None
		
		#printl("mainMenuList: " + str(mainMenuList), self, "D")
		printl("", self, "C")
		return mainMenuList  

	#===============================================================================
	# 
	#===============================================================================
	def addGUIItem(self, url, details, extraData, context, seenVisu, folder=True ):
		printl("", self, "S")
		if details.get('title','') == '':
			printl('leaving now because title is empty', self, "I")
			printl("", self, "C")
			return
			  
		if (extraData.get('token',None) is None) and self.g_myplex_accessToken:
			printl("no token found .. using g_myplex_accessToken", self, "D")
			extraData['token']=self.g_myplex_accessToken

		#aToken=self.getAuthDetails(extraData)
		#uToken = self.get_uTokenForServer()
		#aToken=self.getAuthDetails(extraData, prefix='?')
		#aToken = self.get_aTokenForServer()
		
		#Create the URL to pass to the item
		if ( not folder) and ( extraData['type'] =="Picture" ):
			newUrl = str(url) + self.get_aTokenForServer()
		else:
			newUrl= str(url) + self.get_uTokenForServer()

		printl("URL to use for listing: " + newUrl, self, "D")
	
		#xcontent = (newUrl, details, extraData, context)
		
		content = (details.get('title',''), details, extraData, context, seenVisu, newUrl)
		# todo hier sollte weider image rein
		
		#printl("content = " + str(content), self, "D")
		printl("", self, "C")
		return content
	
	
	#===============================================================================
	# 
	#===============================================================================
	def getSectionUrl(self, address, path):
		printl("", self, "S")

		sectionUrl = 'http://%s%s' % ( address, path)
		
		printl("sectionUrl = " + sectionUrl, self, "D")
		printl("", self, "C")
		return sectionUrl

	#====================================================================
	# 
	#====================================================================
	def getAuthDetails(self, details, url_format=True, prefix="&" ): # CHECKED
		'''
			Takes the token and creates the required arguments to allow
			authentication.  This is really just a formatting tools
			@input: token as dict, style of output [opt] and prefix style [opt]
			@return: header string or header dict
		'''
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

	#===================================================================
	# 
	#===================================================================
	def getMyPlexServers(self): # CHECKED
		'''
			Connect to the myplex service and get a list of all known
			servers.
			@input: nothing
			@return: a list of servers (as Dict)
		'''
		printl("", self, "S")
		
		
		tempServers=[]
		url_path="/pms/servers"
		
		html = self.getMyPlexURL(url_path)
		
		if html is False:
			printl("", self, "C")
			return
			
		try:
			server=etree.fromstring(html).findall('Server')
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)
		
		count=0
		for servers in server:
			data=dict(servers.items())
			
			if data.get('owned',None) == "1":
				if count == 0:
					master=1
					count=-1
				accessToken=self.getMyPlexToken()
			else:
				master='0'
				accessToken=data.get('accessToken',None)
			
			tempServers.append({'serverName': data['name'].encode('utf-8') ,
								'address'   : data['address']+":"+data['port'] ,
                                'version'   : data['version'] ,
								'discovery' : 'myplex' , 
								'token'	 : accessToken ,
								'uuid'	  : data['machineIdentifier'] ,
								'owned'	 : data.get('owned',0) ,  
								'master'	: master })

		
		#printl("tempServers = " + tempServers, self, "C") 
		printl("", self, "C")					   
		return tempServers						 
		
	#===========================================================================
	# 
	#===========================================================================
	def getLocalServers(self): # CHECKED
		'''
			Connect to the defined local server (either direct or via bonjour discovery)
			and get a list of all known servers.
			@input: nothing
			@return: a list of servers (as Dict)
		'''
		printl("", self, "S")
	
		tempServers=[]
		url_path="/servers"
		html=False
		
		for local in self.g_serverDict:
		
			if local.get('discovery') == "local" or local.get('discovery') == "bonjour":
				html = self.doRequest(local['address']+url_path)
				break
			
		if html is False:
			printl("", self, "C")
			return tempServers
		
		try:
			server=etree.fromstring(html).findall('Server')
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)
		
		count=0
		for servers in server:
			data=dict(servers.items())
			
			if count == 0:
				master=1
			else:
				master=0
			
			tempServers.append({'serverName': data['name'].encode('utf-8') ,
								'address'   : data['address']+":"+data['port'] ,
                                'version'   : data['version'] ,
								'discovery' : 'local' , 
								'token'	 : data.get('accessToken',None) ,
								'uuid'	  : data['machineIdentifier'] ,
								'owned'	 : '1' ,
								'master'	: master })
	
			count+=1 
			
		#printl("tempServers = " + str(tempServers), self, "C")
		printl("", self, "C")				   
		return tempServers						 

	#===============================================================================
	# 
	#===============================================================================
	def getMyPlexURL(self, url_path, renew=False, suppress=True ): # CHECKED
		'''
			Connect to the my.plexapp.com service and get an XML pages
			A seperate function is required as interfacing into myplex
			is slightly different than getting a standard URL
			@input: url to get, whether we need a new token, whether to display on screen err
			@return: an xml page as string or false
		'''
		printl("", self, "S")				
		printl("url = " + MYPLEX_SERVER + url_path, self, "D")
	
		printl( "Starting request", self, "D")
		curl_string = 'curl -s -k "%s"' % ("https://" + MYPLEX_SERVER + url_path + "?X-Plex-Token=" + str(self.g_myplex_token))
		
		printl("curl_string: " + str(curl_string), self, "D", True, 10)
		response = os.popen(curl_string).read()
		
		#printl("====== XML returned =======", self, "D")
		#printl("link = " + str(response), self, "D")
		#printl("====== XML finished ======", self, "D")
		
		
		printl("", self, "C")
		return response
		
	#=============================================================================
	# 
	#=============================================================================
	def getMyPlexToken(self, renew=False ): # CHECKED
		'''
			Get the myplex token.  If the user ID stored with the token
			does not match the current userid, then get new token.  This stops old token
			being used if plex ID is changed. If token is unavailable, then get a new one
			@input: whether to get new token
			@return: myplex token
		'''
		printl("", self, "S")
		
		try:
			#user,token = (__settings__.getSetting('self.g_myplex_token')).split('|')
			token = self.g_myplex_token
			#user = self.g_myplex_token.split('|')[1]
		except:
			token=""
			user=""
			
		if ( token == "" ) or (renew) or (user != self.g_myplex_username):
			token = self.getNewMyPlexToken()
		
		printl("Using token: " + str(token), self, "D", True, 8)
		printl("", self, "C")
		return token

	#============================================================================
	# 
	#============================================================================
	def getNewMyPlexToken(self): # CHECKED
		'''
			Get a new myplex token from myplex API
			@input: nothing
			@return: myplex token
		'''
		printl("", self, "S")
	
		printl("Getting new token", self, "I")
			
		if ( self.g_myplex_username or self.g_myplex_password ) == "":
			printl("Missing myplex details in config...", self, "I")
			
			printl("", self, "C")
			return False
		
		base64string = base64.encodestring('%s:%s' % (self.g_myplex_username, self.g_myplex_password)).replace('\n', '')
		txdata=""
		token = None
		
		myplex_header = []
		# todo add function to return version
		myplex_header.append('X-Plex-Platform: Enigma2')
		myplex_header.append('X-Plex-Platform-Version: oe2.0')
		myplex_header.append('X-Plex-Provides: player')
		myplex_header.append('X-Plex-Product: DreamPlex')
		myplex_header.append('X-Plex-Version: 0.9.2beta')  
		myplex_header.append('X-Plex-Device: DM500HD')
		myplex_header.append('X-Plex-Client-Identifier: 1234567890')
		myplex_header.append('Authorization: Basic ' + base64string)
		
		printl( "Starting auth request", self, "I")
		curl_string = 'curl -s -k -X POST "%s"' % ("https://" + MYPLEX_SERVER + "/users/sign_in.xml")
		
		for child in myplex_header:
			curl_string += ' -H "' + child + '"'
		
		printl("curl_string: " + str(curl_string), self, "D")
		response = os.popen(curl_string).read()

		try:
			token = etree.fromstring(response).findtext('authentication-token')
		except Exception, e:
			self._showErrorOnTv("no xml as response", response)
			 
		if token == None:
			self._showErrorOnTv("", response)
			
			printl("", self, "C")
			return False
		
			self.g_myplex_token = token
			self.g_serverConfig.myplexTokenUsername.value = self.g_myplex_username
			self.g_serverConfig.myplexTokenUsername.save()
			self.g_serverConfig.myplexToken.value = self.g_myplex_token
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
	def doRequest(self, url, type="GET", popup=0 ): # CHECKED
		printl("", self, "S")

		try:		
			if url[0:4] == "http":
				serversplit=2
				urlsplit=3
			else:
				serversplit=0
				urlsplit=1
				
			server=url.split('/')[serversplit]
			printl("server: " + str(server), self, "D")
			
			urlPath="/"+"/".join(url.split('/')[urlsplit:])
			printl("urlPath: " + str(urlPath), self, "D")

			self.urlPath = urlPath
			conn = httplib.HTTPConnection(server)

			authHeader = self.get_hTokenForServer()
			printl("header: " + str(authHeader), self, "D", True, 8)
			conn.request(type, urlPath, headers=authHeader)

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
	def getTimelineURL(self, server, container, id, state, time=0, duration=0):
		printl("", self, "S")
		try:

			urlPath="/:/timeline?containerKey=" + container + "&key=/library/metadata/" + id + "&ratingKey=" + id

			if state == "buffering":
				urlPath += "&state=buffering&time=" + str(time)        	
			elif state == "playing":
				urlPath += "&state=playing&time=" + str(time) + "&duration=" + str(duration)
			elif state == "stopped":
				urlPath += "&state=stopped&time=" + str(time) + "&duration=" + str(duration)
			elif state == "paused":
				urlPath += "&state=paused&time=" + str(time) + "&duration=" + str(duration)
			else:
				printl("No valid state supplied for getTimelineURL. State: " + str(state), self, "D")
				return

			#accessToken = self.getAuthDetails({'token':self.g_myplex_accessToken})
			urlPath += self.get_uTokenForServer()

			if self.g_sessionID is None:
				self.g_sessionID=str(uuid.uuid4())
			
			# TODO lets make this dynamic
			getHeader={'X-Plex-Platform': "Enigma2-DreamPlex",
					'X-Plex-Platform-Version': "oe2.0",
					'X-Plex-Provides': "player",
					'X-Plex-Product': "DreamPlex",
					'X-Plex-Version': "0.9.2",
					'X-Plex-Device': "Dreambox",
					'X-Plex-Client-Identifier': self.g_sessionID,
					'X-Plex-Device-Name': "Dreambox-DreamPlex"}

			conn = httplib.HTTPConnection(server)#,timeout=5)
			conn.request("GET", urlPath, headers=getHeader)
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

		try: conn.close()
		except: pass

		printl("", self, "C")
		return False

	#========================================================================
	# 
	#========================================================================
	def mediaType(self, partData, server, dvdplayback=False ): # CHECKED
		printl("", self, "S")   
		stream = partData['key']
		file = partData['file']
		self.fallback = False
		self.locations = ""
		
		#First determine what sort of 'file' file is
		printl("physical file location: " + str(file), self, "I")   
		try:
			if file[0:2] == "\\\\":
				printl("Looks like a UNC",self, "I")
				type="UNC"
			elif file[0:1] == "/" or file[0:1] == "\\":
				printl("looks like a unix file", self, "I")
				type="unixfile"
			elif file[1:3] == ":\\" or file[1:2] == ":/":
				printl("looks like a windows file", self, "I")
				type="winfile"
			else:
				printl("uknown file type", self, "I")
				printl("file = " + str(file),self, "I")
				type="notsure"
		except Exception:
				printl("uknown file type", self, "I")
				printl("file = " + str(file),self, "I")
				type="notsure"  
		
		self.currentFile = file
		self.currentType = type
		self.fallback = ""
		
		# 0 is linux local mount override
		if self.g_stream == "0":
			#check if the file can be found locally
			if type == "unixfile" or type == "winfile" or type == "UNC":
				
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
							if locationCheck != False:
								return locationCheck

				printl("Sorry I didn't find the file on the provided locations", self, "I")
			
			self.fallback = True
			printl("No local mount override possible ... switching to transcoded mode", self, "I")
			#===================================================================
			# global self.g_stream
			#===================================================================
			if dvdplayback:
				printl("Forcing SMB for DVD playback", self, "I")
				self.g_stream="2"
			else:
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
			if type=="UNC":
				filelocation=protocol+":"+file.replace("\\","/")
			else:
				#Might be OSX type, in which case, remove Volumes and replace with server
				server=server.split(':')[0]
				loginstring=""
	
				if self.g_nasoverride == "true":
					if not self.g_nasoverrideip == "":
						server=self.g_nasoverrideip
						printl("Overriding server with: " + server, self, "I")
						
					#===========================================================
					# nasuser = __settings__.getSetting('self.g_nasuserid')
					#===========================================================
					nasuser = self.g_nasuserid
					if not nasuser == "":
						#=======================================================
						# loginstring=__settings__.getSetting('self.g_nasuserid')+":"+__settings__.getSetting('naspass')+"@"
						#=======================================================
						loginstring = self.g_nasuserid +":"+ self.g_naspass + "@"
						printl("Adding AFP/SMB login info for user " + nasuser, self, "I")
					
					
				if file.find('Volumes') > 0:
					filelocation=protocol+":/"+file.replace("Volumes",loginstring+server)
				else:
					if type == "winfile":
						filelocation=protocol+"://"+loginstring+server+"/"+file[3:]
					else:
						#else assume its a file local to server available over smb/samba (now we have linux PMS).  Add server name to file path.
						filelocation=protocol+"://"+loginstring+server+file
						
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
		file = self.currentFile
		
		file = file.replace(remotePathPart, localPathPart)
		
		# now we change backslahes back to slahes
		if self.currentType == "winfile" or self.currentType == "UNC":
			file = file.replace("\\", "/")

		file = urllib.unquote(file)
		
		printl("altered file string: " + str(file), self, "I")
		try:
			exists = open(file, 'r')
			printl("Local file found, will use this", self, "I")
			exists.close()
			
			printl("", self, "C")
			return "file:"+file
		except:
			self.locations += str(file) + "\n"
			printl("", self, "C")
			return False
			
	#===========================================================================
	# 
	#===========================================================================
	def getMoviesFromSection(self, url, tree=None ): # CHECKED
		printl("", self, "S")
		printl("url: " + str(url), self, "D")
		
		fullList=[]
		self.tmpAbc = []
		self.tmpGenres = []
		server=self.getServerFromURL(url)
		self.g_currentServer = server		
		#get the server name from the URL, which was passed via the on screen listing..
		if tree is None:
			#Get some XML and parse it
			html=self.doRequest(url)
			
			if html is False:
				printl("", self, "C")
				return
	
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
	

		#Find all the video tags, as they contain the data we need to link to a file.
		movies=tree.findall('Video')
		
		for movie in movies:
			#Right, add that link...and loop around for another entry
			content = self.movieTag(url, server, tree, movie)
			fullList.append(content)

		printl("", self, "C")
		return fullList, self.tmpAbc , self.tmpGenres

	#=======================================================================
	# 
	#=======================================================================
	def getShowsFromSection(self, url, tree=None ): # CHECKED
		printl("", self, "S")
		
		fullList=[]
		self.tmpAbc = []
		self.tmpGenres = []
		
		server=self.getServerFromURL(url)
		self.g_currentServer = server
		
		#Get the URL and server name.  Get the XML and parse
		if tree is None:
			html=self.doRequest(url)
		
			if html is False:
				printl("", self, "C")
				return
			
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
	

		
		#For each directory tag we find
		ShowTags=tree.findall('Directory') 
		
		for show in ShowTags:
			tempgenre=[]
			tempcast=[]
			tempdir=[]
			tempwriter=[]
			
			#Lets grab all the info we can quickly through either a dictionary, or assignment to a list
			#We'll process it later
			for child in show:
				if child.tag == "Media":
					mediaarguments = dict(child.items())
				
				elif child.tag == "Genre" and self.g_skipmetadata == "false":
					genreTag = child.get('tag')
					tempgenre.append(genreTag)
					
					# fill genre filter
					if genreTag not in self.tmpGenres:
						self.tmpGenres.append(genreTag)
				
				elif child.tag == "Writer"  and self.g_skipmetadata == "false":
					tempwriter.append(child.get('tag'))
				
				elif child.tag == "Director"  and self.g_skipmetadata == "false":
					tempdir.append(child.get('tag'))
				
				elif child.tag == "Role"  and self.g_skipmetadata == "false":
					tempcast.append(child.get('tag'))

			details = {}
			details["viewMode"]				 = "ShowSeasons"
			details['ratingKey']				= str(show.get('ratingKey', 0)) # primary key in plex
			details['summary']				  = show.get('summary','')
			details['title']					= show.get('title','').encode('utf-8')
			details['episode']				  = int(show.get('leafCount',0))
			details['rating']				   = show.get('rating', 0)
			details['studio']				   = show.get('studio','')
			details['year']					 = show.get('year', 0)
			details['tagline']				  = show.get('tagline','')
			details['server']				   = str(server)
			details['genre']					= " / ".join(tempgenre)
			details['viewOffset']			   = show.get('viewOffset',0)
			details['director']				 = " / ".join(tempdir)
			details['originallyAvailableAt']	= show.get('originallyAvailableAt','')
			
			#Extended Metadata
			if self.g_skipmetadata == "false":
				details['cast']	 = tempcast
				details['writer']   = " / ".join(tempwriter)
			
			watched = int(show.get('viewedLeafCount',0))
			
			extraData = {}
			extraData['type']			   = "video"
			extraData['ratingKey']		  = str(show.get('ratingKey', 0)) # primary key in plex
			extraData['seenEpisodes']	   = watched
			extraData['unseenEpisodes']	 = details['episode'] - watched
			extraData['thumb']			  = self.getImage(show, server, x = 195, y = 268, type = "thumb")
			extraData['fanart_image']	   = self.getImage(show, server, x = 560, y = 315, type = "art")
			extraData['token']			  = self.g_myplex_accessToken
			extraData['theme']			  = show.get('theme', '')
			extraData['key']				= show.get('key','')
			
			# lets add this for another filter
			if int(extraData['seenEpisodes']) == int(details['episode']):
				details['viewState'] = "seen"
				seenVisu = self.seenPic
			
			elif int(extraData['seenEpisodes']) > 0:
				details['viewState']		= "started"
				seenVisu = self.startedPic
			
			else:
				details['viewState'] = "unseen"
				seenVisu = self.unseenPic
			
			if self.g_showUnSeenCounts == True:
				details['title'] = details['title'] + " ("+ str(details['episode']) + "/" + str(watched) + ")"
			
			if show.get('banner',None) is not None:
				extraData['banner']='http://'+server+show.get('banner').split('?')[0]+"/banner.jpg"
	
			#Add extra media flag data
			if self.g_skipmediaflags == "false":
				extraData['contentRating']	  = show.get('contentRating', '')
				
			# lets add this for another filter
			if int(extraData['unseenEpisodes']) == 0:
				details['viewState']		= "seen"
			else:
				details['viewState']		= "unseen"
		
			#Build any specific context menu entries
			if self.g_skipcontext == "false":
				context=self.buildContextMenu(url, extraData)
			else:
				context=None
			
			# fill genre filter
			if details['genre'] not in self.tmpGenres:
				self.tmpGenres.append(details['genre'])
			
			# fill title filter
			if details["title"].upper() not in self.tmpAbc:
				self.tmpAbc.append(details["title"].upper())
				
			#Create URL based on whether we are going to flatten the season view
			if self.g_flatten == "2":
				printl("Flattening all shows", self, "I")
				u='http://%s%s&mode=%s'  % ( server, extraData['key'].replace("children","allLeaves"), str(_MODE_TVEPISODES))
			else:
				u='http://%s%s&mode=%s'  % ( server, extraData['key'], str(_MODE_TVEPISODES))
				
			#Right, add that link...and loop around for another entry
			content = self.addGUIItem(u,details,extraData, context, seenVisu)

			fullList.append(content)
			
		printl("", self, "C")
		return fullList, self.tmpAbc , self.tmpGenres

	#===========================================================================
	# 
	#===========================================================================
	def getSeasonsOfShow(self, url ): # CHECKED
		printl("", self, "S")
		#Get URL, XML and parse
		server=self.getServerFromURL(url)
		html=self.doRequest(url)
		
		if html is False:
			printl("", self, "C")
			return

		try:
			tree = etree.fromstring(html)
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)
		
		willFlatten=False
		if self.g_flatten == "1":
			#check for a single season
			if int(tree.get('size',0)) == 1:
				printl("Flattening single season show", self, "I")
				willFlatten=True
		
		sectionart=self.getFanart(tree, server)
			  
		#For all the directory tags
		SeasonTags=tree.findall('Directory')
		
		fullList=[]
		
		for season in SeasonTags:
			#printl("season: " + str(season),self, "D")
	
			if willFlatten:
				url='http://'+server+season.get('key')
				self.getEpisodesOfSeason(url)
				return
			
			watched=int(season.get('viewedLeafCount',0))
		
			details = {}
			details["viewMode"]				 = "ShowEpisodes"
			details['ratingKey']				= str(season.get('ratingKey', 0)) # primary key in plex
			details['summary']				  = season.get('summary','')
			details['season']				   = season.get('index','0')
			details['title']					= season.get('title','').encode('utf-8')
			details['episode']				  = int(season.get('leafCount',0))
			details['rating']				   = season.get('rating', 0)
			details['studio']				   = season.get('studio','')
			details['year']					 = season.get('year', 0)
			details['tagline']				  = season.get('tagline','')
			details['server']				   = str(server)
			details['viewOffset']			   = season.get('viewOffset',0)
			details['originallyAvailableAt']	= season.get('originallyAvailableAt','')
			
			extraData = {}
			extraData['type']			   = "video"
			extraData['ratingKey']		  = str(season.get('ratingKey', 0)) # primary key in plex
			extraData['seenEpisodes']	   = watched
			extraData['unseenEpisodes']	 = details['episode'] - watched
			extraData['thumb']			  = self.getThumb(season, server)
			extraData['fanart_image']	   = self.getFanart(season, server)
			#extraData['thumb']			  = self.getImage(season, server, x = 195, y = 268, type = "thumb")
			#extraData['fanart_image']	   = self.getImage(season, server, x = 560, y = 315, type = "art")
			extraData['token']			  = self.g_myplex_accessToken
			extraData['theme']			  = season.get('theme', '')
			extraData['key']				= season.get('key','')
			 
			# lets add this for another filter
			if int(extraData['seenEpisodes']) == int(details['episode']):
				details['viewState'] = "seen"
				seenVisu = self.seenPic
			
			elif int(extraData['seenEpisodes']) > 0:
				details['viewState']		= "started"
				seenVisu = self.startedPic
			
			else:
				details['viewState'] = "unseen"
				seenVisu = self.unseenPic
						 
			if extraData['fanart_image'] == "":
				extraData['fanart_image'] = sectionart
	
			url='http://%s%s&mode=%s' % ( server , extraData['key'], str(_MODE_TVEPISODES) )
	
			if self.g_skipcontext == "false":
				context=self.buildContextMenu(url, season)
			else:
				context=None
				
			content = self.addGUIItem(url, details, extraData, context, seenVisu)

			fullList.append(content)

		printl("", self, "C")
		return fullList
	
	#===============================================================================
	# 
	#===============================================================================
	def getUniqueId (self, path):
		printl("", self, "S")
		
		parts = string.split(path, "/")
		id = parts[3]
		
		printl("", self, "C")
		return id
	
	#===============================================================================
	# 
	#===============================================================================
	def getEpisodesOfSeason(self, url, tree=None ): # CHECKED	
		printl("", self, "S")
					
		if tree is None:
			#Get URL, XML and Parse
			html=self.doRequest(url)
			
			if html is False:
				printl("", self, "C")
				return
			
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		ShowTags=tree.findall('Video')
		server=self.getServerFromURL(url)
		
		if self.g_skipimages == "false":		
			sectionart=self.getThumb(tree, server)
		
		fullList=[]
		 
		for episode in ShowTags:
			tempgenre=[]
			tempcast=[]
			tempdir=[]
			tempwriter=[]
			
			#Lets grab all the info we can quickly through either a dictionary, or assignment to a list
			#We'll process it later
			for child in episode:
				if child.tag == "Media":
					mediaarguments = dict(child.items())
				elif child.tag == "Genre" and self.g_skipmetadata == "false":
					genreTag = child.get('tag')
					tempgenre.append(genreTag)
				elif child.tag == "Writer"  and self.g_skipmetadata == "false":
					tempwriter.append(child.get('tag'))
				elif child.tag == "Director"  and self.g_skipmetadata == "false":
					tempdir.append(child.get('tag'))
				elif child.tag == "Role"  and self.g_skipmetadata == "false":
					tempcast.append(child.get('tag'))
	
			#Gather some data
			duration = int(mediaarguments.get('duration',episode.get('duration',0)))/1000
					 
			#Required listItem entries for XBMC
			details = {}
			details["viewMode"]			 = "play"
			details['ratingKey']			= str(episode.get('ratingKey', 0)) # primary key in plex
			details['title']				= episode.get('title','Unknown').encode('utf-8')
			details['summary']			  = episode.get('summary','')
			details['episode']			  = int(episode.get('index',0))
			details['title']				= str(details['episode']).zfill(2) + ". " + details['title']
			details['tvshowtitle']		  = episode.get('grandparentTitle',tree.get('grandparentTitle','')).encode('utf-8')
			details['season']			   = episode.get('parentIndex',tree.get('parentIndex',0))
			details['viewCount']			= episode.get('viewCount', 0)
			details['rating']			   = episode.get('rating', 0)
			details['studio']			   = episode.get('studio','')
			details['year']				 = episode.get('year', 0)
			details['tagline']			  = episode.get('tagline','')
			details['runtime']			  = str(datetime.timedelta(seconds=duration))
			details['server']			   = str(server)
			details['genre']				= " / ".join(tempgenre)
			details['viewOffset']		   = episode.get('viewOffset',0)
			details['director']			 = " / ".join(tempdir)
			
			if tree.get('mixedParents',0) == 1:
				details['title'] = details['tvshowtitle'] + ": " + details['title']
			
			# lets add this for another filter
			if details['viewCount'] > 0:
				details['viewState'] = "seen"
				seenVisu = self.seenPic
			
			elif details['viewCount'] > 0 and details['viewOffset'] > 0:
				details['viewState']		= "started"
				seenVisu = self.startedPic
			
			else:
				details['viewState'] = "unseen"
				seenVisu = self.unseenPic
			
			#Extended Metadata
			if self.g_skipmetadata == "false":
				details['cast']	 = tempcast
				details['writer']   = " / ".join(tempwriter)
			
			extraData = {}
			extraData['type']			   = "Video"
			extraData['ratingKey']		  = str(episode.get('ratingKey', 0)) # primary key in plex
			extraData['thumb']			  = self.getImage(episode, server, x = 195, y = 268, type = "grandparentThumb")
			extraData['fanart_image']	   = self.getImage(episode, server, x = 560, y = 315, type = "thumb") #because this is a episode we have to use thumb
			extraData['token']			  = self.g_myplex_accessToken
			extraData['key']				= episode.get('key','')
	
			#Add extra media flag data
			if self.g_skipmediaflags == "false":
				extraData['contentRating']   = episode.get('contentRating', '')
				extraData['videoResolution'] = mediaarguments.get('videoResolution', '')
				extraData['videoCodec']	  = mediaarguments.get('videoCodec', '')
				extraData['audioCodec']	  = mediaarguments.get('audioCodec', '')
				extraData['aspectRatio']	 = mediaarguments.get('aspectRatio', '')
				extraData['audioCodec']	  = mediaarguments.get('audioCodec', '')
		
			#Build any specific context menu entries
			if self.g_skipcontext == "false":
				context=self.buildContextMenu(url, extraData)
			else:
				context=None
			
			content = self.addGUIItem(url, details, extraData, context, seenVisu)

			fullList.append(content)
		
		#printl ("fullList = " + fullList, self, "D")
		printl("", self, "C")
		return fullList
	
	#===========================================================================
	# 
	#===========================================================================
	def getStreamDataById(self, server, id):
		printl("", self, "S")

		printl("Gather media stream info", self, "I" ) 
		
		#get metadata for audio and subtitle
		suburl="http://"+server+"/library/metadata/"+id
				
		html=self.doRequest(suburl)
		#printl("retrived html: " + str(html), self, "D")
		
		try:
			tree = etree.fromstring(html)
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)
		
		printl("", self, "C")
		return tree
	
	#===========================================================================
	# 
	#===========================================================================
	def getSelectedSubtitleDataById(self, server, id):
		printl("",self, "S")
		printl("server +  id: " + str(server) + " / " + str(id), self, "D")
		
		tree = self.getStreamDataById(server, id)
		
		fromParts = tree.getiterator('Part')	
		
		#Get the Parts info for media type and source selection 
		for part in fromParts:
			try:
				partitem=part.get('id'), part.get('file')
				
			except: pass
			
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
	def getSubtitlesById(self, server, id):
		'''
		sample: 
		<Stream id="25819" streamType="3" selected="1" default="1" index="4" language="Deutsch" languageCode="ger" format="srt"/>
		<Stream id="25820" streamType="3" index="5" language="English" languageCode="eng" format="srt"/>
		'''
		printl("", self, "S")
		
		subtitlesList = []
		
		tree = self.getStreamDataById(server, id)
		
		fromParts = tree.getiterator('Part')	
		
		#Get the Parts info for media type and source selection 
		for part in fromParts:
			try:
				partitem=part.get('id'), part.get('file')
				
			except: pass
			
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
	def setSubtitleById(self, server, sub_id, languageCode, part_id):
		printl("", self, "S")
		
		url = "http://"+str(server)+"/library/parts/"+str(part_id)+"?subtitleStreamID="+ str(sub_id)
		
		html = self.doRequest(url, type="PUT")
		
		printl("", self, "C")
		
		
	#===========================================================================
	# 
	#===========================================================================
	def getAudioSubtitlesMedia(self, server, id ): # CHECKED
		'''
		Cycle through the Parts sections to find all "selected" audio and subtitle streams
		If a stream is marked as selected=1 then we will record it in the dict
		Any that are not, are ignored as we do not need to set them
		We also record the media locations for playback decision later on
		'''
		printl("", self, "S")
		
		tree = self.getStreamDataById(server, id)
			
		parts=[]
		partsCount=0
		subtitle={}
		subCount=0
		audio={}
		audioCount=0
		external={}
		media={}
		videoData={}
		mediaData={}
		subOffset=-1
		audioOffset=-1
		selectedSubOffset=-1
		selectedAudioOffset=-1
		
		fromVideo = tree.find('Video')
	
		videoData['title'] = fromVideo.get('title', "")
		videoData['tagline'] = fromVideo.get('tagline', "")
		videoData['summary'] = fromVideo.get('summary', "")
		videoData['year'] = fromVideo.get('year', "")
		videoData['studio'] = fromVideo.get('studio', "")
		videoData['viewOffset']=fromVideo.get('viewOffset',0)
		videoData['duration']=fromVideo.get('duration',0)
		videoData['contentRating'] = fromVideo.get('contentRating', "")
		
		
		fromMedia = tree.find('Media')
		
		mediaData['audioCodec'] = fromVideo.get('audioCodec', "")
		mediaData['videoCodec'] = fromVideo.get('videoCodec', "")
		mediaData['videoResolution'] = fromVideo.get('videoResolution', "")
		mediaData['videoFrameRate'] = fromVideo.get('videoFrameRate', "")
		
		fromParts = tree.getiterator('Part')	
		
		contents="type"
		
		#Get the Parts info for media type and source selection 
		for part in fromParts:
			try:
				bits=part.get('key'), part.get('file')
				parts.append(bits)
				partsCount += 1
			except: pass
			
		if self.g_streamControl == "1" or self.g_streamControl == "2":
	
			contents="all"
			tags=tree.getiterator('Stream')

			#streamType: The type of media stream/track it is (1 = video, 2 = audio, 3 = subtitle) 
			
			for bits in tags:
				stream=dict(bits.items())
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
	def getMediaOptionsToPlay(self, id, vids, override=False ): # CHECKED
		printl("", self, "S")
		
		self.getTranscodeSettings(override)
		self.server = self.getServerFromURL(vids)
		self.streams=self.getAudioSubtitlesMedia(self.server,id) 
		
		printl("partsCount: " + str(self.streams['partsCount']), self, "D")
		printl("parts: " + str(self.streams['parts']), self, "D")
		printl("server: " + str(self.streams), self, "D")	
		
		printl("", self, "C")
		return self.streams['partsCount'], self.streams['parts'], self.server
	
	#========================================================================
	# 
	#========================================================================
	def playLibraryMedia(self, id, url): # CHECKED
		printl("", self, "S")
		 
		printl("url: " + str(url), self, "I")

		if url is None:
			return
			
		protocol=url.split(':',1)[0]
		
		# set standard playurl
		playurl=url
		
		token = self.get_aTokenForServer()

		#alter playurl if needed
		if protocol == "file":
			printl( "We are playing a local file", self, "I")
			playurl=url.split(':',1)[1]
		
		elif protocol == "http":
			printl( "We are playing a stream", self, "I")
			if self.g_transcode == "true":
				printl( "We will be transcoding the stream", self, "I")
				playurl = self.transcode(id,url+token)
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

		self.monitorPlayback(id,self.server)

		serverMultiUser = False
		if self.getServerVersion() >= "0.9.8.0":
			serverMultiUser = True
		
		printl("Server is MultiUser version: " + str(serverMultiUser),self,"I")
		
		#TODO return playurl
		#=======================================================================
		# printl("TEST URL: " + test, False)
		#=======================================================================
		printl("PLAYURL => " + playurl, self, "I")
		printl("RESUME => " + str(resume), self, "I")
		printl("", self, "C")
		
		playerData = {}
		playerData["playUrl"] = playurl
		playerData["resumeStamp"] = resume
		playerData["server"] = self.server
		playerData["id"] = id
		playerData["servermultiuser"] = serverMultiUser
		playerData["playbackType"] =self.g_playbackType
		playerData["transcodingSession"] = self.g_sessionID
		playerData["videoData"] = self.streams['videoData']
		playerData["mediaData"] = self.streams['mediaData']
		playerData["fallback"] = self.fallback
		playerData["locations"] = self.locations
		playerData["currentFile"] = self.currentFile
		
		return playerData
	
	#===========================================================================
	# 
	#===========================================================================
	def setAccessTokenHeader(self):
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
			
		printl("g_myplex_accessTokenDict: " + str(self.g_myplex_accessTokenDict), self, "D")

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def get_hTokenForServer(self):
		printl("", self, "S")
		printl("self.g_myplex_accessTokenDict: " + str(self.g_myplex_accessTokenDict), self, "D")
		printl("self.g_currentServer: " + str(self.g_currentServer), self, "D")
		printl("", self, "C")
		return self.g_myplex_accessTokenDict[self.g_currentServer]["hToken"]

	#===========================================================================
	# 
	#===========================================================================
	def get_aTokenForServer(self):
		printl("", self, "S")
		printl("self.g_myplex_accessTokenDict: " + str(self.g_myplex_accessTokenDict), self, "D")
		printl("", self, "C")   
		return self.g_myplex_accessTokenDict[self.g_currentServer]["aToken"]

	#===========================================================================
	# 
	#===========================================================================
	def get_uTokenForServer(self):
		printl("", self, "S")
		printl("self.g_myplex_accessTokenDict: " + str(self.g_myplex_accessTokenDict), self, "D")
		printl("", self, "C")   
		return self.g_myplex_accessTokenDict[self.g_currentServer]["uToken"]
	
	#===========================================================================
	# 
	#===========================================================================
	def setAudioSubtitles(self, stream ): # CHECKED
		printl("", self, "S")
			
		if stream['contents'] == "type":
			printl ("No streams to process.", self, "I")
			
			if self.g_streamControl == "3":
				#===============================================================
				# xbmc.Player().showSubtitles(False)	
				#===============================================================
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
						#=======================================================
						# xbmc.Player().setAudioStream(stream['audioOffset'])
						#=======================================================
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
					#===========================================================
					# xbmc.Player().showSubtitles(False)
					# xbmc.Player().setSubtitleStream(stream['subOffset'])
					#===========================================================
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
							#===================================================
							# xbmc.Player().setSubtitles(external['key'])
							#===================================================
							printl("", self, "C")   
							return True
					except: pass					
				else:
					printl ("No external subtitles available. Will turn off subs", self, "I")
			except:
				printl ("No External subs to set", self, "I")
				
		#=======================================================================
		# xbmc.Player().showSubtitles(False)	
		#=======================================================================
		printl("", self, "C")   
		return False

	#=================================================================
	# 
	#=================================================================
	def remove_html_tags(self, data): # CHECKED
		printl("", self, "S")
		
		p = re.compile(r'<.*?>')
		
		printl("", self, "C")   
		return p.sub('', data)

	#===============================================================================
	# 
	#===============================================================================
	def monitorPlayback(self, id, server ): # CHECKED
		printl("", self, "S")
		#TODO?: code goes here
		printl("", self, "C")	   
		return
	#============================================================================
	# 
	#============================================================================
	def PLAY(self, url ): # CHECKED
		printl("", self, "S")
			  
		if url[0:4] == "file":
			printl( "We are playing a local file")
			#Split out the path from the URL
			playurl=url.split(':',1)[1]
		elif url[0:4] == "http":
			printl( "We are playing a stream", self, "I")
			if '?' in url:
				playurl=url+ self.get_uTokenForServer() #self.getAuthDetails({'token':self.g_myplex_accessToken})
			else:
				playurl=url+self.get_aTokenForServer() #self.getAuthDetails({'token':self.g_myplex_accessToken},prefix="?")
		else:
			playurl=url


		printl("", self, "C")   
		return playurl
	
	#===============================================================================
	# 
	#===============================================================================
	def videoPluginPlay(self, vids, prefix=None ): # CHECKED
		'''
			Plays Plugin Videos, which do not require library feedback 
			but require further processing
			@input: url of video, plugin identifier
			@return: nothing. End of Script
		'''
		printl("", self, "S")
			   
		server=self.getServerFromURL(vids)
		
		#If we find the url lookup service, then we probably have a standard plugin, but possibly with resolution choices
		if '/services/url/lookup' in vids:
			printl("URL Lookup service", self, "I")
			html=self.doRequest(vids, suppress=False)
			if not html:
				printl("", self, "C")   
				return
			
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
			
			mediaCount=0
			mediaDetails=[]
			for media in tree.getiterator('Media'):
				mediaCount+=1
				tempDict={'videoResolution' : media.get('videoResolution',"Unknown")}
				
				for child in media:
					tempDict['key']=child.get('key','')
				
				tempDict['identifier']=tree.get('identifier','')
				mediaDetails.append(tempDict)
						
			printl( str(mediaDetails), self, "I" )			
						
			#If we have options, create a dialog menu
			result=0
			if mediaCount > 1:
				printl ("Select from plugin video sources", self, "I")
				dialogOptions=[x['videoResolution'] for x in mediaDetails ]
				
				#===============================================================
				# result = videoResolution.select('Select resolution..',dialogOptions)
				#===============================================================
				
				if result == -1:
					printl("", self, "C")   
					return
	
			self.videoPluginPlay(self.getLinkURL('',mediaDetails[result],server))
			printl("", self, "C")   
			return  
			
		#Check if there is a further level of XML required
		if '&indirect=1' in vids:
			printl("Indirect link", self, "I")
			html=self.doRequest(vids, suppress=False)
			if not html:
				printl("", self, "C")   
				return
			
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
			
			for bits in tree.getiterator('Part'):
				self.videoPluginPlay(self.getLinkURL(vids,bits,server))
				break
			
			printl("", self, "C")	   
			return
		
		#if we have a plex URL, then this is a transcoding URL
		if 'plex://' in vids:
			printl("found webkit video, pass to self.transcoder", self, "I")
			self.getTranscodeSettings(True)
			if not (prefix):
				prefix="system"
			vids=self.transcode(0, vids, prefix)
			session=vids
		
		#Everything else should be this
		#else:
		#	printl("Direct link")
		#	output=self.doRequest(vids, type="HEAD", suppress=False)
		#	if not output:
		#		return
		#		
		#	printl(str(output))
		#	if ( output[0:4] == "http" ) or ( output[0:4] == "plex" ):
		#		printl("Redirect.  Getting new URL")
		#		vids=output
		#		printl("New URL is: "+ vids)
		#		parameters=self.get_params(vids)
		#		
		#		prefix=parameters.get("prefix",'')
		#		extraData={'key'		: vids ,
		#				   'identifier' : prefix }
		#
		#		vids=self.getLinkURL(vids, extraData ,server)  
		
		printl("URL to Play: " + vids, self, "I")
		printl("Prefix is: " + str(prefix), self, "I")
			
		#If this is an Apple movie trailer, add User Agent to allow access
		if 'trailers.apple.com' in vids:
			url=vids+"|User-Agent=QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)"
		elif server in vids:
			url=vids+self.get_uTokenForServer() #self.getAuthDetails({'token': self.g_myplex_accessToken})
		else:
			url=vids

		printl("Final URL is : " + url, self, "I")
		
	
		if 'self.transcode' in url:
			try:
				self.pluginTranscodeMonitor(self.g_sessionID,server)
			except: 
				printl("Unable to start self.transcode monitor", self, "I")
		else:
			printl("Not starting monitor", self, "I")
			
		printl("", self, "C")   
		return
	
	#===============================================================================
	# 
	#===============================================================================
	def pluginTranscodeMonitor(self, sessionID, server ): # CHECKED
		printl("", self, "S")
	
		#TODO?: Code goes here

		printl("", self, "C")   
		return

	#===============================================================================
	# 
	#===============================================================================
	def get_params(self, paramstring ): # CHECKED
		printl("", self, "S")
		
		printl("Parameter string: " + paramstring, self, "I")
		param={}
		if len(paramstring)>=2:
				params=paramstring
				
				if params[0] == "?":
					cleanedparams=params[1:] 
				else:
					cleanedparams=params
					
				if (params[len(params)-1]=='/'):
						params=params[0:len(params)-2]
				
				pairsofparams=cleanedparams.split('&')
				for i in range(len(pairsofparams)):
						splitparams={}
						splitparams=pairsofparams[i].split('=')
						if (len(splitparams))==2:
								param[splitparams[0]]=splitparams[1]
						elif (len(splitparams))==3:
								param[splitparams[0]]=splitparams[1]+"="+splitparams[2]
		printl("Returning: " + str(param), self, "I")						
		printl("", self, "C")   
		return param

	#============================================================================
	# 
	#============================================================================
	def getContent(self, url ):  # CHECKED
		'''
			This function takes teh URL, gets the XML and determines what the content is
			This XML is then redirected to the best processing function.
			If a search term is detected, then show keyboard and run search query
			@input: URL of XML page
			@return: nothing, redirects to another function
		'''
		printl("", self, "S")
			
		server = self.getServerFromURL(url)
		lastbit=url.split('/')[-1]
		printl("URL suffix: " + str(lastbit), self, "I")
		
		 
		html=self.doRequest(url, suppress=False, popup=1 )
		
		if html is False:
			printl("", self, "C")   
			return
			
		try:
			tree = etree.fromstring(html)
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)

		if lastbit == "folder":
			self.processXML(url,tree)
			return

		view_group=tree.get('viewGroup',None)
	
		if view_group == "movie":
			printl( "This is movie XML, passing to self.Movies", self, "I")

			self.getMoviesFromSection(url, tree)
		elif view_group == "show":
			printl( "This is tv show XML", self, "I")
			self.getShowsFromSection(url,tree)
		elif view_group == "episode":
			printl("This is TV episode XML", self, "I")
			self.getEpisodesOfSeason(url,tree)
		elif view_group == 'artist':
			printl( "This is music XML", self, "I")
			self.artist(url, tree)
		elif view_group== 'album' or view_group == 'albums':
			self.albums(url,tree)
		elif view_group == "track":
			printl("This is track XML", self, "I")
			self.tracks(url, tree)
		elif view_group =="photo":
			printl("This is a photo XML", self, "I")
			self.photo(url,tree)
		else:
			self.processDirectory(url,tree)
		
		printl("", self, "C")	   
		return

	#===========================================================================
	# 
	#===========================================================================
	def processDirectory(self, url, tree=None ): # CHECKED
		printl("", self, "S")
		printl("Processing secondary menus", self, "I")

		server=self.getServerFromURL(url)
		
		for directory in tree:
			details={'title' : directory.get('title','Unknown').encode('utf-8') }
			extraData={'thumb'		: self.getThumb(directory, server) ,
					   'fanart_image' : self.getFanart(tree, server, False) } 
			
			if extraData['thumb'] == '':
				extraData['thumb']=extraData['fanart_image']
			
			u='%s&mode=%s' % ( self.getLinkURL(url,directory,server), _MODE_GETCONTENT )
	
			self.addGUIItem(u,details,extraData)
			
		printl("", self, "C")   
		
	#===============================================================================
	# 
	#===============================================================================
	def getMasterServer(self):
		printl("", self, "S")
		
		self.prepareServerDict()
		possibleServers=[]
		for serverData in self.resolveAllServers():
			printl("serverData: " + str(serverData), self, "D")
			if serverData['master'] == 1:
				possibleServers.append({'address' : serverData['address'] ,
										'discovery' : serverData['discovery'] })
		printl("possibleServers:"  + str(possibleServers),self, "D")
		if len(possibleServers) > 1:
			preferred="local"
			for serverData in possibleServers:
				if preferred == "any":
					return serverData['address']
				else:
					if serverData['discovery'] == preferred:
						return serverData['address']
		
		printl("", self, "C")				   
		return possibleServers[0]['address']				

	#===========================================================================
	# 
	#===========================================================================
	def transcode(self, id, url, identifier=None ): # CHECKED
		printl("", self, "S")

		server=self.getServerFromURL(url)
		
		#Check for myplex user, which we need to alter to a master server
		if 'plexapp.com' in url:
			server=self.getMasterServer()
		
		printl("Using preferred transcoding server: " + server, self, "I")
			
		#filename=urllib.quote_plus("/"+"/".join(url.split('/')[3:]))
		filename= '/'.join(url.split('/')[3:])

		#These are the DEV API keys - may need to change them on release
		publicKey="KQMIY6GATPC63AIMC4R2" #self.pKey
		privateKey = "k3U6GLkZOoNIoSgjDshPErvqMIFdE0xMTx8kgsrhnC0="  #pac
		#privateKey = base64.decodestring("k3U6GLkZOoNIoSgjDshPErvqMIFdE0xMTx8kgsrhnC0=")   #pac
			
		streamURL = ""
		transcode = []
		universalTranscoder = False
		if universalTranscoder == False:
			ts = int(time())
			printl("Setting up HTTP Stream", self, "I")
			streamPath = "video/:/transcode/segmented"
			streamFile = 'start.m3u8'
			transcode.append("identifier=com.plexapp.plugins.library")
			transcode.append("ratingKey=%s" % id)
			transcode.append("offset=0")
			transcode.append("quality=%d" % int(self.g_quality ))
			transcode.append("session=%s" % self.g_sessionID)
			transcode.append("secondsPerSegment=%d" % int(self.g_segments ))
			transcode.append("url=%s%s" % (quote_plus('http://127.0.0.1:32400/'), quote_plus(filename)))
			transcode.append("key=%s%s" % (quote_plus('http://127.0.0.1:32400/library/metadata/'), id))
			transcode.append("3g=0")
			transcode.append("httpCookies=")
			transcode.append("userAgent=")
			timestamp = "@%d" % ts
			streamParams = "%s/%s?%s" % (streamPath, streamFile, "&".join(transcode))
			pac = quote_plus(b64encode(hmac.new(b64decode(privateKey), '/' + streamParams + timestamp, digestmod=sha256).digest()).decode()).replace('+', '%20')
			streamURL += "http://%s/%s&X-Plex-Client-Capabilities=%s&X-Plex-Access-Key=%s&X-Plex-Access-Time=%d&X-Plex-Access-Code=%s" % (server, streamParams, self.g_capability, publicKey, ts, pac)
			printl("Encoded HTTP Stream URL: " + str(streamURL), self, "I")
		else:
			ts = int(time())
			printl("Setting up HTTP Stream with universal transcoder", self, "I")
			streamPath = "video/:/transcode/universal"
			streamFile = 'start.m3u8'
			#transcode.append("path=%s%s" % (quote_plus('http://localhost:32400/'), quote_plus(filename)))
			#transcode.append("path=http%3A%2F%2F127.0.0.1%3A32400%2Flibrary%2Fmetadata%2F10635")
			transcode.append("path=%s%s" % (quote_plus('http://127.0.0.1:32400'), quote_plus(self.urlPath)))
			transcode.append("session=%s" % self.g_sessionID)
			transcode.append("protocol=hls")
			transcode.append("offset=0")
			transcode.append("3g=0")
			transcode.append("directPlay=0")
			transcode.append("directStream=0")
			transcode.append("videoQuality=60")
			transcode.append("videoResolution=1920x1080")
			transcode.append("maxVideoBitrate=8000")
			transcode.append("subtitleSize=100")
			transcode.append("audioBoost=100")
			transcode.append("waitForSegments=1")
			transcode.append("X-Plex-Device=iPhone")
			transcode.append("X-Plex-Token=ztTLp3RYymrsCH7XP6Zp")
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

	#===========================================================================
	# 
	#===========================================================================
	def getMusicTypes(self, url):
		printl("", self, "S")
		mainMenuList = []
		server=self.getServerFromURL(url)
		details = {'title'	   : "by Album" }
		details["viewMode"]				 = "ShowSeasons"
		details["ratingKey"]				 = "1"
		details['server']				   = str(server)
		extraData = {}
		extraData['theme']="1"
		extraData['key'] = "1"
		context = {}
		context["watchedURL"]				 = "1"
		seenVisu = None
		content = self.addGUIItem(url, details, extraData, context, seenVisu)
		mainMenuList.append(content)
		
		details = {'title'	   : "by Artists" }
		details["viewMode"]				 = "ShowSeasons"
		details["ratingKey"]				 = "1"
		details['server']				   = str(server)


		content = self.addGUIItem(url, details, extraData, context, seenVisu)
		mainMenuList.append(content)
		
		
		printl("mainMenuList: " + str(mainMenuList), self, "D")
				
		printl("", self, "C")
		return mainMenuList  

	#============================================================================
	# 
	#============================================================================
	def music(self, url, tree=None ): # CHECKED
		printl("", self, "S")
		
		fullList = []
		
		server=self.getServerFromURL(url)
		
		if tree is None:
			html=self.doRequest(url)
		
			if html is False:
				printl("", self, "C")
				return

			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)

		for grapes in tree:
		   
			if grapes.get('key',None) is None:
				continue
	
			details={'genre'	   : grapes.get('genre','') ,
					 'artist'	  : grapes.get('artist','') ,
					 'year'		: int(grapes.get('year',0)) ,
					 'album'	   : grapes.get('album','') ,
					 'tracknumber' : int(grapes.get('index',0)) ,
					 'title'	   : "Unknown" }
	
			
			extraData={'type'		: "Music" ,						  
					   'thumb'	   : self.getThumb(grapes, server) ,
					   'fanart_image': self.getFanart(grapes, server) }
	
			if extraData['fanart_image'] == "":
				extraData['fanart_image']=self.getFanart(tree, server)
				
			
			details["viewMode"]				 = "ShowSeasons"
			details["ratingKey"]				 = "1"
			details['server']				   = str(server)

			extraData['theme']="1"
			extraData['key'] = "1"
			context = {}
			context["watchedURL"]				 = "1"
	
			u=self.getLinkURL(url, grapes, server)
			
			if grapes.tag == "Track":
				printl("Track Tag", self, "I")
				
				details['title']=grapes.get('track','Unknown').encode('utf-8')
				details['duration']=int(grapes.get('totalTime',0)/1000)
		
				#context = None
				seenVisu = None
	
				content = self.addGUIItem(u, details, extraData, context, seenVisu)
				fullList.append(content)
	
			else: 
			
				if grapes.tag == "Artist":
					printl("Artist Tag", self, "I")

					details['title']=grapes.get('artist','Unknown')

				elif grapes.tag == "Album":
					printl("Album Tag", self, "I")

					details['title']=grapes.get('album','Unknown')
	
				elif grapes.tag == "Genre":
					details['title']=grapes.get('genre','Unknown')
				
				else:
					printl("Generic Tag: " + grapes.tag, self, "I")
					details['title']=grapes.get('title','Unknown')
					
				details["viewMode"]				 = "ShowSeasons"
				details["ratingKey"]				 = "1"
				details['server']				   = str(server)
	
				extraData['theme']="1"
				extraData['key'] = "1"
				context = {}
				context["watchedURL"]				 = "1"
				#context = None
				seenVisu = None
	
				content = self.addGUIItem(u, details, extraData, context, seenVisu)
				fullList.append(content)
		
		#printl ("fullList = " + fullList, self, "D")
		printl("", self, "C")
		return fullList
	
	#===============================================================================
	# 
	#===============================================================================
	def artist(self, url, tree=None ): # CHECKED
		'''
			Process artist XML and display data
			@input: url of XML page, or existing tree of XML page
			@return: nothing
		'''
		printl("", self, "S")

		
		#Get the URL and server name.  Get the XML and parse
		if tree is None:	  
			html=self.doRequest(url)
			if html is False:
				printl("", self, "C")
				return

			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		server=self.getServerFromURL(url)
		
		ArtistTag=tree.findall('Directory')
		for artist in ArtistTag:
		
			details={'plot'	: artist.get('summary','') ,
					 'artist'  : artist.get('title','').encode('utf-8') }
			
			details['title']=details['artist']
			  
			extraData={'type'		 : "Music" ,
					   'thumb'		: self.getThumb(artist, server) ,
					   'fanart_image' : self.getFanart(artist, server) ,
					   'ratingKey'	: artist.get('title','') ,
					   'key'		  : artist.get('key','') }
	
			url='http://%s%s&mode=%s' % (server, extraData['key'], str(_MODE_ALBUMS) )
			
			self.addGUIItem(url,details,extraData) 
			printl("", self, "C")   

	
	#===============================================================================
	# 
	#===============================================================================
	def albums(self, url, tree=None ): # CHECKED
		printl("", self, "S")

		fullList = []
		#Get the URL and server name.  Get the XML and parse
		if tree is None:
			html=self.doRequest(url)
			if html is False:
				printl("", self, "C")
				return

			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		server=self.getServerFromURL(url)		
		sectionart=self.getFanart(tree, server)
		
		AlbumTags=tree.findall('Directory')
		for album in AlbumTags:
		 
			details={'album'   : album.get('title','').encode('utf-8') ,
					 'year'	: int(album.get('year',0)) ,
					 'artist'  : tree.get('parentTitle', album.get('parentTitle','')) ,
					 'plot'	: album.get('summary','') }
			
			details["viewMode"]				 = "ShowSeasons"
			details["ratingKey"]				 = "1"
			details['server']				   = str(server)
			
			details['title']=details['album']
	
			extraData={'type'		 : "Music" ,
					   'thumb'		: self.getThumb(album, server) ,
					   'fanart_image' : self.getFanart(album, server) ,
					   'key'		  : album.get('key','') }
	
			if extraData['fanart_image'] == "":
				extraData['fanart_image']=sectionart
			
			extraData['theme']="1"
			context = {}
			context["watchedURL"]				 = "1"
										
			url='http://%s%s&mode=%s' % (server, extraData['key'], str(_MODE_TRACKS) )
	
			#context = None
			seenVisu = None

			content = self.addGUIItem(url, details, extraData, context, seenVisu)
			fullList.append(content)
		
		#printl ("fullList = " + fullList, self, "D")
		printl("", self, "C")
		return fullList
	
	#===========================================================================
	# 
	#===========================================================================
	def tracks(self, url,tree=None ): # CHECKED
		printl("", self, "S")

		fullList = []
					
		if tree is None:	   
			html=self.doRequest(url)		  
			if html is False:
				printl("", self, "C")
				return

			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		server = self.getServerFromURL(url)							   
		sectionart = self.getFanart(tree,server) 
		TrackTags = tree.findall('Track')	  
		for track in TrackTags:		
			content = self.trackTag(server, tree, track)
			fullList.append(content)
			
		printl("fullList: " + str(fullList), self, "D")
		return fullList
		printl("", self, "C")   

	#===============================================================================
	# 
	#===============================================================================
	def trackTag(self, server, tree, track ): # CHECKED
		printl("", self, "S")
		
		for child in track:
			for babies in child:
				if babies.tag == "Part":
					partDetails=(dict(babies.items()))
		
		printl( "Part is " + str(partDetails), self, "I")
	
		details={'TrackNumber' : int(track.get('index',0)) ,
				 'title'	   : str(track.get('index',0)).zfill(2)+". "+track.get('title','Unknown').encode('utf-8') ,
				 'rating'	  : float(track.get('rating',0)) ,
				 'album'	   : track.get('parentTitle', tree.get('parentTitle','')) ,
				 'artist'	  : track.get('grandparentTitle', tree.get('grandparentTitle','')) ,
				 'duration'	: int(track.get('duration',0))/1000 }
		
		details["viewMode"]				 = "ShowSeasons"
		details["ratingKey"]				 = "1"
		details['server']				   = str(server)
								   
		extraData={'type'		 : "Music" ,
				   'fanart_image' : self.getFanart(track, server) ,
				   'thumb'		: self.getThumb(track, server) ,
				   'ratingKey'	: track.get('key','') }
	
		if '/resources/plex.png' in extraData['thumb']:
			printl("thumb is default", self, "I")
			extraData['thumb']=self.getThumb(tree, server)
			
		if extraData['fanart_image'] == "":
			extraData['fanart_image']=self.getFanart(tree, server)
			
		extraData['theme']="1"
		context = {}
		context["watchedURL"]	 = "1"
		seenVisu = None
		
		#If we are streaming, then get the virtual location
		url=self.mediaType(partDetails,server)
	
		u="%s&mode=%s&id=%s" % (url, str(_MODE_BASICPLAY), str(extraData['ratingKey']))
			
		guiItem = self.addGUIItem(url, details, extraData, context, seenVisu)
		
		#printl ("fullList = " + fullList, self, "D")
		printl("", self, "C")
		return guiItem	

	#===========================================================================
	# 
	#===========================================================================
	def PlexPlugins(self, url, tree=None ): # CHECKED
		'''
			Main function to parse plugin XML from PMS
			Will create dir or item links depending on what the 
			main tag is.
			@input: plugin page URL
			@return: nothing, creates XBMC GUI listing
		'''
		printl("", self, "S")

		server=self.getServerFromURL(url)
		if tree is None:
	
			html=self.doRequest(url)
		
			if html is False:
				printl("", self, "C")
				return
	
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		for plugin in tree:
	
			details={'title'   : plugin.get('title','Unknown').encode('utf-8') }
	
			if details['title'] == "Unknown":
				details['title']=plugin.get('name',"Unknown").encode('utf-8')
	
			extraData={'thumb'		: self.getThumb(plugin, server) , 
					   'fanart_image' : self.getFanart(plugin, server) ,
					   'identifier'   : tree.get('identifier','') ,
					   'type'		 : "Video" ,
					   'key'		  : plugin.get('key','') }
			
			if extraData['fanart_image'] == "":
				extraData['fanart_image']=self.getFanart(tree, server)
				
			p_url=self.getLinkURL(url, extraData, server)

			if plugin.tag == "Directory" or plugin.tag == "Podcast":
				self.addGUIItem(p_url+"&mode="+str(_MODE_PLEXPLUGINS), details, extraData)
					
			elif plugin.tag == "Video":
				self.addGUIItem(p_url+"&mode="+str(_MODE_VIDEOPLUGINPLAY), details, extraData, folder=False)
			
			printl("", self, "C")


	#============================================================================
	# 
	#============================================================================
	def processXML(self, url, tree=None ):
		'''
			Main function to parse plugin XML from PMS
			Will create dir or item links depending on what the 
			main tag is.
			@input: plugin page URL
			@return: nothing, creates XBMC GUI listing
		'''
		printl("", self, "S")

		server=self.getServerFromURL(url)
		if tree is None:
	
			html=self.doRequest(url)
		
			if html is False:
				printl("", self, "C")   
				return
	
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		for plugin in tree:
	
			details={'title'   : plugin.get('title','Unknown').encode('utf-8') }
	
			if details['title'] == "Unknown":
				details['title']=plugin.get('name',"Unknown").encode('utf-8')
	
			extraData={'thumb'		: self.getThumb(plugin, server) , 
					   'fanart_image' : self.getFanart(plugin, server) ,
					   'identifier'   : tree.get('identifier','') ,
					   'type'		 : "Video" }
			
			if extraData['fanart_image'] == "":
				extraData['fanart_image']=self.getFanart(tree, server)
				
			p_url=self.getLinkURL(url, plugin, server)

			if plugin.tag == "Directory" or plugin.tag == "Podcast":
				self.addGUIItem(p_url+"&mode="+str(_MODE_PROCESSXML), details, extraData)
	
			elif plugin.tag == "Track":
				self.trackTag(server, tree, plugin)
					
			elif tree.get('viewGroup') == "movie":
				self.getMoviesFromSection(url, tree)
				printl("", self, "C")   
				return
	
			elif tree.get('viewGroup') == "episode":
				self.getEpisodesOfSeason(url, tree)
				printl("", self, "C")   
				return

	#===============================================================================
	# 
	#===============================================================================
	def movieTag(self, url, server, tree, movie):
		printl("", self, "S")

		tempgenre=[]
		tempcast=[]
		tempdir=[]
		tempwriter=[]
		
		#Lets grab all the info we can quickly through either a dictionary, or assignment to a list
		#We'll process it later
		for child in movie:
			if child.tag == "Media":
				mediaarguments = dict(child.items())
			elif child.tag == "Genre" and self.g_skipmetadata == "false":
				genreTag = child.get('tag')
				tempgenre.append(genreTag)
				# fill genre filter
				if genreTag not in self.tmpGenres:
					self.tmpGenres.append(genreTag)
			elif child.tag == "Writer"  and self.g_skipmetadata == "false":
				tempwriter.append(child.get('tag'))
			elif child.tag == "Director"  and self.g_skipmetadata == "false":
				tempdir.append(child.get('tag'))
			elif child.tag == "Role"  and self.g_skipmetadata == "false":
				tempcast.append(child.get('tag'))

		#Gather some data 
		duration = int(mediaarguments.get('duration',movie.get('duration',0)))/1000
				 
		#Required listItem entries for XBMC
		details = {}
		details["viewMode"]			 = "play"
		details['ratingKey']			= str(movie.get('ratingKey', 0)) # primary key in plex
		details['summary']			  = movie.get('summary','')
		details['title']				= movie.get('title','').encode('utf-8')
		details['viewCount']			= int(movie.get('viewCount', 0))
		details['rating']			   = movie.get('rating', 0)
		details['studio']			   = movie.get('studio','')
		details['year']				 = movie.get('year', 0)
		details['tagline']			  = movie.get('tagline','')
		details['runtime']			  = str(datetime.timedelta(seconds=duration))
		details['server']			   = str(server)
		details['genre']				= " / ".join(tempgenre)
		details['viewOffset']		   = int(movie.get('viewOffset',0))
		details['director']			 = " / ".join(tempdir)
		
		# lets add this for another filter
		if details['viewCount'] > 0:
			details['viewState'] = "seen"
			seenVisu = self.seenPic
		
		elif details['viewCount'] > 0 and details['viewOffset'] > 0:
			details['viewState']		= "started"
			seenVisu = self.startedPic
		
		else:
			details['viewState'] = "unseen"
			seenVisu = self.unseenPic
		
		#Extended Metadata
		if self.g_skipmetadata == "false":
			details['cast']	 = tempcast
			details['writer']   = " / ".join(tempwriter)
		
		extraData = {}
		extraData['type']			   = "Video"
		extraData['ratingKey']		  = str(movie.get('ratingKey', 0)) # primary key in plex
		extraData['thumb']			  = self.getImage(movie, server, x = 195, y = 268, type = "thumb")
		extraData['fanart_image']	   = self.getImage(movie, server, x = 560, y = 315, type = "art")
		extraData['token']			  = self.g_myplex_accessToken
		extraData['key']				= movie.get('key','')
		
		subtitleData = self.getSelectedSubtitleDataById(details['server'], extraData['ratingKey'])
		extraData['selectedSub']	= subtitleData.get('language')
		
		extraData['selectedAudio']	= ""

		#Add extra media flag data
		if self.g_skipmediaflags == "false":
			extraData['contentRating']   = movie.get('contentRating', '')
			extraData['videoResolution'] = mediaarguments.get('videoResolution', '')
			extraData['videoCodec']	  = mediaarguments.get('videoCodec', '')
			extraData['audioCodec']	  = mediaarguments.get('audioCodec', '')
			extraData['aspectRatio']	 = mediaarguments.get('aspectRatio', '')
			extraData['audioCodec']	  = mediaarguments.get('audioCodec', '')
	
		#Build any specific context menu entries
		if self.g_skipcontext == "false":
			context=self.buildContextMenu(url, extraData)
		else:
			context=None
		
		# fill title filter
		if details["title"].upper() not in self.tmpAbc:
			self.tmpAbc.append(details["title"].upper())
			
		guiItem = self.addGUIItem(url, details, extraData, context, seenVisu, folder=False)
		
		printl("", self, "C")   
		return guiItem		
		
	
	#===============================================================================
	# 
	#===============================================================================
	def photo(self, url,tree=None ): # CHECKED
		printl("", self, "S")
		
		server=url.split('/')[2]

		
		if tree is None:
			html=self.doRequest(url)
			
			if html is False:
				printl("", self, "C")
				return
			
			try:
				tree = etree.fromstring(html)
			except Exception, e:
				self._showErrorOnTv("no xml as response", html)
		
		sectionArt=self.getFanart(tree,server)

		for picture in tree:
			
			details={'title' : picture.get('title',picture.get('name','Unknown')).encode('utf-8') } 
			
			extraData={'thumb'		: self.getThumb(picture, server) ,
					   'fanart_image' : self.getFanart(picture, server) ,
					   'type'		 : "Picture" }
	
			if extraData['fanart_image'] == "":
				extraData['fanart_image']=sectionArt
	
			u=self.getLinkURL(url, picture, server)   
					
			if picture.tag == "Directory":
				u=u+"&mode="+str(_MODE_PHOTOS)
				self.addGUIItem(u,details,extraData)
		
			elif picture.tag == "Photo":
			
				if tree.get('viewGroup','') == "photo":
					for photo in picture:
						if photo.tag == "Media":
							for images in photo:
								if images.tag == "Part":
									printl("found part tag", self, "D")
									extraData['key']="http://"+server+images.get('key','')
									u=extraData['key']
				
				self.addGUIItem(u,details,extraData,folder=False)
			
			printl("", self, "C")

	

	#=============================================================================
	# 
	#=============================================================================
	def getImage(self,  data, server, x, y, type, transcode = True): # CHECKED
		'''
			Simply take a URL or path and determine how to format for images
			@ input: elementTree element, server name
			@ return formatted URL
		'''
		printl("", self, "S")
		
		image = data.get(type,'').split('?t')[0]

		if image == '':
			printl("", self, "C")   
			return self.g_loc+'/resources/plex.png'
			
		elif image[0:4] == "http" :
			printl("", self, "C")   
			return image
		
		elif image[0] == '/':
			if transcode:
				printl("", self, "C")   
				return self.photoTranscode(server,'http://localhost:32400'+image, str(x), str(y))
			else:
				printl("", self, "C")   
				return 'http://'+server+image
		
		else: 
			printl("", self, "C")   
			return self.g_loc+'/resources/plex.png'
	
	#=============================================================================
	# 
	#=============================================================================
	def getThumb(self,  data, server, transcode = True, x = 195, y = 268): # CHECKED
		'''
			Simply take a URL or path and determine how to format for images
			@ input: elementTree element, server name
			@ return formatted URL
			str(195), str(268)
		'''
		printl("", self, "S")
		
		thumbnail=data.get('thumb','').split('?t')[0]

		if thumbnail == '':
			printl("", self, "C")   
			return self.g_loc+'/resources/plex.png'
			
		elif thumbnail[0:4] == "http" :
			printl("", self, "C")   
			return thumbnail
		
		elif thumbnail[0] == '/':
			if transcode:
				printl("", self, "C")   
				return self.photoTranscode(server,'http://localhost:32400'+thumbnail, str(x), str(y))
			else:
				printl("", self, "C")   
				return 'http://'+server+thumbnail
		
		else: 
			printl("", self, "C")   
			return self.g_loc+'/resources/plex.png'
	
	#============================================================================
	# 
	#============================================================================
	def getFanart(self, data, server, transcode=True, x= 560, y= 315 ): # CHECKED
		'''
			Simply take a URL or path and determine how to format for fanart
			@ input: elementTree element, server name
			@ return formatted URL for photo resizing
			str(450), str(260)
		'''
		printl("", self, "S")
		printl("art: "  + str(data.get('art','')), self, "D")
		
		fanart=data.get('art','')
		
		if fanart == '':
			printl("", self, "C")   
			return ''
	
		elif fanart[0:4] == "http" :
			printl("", self, "C")   
			return fanart
			
		elif fanart[0] == '/':
			if transcode:
				printl("", self, "C")   
				return self.photoTranscode(server,'http://localhost:32400'+fanart, str(x), str(y))
			else:
				printl("", self, "C")   
				return 'http://%s%s' % (server, fanart)
			
		else: 
			printl("", self, "C")	
			return ''

	#===========================================================================
	# 
	#===========================================================================
	def getServerFromURL(self, url ): # CHECKED
		'''
		Simply split the URL up and get the server portion, sans port
		@ input: url, woth or without protocol
		@ return: the URL server
		'''
		printl("", self, "S")

		if url[0:4] == "http" or url[0:4] == "plex":
			printl("", self, "C")   
			return url.split('/')[2]
		else:
			printl("", self, "C")   
			return url.split('/')[0]
	
	#============================================================================
	# 
	#============================================================================
	def getLinkURL(self, url, pathData, server ): # CHECKED
		'''
			Investigate the passed URL and determine what is required to 
			turn it into a usable URL
			@ input: url, XML data and PM server address
			@ return: Usable http URL
		'''
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

		printl("", self, "C")   
		return url

	#===============================================================================
	# 
	#===============================================================================
	def plexOnline(self, url ): # CHECKED
		printl("", self, "S")

	
		server=self.getServerFromURL(url)
		
		html=self.doRequest(url)
		
		if html is False:
			printl("", self, "C")
			return
		
		try:
			tree = etree.fromstring(html)
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)
			
		for plugin in tree:
		   
			details={'title' : plugin.get('title',plugin.get('name','Unknown')).encode('utf-8') }
			extraData={'type'	  : "Video" , 
					   'installed' : int(plugin.get('installed',2)) ,
					   'key'	   : plugin.get('key','') ,
					   'thumb'	 : self.getThumb(plugin,server)} 
					   
			mode=_MODE_CHANNELINSTALL
			
			if extraData['installed'] == 1:
				details['title']=details['title']+" (installed)"
				
			elif extraData['installed'] == 2:	  
				mode=_MODE_PLEXONLINE
			
			u=self.getLinkURL(url, plugin, server)
			
			u=u+"&mode="+str(mode)+"&name="+urllib.quote_plus(details['title'])
			self.addGUIItem(u, details, extraData)
			printl("", self, "C")   


	#==========================================================================
	# 
	#==========================================================================
	def install(self, url, name ): # CHECKED
		printl("", self, "S")
		
		html=self.doRequest(url)

	
		printl("", self, "C")   
		return   
	
	#=============================================================================
	# 
	#=============================================================================
	def channelView(self, url ): # CHECKED 
		printl("", self, "S")

		html=self.doRequest(url)
		if html is False:
			printl("", self, "C")
			return
		
		try:
			tree = etree.fromstring(html)
		except Exception, e:
			self._showErrorOnTv("no xml as response", html)	
		
		
		server=self.getServerFromURL(url)   
		for channels in tree.getiterator('Directory'):
		
			if channels.get('local','') == "0":
				continue
				
			arguments=dict(channels.items())
	
			extraData={'fanart_image' : self.getFanart(channels, server) ,
					   'thumb'		: self.getThumb(channels, server) }
			
			details={'title' : channels.get('title','Unknown') }
	
			suffix=channels.get('path').split('/')[1]
			
			if channels.get('unique','')=='0':
				details['title']=details['title']+" ("+suffix+")"
				   
			p_url=self.getLinkURL(url, channels, server)  
			
			if suffix == "photos":
				mode=_MODE_PHOTOS
			elif suffix == "video":
				mode=_MODE_PLEXPLUGINS
			elif suffix == "music":
				mode=_MODE_MUSIC
			else:
				mode=_MODE_GETCONTENT
			
			self.addGUIItem(p_url+'&mode='+str(mode),details,extraData)
			
			printl("", self, "C")   
		#=======================================================================
		# xbmcplugin.endOfDirectory(pluginhandle)
		#=======================================================================

	#===========================================================================
	# 
	#===========================================================================
	def photoTranscode(self, server, url, width, height ): # CHECKED
		printl("", self, "S")
		
		transcode_url = 'http://%s/photo/:/transcode?url=%s&width=%s&height=%s%s' % (server, urllib.quote_plus(url), width, height, self.get_uTokenForServer())
		printl("transcode_url: " + str(transcode_url), self, "D")
#		

		#if self.g_connectionType == "2": # MYPLEX
#			
#			if self.g_accessTokenHeader == None:
#				token = self.getAccessToken()
#			else:
#				token = self.g_accessTokenHeader
#			
#			new_url += token
		
		printl("", self, "C")   
		return transcode_url
				  
	#===============================================================================
	# 
	#===============================================================================
	def skin(self ): # CHECKED
		printl("", self, "S")
		#Get the global host variable set in settings

		printl("", self, "C")   
		return

	#============================================================================
	# 
	#============================================================================
	def myPlexQueue(self): # CHECKED
		printl("", self, "S")	

		printl("", self, "C")   
		return
		
	#===============================================================================
	# 
	#===============================================================================
	def libraryRefresh(self, url ): # CHECKED
		printl("", self, "S")

		printl("", self, "C")   
		return

	#============================================================================
	# 
	#============================================================================
	def watched(self, url ): # CHECKED
		printl("", self, "S")
	
		if url.find("unscrobble") > 0:
			printl ("Marking as unwatched with: " + url, self, "I")
		else:
			printl ("Marking as watched with: " + url, self, "I")
		
		html=self.doRequest(url)

		printl("", self, "C")   
		return

	#==========================================================================
	# 
	#==========================================================================
	def displayServers(self, url ): # CHECKED
		printl("", self, "S")

		type=url.split('/')[2]
		printl("Displaying entries for " + type, self, "I")
		Servers = self.resolveAllServers()
	
		#For each of the servers we have identified
		for mediaserver in Servers:
		
			details={'title' : mediaserver.get('serverName','Unknown') }
	
			if type == "video":
				s_url='http://%s/video&mode=%s' % ( mediaserver.get('address','') , _MODE_PLEXPLUGINS )
				
			elif type == "online":
				s_url='http://%s/system/plexonline&mode=%s' % ( mediaserver.get('address','') , _MODE_PLEXONLINE )
				
			elif type == "music":
				s_url='http://%s/music&mode=%s' % ( mediaserver.get('address','') , _MODE_MUSIC )
				
			elif type == "photo":
				s_url='http://%s/photos&mode=%s' % ( mediaserver.get('address','') , _MODE_PHOTOS )
					
			self.addGUIItem(s_url, details, {} )
		
		printl("", self, "C")   


	#===============================================================================
	# 
	#===============================================================================
	def getTranscodeSettings(self, override=False ): # CHECKED
		printl("", self, "S")

		if override is True:
			printl( "Transcode override.  Will play media with addon transcoding settings", self, "I")
			self.g_transcode="true"
	
		if self.g_transcode == "true":
			
			printl( "We are set to Transcode, overriding stream selection", self, "I")
		
			printl( "Transcode quality is " + self.g_quality, self, "I")
			
			#protocols = "protocols=http-live-streaming,http-mp4-streaming,http-streaming-video,http-mp4-video;"
			protocols = "protocols=http-video;"
			
			videoDecoders = "videoDecoders=mpeg2video{profile:high&resolution:1080&level:51},mpeg4{profile:high&resolution:1080&level:51},mpeg1video{profile:high&resolution:1080&level:51},mp4{profile:high&resolution:1080&level:51},h264{profile:high&resolution:1080&level:51}"
			
			#videoDecoders = "videoDecoders=h264{profile:high&resolution:1080&level:41}"
			#audioDecoders = "audioDecoders=mp3,dts{bitrate:2560000&channels:6},ac3{bitrate:2560000&channels:6}"
			
			#dts is not running for some reason
			audioDecoders = "audioDecoders=mp3,aac"

			self.g_capability = urllib.quote_plus(protocols + ";" + videoDecoders + ";" + audioDecoders)

			printl("Plex Client Capability = " + self.g_capability, self, "I")
			
			printl("", self, "C")   
			
	#===============================================================================
	# 
	#===============================================================================
	def deleteMedia(self, url ): # CHECKED
		printl("", self, "S")
		printl ("deleting media at: " + url, self, "I")
		
		return_value = True
		if return_value:
			printl("Deleting....")
			installed = self.doRequest(url,type="DELETE")	
		
		printl("", self, "C")   
		return True
	
	

	#===============================================================================
	# 
	#===============================================================================
	def buildContextMenu(self, url, itemData ): # CHECKED
		printl("", self, "S")
		context={}
		server=self.getServerFromURL(url)
		ID=itemData.get('ratingKey','0')
	
		#Initiate Library refresh 
		refreshURL=url.replace("/all", "/refresh")
		libraryRefreshURL = refreshURL.split('?')[0]+self.get_aTokenForServer() #self.getAuthDetails(itemData,prefix="?")
		context['libraryRefreshURL'] = libraryRefreshURL
		
		#Mark media unwatched
		unwatchedURL="http://"+server+"/:/unscrobble?key="+ID+"&identifier=com.plexapp.plugins.library"+self.get_uTokenForServer() #self.getAuthDetails(itemData)
		context['unwatchURL'] = unwatchedURL
				
		#Mark media watched		
		watchedURL="http://"+server+"/:/scrobble?key="+ID+"&identifier=com.plexapp.plugins.library"+self.get_uTokenForServer() #self.getAuthDetails(itemData)
		context['watchedURL'] = watchedURL
	
		#Delete media from Library
		deleteURL="http://"+server+"/library/metadata/"+ID+self.get_uTokenForServer() #self.getAuthDetails(itemData)
		context['deleteURL'] = deleteURL
	
		#Display plugin setting menu
		#settingDisplay=plugin_url+"setting)"
		#context.append(('DreamPlex settings', settingDisplay , ))
	
		#Reload media section
		#listingRefresh=plugin_url+"refresh)"
		#context.append(('Reload Section', listingRefresh , ))
	
		#printl("Using context menus " + str(context), self, "I")
		
		printl("", self, "C")   
		return context

#===============================================================================
# HELPER FUNCTIONS
#===============================================================================
	
	#===========================================================================
	# 
	#===========================================================================
	def _showErrorOnTv(self, text, content):
	   self.session.open(MessageBox,_("UNEXPECTED ERROR:\n%s\n%s") % (text, content), MessageBox.TYPE_INFO, timeout = 5)

	#===============================================================================
	# 
	#===============================================================================
	def checkNasOverride(self):
		printl("", self, "S")
		
		#NAS Override
		#===========================================================================
		# self.g_nasoverride = __settings__.getSetting('nasoverride')
		#===========================================================================
		printl("DreamPlex -> check SMB IP Override: " + self.g_nasoverride, self, "I")
		
		if self.g_nasoverride == "true":
			#===================================================================
			# self.g_nasoverrideip = __settings__.getSetting('nasoverrideip')
			#===================================================================
			if self.g_nasoverrideip == "":
				printl("DreamPlex -> No NAS IP Specified.  Ignoring setting", self, "I")
			else:
				printl("DreamPlex -> NAS IP: " + self.g_nasoverrideip, self, "I")
				
			#===================================================================
			# self.g_nasroot = __settings__.getSetting('nasroot')
			#===================================================================

	#===========================================================================
	# #Get look and feel
	# if __settings__.getSetting("contextreplace") == "true":
	#	g_contextReplace=True
	# else:
	#	g_contextReplace=False
	#===========================================================================
	
	#===========================================================================
	# self.g_skipcontext = __settings__.getSetting("skipcontextmenus")	
	# self.g_skipmetadata= __settings__.getSetting("skipmetadata")
	# self.g_skipmediaflags= __settings__.getSetting("skipflags")
	# self.g_skipimages= __settings__.getSetting("skipimages")
	# 
	# self.g_loc = "special://home/addons/plugin.video.DreamPlex"
	#===========================================================================
	
	#===========================================================================
	# #Create the standard header structure and load with a User Agent to ensure we get back a response.
	# g_txheaders = {
	#			  'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',	
	#			  }
	#===========================================================================
	
	#===========================================================================
	# #Set up holding variable for session ID
	# global self.g_sessionID
	# self.g_sessionID=None
	#===========================================================================
		
		printl("", self, "C")
		
	def prepareServerDict(self): # CHECKED
		printl("", self, "S")

		#!!!!
		self.g_serverDict=[] #we clear g_serverDict because we use plex for now only with one server to seperate them within the plugin
		#!!!!
			
		if self.g_connectionType == "2": # MYPLEX
			printl( "DreamPlex -> Adding myplex as a server location", self, "I")
			self.g_serverDict.append({	'serverName'	: 'MYPLEX',
										'address'		: "my.plex.app",
										'discovery'		: 'myplex',
										'token'			: None,
										'uuid'			: None,
										'role'			: 'master'})
		else:
			if not self.g_host or self.g_host == "<none>":
				self.g_host = None
			
			elif not self.g_port:
				printl( "No port defined.  Using default of " + DEFAULT_PORT, self, "I")
				self.g_address = self.g_host + ":" + DEFAULT_PORT
			
			else:
				self.g_address = self.g_host + ":" + self.g_port
				printl( "Settings hostname and port: " + self.g_address, self, "I")
		
			if self.g_address is not None:
				self.g_serverDict.append({	'serverName'	: self.g_name,
											'address'		: self.g_address,
											'discovery'		: 'local', 
											'token'			: None,
											'uuid'			: None,
											'role'			: 'master' })
			
			self.g_currentServer = self.g_address
			printl("currentServer: " + str(self.g_currentServer), self, "D")
			
			self.g_myplex_accessTokenDict = {}
			self.g_myplex_accessTokenDict[str(self.g_address)] = None
			self.setAccessTokenHeader()

		printl("DreamPlex -> serverList is " + str(self.g_serverDict), self, "I")
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def resolveAllServers(self): # CHECKED
		'''
		  Return list of all media sections configured
		  within DreamPlex
		  @input: None
		  @Return: unique list of media sections
		'''
		printl("", self, "S")

		localServers=[]
		  
		for servers in self.g_serverDict:
		
			if ( servers['discovery'] == 'local' ) or ( servers['discovery'] == 'bonjour' ):
				localServers += self.getLocalServers()
			elif servers['discovery'] == 'myplex':
				localServers += self.getMyPlexServers()
		
			printl ("Resolved server List: " + str(localServers), self, "I")
		
		'''If we have more than one server source, then
		   we need to ensure uniqueness amonst the
		   seperate servers.
		   
		   If we have only one server source, then the assumption
		   is that Plex will deal with this for us.
		'''
		
		if len(self.g_serverDict) > 1:
			oneCount=0
			for onedevice in localServers:
			
				twoCount=0
				for twodevice in localServers:
	
					printl( "["+str(oneCount)+":"+str(twoCount)+"] Checking " + onedevice['uuid'] + " and " + twodevice['uuid'])
	
					if oneCount == twoCount:
						printl( "skip" )
						twoCount+=1
						continue
						
					if onedevice['uuid'] == twodevice['uuid']:
						printl ( "match" )
						if onedevice['discovery'] == "local":
							localServers.pop(twoCount)
						else:
							localServers.pop(oneCount)
					else:
						printl( "no match" )
					
					twoCount+=1

				oneCount+=1
		
		printl("Unique server List: " + str(localServers), self, "I")
		printl("", self, "C")
		return localServers   

	#===========================================================================
	# 
	#===========================================================================
	def __xmlRequest(self, uri, params):
		printl("", self, "S")
		
		if params is not None: uri = uri + "?" + urlencode(params).replace('+', '%20')
		location = "%s:%d" % (self.getHost(), self.getHttpPort())
		resp = urlopen("http://" + location + uri)
		if resp is None:
			raise IOError, "No response from Server"
		xml = parse(resp)
		resp.close()
		
		printl("", self, "C")
		return xml

	#===========================================================================
	# 
	#===========================================================================
	def getServerName(self):
		printl("", self, "S")
		
		printl("", self, "C")
		return self.g_name
	
	#===========================================================================
	# 
	#===========================================================================
	def getServerVersion(self):
		printl("", self, "S")
		if self.g_address is None:
			# todo we have to find out a way to get the version even with myplex servers
			self.g_serverVersion = "myPlex Server"
			
		if self.g_serverVersion is None:
			url = self.g_address + "/servers"
			xml = self.doRequest(url)
			
			tree = etree.fromstring(xml).findall("Server")

			# this should be only one run. maybe i find a way to read directly without the for :-)
			for server in tree:
				version = server.get("version").split('-')[0]

			self.g_serverVersion = str(version)

		printl("", self, "C")
		return self.g_serverVersion

