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
import math
import os

#noinspection PyUnresolvedReferences
from enigma import eTimer

from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.config import config
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.AVSwitch import AVSwitch
from Components.Sources.List import List

from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox

from Tools.Directories import fileExists

from enigma import eServiceReference
from enigma import ePicLoad

from urllib import quote_plus
from twisted.web.client import downloadPage

from DP_Player import DP_Player
from DP_Settings import DPS_Settings
from DP_Server import DPS_Server

from DPH_StillPicture import StillPicture
from DPH_Singleton import Singleton
from DPH_ScreenHelper import DPH_ScreenHelper, DPH_MultiColorFunctions, DPH_Screen, DPH_Filter
from DP_ViewFactory import getNoneDirectoryElements, getDefaultDirectoryElementsList, getGuiElements

from __common__ import printl2 as printl, loadPicture, durationToTime, getLiveTv, encodeThat, getOeVersion, checkXmlFile, getXmlContent
from __plugin__ import Plugin
from __init__ import _ # _ is translation

#===========================================================================
#
#===========================================================================
class DP_View(DPH_Screen, DPH_ScreenHelper, DPH_MultiColorFunctions, DPH_Filter):

	ON_CLOSED_CAUSE_CHANGE_VIEW = 1
	ON_CLOSED_CAUSE_SAVE_DEFAULT = 2
	ON_CLOSED_CAUSE_CHANGE_VIEW_FORCE_UPDATE = 3

	onNumberKeyLastChar             = "#"
	returnTo                        = None
	currentEntryDataDict            = {}
	currentIndexDict                = {}
	currentTagTypeDict              = {}
	showMedia                       = False
	showDetail                      = False
	isFolder                        = False
	forceUpdate                     = False
	lastTagType                     = None
	sessionData                     = False

	backdrop_postfix                = ""
	poster_postfix                  = ""
	image_prefix                    = ""
	whatPoster                      = None
	whatBackdrop                    = None
	myParams                        = None
	seenUrl                         = None
	unseenUrl                       = None
	deleteUrl                       = None
	refreshUrl                      = None
	details                         = None
	extraData                       = None
	context                         = None
	resetPoster                     = True
	resetBackdrop                   = True
	posterHeight                    = None
	posterWidth                     = None
	backdropHeight                  = None
	backdropWidth                   = None
	EXpicloadPoster                 = None
	EXpicloadBackdrop               = None
	EXscale                         = None
	playTheme                       = False
	startPlaybackNow                = False
	changePoster                    = True
	changeBackdrop                  = True
	fastScroll                      = False
	viewStep                        = 0 # we use this to know the steps we did to store the changes form subviews
	viewChangeStorage               = {} # we use this to save changed value if we have subViews
	loadedStillPictureLib           = False # until we do not know if we can load the libs it will be false
	usedStillPicture                = False
	refreshTimer                    = None # initial value to stay agile in list of media
	selection                       = None # this stores the current list entry of list
	leaving                         = False # we use this to know if we are going deeper into the lib or leaving e.g. show - season - episode

	playerData                      = {} # inital playerData dict
	currentQueuePosition            = 0 # this is the current selection id
	detailsPaneVisible              = False # is shortDescription or details visible
	autoPlayMode                    = False
	resumeMode                      = True
	currentFunctionLevel            = "1"
	currentService                  = None
	miniTvInUse                     = False
	keyOneDisabled                  = False
	filterMode                      = False
	playbackMode                    = "default"
	themeMusicIsRunning             = False
	lastPlayedTheme                 = None
	filterableContent               = False
	subtitlesList                   = None
	subtitleData                    = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, viewClass, libraryName, loadLibraryFnc, viewParams):
		"""
		@param viewClass: is the screen session (eg DP_ViewShows)
		@param libraryName: movie, show, music
		@type loadLibraryFnc: is loadLibrary Function from Lib_class (eg DP_LibShows)
		@param viewParams: are the params for dynamic screen handling from skin params
		@return:
		"""
		printl("", self, "S")
		DPH_Screen.__init__(self, viewClass)
		self.viewParams = viewParams
		self.miniTv = self.viewParams["settings"]["miniTv"]

		if self.miniTv:
			DPH_ScreenHelper.__init__(self, forceMiniTv= True)
		else:
			DPH_ScreenHelper.__init__(self)

		DPH_MultiColorFunctions.__init__(self)
		DPH_Filter.__init__(self)

		self.initScreen(libraryName)

		printl("viewParams: " + str(self.viewParams), self, "D")
		printl("libraryName: " + str(libraryName), self, "D")

		self.skinName = self.viewParams["settings"]["screen"]
		printl("self.skinName: " + str(self.skinName), self, "D")

		self.currentViewName = str(self.viewParams["settings"]["name"])
		printl("self.currentViewName: " + str(self.currentViewName), self, "D")

		self.currentViewType = str(self.viewParams["settings"]["type"])

		self.stillPictureEnabledInView = self.viewParams["settings"]["backdropVideos"]
		self.stillPictureEnabledInSettings = config.plugins.dreamplex.useBackdropVideos.value

		self.plexInstance = Singleton().getPlexInstance()

		self.libraryName = libraryName
		self.loadLibrary = loadLibraryFnc

		self.setListViewElementsCount()

		self.usePicCache = config.plugins.dreamplex.usePicCache.value

		self.noneDirectoryElementsList = getNoneDirectoryElements()
		self.directoryElementsList = getDefaultDirectoryElementsList()

		# Initialise library list
		myList = []
		self["listview"] = List(myList, True)

		self.seenPng = None
		self.unseenPng = None
		self.startedPng = None

		self["actions"] = HelpableActionMap(self, "DP_View",
		{
			"ok":			(self.onKeyOk, ""),
			"cancel":		(self.onKeyCancel, ""),
			"left":			(self.onKeyLeft, ""),
			"right":		(self.onKeyRight, ""),
			"up":			(self.onKeyUp, ""),
			"down":			(self.onKeyDown, ""),
			"info":			(self.onKeyInfo, ""),
			"menu":			(self.onKeyMenu, ""),
			"video":		(self.onKeyVideo, ""),
			"audio":		(self.onKeyAudio, ""),
			"red":			(self.onKeyRed, ""),
			"yellow":		(self.onKeyYellow, ""),
			"blue":			(self.onKeyBlue, ""),
			"green":		(self.onKeyGreen, ""),
			"text":			(self.onKeyText, ""),
			"red_long":		(self.onKeyRedLong, ""),
			"yellow_long":	(self.onKeyYellowLong, ""),
			"blue_long":	(self.onKeyBlueLong, ""),

			"bouquet_up":	(self.bouquetUp, ""),
			"bouquet_down":	(self.bouquetDown, ""),

		}, -2)

		self.guiElements = getGuiElements()

		# set navigation values
		#DP_View.setListViewElementsCount("DPS_ViewList")

		# get needed config parameters
		self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
		self.fastScroll = config.plugins.dreamplex.fastScroll.value
		self.liveTvInViews = config.plugins.dreamplex.liveTvInViews.value
		self.startWithFilterMode = config.plugins.dreamplex.startWithFilterMode.value

		# get data from plex library
		self.image_prefix = self.plexInstance.getServerName().lower()

		# get server config
		self.serverConfig = self.plexInstance.getServerConfig()

		# init skin elements
		self.setMultiLevelElements(levels=4)

		self["totalLabel"] = Label()
		self["totalLabel"].setText(_("Total:"))
		self["total"] = Label()

		self["number_key_popup"] = Label()
		self["number_key_popup"].hide()

		self["paginationLabel"] = Label()
		self["paginationLabel"].setText(_("Pages:"))
		self["pagination"] = Label()

		self["btn_red"]			= Pixmap()
		self["btn_yellow"]		= Pixmap()
		self["btn_blue"]		= Pixmap()
		self["btn_green"]		= Pixmap()

		self["btn_redText"]			= Label()
		self["btn_yellowText"]		= Label()
		self["btn_blueText"]		= Label()
		self["btn_greenText"]		= Label()

		self["sound"] = MultiPixmap()

		self["soundchannels"] = MultiPixmap()

		self["resolution"] = MultiPixmap()

		self["aspect"] = MultiPixmap()

		self["codec"] = MultiPixmap()

		self["rated"] = MultiPixmap()

		self["title"] = Label()
		self["grandparentTitle"] = Label()

		self["tag"] = Label()

		self["cast"] = Label()
		self["castLabel"] = Label()
		self["castLabel"].setText(_("Cast:"))

		self["shortDescription"] = ScrollLabel()

		self["subtitles"] = Label()
		self["subtitles"].setText(_("press 'Text'"))
		self["subtitlesLabel"] = Label()
		self["subtitlesLabel"].setText(_("Subtitles:"))

		self["audio"] = Label()
		self["audio"].setText(_("press 'Audio' or 'Radio'"))
		self["audioLabel"] = Label()
		self["audioLabel"].setText(_("Audio:"))

		self["info"] = Label()
		self["info"].setText(_("press 'Info'"))
		self["infoLabel"] = Label()
		self["infoLabel"].setText(_("Info:"))

		self["director"] = Label()
		self["directorLabel"] = Label()
		self["directorLabel"].setText(_("Director:"))

		self["writer"] = Label()
		self["writerLabel"] = Label()
		self["writerLabel"].setText(_("Writer:"))

		self["genre"] = Label()
		self["genreLabel"] = Label()
		self["genreLabel"].setText(_("Genre:"))

		self["year"] = Label()
		self["yearLabel"] = Label()
		self["yearLabel"].setText(_("Year:"))

		self["leafCount"] = Label()
		self["leafCountLabel"] = Label()
		self["leafCountLabel"].setText(_("Medias:"))

		self["unviewedLeafCount"] = Label()
		self["unviewedLeafCountLabel"] = Label()
		self["unviewedLeafCountLabel"].setText(_("Unseen:"))

		self["viewedLeafCount"] = Label()
		self["viewedLeafCountLabel"] = Label()
		self["viewedLeafCountLabel"].setText(_("Seen:"))

		self["childCount"] = Label()
		self["childCountLabel"] = Label()
		self["childCountLabel"].setText(_("Seasons:"))

		self["studio"] = Label()
		self["studioLabel"] = Label()
		self["studioLabel"].setText(_("Studio:"))

		self["duration"] = Label()
		self["durationLabel"] = Label()
		self["durationLabel"].setText(_("Runtime:"))

		self["backdrop"] = Pixmap()

		if self.liveTvInViews:
			self["backdrop"].hide()

		self["poster"] = Pixmap()
		self["rating_stars"] = ProgressBar()

		# media details
		self["videoCodec"] = Label()
		self["videoCodecLabel"] = Label()
		self["videoCodecLabel"].setText(_("Video Codec:"))

		self["bitrate"] = Label()
		self["bitrateLabel"] = Label()
		self["bitrateLabel"].setText(_("Bitrate:"))

		self["videoFrameRate"] = Label()
		self["videoFrameRateLabel"] = Label()
		self["videoFrameRateLabel"].setText(_("Framerate:"))

		self["audioChannels"] = Label()
		self["audioChannelsLabel"] = Label()
		self["audioChannelsLabel"].setText(_("Audio Channels:"))

		self["aspectRatio"] = Label()
		self["aspectRatioLabel"] = Label()
		self["aspectRatioLabel"].setText(_("Aspect Ratio:"))

		self["videoResolution"] = Label()
		self["videoResolutionLabel"] = Label()
		self["videoResolutionLabel"].setText(_("Resultion:"))

		self["audioCodec"] = Label()
		self["audioCodecLabel"] = Label()
		self["audioCodecLabel"].setText(_("Audio Codec:"))

		self["file"] = Label()
		self["fileLabel"] = Label()
		self["fileLabel"].setText(_("File:"))

		self["casePic"] = Pixmap()

		# Poster
		self.EXpicloadPoster = ePicLoad()
		self.posterHeight = self.viewParams["settings"]["posterHeight"]
		self.posterWidth = self.viewParams["settings"]["posterWidth"]
		self.poster_postfix = "_poster_" + self.posterWidth + "x" + self.posterHeight + "_v2.jpg"

		# Backdrops
		self.EXpicloadBackdrop = ePicLoad()
		self.backdropHeight = self.viewParams["settings"]["backdropHeight"]
		self.backdropWidth = self.viewParams["settings"]["backdropWidth"]
		self.backdrop_postfix = "_backdrop_" + self.backdropWidth + "x" + self.backdropHeight + "_v2.jpg"

		# now we try to enable stillPictureSupport
		if self.stillPictureEnabledInSettings and self.stillPictureEnabledInView:
			# if liveTv is not stopped on startup we have to do so now
			if not config.plugins.dreamplex.stopLiveTvOnStartup.value:
				self.session.nav.stopService()

			try:
				self["stillPicture"] = StillPicture(viewClass) # this is working over an renderer
				# we use this to be able to resize the tv picture and show as backdrop
				self.loadedStillPictureLib = True

			except Exception, ex:
				printl("Exception: " + str(ex), self, "D")
				printl("was not able to import lib for stillpictures", self, "D")

				# we need this as dummy
				self["stillPicture"] = Label()
		else:
			# we need this as dummy
			self["stillPicture"] = Label()

		# on layout finish we have to do some stuff
		self.onLayoutFinish.append(self.setPara)
		self.onLayoutFinish.append(self.processGuiElements)
		self.onLayoutFinish.append(self.finishLayout)
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.getViewListData)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setCustomTitle(self):
		printl("", self, "S")

		self.myTitle = _(self.libraryName)
		self.myTitle = self.myTitle[0].upper() + self.myTitle[1:]
		self.setTitle(_(self.myTitle))

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def setPara(self):
		"""
		set params for poster and backdrop via ePicLoad object
		"""
		printl("", self, "S")

		self.EXscale = (AVSwitch().getFramebufferScale())

		self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
		self.EXpicloadBackdrop.setPara([self["backdrop"].instance.size().width(), self["backdrop"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setListViewElementsCount(self):
		printl("", self, "S")

		self.itemsPerPage = int(self.viewParams["settings"]['itemsPerPage'])

		printl("self.itemsPerPage: " + str(self.itemsPerPage), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getViewListData(self):
		printl("", self, "S")

		# we have to initialize here as well
		self.viewStep = 0
		self.currentEntryDataDict = {}
		self.currentIndexDict = {}
		self.currentTagTypeDict = {}

		self._load()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def bouquetUp(self):
		printl("", self, "S")

		self["shortDescription"].pageUp()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def bouquetDown(self):
		printl("", self, "S")

		self["shortDescription"].pageDown()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyOk(self):
		printl("", self, "S")

		self.onEnter()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyCancel(self):
		printl("", self, "S")

		self.onLeave()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyInfo(self):
		printl("", self, "S")

		self.showMedia = True
		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyMenu(self):
		printl("", self, "S")

		#self.displayOptionsMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyVideo(self):
		printl("", self, "S")

		if self.serverConfig.loadExtraData.value == "1":
			#self.onEnter(loadExtraData=True)
			selection = self["listview"].getCurrent()
			media_id = selection[1]['ratingKey']
			server = selection[1]['server']

			count, options, server = Singleton().getPlexInstance().getMediaOptionsToPlay(media_id, server, False, myType=selection[1]['tagType'], loadExtraData=True)

			self.selectMedia(count, options, server)

		elif self.serverConfig.loadExtraData.value == "2":
			try:
				from Plugins.Extensions.YTTrailer.plugin import YTTrailer
				ytTrailer = YTTrailer(self.session)
				ytTrailer.showTrailer(encodeThat(self.details.get("title", " ")))
			except Exception:
				printl("YTTrailer not found", self, "D")

		printl("", self, "C")

	#===========================================================
	#
	#===========================================================
	def selectMedia(self, count, options, server ):
		printl("", self, "S")

		#if we have two or more extras then present a screen
		self.options = options
		self.server = server
		if not self.options:
			self.session.open(MessageBox,(_("No extras found ...\n\nPress exit to return.")), MessageBox.TYPE_INFO)
		else:
			if count > 1:
				printl("we have more than one playable part ...", self, "I")
				indexCount=0
				functionList = []

				for items in self.options:
					printl("item: " + str(items), self, "D")
					if items[1] is not None:
						name=items[1].split('/')[-1]
						url = items[0]
						ratingKey = items[5]

					printl("name " + str(name), self, "D")
					functionList.append((name ,indexCount, url, ratingKey))
					indexCount+=1

				self.session.openWithCallback(self.setSelectedMedia, ChoiceBox, title=_("Select media to play"), list=functionList)

			else:
				self.setSelectedMedia()

			printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setSelectedMedia(self, choice=None):
		printl("", self, "S")
		printl("choice: " + str(choice), self, "D")

		if choice is not None:
			url = "http://"+ self.server + choice[2]
			ratingKey = choice[3]

			printl("url: " + str(url), self, "D")
			printl("ratingKey: " + str(ratingKey), self, "D")
			isExtraData = ratingKey, url

			listViewList, mediaContainer = self.plexInstance.getMoviesFromSection( "http://"+ self.server +"/library/metadata/" + ratingKey)
			autoPlayMode = False
			resumeMode = False # this is always false because we are in extradata here
			playbackMode = str(1) #because we are a trailer we override to streamed self.serverConfig.playbackType.value
			currentIndex = 0
			libraryName = "Mixed"
			forceResume = False

			self.session.open(DP_Player, listViewList, currentIndex, libraryName, autoPlayMode, resumeMode, playbackMode, forceResume=forceResume, isExtraData=isExtraData)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def myCallback(self, stillPlaying):
		printl("", self, "S")

		if stillPlaying[0]: # Bool
			self.sessionData = stillPlaying[1] # is list with data
			currentIndex = int(self.sessionData[3])
			self["listview"].setIndex(currentIndex)
			self.refresh()

		else:
			self.sessionData = False
			if not config.plugins.dreamplex.stopLiveTvOnStartup.value and self.liveTvInViews:
				self.restoreLiveTv()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyAudio(self):
		printl("", self, "S")

		self.displayAudioMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyText(self):
		printl("", self, "S")

		self.displaySubtitleMenu()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyLeft(self):
		printl("", self, "S")

		self.onPreviousPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRight(self):
		printl("", self, "S")

		self.onNextPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyUp(self):
		printl("", self, "S")

		self.onPreviousEntry()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyDown(self):
		printl("", self, "S")

		self.onNextEntry()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRed(self):
		printl("", self, "S")

		func = self.getColorFunction("red", self.currentFunctionLevel)
		if func:
			func()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initColorFunctions(self):
		printl("", self, "S")

		self.setColorFunction(color="red", level="1", functionList=("", self.togglePlayMode))
		self.setColorFunction(color="green", level="1", functionList=("", self.toggleResumeMode))
		self.setColorFunction(color="yellow", level="1", functionList=("", self.executeLibraryFunction)) # name is empty because we set it dynamical
		self.setColorFunction(color="blue", level="1", functionList=(_("playback mode '" + self.playbackModes[self.configuredPlaybackMode][1] + "'"), self.togglePlaybackMode))

		self.setColorFunction(color="red", level="2", functionList=(_("View '") + str(self.currentViewName) + " '", self.onToggleView))
		self.setColorFunction(color="green", level="2", functionList=("", self.toggleFastScroll)) # name is empty because we set it dynamical
		self.setColorFunction(color="yellow", level="2", functionList=("refresh Library", self.initiateRefresh))
		self.setColorFunction(color="blue", level="2", functionList=(_("show 'Details'"), self.toggleDetails))

		self.setColorFunction(color="red", level="3", functionList=("Server Settings", self.showServerSettings))
		self.setColorFunction(color="green", level="3", functionList=("Plex Settings", self.showGeneralSettings))
		self.setColorFunction(color="yellow", level="3", functionList=(_("delete Medias"), self.deleteMedias))
		self.setColorFunction(color="blue", level="3", functionList=(_("use for Mapping"), self.useForMappingHelper))

		self.setColorFunction(color="red", level="4", functionList=("", self.toggleFilterMode)) # name is empty because we set it dynamical
		self.setColorFunction(color="green", level="4", functionList=None)
		self.setColorFunction(color="yellow", level="4", functionList=None)
		self.setColorFunction(color="blue", level="4", functionList=None)

		self.alterColorFunctionNames(level="1")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def deleteMedias(self):
		printl("", self, "S")
		from os import remove

		remove(self.whatPoster)
		remove(self.whatBackdrop)

		text = "Successfully removed images!"
		self.session.open(MessageBox,_("\n%s") % text, MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def useForMappingHelper(self):
		printl("", self, "S")
		import string
		from DP_Mappings import DPS_MappingsEntryList

		isWindowsLocation = False
		remotePath = self["file"].getText()

		if "\\" in remotePath:
			isWindowsLocation = True
			remotePath = remotePath.replace("\\", "/")

		pathElements = string.split(remotePath, "/")
		fileName = pathElements[-1]

		# search for the file on the box
		localPath = self.searchForLocalFile(fileName)

		if localPath is not None:
			printl("remotePath: " + str(remotePath), self, "D")
			printl("localPath: " + str(localPath), self, "D")

			# first we remove the filename itself
			currentRemotePath, currentLocalPath, reductionSuccessState = self.reduceMappings(remotePath, localPath, fileName)

			# now we reduce the identical folders
			while reductionSuccessState:
				pathElements = string.split(currentRemotePath, "/")
				currentLimiter = pathElements[-2] # [-1] would lead to " " empty limiter due to the fact that there is a / at the end
				printl("pathElements: " + str(pathElements), self, "D")
				currentRemotePath, currentLocalPath, reductionSuccessState = self.reduceMappings(currentRemotePath, currentLocalPath, currentLimiter)

			# finally
			if isWindowsLocation:
				currentRemotePath = currentRemotePath.replace("/", "\\")

			printl("currentRemotePath: " + str(currentRemotePath), self, "D")
			printl("currentLocalPath: " + str(currentLocalPath), self, "D")

			serverID = self.serverConfig.id.value
			printl("serverID: " + str(serverID), self, "D")

			self.location = config.plugins.dreamplex.configfolderpath.value + "mountMappings"
			checkXmlFile(self.location)
			tree = getXmlContent(self.location)

			isUnique = self.checkForDuplicateMapping(serverID, tree, currentRemotePath, currentLocalPath)

			if isUnique:
				mappingsObject = DPS_MappingsEntryList([], serverID, tree)
				mappingsObject.addNewMapping(currentRemotePath, currentLocalPath)
				text = "Mapping added successfully.\n\nRemotePath: " + str(currentRemotePath) + "\nLocalPath: " + str(currentLocalPath)
			else:
				text = "Duplicate mapping detected.\n\nRemotePath: " + str(currentRemotePath) + "\nLocalPath: " + str(currentLocalPath) + "\n\nWe are not saving this!"
		else:
			# we did not found the file on the box
			text = "Couldn't find the file on your box.\n\nPlease check if the mount in /mnt/net/ is working!"

		self.session.open(MessageBox,_("\n%s") % text, MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkForDuplicateMapping(self, serverID, tree, currentRemotePath, currentLocalPath):
		printl("", self, "S")
		isUnique = True

		printl("serverID: " + str(serverID), self, "D")
		for server in tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(serverID):

				for mapping in server.findall('mapping'):
					remotePathPart = mapping.attrib.get("remotePathPart")
					localPathPart = mapping.attrib.get("localPathPart")

					if remotePathPart == currentRemotePath and localPathPart == currentLocalPath:
						isUnique = False

		printl("", self, "C")
		return isUnique
	#===========================================================================
	#
	#===========================================================================
	def reduceMappings(self, currentRemotePath, currentLocalPath, currentLimiter):
		printl("", self, "S")
		printl("currentRemotePath: " + str(currentRemotePath), self, "D")
		printl("currentLocalPath: " + str(currentLocalPath), self, "D")
		printl("currentLimiter: " + str(currentLimiter), self, "D")

		localPathIndex = str(currentLocalPath).find(str(currentLimiter))
		remotePathIndex = str(currentRemotePath).find(str(currentLimiter))

		printl("localPathIndex: " + str(localPathIndex), self, "D")
		printl("remotePathIndex: " + str(remotePathIndex), self, "D")

		if localPathIndex != -1 and remotePathIndex != -1 and localPathIndex != 0 and remotePathIndex != 0:
			remotePathResult = str(currentRemotePath)[0:remotePathIndex]
			localPathResult = str(currentLocalPath)[0:localPathIndex]

			printl("remotePathResult: " + str(remotePathResult), self, "D")
			printl("localPathResult: " + str(localPathResult), self, "D")
			reductionSuccessState = True
		else:
			reductionSuccessState = False
			remotePathResult = currentRemotePath
			localPathResult = currentLocalPath

		printl("", self, "C")
		return remotePathResult, localPathResult, reductionSuccessState

	#===========================================================================
	#
	#===========================================================================
	def searchForLocalFile(self, fileName):
		printl("", self, "S")
		import os

		for root, dirs, files in os.walk("/hdd", topdown=False):
			for currentFile in files:
				if currentFile == fileName:
					localPath = os.path.join(root, currentFile)
					return localPath

		#if we find nothing we return nothing
		printl("", self, "C")
		return None

	#===========================================================================
	#
	#===========================================================================
	def initPlayMode(self):
		printl("", self, "S")

		color = "red"

		if self.autoPlayMode:
			self["btn_"+ color + "Text"].setText(_("playmode 'multi'"))
		else:
			self["btn_"+ color + "Text"].setText(_("playmode 'single'"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def togglePlayMode(self):
		printl("", self, "S")
		color = "red"

		if self.autoPlayMode:
			self.autoPlayMode = False
			self["btn_"+ color + "Text"].setText(_("playmode 'single'"))
		else:
			self.autoPlayMode = True
			self["btn_"+ color + "Text"].setText(_("playmode 'multi'"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initResumeMode(self):
		printl("", self, "S")

		color = "green"

		if self.resumeMode:
			self["btn_"+ color + "Text"].setText(_("resume 'On'"))
		else:
			self["btn_"+ color + "Text"].setText(_("resume 'Off'"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleResumeMode(self):
		printl("", self, "S")
		color = "green"

		if self.resumeMode:
			self.resumeMode = False
			self["btn_"+ color + "Text"].setText(_("resume 'Off'"))
		else:
			self.resumeMode = True
			self["btn_"+ color + "Text"].setText(_("resume 'On'"))

		# we have to reset here to force changes on the screen that are fastscroll related
		self.lastTagType = None

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initFastScroll(self):
		printl("", self, "S")

		color = "green"
		if self.fastScroll:
			self["btn_"+ color + "Text"].setText(_("fastScroll 'On'"))
		else:
			self["btn_"+ color + "Text"].setText(_("fastScroll 'Off'"))
			self["info"].hide()
			self["infoLabel"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleFastScroll(self):
		printl("", self, "S")

		color = "green"

		if self.fastScroll:
			self.fastScroll = False
			self["btn_" + color + "Text"].setText("fastScroll 'Off'")
			self["info"].hide()
			self["infoLabel"].hide()
		else:
			self.fastScroll = True
			self["btn_" + color + "Text"].setText("fastScroll 'On'")
			self["info"].show()
			self["infoLabel"].show()
			self["miniTv"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showServerSettings(self):
		printl("", self, "S")

		printl("", self, "C")
		self.session.open(DPS_Server)

	#===========================================================================
	#
	#===========================================================================
	def initPlaybackMode(self):
		printl("", self, "S")

		self.playbackModes = [("0", _("Streamed")),("1", _("Transcoded")), ("2", _("Direct Local"))]
		self.configuredPlaybackMode = int(self.serverConfig.playbackType.value)
		self.nextPlaybackMode = self.configuredPlaybackMode
		self.lengthOfPlaybackModes = len(self.playbackModes)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def togglePlaybackMode(self):
		printl("", self, "S")

		color = "blue"

		self.nextPlaybackMode += 1

		if self.nextPlaybackMode >= self.lengthOfPlaybackModes:
			self.nextPlaybackMode = 0

		myName = self.playbackModes[self.nextPlaybackMode][1]

		self.playbackMode = self.nextPlaybackMode

		self["btn_" + color + "Text"].setText("playback mode '" + myName + "'")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initFilterMode(self):
		printl("", self, "S")
		color = "red"

		self.filterMode = True
		self["L1"].hide()
		self["L2"].hide()
		self["L3"].hide()

		self["btn_"+ color + "Text"].setText(_("turn filter mode off"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleFilterMode(self, quit=False):
		printl("", self, "S")

		if self.filterMode or quit:
			self.filterMode = False
			if self.keyOneDisabled:
				self.onKey2()
			else:
				self.onKey1() # we return to normal functions
				self["L1"].show()

			self["L2"].show()
			self["L3"].show()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showGeneralSettings(self):
		printl("", self, "S")

		printl("", self, "C")
		self.session.open(DPS_Settings)

	#===========================================================================
	#
	#===========================================================================
	def executeLibraryFunction(self):
		printl("", self, "S")

		if self.seen:
			self.markUnwatched()
		else:
			self.markWatched()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyRedLong(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyYellow(self):
		printl("", self, "S")

		func = self.getColorFunction("yellow", self.currentFunctionLevel)
		if func:
			func()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyYellowLong(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyBlue(self):
		printl("", self, "S")

		func = self.getColorFunction("blue", self.currentFunctionLevel)
		if func:
			func()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyGreen(self):
		printl("", self, "S")

		func = self.getColorFunction("green", self.currentFunctionLevel)
		if func:
			func()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey1(self, initial=False):
		printl("", self, "S")

		if not self.filterMode:
			if not self.keyOneDisabled:
				self.setLevelActive(currentLevel="1")
				self.alterColorFunctionNames(level="1")

				if not initial:
					self.refreshFunctionName()

				self.lastTagType = None

		else:
			self.onNumberKey(1)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey2(self):
		printl("", self, "S")

		if not self.filterMode:
			self.setLevelActive(currentLevel="2")
			self.alterColorFunctionNames(level="2")

			self.initFastScroll()

		else:
			self.onNumberKey(2)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey3(self):
		printl("", self, "S")

		if not self.filterMode:
			self.setLevelActive(currentLevel="3")
			self.alterColorFunctionNames(level="3")

		else:
			self.onNumberKey(3)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey4(self):
		printl("", self, "S")

		if not self.filterMode:
			self.setLevelActive(currentLevel="4")
			self.alterColorFunctionNames(level="4")

			self.initFilterMode()

		else:
			self.onNumberKey(4)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey5(self):
		printl("", self, "S")

		if not self.filterMode:
			pass

		else:
			self.onNumberKey(5)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey6(self):
		printl("", self, "S")

		if not self.filterMode:
			pass

		else:
			self.onNumberKey(6)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey7(self):
		printl("", self, "S")
		if not self.filterMode:
			pass

		else:
			self.onNumberKey(7)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey8(self):
		printl("", self, "S")
		if not self.filterMode:
			pass

		else:
			self.onNumberKey(8)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey9(self):
		printl("", self, "S")
		if not self.filterMode:
			pass

		else:
			self.onNumberKey(9)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey0(self):
		printl("", self, "S")
		if not self.filterMode:
			pass

		else:
			self.onNumberKey(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKeyBlueLong(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onToggleView(self):
		printl("", self, "S")

		if config.plugins.dreamplex.useBackdropVideos.value and self.loadedStillPictureLib:
			self.stopBackdropVideo()
		cause = (DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW, )
		self.leaveNow(cause)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNextEntry(self):
		printl("", self, "S")

		# reset subtitlesList
		self.subtitlesList = None

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onPreviousEntry(self):
		printl("", self, "S")

		# reset subtitlesList
		self.subtitlesList = None

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNextPage(self):
		printl("", self, "S")
		itemsTotal = self["listview"].count()
		index = self["listview"].getIndex()

		if index >= itemsTotal:
			index = itemsTotal - 1
		self["listview"].setIndex(index)

		# reset subtitlesList
		self.subtitlesList = None

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onPreviousPage(self):
		printl("", self, "S")
		index = self["listview"].getIndex()

		if index < 0:
			index = 0
		self["listview"].setIndex(index)

		# reset subtitlesList
		self.subtitlesList = None

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onEnter(self):
		printl("", self, "S")
		self.lastTagType = None

		selection = self["listview"].getCurrent()

		# we turn off here to avoid mixed functions
		self.toggleFilterMode(quit=True)

		if selection is not None:
			entryData		= selection[1]
			#context		= selection[2]
			nextContentUrl = selection[4]

			# we extend details for provide the next data location
			entryData["contentUrl"] = nextContentUrl

			self.currentViewMode	= entryData['currentViewMode']
			printl("currentViewMode: " + str(self.currentViewMode), self, "D")

			# we need this for onEnter-func in child lib

			if entryData['tagType'] == "Track" or entryData['tagType'] == "Video":
				if config.plugins.dreamplex.useBackdropVideos.value and self.loadedStillPictureLib:
					self.stopBackdropVideo()

				currentIndex = self["listview"].getIndex()

				if self.sessionData and str(self.sessionData[2]) == str(self.listViewList[int(currentIndex)][1]['ratingKey']):
					self.session.openWithCallback(self.myCallback, DP_Player, self.listViewList, currentIndex, self.libraryName, self.autoPlayMode, self.resumeMode, self.playbackMode, sessionData=self.sessionData)
				else:
					if self.serverConfig.useForcedSubtitles.value and self.serverConfig.playbackType.value == "2":
						self.subtitleData = Singleton().getPlexInstance().getSelectedSubtitleDataById(entryData["server"], entryData["ratingKey"])

					self.session.openWithCallback(self.myCallback, DP_Player, self.listViewList, currentIndex, self.libraryName, self.autoPlayMode, self.resumeMode, self.playbackMode, subtitleData=self.subtitleData)

			else:
				# save index here because user moved around for sure
				self.currentIndexDict[self.viewStep] = self["listview"].getIndex()

				self.viewStep += 1
				self._load(entryData)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleDetails(self):
		printl("", self, "S")

		if self.detailsPaneVisible:
			self.hideDetails()
		else:
			self.showDetails()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def hideDetails(self):
		printl("", self, "S")

		color = "blue"

		self.detailsPaneVisible = False
		self["shortDescription"].show()
		self["btn_" + color + "Text"].setText(_("show 'Details'"))

		self.toggleElementVisibilityWithLabel("videoCodec", "hide")
		self.toggleElementVisibilityWithLabel("bitrate", "hide")
		self.toggleElementVisibilityWithLabel("videoFrameRate", "hide")
		self.toggleElementVisibilityWithLabel("audioChannels", "hide")
		self.toggleElementVisibilityWithLabel("aspectRatio", "hide")
		self.toggleElementVisibilityWithLabel("videoResolution", "hide")
		self.toggleElementVisibilityWithLabel("audioCodec", "hide")
		self.toggleElementVisibilityWithLabel("file", "hide")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showDetails(self):
		printl("", self, "S")

		color = "blue"

		self.detailsPaneVisible = True
		self["shortDescription"].hide()
		self["btn_"  + color + "Text"].setText(_("show 'Description'"))

		self.toggleElementVisibilityWithLabel("videoCodec")
		self.toggleElementVisibilityWithLabel("bitrate")
		self.toggleElementVisibilityWithLabel("videoFrameRate")
		self.toggleElementVisibilityWithLabel("audioChannels")
		self.toggleElementVisibilityWithLabel("aspectRatio")
		self.toggleElementVisibilityWithLabel("videoResolution")
		self.toggleElementVisibilityWithLabel("audioCodec")
		self.toggleElementVisibilityWithLabel("file")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def toggleElementVisibilityWithLabel(self, elementName, action="show"):

		if action == "show":
			self[elementName].show()
			self[elementName+ "Label"].show()
		elif action == "hide":
			self[elementName].hide()
			self[elementName+ "Label"].hide()

	#===========================================================================
	#
	#===========================================================================
	def onLeave(self):
		printl("", self, "S")

		# first decrease by one
		self.viewStep -= 1

		printl("returnTo: " + str(self.returnTo), self, "D")

		if self.detailsPaneVisible:
			self.hideDetails()

		if config.plugins.dreamplex.playTheme.value:
			printl("stoping theme playback", self, "D")
			if self.themeMusicIsRunning:
				self.session.nav.stopService()

		if self.viewStep >= 0:
			self["listview"].setList(self.currentEntryDataDict[self.viewStep])
			self["listview"].setIndex(self.currentIndexDict[self.viewStep])

			if self.filterMode:
				self.toggleFilterMode(quit=True)

			self.selection = self["listview"].getCurrent()
			if self.selection is not None:
				self.details 	= self.selection[1]
				self.context	= self.selection[2]

			if self.viewStep >= 1:
				self.leaving = False
			else:
				self.leaving = True
		else:
			self.leaveNow()

		printl("", self, "C")

	#===========================================================================
	# cause is used e.g. toggle view
	#===========================================================================
	def leaveNow(self, cause=None):
		printl("", self, "S")

		if self.loadedStillPictureLib:
			self.stopBackdropVideo()

		# this seems to be uneeded
		# if not config.plugins.dreamplex.stopLiveTvOnStartup.value and cause is None:
		# 	self.restoreLiveTv()

		if cause is not None:
			printl("", self, "C")
			self.close(cause)
		else:
			printl("", self, "C")
			self.close()

	#===========================================================================
	#
	#===========================================================================
	def _load(self, entryData = None):
		printl("", self, "S")
		printl("entryData: " + str(entryData), self, "D")

		# loadLibrary is a function in each class that inherits from DP_LibMain (DP_LibMovies, DP_LibSHows, DP_LibMusic)
		libraryDataArr = self.loadLibrary(entryData, self.forceUpdate)
		self.forceUpdate=False

		# this is the content for the list (must be tuple no dict)
		self.libraryData = libraryDataArr[0]

		# enable this only if you realy need the information for debuging
		#printl("libraryData: " + str(self.libraryData), self, "D")

		# we need to do this because since we save cache via pickle the seen pic object cant be saved anymore
		self.listViewList = self.alterViewStateInList(self.libraryData)
		self.beforeFilterListViewList = self.listViewList

		# mediaContainer on top of xml
		self.mediaContainer = libraryDataArr[1]
		printl("mediaContainer: " + str(self.mediaContainer), self, "D")

		# we save the list to be able to restore
		self.currentEntryDataDict[self.viewStep] = self.listViewList

		# now just refresh list
		self.updateList()

		# now refresh
		self.refresh()

		# check in settings
		if self.startWithFilterMode and self.filterableContent:
			self.onKey4()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def alterViewStateInList(self, listViewList):
		printl("", self, "S")
		#printl("listViewList: " + str(listViewList), self, "S")
		newList = []
		undefinedIcon = loadPicture('/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/default/images/picreset.png')

		for listViewEntry in listViewList:
			viewState = str(listViewEntry[3])

			if listViewEntry is not None:
				#printl("seenVisu location: " + str(listViewEntry[3]), self, "D")
				if viewState == 'seen':
					viewState = self.seenPic

				elif viewState == 'started':
					viewState = self.startedPic

				elif viewState == 'unseen':
					viewState = self.unseenPic

				else:
					viewState = undefinedIcon

			content = (listViewEntry[0], listViewEntry[1], listViewEntry[2], viewState ,listViewEntry[4])
			newList.append(content)

		printl("", self, "C")
		return newList

	#===========================================================================
	#
	#===========================================================================
	def updateList(self, myIndex=None):
		printl("", self, "S")

		self["listview"].setList(self.listViewList)
		if myIndex is not None:
			self["listview"].setIndex(myIndex)
		else:
			self["listview"].setIndex(0)

		# now we set the currentViewMode to be able to alter skin elements according to their settings in the params file
		self.selection = self["listview"].getCurrent()

		# none is possible if there is no data in the section
		if self.selection is not None:
			self.currentViewMode = self.selection[1]["currentViewMode"]
			printl("currentViewMode: " + str(self.currentViewMode), self, "D")
			self.processSubViewElements(myType=self.currentViewMode)
		else:
			text = "You have no data in this section!"
			self.session.open(MessageBox,_("\n%s") % text, MessageBox.TYPE_INFO)
			self.leaveNow()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def refresh(self):
		printl("", self, "S")

		# todo we can make this as option if the new boxes have enough power to cicle through the list and showing backdrops as well fast
		# we kill a former timer to start a new one
		if self.refreshTimer is not None:
			self.refreshTimer.stop()

		# show content for selected list item
		self.selection = self["listview"].getCurrent()

		if self.selection is not None:
			printl("selection: " + str(self.selection), self, "D")
			self.tagType = self.selection[1]['tagType']
			self.type = self.selection[1]['type']

			# we are a real folder on os level
			if self.type == "Folder":
				self.isFolder = True
				if self.currentFunctionLevel == "2":
					self.hideRefreshFunction()
			else:
				self.isFolder = False
				if self.currentFunctionLevel == "2":
					self.showRefreshFunction()
			printl("isFolder: " + str(self.isFolder), self, "D")

			# we are a xml directory tag
			if self.tagType != "Directory":
				self.handleViewStateInformation()

		printl("fastScroll: " + str(self.fastScroll), self, "D")
		printl("self.viewParams: " + str(self.viewParams), self, "D")

		printl("showMedia: " + str(self.showMedia), self, "D")

		if self.selection is not None:
			self.details 	= self.selection[1]
			self.context	= self.selection[2]

			# navigation
			self.handleNavigationData()

			if not self.isFolder:
				# if we are in fastScrollMode we have to reset some screen elements
				if self.fastScroll:
					self.resetGuiElementsInFastScrollMode()
				else:
					self.initFastScroll()

				# to avoid unneeded skin changes we check here if the type is equal to the last one
				if self.tagType != self.lastTagType:
					# if we were are no folder anymore we switch back
					self.unsetFromDirectoryMode()
					if self.tagType == "Track" or self.tagType == "Video":
						self.showMediaFunctions()

				# now we go with the type related stuff like movie, music, etc.
				self._refresh()

			else:
				self.changeBackdrop = False

				# to avoid unneeded skin changes we check here if the type is equal to the last one
				if self.tagType != self.lastTagType:
					self.changePoster = True
					self.resetPoster = True
				else:
					self.changePoster = False
					self.resetPoster = False

				# if we are a folder within a specific library we switch to folder mode
				self.setToDirectoryMode()

			# we save this to avoid extensive unnessary skin changes
			self.lastTagType = self.tagType

			# depending on the settings in params we reset all images that are needed to
			self.resetCurrentImages()

			# supress changing backdrop if we want liveTv in views via settings
			if self.liveTvInViews:
				self.changeBackdrop = False

			# now go for it
			self.handlePictures()

		else:
			self["title"].setText( "no data retrieved")
			self["shortDescription"].setText("no data retrieved")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleViewStateInformation(self):
		printl("", self, "S")

		self.seen = False
		if "viewCount" in self.selection[1]:
			if "viewCount" > 0:
				self.seen = True

		if self.currentFunctionLevel == "1":
			self.refreshFunctionName()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def refreshFunctionName(self, noInit=False):
		printl("", self, "S")

		color = "yellow"

		if self.seen:
			viewStateName = "set 'Unseen'"
		else:
			viewStateName = "set 'Seen'"

		if not noInit:
			self.initPlayMode()
			self.initResumeMode()

		self["btn_"+ color + "Text"].setText(viewStateName)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def _refresh(self):
		printl("", self, "S")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setDuration(self):
		printl("", self, "S")

		duration = str(self.details.get("duration", " - "))

		if duration == " - ":
			self["duration"].setText(duration)
		else:
			self["duration"].setText(durationToTime(duration))

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setMediaFunctions(self):
		printl("", self, "S")

		if self.context is not None:
			# lets set the urls for context functions of the selected entry
			self.seenUrl = self.context.get("watchedURL", None)
			self.unseenUrl = self.context.get("unwatchURL", None)
			self.deleteUrl = self.context.get("deleteURL", None)
			self.refreshUrl = self.context.get("libraryRefreshURL", None)
			printl("seenUrl: " + str(self.seenUrl),self, "D")
			printl("unseenUrl: " + str(self.unseenUrl),self, "D")
			printl("deleteUrl: " + str(self.deleteUrl),self, "D")
			printl("refreshUrl: " + str(self.refreshUrl),self, "D")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def unsetFromDirectoryMode(self):
		printl("", self, "S")

		# we need those for fastScroll
		# this prevents backdrop load on next item
		self.showMedia = False
		self.changeBackdrop = True

		self["backdrop"].show()

		if self.miniTvInUse:
			self["miniTv"].show()
		if self.lastTagType == "Directory":
			self.toggleElementVisibilityWithLabel("audio")
			self.toggleElementVisibilityWithLabel("subtitles")
			self.toggleElementVisibilityWithLabel("genre")
			self.toggleElementVisibilityWithLabel("duration")
			self.toggleElementVisibilityWithLabel("year")

		printl("", self, "C")
	#===============================================================================
	#
	#===============================================================================
	def setToDirectoryMode(self):
		printl("", self, "S")

		if self.tagType != self.lastTagType or self.tagType is None:
			for element in self.noneDirectoryElementsList:
				try:
					self.toggleElementVisibilityWithLabel(element, "hide")
				except: pass

			self.hideMediaFunctions()
			self.hideMediaPixmaps()

			if self.miniTvInUse:
				self["miniTv"].hide()

		self["title"].setText("Directory")
		self["tag"].setText("Name:")
		self["shortDescription"].setText(self.details.get("title", " ").encode('utf-8'))

		self.whatPoster = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skin.value + "/all/folder-fs8.png"
		self["poster"].show()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def showVideoDetails(self):
		printl("", self, "S")

		self.toggleElementVisibilityWithLabel("writer")
		self.toggleElementVisibilityWithLabel("director")
		self.toggleElementVisibilityWithLabel("cast")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def hideVideoDetails(self):
		printl("", self, "S")

		self.toggleElementVisibilityWithLabel("writer", "hide")
		self.toggleElementVisibilityWithLabel("director", "hide")
		self.toggleElementVisibilityWithLabel("cast", "hide")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def hideRefreshFunction(self):
		printl("", self, "S")

		self["btn_yellow"].hide()
		self["btn_yellowText"].hide()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def showRefreshFunction(self):
		printl("", self, "S")

		self["btn_yellow"].show()
		self["btn_yellowText"].show()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def hideMediaPixmaps(self):
		printl("", self, "S")

		self["rating_stars"].hide()
		self["codec"].hide()
		self["aspect"].hide()
		self["resolution"].hide()
		self["rated"].hide()
		self["sound"].hide()
		self["soundchannels"].hide()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def handlePictures(self):
		printl("", self, "S")

		# now lets switch images
		if self.changePoster:
			self.showPoster()

		if not self.fastScroll or self.showMedia:
			if self.changeBackdrop:
				# check if showiframe lib loaded ...
				if self.loadedStillPictureLib and "ratingKey" in self.details:
					printl("self.loadedStillPictureLib: " + str(self.loadedStillPictureLib), self, "D")

					#first we need to remove the file extension
					myFileWoExtension = self.whatBackdrop

					# now add the m1v file extension
					self.whatBackdrop = myFileWoExtension + ".m1v"

					# we used this code earlier. but this leads to no m1v usage in shows
					# todo after tests remove this
					# backdrop = config.plugins.dreamplex.mediafolderpath.value + str(self.image_prefix) + "_" + str(self.details["ratingKey"]) + "_backdrop_1280x720_v2.m1v"
					printl("backdrop: " + str(self.whatBackdrop), self, "D")

					# check if the backdrop m1v exists
					if os.access(self.whatBackdrop, os.F_OK):
						printl("yes", self, "D")
						self["miniTv"].show()
						self["stillPicture"].setStillPicture(self.whatBackdrop)
						self["backdrop"].hide()
						self.usedStillPicture = True
					else:
						printl("no", self, "D")
						self["miniTv"].hide()
						self["backdrop"].show()

						self["stillPicture"].finishStillPicture()

						# if not handle as normal backdrop
						self.handleBackdrop()

				else:
					# if not handle as normal backdrop
					self.handleBackdrop()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def hideMediaFunctions(self):
		printl("", self, "S")

		self["btn_red"].hide()
		self["btn_redText"].hide()
		self["btn_yellow"].hide()
		self["btn_yellowText"].hide()
		self["btn_blue"].hide()
		self["btn_blueText"].hide()
		self["btn_green"].hide()
		self["btn_greenText"].hide()

		self.keyOneDisabled = True
		if not self.filterMode:
			self.onKey2()
		self["L1"].hide()
		#self["L2"].hide()
		#self["L3"].hide()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def showMediaFunctions(self):
		printl("", self, "S")

		self["btn_red"].show()
		self["btn_redText"].show()
		self["btn_yellow"].show()
		self["btn_yellowText"].show()
		self["btn_blue"].show()
		self["btn_blueText"].show()
		self["btn_green"].show()
		self["btn_greenText"].show()

		self.keyOneDisabled = False
		if not self.filterMode:
			self.onKey1()
			self["L1"].show()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def handleBackdrop(self):
		printl("", self, "S")

		self.usedStillPicture = False

		printl("showing backdrop with timeout ...", self, "D")
		# we use this to give enough time to jump through the list before we start encoding pics and reading all the data that have to be switched = SPEEDUP :-)
		self.refreshTimer = eTimer()

		if getOeVersion() != "oe22":
			self.refreshTimer.callback.append(self.showBackdrop)
		else:
			self.refreshTimerConn = self.refreshTimer.timeout.connect(self.showBackdrop)

		self.refreshTimer.start(500, True)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleNavigationData(self):
		printl("", self, "S")

		itemsPerPage = self.itemsPerPage
		itemsTotal = self["listview"].count()
		correctionVal = 0.5

		if (itemsTotal%itemsPerPage) == 0:
			correctionVal = 0

		pageTotal = int(math.ceil((itemsTotal / itemsPerPage) + correctionVal))
		pageCurrent = int(math.ceil((self["listview"].getIndex() / itemsPerPage) + 0.5))

		self["total"].setText(_(str(itemsTotal)))
		self["pagination"].setText(_(str(pageCurrent) + "/" + str(pageTotal)))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenu(self):
		printl("", self, "S")

		functionList = []

		functionList.append((_("Mark media unwatched"), Plugin("View", fnc = self.markUnwatched), ))
		functionList.append((_("Mark media watched"), Plugin("View", fnc = self.markWatched), ))
		functionList.append((_("Initiate Library refresh"), Plugin("View", fnc = self.initiateRefresh), ))
		#functionList.append((_("Delete media from Library"), Plugin("View", fnc=self.deleteFromLibrary), ))

		self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, title=_("Media Functions"), list=functionList)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayOptionsMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			printl("choice: None - we pressed exit", self, "D")
			return

		printl("choice: " + str(choice[1]), self, "D")

		if choice[1].fnc:
			printl("5", self, "D")
			choice[1].fnc()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getSubtitleList(self):
		printl("", self, "S")

		if self.subtitlesList is None:
			selection = self["listview"].getCurrent()

			self.media_id = selection[1]['ratingKey']
			self.server = selection[1]['server']

			self.subtitlesList = Singleton().getPlexInstance().getSubtitlesById(self.server, self.media_id)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displaySubtitleMenu(self):
		printl("", self, "S")

		self.getSubtitleList()

		functionList = []


		for item in self.subtitlesList:
			languageText = item.get('language').encode("utf-8", "")
			myFormat = item.get("myFormat", None)
			if myFormat:
				formatText = " (" + myFormat + ")"
			else:
				formatText = ""

			forced = item['forced']
			if forced:
				forcedText = " forced"
			else:
				forcedText = ""

			selected = item.get('selected', None)
			if selected:
				enabledText = " => enabled"
			else:
				enabledText = ""

			name = languageText + formatText + forcedText + enabledText

			sub_id = item.get('id', "")
			languageCode = item.get('languageCode', "")
			part_id = item.get('partid', "")

			functionList.append((name, self.media_id, languageCode, sub_id, self.server, part_id, selected))

		selection = 0
		for i in range(len(functionList)):
			if functionList[i][6] == "1":
				selection = i
				break

		self.session.openWithCallback(self.displaySubtitleMenuCallback, ChoiceBox, title=_("Subtitle Functions\n\nPlease take note that switching the subtitles here will take only effect if you use direct local or transcoding!"), list=functionList,selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def displayAudioMenu(self):
		printl("", self, "S")

		selection = self["listview"].getCurrent()

		media_id = selection[1]['ratingKey']
		server = selection[1]['server']

		functionList = []

		audioList = Singleton().getPlexInstance().getAudioById(server, media_id)

		for item in audioList:

			selected = item.get('selected', "")
			if selected == "1":
				name = item.get('language').encode("utf-8", "") + " [Currently Enabled]"
			else:
				name = item.get('language').encode("utf-8", "")

			stream_id = item.get('id', "")
			languageCode = item.get('languageCode', "")
			part_id = item.get('partid', "")

			functionList.append((name, media_id, languageCode, stream_id, server, part_id, selected))

		selection = 0
		for i in range(len(functionList)):
			if functionList[i][6] == "1":
				selection = i
				break

		self.session.openWithCallback(self.displayAudioMenuCallback, ChoiceBox, title=_("Audio Functions\n\nPlease take note that switching the language here will take only effect if you enable transcoding!"), list=functionList,selection=selection)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def markUnwatched(self):
		printl("", self, "S")
		self.forceUpdate = True

		Singleton().getPlexInstance().doRequest(self.unseenUrl)

		currentIndex = self["listview"].getIndex()
		currentSelection = self["listview"].getCurrent()
		myList = list(currentSelection)
		myList[3] = self.unseenPic
		myList[1]["viewCount"] = 0
		self["listview"].modifyEntry(currentIndex, tuple(myList))

		self.seen = False

		self.refreshFunctionName(noInit=True)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def markWatched(self):
		printl("", self, "S")
		self.forceUpdate = True

		Singleton().getPlexInstance().doRequest(self.seenUrl)

		currentIndex = self["listview"].getIndex()
		currentSelection = self["listview"].getCurrent()
		myList = list(currentSelection)
		myList[3] = self.seenPic
		myList[1]["viewCount"] = 1
		self["listview"].modifyEntry(currentIndex, tuple(myList))

		self.seen = True

		self.refreshFunctionName(noInit=True)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def initiateRefresh(self):
		printl("", self, "S")
		self.forceUpdate = True

		if not self.isFolder:
			Singleton().getPlexInstance().doRequest(self.refreshUrl)
			self.getViewListData()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def deleteFromLibrary(self):
		printl("", self, "S")

		self.session.openWithCallback(self.executeLibraryDelete, MessageBox, _("Are you sure?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def executeLibraryDelete(self, confirm):
		printl("", self, "S")

		if confirm:
			Singleton().getPlexInstance().doRequest(self.deleteUrl)
			self.getViewListData()
		else:
			self.session.open(MessageBox,_("Deleting aborted!"), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	# choice = name, media_id, languageCode, stream_id, server, part_id, selected
	#===========================================================================
	def displayAudioMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		printl("choice" + str(choice), self, "D")

		Singleton().getPlexInstance().setAudioById(choice[4], choice[3], choice[5])

		printl("", self, "C")

	#===========================================================================
	# choice = name, media_id, languageCode, stream_id, server, part_id, selected
	#===========================================================================
	def displaySubtitleMenuCallback(self, choice):
		printl("", self, "S")

		if choice is None or choice[1] is None:
			return

		printl("choice" + str(choice), self, "D")

		Singleton().getPlexInstance().setSubtitleById(choice[4], choice[3], choice[5])

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startThemePlayback(self):
		printl("", self, "S")

		if self.lastPlayedTheme != self.details["theme"]:
			printl("start pĺaying theme", self, "D")
			theme = self.details["theme"]
			server = self.details["server"]
			accessToken = Singleton().getPlexInstance().get_aTokenForServer(server)
			printl("theme: " + str(theme), self, "D")
			url = "http://" + str(server) + str(theme) + str(accessToken)
			sref = "4097:0:0:0:0:0:0:0:0:0:%s" % quote_plus(url)
			printl("sref: " + str(sref), self, "D")
			self.session.nav.stopService()
			self.session.nav.playService(eServiceReference(sref))
			self.themeMusicIsRunning = True
			self.lastPlayedTheme = self.details["theme"]
		else:
			printl("not starting theme for the same show again", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showPoster(self, forceShow = False):
		printl("", self, "S")

		if forceShow:
			if self.whatPoster is not None:
				if getOeVersion() != "oe22":
					self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
				else:
					self.EXpicloadPoster.startDecode(self.whatPoster,False)

				ptr = self.EXpicloadPoster.getData()

				if ptr is not None:
					self["poster"].instance.setPixmap(ptr)

		elif self.usePicCache:
			if fileExists(self.whatPoster):

				if self.whatPoster is not None:
					if getOeVersion() != "oe22":
						self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
					else:
						self.EXpicloadPoster.startDecode(self.whatPoster,False)

					ptr = self.EXpicloadPoster.getData()

					if ptr is not None:
						self["poster"].instance.setPixmap(ptr)

			else:
				self.downloadPoster()
		else:
			self.downloadPoster()

		printl("", self, "C")
		return

	#===========================================================================
	#
	#===========================================================================
	def showBackdrop(self, forceShow = False):
		printl("", self, "S")

		if forceShow:
			if self.whatBackdrop is not None:
				if getOeVersion() != "oe22":
					self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
				else:
					self.EXpicloadBackdrop.startDecode(self.whatBackdrop,False)

				ptr = self.EXpicloadBackdrop.getData()

				if ptr is not None:
					self["backdrop"].instance.setPixmap(ptr)

		elif self.usePicCache :
			if fileExists(self.whatBackdrop):

				if self.whatBackdrop is not None:
					if getOeVersion() != "oe22":
						self.EXpicloadBackdrop.startDecode(self.whatBackdrop,0,0,False)
					else:
						self.EXpicloadBackdrop.startDecode(self.whatBackdrop,False)

					ptr = self.EXpicloadBackdrop.getData()

					if ptr is not None:
						self["backdrop"].instance.setPixmap(ptr)

			else:
				self.downloadBackdrop()
		else:
			self.downloadBackdrop()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def resetCurrentImages(self):
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skin.value + "/images/picreset.png"

		if self.viewParams["elements"]["poster"]["visible"]:
			if self.resetPoster:
				self["poster"].instance.setPixmapFromFile(ptr)

		if self.viewParams["elements"]["backdrop"]["visible"] and not self.usedStillPicture:
			if self.resetBackdrop:
				self.resetBackdropImage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadPoster(self):
		printl("", self, "S")
		printl("self.posterWidth:" + str(self.posterWidth), self, "D")
		printl("self.posterHeight:" + str(self.posterHeight), self, "D")
		printl("self.poster_postfix:" + str(self.poster_postfix), self, "D")
		printl("self.image_prefix:" + str(self.image_prefix), self, "D")

		if "thumb" in self.details:
			if self.details["thumb"] != "":
				download_url = self.details["thumb"]
				download_url = download_url.replace('&width=999&height=999', '&width=' + self.posterWidth + '&height=' + self.posterHeight)
				printl( "download url: " + download_url, self, "D")
				printl("starting download", self, "D")
				authHeader = self.plexInstance.get_hTokenForServer(self.details["server"])
				printl("header: " + str(authHeader), self, "D")
				downloadPage(str(download_url), self.whatPoster, headers=authHeader).addCallback(lambda _: self.showPoster(forceShow = True))
			else:
				self.noPicData()
		else:
			self.noPicData()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadBackdrop(self):
		printl("", self, "S")
		printl("self.backdropWidth:" + str(self.backdropWidth), self, "D")
		printl("self.backdropHeight:" + str(self.backdropHeight), self, "D")
		printl("self.backdrop_postfix:" + str(self.backdrop_postfix), self, "D")
		printl("self.image_prefix:" + str(self.image_prefix), self, "D")

		if "art" in self.details:
			if self.details["art"] != "":
				download_url = self.details["art"]
				download_url = download_url.replace('&width=999&height=999', '&width=' + self.backdropWidth + '&height=' + self.backdropHeight)
				printl( "download url: " + download_url, self, "D")
				printl("starting download", self, "D")
				authHeader = self.plexInstance.get_hTokenForServer(self.details["server"])
				printl("header: " + str(authHeader), self, "D")
				downloadPage(download_url, self.whatBackdrop, headers=authHeader).addCallback(lambda _: self.showBackdrop(forceShow = True))
			else:
				self.noPicData()
		else:
			self.noPicData()

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def noPicData(self):

		printl("no pic data available", self, "D")
	#==============================================================================
	#
	#==============================================================================
	def finishLayout(self):
		"""
		adds buttons pics from xml and handles fastScrollMode function
		"""
		printl("", self, "S")

		printl("guiElements_key_red" +self.guiElements["key_red"], self, "D")

		# we use this for override playback mode if wanted
		self.initPlaybackMode()

		self.initColorFunctions()

		self.setLevelActive(currentLevel=1)

		if self.miniTv:
			self.initMiniTv(self.viewParams["settings"]["backdropVideoWidth"], self.viewParams["settings"]["backdropVideoHeight"])

		# we do like we pressed the button to init the right names
		self.onKey1(initial=True)

		# first we set the pics for buttons
		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])
		self["btn_yellow"].instance.setPixmapFromFile(self.guiElements["key_yellow"])
		self["btn_blue"].instance.setPixmapFromFile(self.guiElements["key_blue"])

		if self.libraryName == "music":
			self["casePic"].instance.setPixmapFromFile(self.guiElements["musicCase"])
			self.autoPlayMode = True
			self.resumeMode = False

		else:
			self["casePic"].instance.setPixmapFromFile(self.guiElements["videoCase"])

		if self.fastScroll:
			# if we are in fastScrollMode we remove some gui elements
			self.resetGuiElementsInFastScrollMode()

		# now we set seen/unseen pictures
		self.getSeenVisus()

		# enable audio and subtitles information if we have transcoding active
		if self.serverConfig.playbackType.value == "1": # transcoded
			printl("audio: " + str(self.viewParams["elements"]["audio"]),self, "D")
			if self.viewParams["elements"]["audio"]["visible"]:
				self.toggleElementVisibilityWithLabel("audio")
			else:
				self.toggleElementVisibilityWithLabel("audio", "hide")

		if self.serverConfig.playbackType.value == "2" or self.serverConfig.playbackType.value == "1":  # direct local and transcoded
			if self.viewParams["elements"]["subtitles"]["visible"]:
				self.toggleElementVisibilityWithLabel("subtitles")
			else:
				self.toggleElementVisibilityWithLabel("subtitles", "hide")

		if not self.fastScroll:
			self["info"].hide()
			self["infoLabel"].hide()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getSeenVisus(self):
		printl("", self, "S")

		self.seenPic = loadPicture(str(self.guiElements["seenPic"]))
		printl("self.seenPic: " + str(self.seenPic), self, "D")

		self.startedPic = loadPicture(str(self.guiElements["startedPic"]))
		printl("self.startedPic: " + str(self.startedPic), self, "D")

		self.unseenPic = loadPicture(str(self.guiElements["unseenPic"]))
		printl("self.unseenPic: " + str(self.unseenPic), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def processGuiElements(self):
		printl("", self, "S")

		# this is always the case when the view starts the first time

		for element in self.viewParams["elements"]:
			printl("element:" + str(element), self, "D")
			visibility = self.viewParams["elements"][element]["visible"]

			self.alterGuiElementVisibility(element, visibility)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def processSubViewElements(self, myType):
		printl("", self, "S")

		printl("myType: " +  str(myType), self, "D")

		# now we check if we are in a special subView with its own params
		if "subViews" in self.viewParams:
			if myType in self.viewParams["subViews"]:
				subViewParams = self.viewParams["subViews"][myType]
				printl("subViewParams: " + str(subViewParams), self, "D")

				self.viewChangeStorage[self.viewStep] = {}
				for element in subViewParams:
					printl("element: " + str(element), self, "D")
					self.viewChangeStorage[self.viewStep][element] = {}
					params = subViewParams[element]
					if "visible" in params:
						visibility = params.get("visible")
						self.viewChangeStorage[self.viewStep][element]["visible"] = not visibility
						self.alterGuiElementVisibility(element, visibility)

					if "xCoord" in params and "yCoord" in params:
						xCoord = params.get("xCoord")
						yCoord = params.get("yCoord")
						position = self[element].getPosition()
						self.viewChangeStorage[self.viewStep][element]["xCoord"] = position[0]
						self.viewChangeStorage[self.viewStep][element]["yCoord"] = position[1]
						self.alterGuiElementPosition(element,xCoord, yCoord)

				printl("viewChangeStorage:" + str(self.viewChangeStorage), self, "D")
		# it not we use the params form the main view
		else:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def restoreElementsInViewStep (self):
		"""
		restores gui elements according to the self.viewChangeStorage dict and self.viewStep
		"""
		printl("", self, "S")
		printl("viewChangeStorage:" + str(self.viewChangeStorage), self, "D")

		# +1 is the correction for viewStep
		key = int(self.viewStep)+1
		printl("key:" + str(key), self, "D")

		# key 0 is when we leave the view there will never be data to change ;-)
		if key != 0 and key in self.viewChangeStorage:
			subViewParams = self.viewChangeStorage[key]
			for element in subViewParams:
				printl("element: " + str(element), self, "D")
				params = subViewParams[element]
				if "visible" in params:
					visibility = params.get("visible")
					self.alterGuiElementVisibility(element, visibility)

				if "xCoord" in params and "yCoord" in params:
					xCoord = params.get("xCoord")
					yCoord = params.get("yCoord")

					self.alterGuiElementPosition(element,xCoord, yCoord)
		else:
			printl("key is 0 or not in storage ...", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def alterGuiElementVisibility(self, element, visibility):
		printl("", self, "C")
		printl("element: " + str(element), self, "D")
		printl("visibility: " + str(visibility), self, "D")
		if visibility:
			self[element].show()
			try:
				self[element+"Label"].show()

				# additional changes
				if element == "backdrop":
					self[element+"Video"].show()

			except Exception, e:
				printl("Exception: " + str(e), self, "D")

			try:
				if element == "btn_red" or element == "green" or element == "btn_yellow" or element == "btn_blue":
					self[element + "Text"].show()
			except Exception, e:
				printl("Exception: " + str(e), self, "D")

		else:
			self[element].hide()
			try:
				self[element+"Label"].hide()

				# additional changes
				if element == "backdrop":
					self[element+"Video"].hide()
			except Exception, e:
				printl("Exception: " + str(e), self, "D")

			try:
				if element == "btn_red" or element == "green" or element == "btn_yellow" or element == "btn_blue":
					self[element + "Text"].hide()
			except Exception, e:
				printl("Exception: " + str(e), self, "D")

		printl("", self, "C")

#===========================================================================
	#
	#===========================================================================
	def alterGuiElementPosition(self, element, xCoord, yCoord):
		printl("", self, "C")

		elementPostion = self[element].getPosition()
		xElement = elementPostion[0]
		yElement = elementPostion[1]

		try:
			labelPosition = self[element+"Label"].getPosition()
			xLabel = labelPosition[0]
			yLabel = labelPosition[1]
			xDiff = int(xLabel) - int(xElement)
			yDiff = int(yLabel) - int(yElement)
			printl("xDiff: " + str(xDiff), self, "D")
			printl("yDiff: " + str(yDiff), self, "D")
			newX = int(xCoord) - (int(xDiff)*-1)
			newY = int(yCoord) - (int(yDiff)*-1)
			printl("newX: " + str(newX), self, "D")
			printl("newY: " + str(newY), self, "D")
			self[element+"Label"].setPosition(newX, newY)
		except Exception, e:
			printl("error: " + str(e), self, "D")

		printl("element: " + str(element), self, "D")
		printl("xCoord: " + str(xCoord), self, "D")
		printl("yCoord: " + str(yCoord), self, "D")

		self[element].setPosition(xCoord, yCoord)

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def resetGuiElementsInFastScrollMode(self):
		printl("", self, "S")

		# lets hide them so that fastScroll does not show up old information
		self["rating_stars"].hide()
		self["codec"].hide()
		self["aspect"].hide()
		self["resolution"].hide()
		self["rated"].hide()
		self["sound"].hide()
		self["soundchannels"].hide()

		if not self.usedStillPicture:
			self.resetBackdropImage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def resetBackdropImage(self):
		printl("", self, "S")

		ptr = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skin.value + "/images/picreset.png"
		self["backdrop"].instance.setPixmapFromFile(ptr)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleRatedPixmaps(self):
		printl("", self, "S")

		mpaa = self.details.get("contentRating", "unknown").upper()
		printl("contentRating: " + str(mpaa), self, "D")

		if mpaa == "PG-13" or mpaa == "TV-14":
			found = True
			self["rated"].setPixmapNum(0)

		elif mpaa == "PG" or mpaa == "TV-PG":
			found = True
			self["rated"].setPixmapNum(1)

		elif mpaa == "R" or mpaa == "14A":
			found = True
			self["rated"].setPixmapNum(2)

		elif mpaa == "NC-17" or mpaa == "TV-MA":
			found = True
			self["rated"].setPixmapNum(3)

		elif mpaa == "DE/0" or mpaa == "G":
			found = True
			self["rated"].setPixmapNum(4)

		elif mpaa == "NOT RATED" or mpaa == "G" or mpaa == "NR":
			found = True
			self["rated"].setPixmapNum(5)

		elif mpaa == "DE/6":
			found = True
			self["rated"].setPixmapNum(6)

		elif mpaa == "DE/12":
			found = True
			self["rated"].setPixmapNum(7)

		elif mpaa == "DE/16":
			found = True
			self["rated"].setPixmapNum(8)

		elif mpaa == "DE/18":
			found = True
			self["rated"].setPixmapNum(9)

		elif mpaa == "UNKNOWN" or mpaa == "UNKNOWN" or mpaa == "":
			found = False

		else:
			printl("we have a value but no match!! mpaa: " + str(mpaa), self, "I")
			found = False

		if found:
			self["rated"].show()
		else:
			self["rated"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleSoundPixmaps(self):
		printl("", self, "S")

		audio = self.details["mediaDataArr"][0].get("audioCodec", "unknown").upper()
		printl("audioCodec: " + str(audio), self, "D")

		if audio == "DCA":
			found = True
			self["sound"].setPixmapNum(0)

		elif audio == "AC3":
			found = True
			self["sound"].setPixmapNum(1)

		elif audio == "MP2":
			found = True
			self["sound"].setPixmapNum(2)

		elif audio == "MP3":
			found = True
			self["sound"].setPixmapNum(3)

		elif audio == "UNKNOWN" or audio == "":
			found = False

		else:
			printl("we have a value but no match!! audio: " + str(audio), self, "I")
			found = False

		if found:
			self["sound"].show()
		else:
			self["sound"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleSoundChannelsPixmaps(self):
		printl("", self, "S")

		soundchannels = self.details["mediaDataArr"][0].get("audioChannels", "unknown").upper()
		printl("soundchannels: " + str(soundchannels), self, "D")

		if soundchannels == "2": #2.0
			found = True
			self["soundchannels"].setPixmapNum(0)

		elif soundchannels == "3": #2.1
			found = True
			self["soundchannels"].setPixmapNum(1)

		elif soundchannels == "6":
			found = True
			self["soundchannels"].setPixmapNum(2)

		elif soundchannels == "7":
			found = True
			self["soundchannels"].setPixmapNum(3)

		elif soundchannels == "8":
			found = True
			self["soundchannels"].setPixmapNum(4)

		elif soundchannels == "9":
			found = True
			self["soundchannels"].setPixmapNum(5)

		elif soundchannels == "UNKNOWN" or soundchannels == "":
			found = False

		else:
			printl("we have a value but no match!! soundchannels: " + str(soundchannels), self, "I")
			found = False

		if found:
			self["soundchannels"].show()
		else:
			self["soundchannels"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleResolutionPixmaps(self):
		printl("", self, "S")

		resolution = self.details["mediaDataArr"][0].get("videoResolution", "unknown").upper()
		printl("videoResolution: " + str(resolution), self, "D")

		if resolution == "1080":
			found = True
			self["resolution"].setPixmapNum(0)

		elif resolution == "720":
			found = True
			self["resolution"].setPixmapNum(1)

		elif resolution == "480" or resolution == "576" or resolution == "SD":
			found = True
			self["resolution"].setPixmapNum(2)

		elif resolution == "UNKNOWN" or resolution == "":
			found = False

		else:
			printl("we have a value but no match!! resolution: " + str(resolution), self, "I")
			found = False

		if found:
			self["resolution"].show()
		else:
			self["resolution"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleAspectPixmaps(self):
		printl("", self, "S")

		aspect = self.details["mediaDataArr"][0].get("aspectRatio", "unknown").upper()
		printl("aspectRatio: " + str(aspect), self, "D")

		if aspect == "1.33":
			found = True
			self["aspect"].setPixmapNum(0)

		elif aspect == "1.66" or aspect == "1.78" or aspect == "1.85":
			found = True
			self["aspect"].setPixmapNum(1)

		elif aspect == "2.35": # 21:9
			found = True
			self["aspect"].setPixmapNum(1)

		elif aspect == "UNKNOWN" or aspect == "":
			found = False

		else:
			printl("we have a value but no match!! aspect: " + str(aspect), self, "I")
			found = False

		if found:
			self["aspect"].show()
		else:
			self["aspect"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleCodecPixmaps(self):
		printl("", self, "S")
		# we take always the first entry. later we have to chech which one is selected
		codec = self.details["mediaDataArr"][0].get("videoCodec", "unknown").upper()
		printl("videoCodec: " + str(codec), self, "D")

		if codec == "VC1":
			found = True
			self["codec"].setPixmapNum(0)

		elif codec == "H264":
			found = True
			self["codec"].setPixmapNum(1)

		elif codec == "MPEG4":
			found = True
			self["codec"].setPixmapNum(2)

		elif codec == "MPEG2VIDEO":
			found = True
			self["codec"].setPixmapNum(3)

		elif codec == "UNKNOWN" or codec == "":
			found = False

		else:
			printl("we have a value but no match!! codec: " + str(codec), self, "I")
			found = False

		if found:
			self["codec"].show()
		else:
			self["codec"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handlePopularityPixmaps(self):
		printl("", self, "S")

		try:
			popularity = float(self.details["rating"])
		except Exception, e:
			popularity = 0
			printl("error in popularity " + str(e), self, "D")

		self["rating_stars"].setValue(int(popularity) * 10)
		self["rating_stars"].show()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getPictureInformationToLoad(self):
		printl("", self, "S")

		# if pic cache is not configured we set a name that will not exist to force download each time from server
		if not self.usePicCache:
			self.pname = "temp"
			self.bname = "temp"
			self.mediaPath = config.plugins.dreamplex.logfolderpath.value

		printl("bname: " + str(self.bname), self, "D")
		printl("pname: " + str(self.pname), self, "D")
		self.whatPoster = self.mediaPath + self.image_prefix + "_" + self.pname + self.poster_postfix
		self.whatBackdrop = self.mediaPath + self.image_prefix + "_" + self.bname + self.backdrop_postfix

		printl("self.whatPoster : " + str(self.whatPoster ), self, "D")
		printl("self.whatBackdrop: " + str(self.whatBackdrop), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showFunctions(self, visible):
		printl("", self, "S")

		self.areFunctionsHidden = visible

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def filter(self):
		printl("", self, "S")

		if self.onNumberKeyLastChar == " ":
			self["listview"].setList(self.beforeFilterListViewList)

			# we also have to reset the variable because this one is passed to player
			self.listViewList = self.beforeFilterListViewList
		else:
			self.listViewList = [x for x in self.beforeFilterListViewList if x[1]["title"][0] == self.onNumberKeyLastChar]
			self["listview"].setList(self.listViewList)

		self.refresh()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def closePlugin(self):
		printl("", self, "S")

		if config.plugins.dreamplex.useBackdropVideos.value and self.loadedStillPictureLib:
			self.stopBackdropVideo()

		super(DP_View,self).closePlugin()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def restoreLiveTv(self):
		printl("", self, "S")

		if not self.liveTvInViews:
			printl("restoring liveTv", self, "D")
			self.session.nav.playService(getLiveTv())

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def stopBackdropVideo(self):
		printl("", self, "S")

		# stop the m1v playback to avoid blocking the playback of the movie
		self["stillPicture"].finishStillPicture()

		printl("", self, "C")
