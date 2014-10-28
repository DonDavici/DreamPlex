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
import threading

from os import remove
from time import sleep, localtime, time, strftime

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.AudioSelection import AudioSelection
from Tools.ISO639 import LanguageCodes

#noinspection PyUnresolvedReferences
from enigma import eServiceReference, eConsoleAppContainer, iPlayableService, eTimer, eServiceCenter, iServiceInformation, ePicLoad

from Tools import Notifications
from Tools.Directories import fileExists

from Components.AVSwitch import AVSwitch
from Components.config import config
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Slider import Slider
from Components.Sources.StaticText import StaticText
from Components.Language import language
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.List import List

from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarSeek, InfoBarAudioSelection, \
	InfoBarServiceNotifications, InfoBarSimpleEventView, \
	InfoBarExtensions, InfoBarNotifications, \
	InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarCueSheetSupport

from DPH_Singleton import Singleton
from DP_Summary import DreamplexPlayerSummary
from DPH_ScreenHelper import DPH_ScreenHelper

from __common__ import printl2 as printl, convertSize, encodeThat
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
class DP_Player(Screen, InfoBarBase, InfoBarShowHide, InfoBarCueSheetSupport,
		InfoBarSeek, InfoBarAudioSelection, HelpableScreen,
		InfoBarServiceNotifications, InfoBarSimpleEventView,
		InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications, DPH_ScreenHelper):

	ENIGMA_SERVICE_ID = None
	ENIGMA_SERVICETS_ID = 0x1		#1
	ENIGMA_SERVIDEM2_ID = 0x3		#3
	ENIGMA_SERVICEGS_ID = 0x1001	#4097
	
	seek = None
	resume = False
	resumeStamp = 0
	server = None
	id = None
	url = None
	transcodingSession = None
	universalTranscoder = False
	transcoderHeartbeat = None
	videoData = None
	mediaData = None
	multiUser = False
	
	tagline = ""
	summary = ""
	year = ""
	studio = ""
	duration = ""
	contentRating = ""

	audioCodec = ""
	videoCodec = ""
	videoResolution = ""
	videoFrameRate = ""
	
	nTracks = False
	switchedLanguage = False
	timeshift_enabled = False
	isVisible = False
	playbackType = None
	timelineWatcher = None
	whatPoster = None
	subtitleStreams = None
	subtitleLanguageCode = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, listViewList, currentIndex, libraryName, autoPlayMode, resumeMode, playbackMode, forceResume=False, isExtraData=False, sessionData=None, subtitleData=None):
		printl("", self, "S")
		Screen.__init__(self, session)

		if libraryName == "music":
			self.skinName = "DPS_MusicPlayer"
			self.calculateEndingTime = False
		else:
			self.skinName = "DPS_VideoPlayer"
			self["endingTime"] = Label()
			self.calculateEndingTime = True

		for x in HelpableScreen, InfoBarShowHide, InfoBarBase, InfoBarSeek, \
				InfoBarAudioSelection, InfoBarSimpleEventView, \
				InfoBarServiceNotifications, InfoBarSubtitleSupport, \
				InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications:
			printl("x: " + str(x), self, "D")
			x.__init__(self)
		printl("currentIndex: " + str(currentIndex), self, "D")

		self.listViewList = listViewList
		self.currentIndex = currentIndex
		self.listCount = len(self.listViewList) - 1# list starts counting with 0
		self.playerData = {}
		self.autoPlayMode = autoPlayMode
		self.resumeMode = resumeMode
		self.forceResume = forceResume # we use this to able to resume out of android or ios
		self.playbackMode = playbackMode
		self.isExtraData = isExtraData
		self.sessionData = sessionData
		self.subtitleData = subtitleData

		# we add this for vix images due to their long press button support
		self.LongButtonPressed = False

		self.libraryName = libraryName

		self.plexInstance = Singleton().getPlexInstance()

		self.initScreen(self.skinName)

		self.bufferslider = Slider(0, 100)
		self["bufferslider"] = self.bufferslider

		self.bufferSeconds = 0
		self.bufferPercent = 0
		self.bufferSecondsLeft = 0
		self.bitrate = 0
		self.endReached = False

		self["actions"] = ActionMap(["DPS_Player"],
		{
		"ok": self.ok,
		"cancel": self.hide,
		"exitFunction": self.exitFunction,
		"keyTv": self.leavePlayer,
		"stop": self.leavePlayer,
		"seekManual": self.seekManual,
		"playNext": self.playNextEntry,
		"playPrevious": self.playPreviousEntry,
		}, -2)

		self["poster"] = Pixmap()
		self["shortDescription"] = Label()
		self["mediaTitle"] = StaticText()

		# Poster
		self.EXpicloadPoster = ePicLoad()

		# it will stop up/down/movielist buttons opening standard movielist whilst playing movie in plex
		if self.has_key('MovieListActions'):
			self["MovieListActions"].setEnabled(False)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		{
			iPlayableService.evUser+10: self.__evAudioDecodeError,
			iPlayableService.evUser+11: self.__evVideoDecodeError,
			iPlayableService.evUser+12: self.__evPluginError,
			iPlayableService.evBuffering: self.__evUpdatedBufferInfo,
			iPlayableService.evEOF: self.__evEOF,
		})

		if not sessionData:
			if self.isExtraData:
				self.media_id = isExtraData[0] #"125629"
				mediaFileUrl = isExtraData[1] #"http://92.60.8.106:34400/services/iva/assets/853333/video.mp4?bitrate=1500"
				self.buildPlayerData(mediaFileUrl, isExtraData=True)
			else:
				# from here we go on
				self.onFirstExecBegin.append(self.playMedia)
		else:
			service1 = self.session.nav.getCurrentService()
			self.seek = service1 and service1.seek()
			self.setSeekState(self.SEEK_STATE_PLAY)

			self.onLayoutFinish.append(self.resumePlayerData)

	#==============================================================================
	#
	#==============================================================================
	def resumePlayerData(self):
		printl("", self, "S")

		self.playerData = self.sessionData[0]

		self.ptr = self.sessionData[1]

		self.renderPoster()

		self.setPlayerData()

		self.startTimelineWatcher()
		self.timelineWatcher.start(5000,False)

		printl("", self, "C")


	#==============================================================================
	# is called automatically
	#==============================================================================
	def createSummary(self):
		printl("", self, "S")

		printl("", self, "C")
		return DreamplexPlayerSummary

	#==============================================================================
	#
	#==============================================================================
	def playMedia(self):
		printl("", self, "S")

		selection = self.listViewList[self.currentIndex]
		printl("selection: " + str(selection), self, "D")

		if "parentRatingKey" in selection[1]: # this is the case with shows
			self.show_id = selection[1]['parentRatingKey']
			self.isShow = True
		else:
			self.isShow = False

		self.media_id = selection[1]['ratingKey']
		self.selection = selection
		server = selection[1]['server']

		self.setPoster()

		self.count, self.options, self.server = Singleton().getPlexInstance().getMediaOptionsToPlay(self.media_id, server, False, myType=selection[1]['tagType'])

		self.selectMedia(self.count, self.options, self.server)

		printl("", self, "C")

	#===========================================================
	#
	#===========================================================
	def selectMedia(self, count, options, server ):
		printl("", self, "S")

		#if we have two or more files for the same movie, then present a screen
		self.options = options
		self.server = server
		self.dvdplayback=False

		if not self.options:
			response = Singleton().getPlexInstance().getLastResponse()
			self.session.open(MessageBox,(_("Error:") + "\n%s") % response, MessageBox.TYPE_INFO)
		else:
			if count > 1:
				printl("we have more than one playable part ...", self, "I")
				indexCount=0
				functionList = []

				for items in self.options:
					printl("item: " + str(items), self, "D")
					if items[1] is not None:
						name=items[1].split('/')[-1]
					else:
						size = convertSize(int(items[3]))
						duration = time.strftime('%H:%M:%S', time.gmtime(int(items[4])))
						# this is the case when there is no information of the real file name
						name = items[0] + " (" + items[2] + " / " + size + " / " + duration + ")"

					printl("name " + str(name), self, "D")
					functionList.append((name ,indexCount, ))
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
		result = 0
		printl("choice: " + str(choice), self, "D")

		if choice is not None:
			result = int(choice[1])

		printl("result: " + str(result), self, "D")

		Singleton().getPlexInstance().setPlaybackType(str(self.playbackMode))

		mediaFileUrl = Singleton().getPlexInstance().mediaType({'key': self.options[result][0], 'file' : self.options[result][1]}, self.server)
		printl("We have selected media at " + mediaFileUrl, self, "I")

		self.buildPlayerData(mediaFileUrl)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def buildPlayerData(self, mediaFileUrl, isExtraData=False):
		printl("", self, "S")

		self.playerData[self.currentIndex] = Singleton().getPlexInstance().playLibraryMedia(self.media_id, mediaFileUrl, isExtraData=isExtraData)

		# populate addional data
		self.setPlayerData()

		self.playSelectedMedia()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def playSelectedMedia(self):
		printl("", self, "S")

		if self.isExtraData:
			self.play()
		else:
			resumeStamp = self.playerData[self.currentIndex]['resumeStamp']
			printl("resumeStamp: " + str(resumeStamp), self, "I")

			if self.playerData[self.currentIndex]['fallback']:
				message = _("Sorry I didn't find the file on the provided locations")
				locations = _("Location:") + "\n " + self.playerData[self.currentIndex]['locations']
				suggestion = _("Please verify you direct local settings")
				fallback = _("I will now try to play the file via transcode.")

				self.session.openWithCallback(self.checkResume, MessageBox,_("Warning:") + "\n%s\n\n%s\n\n%s\n\n%s" % (message, locations, suggestion, fallback), MessageBox.TYPE_ERROR)
			else:
				self.checkResume(resumeStamp)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkResume(self, resumeStamp):
		printl("", self, "S")

		if resumeStamp > 0 and self.resumeMode:
			self.session.openWithCallback(self.handleResume, MessageBox, _(" This file was partially played.\n\n Do you want to resume?"), MessageBox.TYPE_YESNO)

		elif self.forceResume:
			self.play(resume = True)

		else:
			self.play()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def handleResume(self, confirm):
		printl("", self, "S")

		if confirm:
			self.play(resume = True)

		else:
			self.play()

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def setPoster(self):
		"""
		set params for poster via ePicLoad object
		"""
		printl("", self, "S")

		self.EXscale = (AVSwitch().getFramebufferScale())

		self.EXpicloadPoster.setPara([self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])

		if self.whatPoster is None:
			self.buildPosterData()

		self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)

		self.ptr = self.EXpicloadPoster.getData()

		self.renderPoster()

		printl("", self, "C")

	#==============================================================================
	#
	#==============================================================================
	def renderPoster(self):
		printl("", self, "S")

		try:
			self["poster"].instance.setPixmap(self.ptr)
		except:
			pass

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def setServiceReferenceData(self):
		printl("", self, "S")

		self.setEnigmaServiceId()

		self.sref = eServiceReference(self.ENIGMA_SERVICE_ID, 0, self.url)
		self.sref.setName(self.title)
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setEnigmaServiceId(self):
		printl("", self, "S")

		# check for playable services
		printl( "Checking for usable gstreamer service (builtin)... ",self, "I")

		# lets built the sref for the movieplayer out of the gathered information
		if self.url[:4] == "http": #this means we are in streaming mode so we will use sref 4097
			self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVICEGS_ID

		elif self.url[-3:] == ".ts" or self.url[-4:] == ".iso": # seems like we have a real ts file ot a iso file so we will use sref 1
			self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVICETS_ID

		elif self.url[-5:] == ".m2ts":
			self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVIDEM2_ID

		else: # if we have a real file but no ts but for eg mkv we will use sref 4097
			if self.isValidServiceId(self.ENIGMA_SERVICEGS_ID):
				printl("we are able to stream over 4097", self, "I")
				self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVICEGS_ID
			else:
				raise Exception

		printl("self.ENIGMA_SERVICE_ID = " + str(self.ENIGMA_SERVICE_ID), self, "I")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def playNextEntry(self):
		printl("", self, "S")
		# first we write back the state of the current file to the plex server
		self.handleProgress()

		printl("currentIndex: " + str(self.currentIndex), self, "D")
		# increase position
		self.currentIndex += 1

		printl("nextIndex: " + str(self.currentIndex), self, "D")
		printl("self.listCount: " + str(self.listCount), self, "D")

		# check if we are at the end of the list we start all over
		if self.currentIndex > self.listCount:
			self.currentIndex = 0

		printl("finalIndex: " + str(self.currentIndex), self, "D")

		# stop current playback if exists
		self.session.nav.stopService()

		# play
		self.playMedia()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def playPreviousEntry(self):
		printl("", self, "S")
		# first we write back the state of the current file to the plex server
		self.handleProgress()

		self.currentIndex -= 1

		# check if we are at the begining of the list we start at the end
		if self.currentIndex < 0:
			self.currentIndex = self.listCount

		# stop current playback if exists
		self.session.nav.stopService()

		# play
		self.playMedia()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def play(self, resume = False):
		printl("", self, "S")

		self.session.nav.stopService()

		# populate self.sref with new data
		self.setServiceReferenceData()

		# start playback
		self.session.nav.playService(self.sref)

		service1 = self.session.nav.getCurrentService()
		self.seek = service1 and service1.seek()

		if resume == True and self.resumeStamp is not None and self.resumeStamp > 0.0:
			self.seekwatcherThread = threading.Thread(target=self.seekWatcher,args=(self,))
			self.seekwatcherThread.start()

		self.startTimelineWatcher()

		if self.subtitleData == "forced" or self.subtitleData:
			self.startSubtitleWatcher()

		if self.playbackType == "2":
			self["bufferslider"].setValue(100)

			# we start here too because it seems that direct local does not hit the buffer full function
			self.timelineWatcher.start(5000,False)
			self.subtitleWatcher.start(10000,False)

		else:
			self["bufferslider"].setValue(1)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startSubtitleWatcher(self):
		printl("", self, "S")

		self.subtitleWatcher = eTimer()
		self.subtitleWatcher.callback.append(self.subtitleChecker)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def subtitleChecker(self):
		printl("", self, "S")

		try:
			subtitles = self.getCurrentServiceSubtitle()
			subtitlelist = subtitles.getSubtitleList()
			subtitleStreams = []
			printl("subtitles: " + str(subtitles), self, "D")
			printl("what: " + str(subtitlelist), self, "D")

			if len(subtitlelist):
				for x in subtitlelist:
					number = str(x[1])
					description = "?"
					myLanguage = _("<unknown>")
					selected = ""

					if x[4] != "und":
						if LanguageCodes.has_key(x[4]):
							myLanguage = LanguageCodes[x[4]][0]
						else:
							myLanguage = x[4]

					if x[0] == 0:
						description = "DVB"
						number = "%x" % (x[1])

					elif x[0] == 1:
						description = "TTX"
						number = "%x%02x" % (x[3],x[2])

					elif x[0] == 2:
						types = (_("<unknown>"), "UTF-8 text", "SSA", "AAS", ".SRT file", "VOB", "PGS (unsupported)")
						description = types[x[2]]

					subs = (x, "", number, description, myLanguage, selected)

					if self.subtitleData == "forced":
						self.enableSubtitle(subs[0])
						self.subtitleWatcher.stop()

					elif self.subtitleData in myLanguage:
						self.enableSubtitle(subs[0])
						self.subtitleWatcher.stop()

					else:
						print self.subtitleData
						print myLanguage
						raise Exception

					# just for debugging
					subtitleStreams.append((x, "", number, description, myLanguage, selected))

					# currentStream = subtitleStreams[0]
					# self.enableSubtitle(currentStream[0])

			printl("subtitleStreams: " + str(subtitleStreams), self, "D")

		except Exception, e:
			printl("Subtitle Message: " + str(e), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def enableSubtitle(self, subtitles):
		printl("", self, "S")

		if self.selected_subtitle != subtitles:
			self.subtitles_enabled = False
			self.selected_subtitle = subtitles
			if subtitles:
				self.subtitles_enabled = True

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startTimelineWatcher(self):
		printl("", self, "S")

		self.timelineWatcher = eTimer()
		self.timelineWatcher.callback.append(self.updateTimeline)

		if self.multiUserServer:
			printl("we are a multiuser server", self, "D")
			self.multiUser = True

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def pauseService(self):
		printl("", self, "S")

		if self.playbackType == "1"  and self.universalTranscoder:
			self.transcoderHeartbeat = eTimer()
			self.transcoderHeartbeat.callback.append(self.keepTranscoderAlive)
			self.transcoderHeartbeat.start(10000,False)

		self.timelineWatcher.stop()

		super(DP_Player,self).pauseService()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def unPauseService(self):
		printl("", self, "S")

		self.hide()
		self.setSeekState(self.SEEK_STATE_PLAY)

		if self.transcoderHeartbeat is not None:
			self.transcoderHeartbeat.stop()

		self.timelineWatcher.start(5000,False)

		printl("", self, "S")
	#===========================================================================
	#
	#===========================================================================
	def getTitle(self):
		printl("", self, "S")

		printl("", self, "C")
		return str(self.playerData[self.currentIndex]['videoData']['title'])

	#===========================================================================
	#
	#===========================================================================
	def setPlayerData(self):
		printl("", self, "S")

		self.playbackData = self.playerData[self.currentIndex]
		self.videoData = self.playerData[self.currentIndex]['videoData']

		# not used for now
		#self.mediaData = self.playerData[self.currentIndex]['mediaData']

		# go through the data out of the function call
		self.resumeStamp = int(self.playbackData['resumeStamp']) / 1000 # plex stores seconds * 1000
		self.server = str(self.playbackData['server'])
		self.id = str(self.playbackData['id'])
		self.multiUserServer = self.playbackData['multiUserServer']
		self.url = str(self.playbackData['playUrl'])
		self.transcodingSession = str(self.playbackData['transcodingSession'])
		self.playbackType = str(self.playbackData['playbackType'])
		self.connectionType = str(self.playbackData['connectionType'])
		self.universalTranscoder = self.playbackData['universalTranscoder']
		self.localAuth = self.playbackData['localAuth']

		self.title = encodeThat(self.videoData['title'])
		self["mediaTitle"].setText(self.title)

		self.shortDescription = encodeThat(self.videoData['summary'])
		self["shortDescription"].setText(self.shortDescription)

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def isValidServiceId(self, myId):
		printl("", self, "S")
		
		testSRef = eServiceReference(myId, 0, "Just a TestReference")
		info = eServiceCenter.getInstance().info(testSRef)
		
		printl("", self, "C")
		return info is not None

	#===========================================================================
	# 
	#===========================================================================
	def __evUpdatedBufferInfo(self):
		#printl("", self, "S")

		if self.playbackType == "2":
			self.bufferFull()
		else:
			self.bufferInfo()
		
		#printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		#printl("", self, "S")

		if self.playbackType != "2":
			self.bufferInfo()

		self.toggleShow()

		#printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def bufferInfo(self):
		#printl("", self, "S")

		try:
			bufferInfo = self.session.nav.getCurrentService().streamed().getBufferCharge()

			self.bufferPercent = bufferInfo[0]
			self.buffer1 = bufferInfo[1]
			self.bufferAvgOutRate = bufferInfo[2]
			self.buffer3 = bufferInfo[3]
			self.buffersize = bufferInfo[4]

			if int(self.bufferPercent) > 10:
				self["bufferslider"].setValue(int(self.bufferPercent))
				#printl("Buffersize[4]: %d BufferPercent[0]: %d Buffer[1]: %d Buffer[3]: %d BufferAvgOutRate[2]: %d" % (self.buffersize, self.bufferPercent, self.buffer1, self.buffer3, self.bufferAvgOutRate), self, "D")
			else:
				self["bufferslider"].setValue(1)

			if self.bufferPercent > 95:
				self.bufferFull()

			if self.bufferPercent == 0 and not self.endReached and (bufferInfo[1] != 0 and bufferInfo[2] !=0):
				self.bufferEmpty()
		except:
			pass

		#printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def __evAudioDecodeError(self):
		printl("", self, "S")
		
		try:
			currPlay = self.session.nav.getCurrentService()
			sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
			printl( "audio-codec %s can't be decoded by hardware" % sTagAudioCodec, self, "I")
			Notifications.AddNotification(MessageBox, _("This Box can't decode %s streams!") % sTagAudioCodec, type=MessageBox.TYPE_INFO, timeout=10)
		
		except Exception, e:
			printl("exception: " + str(e), self, "W")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def __evVideoDecodeError(self):
		printl("", self, "S")
		
		try:
			currPlay = self.session.nav.getCurrentService()
			sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
			printl( "video-codec %s can't be decoded by hardware" % sTagVideoCodec, self, "I")
			Notifications.AddNotification(MessageBox, _("This Box can't decode %s streams!") % sTagVideoCodec, type=MessageBox.TYPE_INFO, timeout=10)
		
		except Exception, e:
			printl("exception: " + str(e), self, "W")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def __evPluginError(self):
		printl("", self, "S")
		
		try:
			currPlay = self.session.nav.getCurrentService()
			message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
			printl( "[PlexPlayer] PluginError " + message, self, "I")
			Notifications.AddNotification(MessageBox, _("Your Box can't decode this video stream!\n%s") % message, type=MessageBox.TYPE_INFO, timeout=10)
		
		except Exception, e:
			printl("exception: " + str(e), self, "W")
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def __evEOF(self):
		printl("", self, "S")
		
		printl( "got evEOF", self, "W")
		
		try:
			err = self.session.nav.getCurrentService().info().getInfoString(iServiceInformation.sUser+12)
			printl( "Error: " + str(err), self, "W")
			
			if err != "":
				Notifications.AddNotification(MessageBox, _("Your Box can't decode this video stream!\n%s") % err, type=MessageBox.TYPE_INFO, timeout=10)
		
		except Exception, e:
			printl("exception: " + str(e), self, "W")
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	#noinspection PyUnusedLocal
	def seekWatcher(self,*args):
		printl("", self, "S")
		
		printl( "seekWatcher started", self, "I")
		try:
			while self is not None and self.resumeStamp is not None:
				self.seekToStartPos()
				sleep(1)
		except Exception, e:
			printl("stopping due to exception in seektostartpos, eg. stopped playback before ready ..." + str(e), self, "W")
		
		printl( "seekWatcher finished ", self, "I")
		printl("", self, "C")
			
	#===========================================================================
	# 
	#===========================================================================
	def seekToStartPos(self):
		printl("", self, "S")
		
		try:
			if self.resumeStamp is not None:
				service = self.session.nav.getCurrentService()
				seek = service and service.seek()
				if seek is not None:
					r = seek.getLength()
					if not r[0]:
						printl ("got duration", self, "I")
						if r[1] == 0:
							printl( "duration 0", self, "I")
							return
						length = r[1]
						r = seek.getPlayPosition()
						if not r[0]:
							printl( "playbacktime " + str(r[1]), self, "I")
							if r[1] < 90000:# ~2 sekunden
								printl( "do not seek yet " + str(r[1]), self, "I")
								printl("", self, "C")
								return
						else:
							printl("", self, "C")
							return
						
						#time = length * self.start
						#time = int(139144271)
						elapsed = self.resumeStamp * 90000
						printl( "seeking to " + str(time) + " length " + str(length) + " ", self, "I")
						self.resumeStamp = None
						if elapsed < 90000:
							printl( "skip seeking < 10s", self, "I")
							printl("", self, "C")
							return
						#if config.plugins.dreamplex.setBufferSize.value:
							#self.session.nav.getCurrentService().streamed().setBufferSize(config.plugins.dreamplex.bufferSize.value)
						self.doSeek(int(elapsed))
		
		except Exception, e:
			printl("exception: " + str(e), self, "W")

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def bufferFull(self):
		#printl("", self, "S")
		
		if self.seekstate != self.SEEK_STATE_PLAY :
			printl( "Buffer filled start playing", self, "I")
			self.setSeekState(self.SEEK_STATE_PLAY)

		self.timelineWatcher.start(5000,False)

		#printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def bufferEmpty(self):
		#printl("", self, "S")
		
		if self.multiUser and self.timelineWatcher is not None:
			self.timelineWatcher.stop()

		#printl("", self, "C")
		

	#===========================================================================
	# 
	#===========================================================================
	def leavePlayer(self):
		printl("", self, "S")
		
		self.leavePlayerConfirmed(True)
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def exitFunction(self):
		printl("", self, "S")

		if config.plugins.dreamplex.exitFunction.value == "2":
			self.close((True, (self.playerData,self.ptr, self.id, self.currentIndex)))

		elif config.plugins.dreamplex.exitFunction.value == "1":
			self.leavePlayer()

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def leavePlayerConfirmed(self, answer):
		printl("", self, "S")

		if answer != "EOF":
			self.handleProgress()

		else:
			self.handleProgress(EOF=True)

		if self.playbackType == "1":
			self.stopTranscoding()

		if config.plugins.dreamplex.lcd4linux.value:
			remove(self.tempPoster)

		# we stop playback here
		self.session.nav.stopService()

		self.close((False, ))
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def doEofInternal(self, playing):
		printl("", self, "S")

		if self.autoPlayMode:
			if not self.nextPlaylistEntryAvailable():
				self.leavePlayerConfirmed("EOF")
			else:
				#start next file
				self.playNextEntry()
		else:
			self.leavePlayerConfirmed("EOF")
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def nextPlaylistEntryAvailable(self):
		printl("", self, "S")

		if self.listCount > 1:
			if (self.currentIndex + 1) < self.listCount:

				printl("", self, "C")
				return True

		printl("", self, "C")
		return False

	#===========================================================================
	# 
	#===========================================================================
	def handleProgress(self, EOF=False):
		printl("", self, "S")

		currentTime = self.getPlayPosition()[1] / 90000
		totalTime = self.getPlayLength()[1] / 90000

		if not EOF and currentTime is not None and currentTime > 0 and totalTime is not None and totalTime > 0:
			progress = currentTime / float(totalTime/100.0)
			printl( "played time is %s secs of %s @ %s%%" % ( currentTime, totalTime, progress),self, "I" )
		else:
			progress = 100
			printl("End of file reached", self, "D")
		
		if self.multiUser and self.timelineWatcher is not None:
			self.timelineWatcher.stop()

			urlPath = self.server + "/:/timeline?containerKey=/library/sections/onDeck&key=/library/metadata/" + self.id + "&ratingKey=" + self.id
			urlPath += "&state=stopped&time=" + str(currentTime*1000) + "&duration=" + str(totalTime*1000)
			self.plexInstance.doRequest(urlPath)

		#Legacy PMS Server server support before MultiUser version v0.9.8.0 and if we are not connected via myPlex
		else:
			if currentTime < 30:
				printl("Less that 30 seconds, will not set resume", self, "I")
		
			#If we are less than 95% complete, store resume time
			elif progress < 95:
				printl("Less than 95% progress, will store resume time", self, "I" )
				self.plexInstance.doRequest("http://"+self.server+"/:/progress?key="+self.id+"&identifier=com.plexapp.plugins.library&time="+str(currentTime*1000))

			#Otherwise, mark as watched
			else:
				printl( "Movie marked as watched. Over 95% complete", self, "I")
				self.plexInstance.doRequest("http://"+self.server+"/:/scrobble?key="+self.id+"&identifier=com.plexapp.plugins.library")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keepTranscoderAlive(self):
		printl("", self, "S")

		self.plexInstance.doRequest("http://"+self.server+"/video/:/transcode/universal/ping?session=" + self.transcodingSession)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def stopTranscoding(self):
		printl("", self, "S")
		
		if self.universalTranscoder:
			self.plexInstance.doRequest("http://"+self.server+"/video/:/transcode/universal/stop?session=" + self.transcodingSession)
		else:
			self.plexInstance.doRequest("http://"+self.server+"/video/:/transcode/segmented/stop?session=" + self.transcodingSession)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def isPlaying(self):
		printl("", self, "S")
		try:
			if self.seekstate != self.SEEK_STATE_PLAY and self.seekstate != self.SEEK_STATE_PAUSE:

				printl("", self, "C")
				return False
			else:

				printl("", self, "C")
				return True
		except:

			printl("", self, "C")
			return False

	#===========================================================================
	# audioTrackWatcher
	#===========================================================================
	#noinspection PyUnusedLocal
	def audioTrackWatcher(self,*args):
		printl("", self, "S")
		
		try:
			while self.nTracks == False and self is not None:
				self.setAudioTrack()
				sleep(1)
		
		except Exception, e:	
			printl("exception: " + str(e), self, "E")
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def updateTimeline(self):
		printl("" ,self,"S")

		currentTime = self.getPlayPosition()[1] / 90000
		totalTime = self.getPlayLength()[1] / 90000
		progress = int(( float(currentTime) / float(totalTime) ) * 100)

		if self.calculateEndingTime:
			try:
				endingTime = localtime(time() + (totalTime - currentTime))
			except Exception, e:
				printl("something went wrong with ending time -> " + str(e), self, "D")
				endingTime = localtime()

			self["endingTime"].setText(strftime("%H:%M:%S", endingTime))

		if self.multiUserServer:
			try:
				printl("currentTime: " + str(currentTime), self, "C")
				printl("totalTime: " + str(totalTime), self, "C")

				urlPath = self.server + "/:/timeline?containerKey=/library/sections/onDeck&key=/library/metadata/" + self.id + "&ratingKey=" + self.id

				seekState = self.seekstate

				if seekState == self.SEEK_STATE_PAUSE:
					printl( "Movies PAUSED time: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress), self,"D" )
					urlPath += "&state=paused&time=" + str(currentTime*1000) + "&duration=" + str(totalTime*1000)

				elif seekState == self.SEEK_STATE_PLAY :
					printl( "Movies PLAYING time: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress),self,"D" )
					urlPath += "&state=playing&time=" + str(currentTime*1000) + "&duration=" + str(totalTime*1000)

				# todo add buffering here if needed
					#urlPath += "&state=buffering&time=" + str(currentTime*1000)

				# todo add stopped here if needed
					#urlPath += "&state=stopped&time=" + str(currentTime*1000) + "&duration=" + str(totalTime*1000)

				self.plexInstance.doRequest(urlPath)

			except Exception, e:
				printl("exception: " + str(e), self, "E")
				return False

		printl("" ,self,"C")
		return True
			
	#===========================================================================
	# 
	#===========================================================================
	def setAudioTrack(self):
		printl("", self, "S")
		if not self.switchedLanguage:
			try:
				service = self.session.nav.getCurrentService()
		
		
				tracks = service and self.getServiceInterface("audioTracks")
				nTracks = tracks and tracks.getNumberOfTracks() or 0
				
				if not nTracks:
					printl("no tracks found yet ... retrying later", self, "D")
					return
				
				self.nTracks = True
				trackList = []
				
				for i in xrange(nTracks):
					audioInfo = tracks.getTrackInfo(i)
					lang = audioInfo.getLanguage()
					printl("lang: " + str(lang), self, "D")
					trackList += [str(lang)]
				
				systemLanguage = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
				printl("found systemLanguage: " +  systemLanguage, self, "I")
				#systemLanguage = "en"
				
				self.tryAudioEnable(trackList, systemLanguage, tracks)
			
			except Exception, e:
				printl("audioTrack exception: " + str(e), self, "W") 
		
		printl("", self, "C")   

	#===========================================================================
	# tryAudioEnable
	#===========================================================================
	def tryAudioEnable(self, alist, match, tracks):
		printl("", self, "S")
		printl("alist: " + str(alist), self, "D")
		printl("match: " + str(match), self, "D")
		index = 0
		for e in alist:
			e.lower()
			if e.find(match) >= 0:
				printl("audio track match: " + str(e), self, "I")
				sleep(2)
				tracks.selectTrack(index)
				
				printl("", self, "S")
				index += 1
			else:
				printl("no audio track match with " + str(e), self, "I")
		
		self.switchedLanguage = True
		printl("", self, "S")
		
	
	#===========================================================================
	# getServiceInterface
	#===========================================================================
	def getServiceInterface(self, iface):
		printl("", self, "S")
		service = self.session.nav.getCurrentService() # self.service
		if service:
			attr = getattr(service, iface, None)
			if callable(attr):
				printl("", self, "C")   
				return attr()
		
		printl("", self, "C")   
		return None
	
	#===========================================================================
	# 
	#===========================================================================
	def seekToMinute(self, minutes):
		printl("", self, "S")

		self.resumeStamp = int(minutes)*60
		self.seekToStartPos()

		printl("", self, "C")   

	#===========================================================================
	# 
	#===========================================================================
	def seekManual(self):
		printl("", self, "S")
		
		self.session.openWithCallback(self.seekToMinute, MinuteInput)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def getPlayLength(self):
		printl("", self, "S")
		
		length = self.seek.getLength()
		
		printl("", self, "C")
		return length
	
	#===========================================================================
	# 
	#===========================================================================
	def getPlayPosition(self):
		printl("", self, "S")

		try:
			position = self.seek.getPlayPosition()
		except:
			return None
		
		printl("", self, "C")
		return position

	#===========================================================================
	#
	#===========================================================================
	def buildPosterData(self):
		printl("", self, "S")

		mediaPath = config.plugins.dreamplex.mediafolderpath.value
		image_prefix = Singleton().getPlexInstance().getServerName().lower()

		self.poster_postfix = "_poster_" + self.width + "x" + self.height + "_v2.jpg"


		if self.isShow:
			self.whatPoster = mediaPath + image_prefix + "_" + self.show_id + self.poster_postfix
		else:
			self.whatPoster = mediaPath + image_prefix + "_" + self.media_id + self.poster_postfix

		printl( "what poster: " + self.whatPoster, self, "D")

		printl("builded poster data: " + str(self.whatPoster), self, "D")

		if not fileExists(self.whatPoster):
			self.downloadPoster()

		if config.plugins.dreamplex.lcd4linux.value:
			self.preparePosterForExternalUsage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadPoster(self):
		printl("", self, "S")
		printl("self.width:" + str(self.width), self, "D")
		printl("self.height:" + str(self.height), self, "D")

		if self.isShow:
			download_url = self.selection[1]["art"]
		else:
			download_url = self.selection[1]["thumb"]

		download_url = download_url.replace('&width=999&height=999', '&width=' + self.width + '&height=' + self.height)

		printl( "download url: " + download_url, self, "D")
		printl( "what poster: " + self.whatPoster, self, "D")

		if download_url != "":
			response = self.plexInstance.doRequest(download_url)

			printl("starting download", self, "D")
			with open(self.whatPoster, "wb") as local_file:
				local_file.write(response)
				local_file.close()
		else:
			printl("no posterdata in xml response, skipping ...", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def preparePosterForExternalUsage(self):
		printl("", self, "S")

		tempPath = config.plugins.dreamplex.logfolderpath.value
		self.tempPoster = tempPath + "dreamplex.jpg"

		from shutil import copy2

		copy2(self.whatPoster, self.tempPoster)

		printl("", self, "C")
