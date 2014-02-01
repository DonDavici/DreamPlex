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

from time import sleep

from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput

#noinspection PyUnresolvedReferences
from enigma import eServiceReference, eConsoleAppContainer, iPlayableService, eTimer, eServiceCenter, iServiceInformation

from Tools import Notifications

from Components.config import config
from Components.ActionMap import ActionMap
from Components.Slider import Slider
from Components.Language import language
from Components.Sources.StaticText import StaticText
from Components.ServiceEventTracker import ServiceEventTracker

from DPH_Singleton import Singleton

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
class DP_Player(MoviePlayer):

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
	
	title = ""
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

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, playerData, resume=False):
		printl("", self, "S")
		
		self.session = session
				
		self.videoData = playerData['videoData']
		self.mediaData = playerData['mediaData']
		
		# go through the data out of the function call
		self.resume = resume
		self.resumeStamp = int(playerData['resumeStamp']) / 1000 # plex stores seconds * 1000
		self.server = str(playerData['server'])
		self.id = str(playerData['id'])
		self.multiUserServer = playerData['multiUserServer']
		self.url = str(playerData['playUrl'])
		self.transcodingSession = str(playerData['transcodingSession'])
		self.playbackType = str(playerData['playbackType'])
		self.connectionType = str(playerData['connectionType'])
		self.universalTranscoder = playerData['universalTranscoder']
		self.localAuth = playerData['localAuth']
		
		# lets prepare all additional data for a better experience :-)
		self.title = str(self.videoData['title'])
		self.tagline = str(self.videoData['tagline'])
		self.summary = str(self.videoData['summary'])
		self.year = str(self.videoData['year'])
		self.studio = str(self.videoData['studio'])
		self.duration = str(self.videoData['duration'])
		self.contentRating = str(self.videoData['contentRating'])
		
		self.audioCodec = str(self.mediaData['audioCodec'])
		self.videoCodec = str(self.mediaData['videoCodec'])
		self.videoResolution = str(self.mediaData['videoResolution'])
		self.videoFrameRate = str(self.mediaData['videoFrameRate'])

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
				# todo add errorhandler
				raise Exception

		
		printl("self.ENIGMA_SERVICE_ID = " + str(self.ENIGMA_SERVICE_ID), self, "I")
		
		sref = eServiceReference(self.ENIGMA_SERVICE_ID, 0, self.url)
		sref.setName(self.title)
		
		# lets call the movieplayer
		MoviePlayer.__init__(self, session, sref)
		
		self.skinName = "DPS_PlexPlayer"
		
		self.service = sref
		self.bufferslider = Slider(0, 100)
		self["bufferslider"] = self.bufferslider
		if self.playbackType == "2":
			self["bufferslider"].setValue(100)
		else:
			self["bufferslider"].setValue(1)
		self["mediaTitle"] = StaticText(self.title)
		self["label_update"] = StaticText()
		self.bufferSeconds = 0
		self.bufferPercent = 0
		self.bufferSecondsLeft = 0
		self.bitrate = 0
		self.endReached = False

		self["actions"] = ActionMap(["OkCancelActions", "TvRadioActions", "InfobarSeekActions", "MediaPlayerActions"],
		{
		"ok": self.ok,
		"cancel": self.hide,
		"keyTV": self.leavePlayer,
		"stop": self.leavePlayer,
		"leavePlayer": self.hide,
		"next": self.seekManual,
		"previous": self.seekManual,
		"stopRunningRecords": self.leavePlayer
		}, -2)
		
		# it will stop up/down/movielist buttons opening standard movielist whilst playing movie in plex
		if self.has_key('MovieListActions'):
			self["MovieListActions"].setEnabled(False)
		
		service1 = self.session.nav.getCurrentService()
		self.seek = service1 and service1.seek()

		# if self.seek != None:
		#	rLen = self.getPlayLength()
		#	rPos = self.getPlayPosition()
		#	printl("rLen: " + str(rLen), self, "I")
		#	printl("rPos: " + str(rPos), self, "I")
		#=======================================================================
			
		if self.resume == True and self.resumeStamp is not None and self.resumeStamp > 0.0:
			seekwatcherThread = threading.Thread(target=self.seekWatcher,args=(self,))
			seekwatcherThread.start()

		if self.multiUserServer:
			printl("we are a multiuser server", self, "D")
			if self.connectionType == "2" or (self.connectionType == "0" and self.localAuth):
				printl("we are configured for multiuser", self, "D")
				self.multiUser = True
			
		if self.multiUser:
			self.timelinewatcherthread_stop = threading.Event()
			self.timelinewatcherthread_wait = threading.Event()
			self.timelinewatcherthread_stop.clear()
			self.timelinewatcherthread_wait.clear()
			self.timelinewatcherThread = threading.Thread(target=self.timelineWatcher,name="TimeLineWatcherThread", args=(self.timelinewatcherthread_stop, self.timelinewatcherthread_wait,))
			self.timelinewatcherThread.daemon = True

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		{
			iPlayableService.evUser+10: self.__evAudioDecodeError,
			iPlayableService.evUser+11: self.__evVideoDecodeError,
			iPlayableService.evUser+12: self.__evPluginError,
			iPlayableService.evBuffering: self.__evUpdatedBufferInfo,
			iPlayableService.evEOF: self.__evEOF,
		})

		if self.playbackType == "2":
			self.bufferFull()
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
		
		self.bufferInfo()
		
		#printl("", self, "C")
	

	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		#printl("", self, "S")
		
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
		
		if self.playbackType == "2":
			self.bufferFull() # redundant
			return
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
						time = self.resumeStamp * 90000
						printl( "seeking to " + str(time) + " length " + str(length) + " ", self, "I")
						self.resumeStamp = None
						if time < 90000:
							printl( "skip seeking < 10s", self, "I")
							printl("", self, "C")
							return
						#if config.plugins.dreamplex.setBufferSize.value:
							#self.session.nav.getCurrentService().streamed().setBufferSize(config.plugins.dreamplex.bufferSize.value)
						self.doSeek(int(time))
		
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
			self.timelinewatcherthread_wait.clear()
			if not self.timelinewatcherThread.isAlive():
				self.timelinewatcherthread_stop.clear()
				sleep(2)
				try:
					self.timelinewatcherThread.start()
				except:
					pass
		
		#printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def bufferEmpty(self):
		#printl("", self, "S")
		
		if config.plugins.dreamplex.showInfobarOnBuffer.value:
			#show infobar to indicate buffer is empty 
			self.show()

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
			self.close()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def doEofInternal(self, playing):
		printl("", self, "S")
		
		self.leavePlayerConfirmed(True)
		
		printl("", self, "C")

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
			progress = 100;
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		
		if self.multiUser:
			plexInstance.getTimelineURL(self.server, "/library/sections/onDeck", self.id, "stopped", str(currentTime*1000), str(totalTime*1000))
		
		#Legacy PMS Server server support before MultiUser version v0.9.8.0 and if we are not connected via myPlex
		else:
			if currentTime < 30:
				printl("Less that 30 seconds, will not set resume", self, "I")
		
			#If we are less than 95% complete, store resume time
			elif progress < 95:
				printl("Less than 95% progress, will store resume time", self, "I" )
				plexInstance.doRequest("http://"+self.server+"/:/progress?key="+self.id+"&identifier=com.plexapp.plugins.library&time="+str(currentTime*1000))

			#Otherwise, mark as watched
			else:
				printl( "Movie marked as watched. Over 95% complete", self, "I")
				plexInstance.doRequest("http://"+self.server+"/:/scrobble?key="+self.id+"&identifier=com.plexapp.plugins.library")

		if self.multiUser and self.timelinewatcherThread.isAlive():
			self.timelinewatcherthread_wait.set()
			self.timelinewatcherthread_stop.set()

		printl("", self, "C")	   

	#===========================================================================
	# stopTranscoding
	#===========================================================================
	def stopTranscoding(self):
		printl("", self, "S")
		
		if self.multiUser:
			self.timelinewatcherthread_wait.set()
			self.timelinewatcherthread_stop.set()
		
		instance = Singleton()
		plexInstance = instance.getPlexInstance()
		
		if self.universalTranscoder:
			plexInstance.doRequest("http://"+self.server+"/video/:/transcode/universal/stop?session=" + self.transcodingSession)
		else:
			plexInstance.doRequest("http://"+self.server+"/video/:/transcode/segmented/stop?session=" + self.transcodingSession)
		
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
	# timelineWatcher
	#===========================================================================
	def timelineWatcher(self, stop_event, wait_event):
		printl("", self, "S")

		while not stop_event.is_set():
			while not wait_event.is_set():
				ret = self.updateTimeline()
				if ret:
					wait_event.wait(3)
					continue
				else:
					wait_event.wait(3)
					break
				
			stop_event.wait(1)
			continue
		
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

			instance = Singleton()
			plexInstance = instance.getPlexInstance()

			seekState = self.seekstate
			if seekState == self.SEEK_STATE_PAUSE:
				printl( "Movies PAUSED time: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress), self,"D" )
				plexInstance.getTimelineURL(self.server, "/library/sections/onDeck", self.id, "paused", str(currentTime*1000), str(totalTime*1000))

			if seekState == self.SEEK_STATE_PLAY :
				printl( "Movies PLAYING time: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress),self,"D" )
				plexInstance.getTimelineURL(self.server, "/library/sections/onDeck", self.id, "playing", str(currentTime*1000), str(totalTime*1000))

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
