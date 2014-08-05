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
import time
from time import sleep

from enigma import ePicLoad, eTimer
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen

#noinspection PyUnresolvedReferences
from enigma import eServiceReference, eConsoleAppContainer, iPlayableService, eTimer, eServiceCenter, iServiceInformation

from Tools import Notifications

from Components.AVSwitch import AVSwitch
from Components.config import config
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Slider import Slider
from Components.Sources.StaticText import StaticText
from Components.Language import language
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase

from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarSeek, InfoBarAudioSelection, \
	InfoBarServiceNotifications, InfoBarSimpleEventView, \
	InfoBarExtensions, InfoBarNotifications, \
	InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarCueSheetSupport

from DPH_Singleton import Singleton

from __common__ import printl2 as printl, convertSize, encodeMe
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
class DP_Player(InfoBarBase, InfoBarShowHide, InfoBarCueSheetSupport,
		InfoBarSeek, InfoBarAudioSelection, HelpableScreen,
		InfoBarServiceNotifications, InfoBarSimpleEventView,
		InfoBarSubtitleSupport, Screen, InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications):

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

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, listViewList, currentIndex, myParams, autoPlayMode, resumeMode, playbackMode, poster):
		printl("", self, "S")
		printl("currentIndex: " + str(currentIndex), self, "D")
		
		self.session = session
		self.listViewList = listViewList
		self.currentIndex = currentIndex
		self.playerData = {}
		self.listCount = len(self.listViewList)
		self.autoPlayMode = autoPlayMode
		self.resumeMode = resumeMode
		self.playbackMode = playbackMode
		self.whatPoster = poster

		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()

		self.myParams = myParams
		self["mediaTitle"] = StaticText()
		Screen.__init__(self, session)

		self.plexInstance = Singleton().getPlexInstance()

		for x in HelpableScreen, InfoBarShowHide, InfoBarBase, InfoBarSeek, \
				InfoBarAudioSelection, InfoBarSimpleEventView, \
				InfoBarServiceNotifications, InfoBarSubtitleSupport, \
				InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarNotifications:
			printl("x: " + str(x), self, "D")
			x.__init__(self)

		self.skinName = "DPS_PlexPlayer"

		self.bufferslider = Slider(0, 100)
		self["bufferslider"] = self.bufferslider

		self.bufferSeconds = 0
		self.bufferPercent = 0
		self.bufferSecondsLeft = 0
		self.bitrate = 0
		self.endReached = False

		self["actions"] = ActionMap(["InfobarSeekActions", "DPS_Player"],
		{
		"ok": self.ok,
		"cancel": self.hide,
		"keyTv": self.leavePlayer,
		"stop": self.leavePlayer,
		"seekManual": self.seekManual,
		"playNext": self.playNextEntry,
		"playPrevious": self.playPreviousEntry,
		}, -2)

		self["poster"] = Pixmap()
		self["shortDescription"] = Label()

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

		self.onLayoutFinish.append(self.setPoster)

		# from here we go on
		self.onFirstExecBegin.append(self.playMedia)

	#==============================================================================
	#
	#==============================================================================
	def playMedia(self):
		printl("", self, "S")

		selection = self.listViewList[self.currentIndex]

		self.media_id = selection[1]['ratingKey']
		server = selection[1]['server']

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

		self.mediaFileUrl = Singleton().getPlexInstance().mediaType({'key': self.options[result][0], 'file' : self.options[result][1]}, self.server)

		self.buildPlayerData()

		printl("We have selected media at " + self.mediaFileUrl, self, "I")
		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def buildPlayerData(self):
		printl("", self, "S")

		Singleton().getPlexInstance().setPlaybackType(str(self.playbackMode))

		self.playerData[self.currentIndex] = Singleton().getPlexInstance().playLibraryMedia(self.media_id, self.mediaFileUrl)

		# populate addional data
		self.setPlayerData()

		self.playSelectedMedia()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def playSelectedMedia(self):
		printl("", self, "S")

		resumeStamp = self.playerData[self.currentIndex]['resumeStamp']
		printl("resumeStamp: " + str(resumeStamp), self, "I")

		if self.playerData[self.currentIndex]['fallback']:
			message = _("Sorry I didn't find the file on the provided locations")
			locations = _("Location:") + "\n " + self.playerData[0]['locations']
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

		self.EXpicloadPoster.startDecode(self.whatPoster,0,0,False)
		ptr = self.EXpicloadPoster.getData()

		self["poster"].instance.setPixmap(ptr)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setServiceReferenceData(self):
		printl("", self, "S")

		self["mediaTitle"].setText(self.title)

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

		# increase position
		self.currentIndex += 1

		# check if we are at the end of the list we start all over
		if self.currentIndex > len(self.listViewList):
			self.currentIndex = 0

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
			self.currentIndex = max(self.listViewList)

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

		# populate self.sref with new data
		self.setServiceReferenceData()

		# start playback
		self.session.nav.playService(self.sref)

		service1 = self.session.nav.getCurrentService()
		self.seek = service1 and service1.seek()

		if resume == True and self.resumeStamp is not None and self.resumeStamp > 0.0:
			seekwatcherThread = threading.Thread(target=self.seekWatcher,args=(self,))
			seekwatcherThread.start()

		if self.multiUserServer:
			printl("we are a multiuser server", self, "D")
			self.multiUser = True
			self.timelineWatcher = eTimer()
			self.timelineWatcher.callback.append(self.updateTimeline)

		if self.playbackType == "2":
			self["bufferslider"].setValue(100)
		else:
			self["bufferslider"].setValue(1)

		printl("", self, "C")

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

		self.title = encodeMe(self.videoData['title'])
		self["shortDescription"].setText(encodeMe(self.videoData['summary']))

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
			# we lock the infobar until the buffer is full for better feedback to user
			self.lockShow()
			self.bufferInfo()
		
		#printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		#printl("", self, "S")

		if self.playbackType != "2":
			self.bufferInfo()

		if self.shown:
			self.hide()
		else:
			self.show()

		#printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def bufferInfo(self):
		#printl("", self, "S")

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
			printl("exception: " + str(e), self, "W")
		
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
	
		if self.multiUser:
			# because the buffer is full we start updating timeline
			self.timelineWatcher.start(5000,False)

		# now we unlock again so that the infobar can dismiss
		self.unlockShow()
		self.hide()

		#printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def bufferEmpty(self):
		#printl("", self, "S")
		
		if config.plugins.dreamplex.showInfobarOnBuffer.value:
			#show infobar to indicate buffer is empty 
			self.show()

		if self.multiUser and self.timelineWatcher is not None:
			self.timelineWatcher.stop()

		#printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def setSeekState(self, state, unknow=False):
		printl("", self, "S")
		
		super(DP_Player, self).setSeekState(state)

		printl("", self, "C")
	
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
	def leavePlayerConfirmed(self, answer):
		printl("", self, "S")
		
		if answer:
			self.handleProgress()

			if self.playbackType == "1":
				self.stopTranscoding()

			self.session.nav.playService(self.currentService)
			self.close()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def doEofInternal(self, playing):
		printl("", self, "S")

		if self.autoPlayMode:
			if not self.nextPlaylistEntryAvailable():
				self.leavePlayerConfirmed(True)
			else:
				# first we write back the state of the current file to the plex server
				self.handleProgress()

				#start next file
				self.playNextEntry()
		else:
			self.leavePlayerConfirmed(True)
		
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
	def handleProgress(self):
		printl("", self, "S")

		currentTime = self.getPlayPosition()[1] / 90000
		totalTime = self.getPlayLength()[1] / 90000

		if currentTime is not None and currentTime > 0 and totalTime is not None and totalTime > 0:
			progress = currentTime / (totalTime/100)
			printl( "played time is %s secs of %s @ %s%%" % ( currentTime, totalTime, progress),self, "I" )
		else:
			progress = 100
		
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
		try:	
			currentTime = self.getPlayPosition()[1] / 90000
			totalTime = self.getPlayLength()[1] / 90000
			progress = int(( float(currentTime) / float(totalTime) ) * 100)
			if totalTime > 100000:
				return True

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
		
		position = self.seek.getPlayPosition()
		
		printl("", self, "C")
		return position
