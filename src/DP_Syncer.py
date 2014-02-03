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
import Components
import os

#noinspection PyUnresolvedReferences
from enigma import eTimer
from threading import Thread

from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from Components.ProgressBar import ProgressBar

from twisted.web.client import downloadPage

from Screens.Screen import Screen

from Tools.Directories import fileExists

from __plugin__ import Plugin
from DP_PlexLibrary import PlexLibrary
from DPH_Singleton import Singleton
from DP_ViewFactory import getMovieViewDefaults

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
# GLOBAL
#===============================================================================
gSyncInfo = None

#===========================================================================
#
#===========================================================================
def getSyncInfoInstance():
	global gSyncInfo
	if gSyncInfo is None:
		gSyncInfo = MediaSyncerInfo()
	return gSyncInfo

#===========================================================================
#
#===========================================================================
def registerOutputInstance(instance, session):
	syncInfo = getSyncInfoInstance()
	printl("registerOutputInstance::type(syncInfo): " + str(type(syncInfo)))
	syncInfo.registerOutputInstance(instance, session)

#===========================================================================
#
#===========================================================================
def unregisterOutputInstance(instance):
	syncInfo = getSyncInfoInstance()
	printl("unregisterOutputInstance::type(syncInfo): " + str(type(syncInfo)))
	syncInfo.unregisterOutputInstance(instance)



#===========================================================================
#
#===========================================================================
class DPS_Syncer(Screen):

	_session = None
	_serverSet = False

	def __init__(self, session):
		Screen.__init__(self, session)

		self._session = session
		self["console"] = ScrollLabel()

		self["txt_red"] = Label()
		self["txt_green"] = Label()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyRed,
			"blue": self.keyBlue,
			"yellow": self.keyYellow,
			"green": self.keyGreen,
			"bouquet_up": self.keyBouquetUp,
			"bouquet_down": self.keyBouquetDown,
			"ok": self.okbuttonClick,
			"cancel": self.keyCancel,
		}, -2)

		self.getServerList()

		self["menu"]= List(self.mainMenuList, True)

		self.onFirstExecBegin.append(self.startup)
		self.onLayoutFinish.append(self.readyToRun)

	#===============================================================================
	#
	#===============================================================================
	def startup(self):
		printl("", self, "S")

		registerOutputInstance(self, self._session)

		self.notifyStatus()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def readyToRun(self):
		printl("", self, "S")

		self["console"].setText("test")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getServerList(self):
		printl("", self, "S")

		self.mainMenuList = []

		# add servers to list
		for serverConfig in config.plugins.dreamplex.Entries:

			# only add the server if state is active
			if serverConfig.state.value:
				serverName = serverConfig.name.value

				self.mainMenuList.append((serverName, Plugin.MENU_SERVER, "serverEntry", serverConfig))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def okbuttonClick(self):
		printl("", self, "S")

		selection = self["menu"].getCurrent()

		if selection is not None:
			self.selectedEntry = selection[1]
			printl("selected entry " + str(self.selectedEntry), self, "D")

			if self.selectedEntry == Plugin.MENU_SERVER:
				printl("found Plugin.MENU_SERVER", self, "D")
				self.g_serverConfig = selection[3]

				# now that we know the server we establish global plexInstance
				self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self._session, self.g_serverConfig))

				self._serverSet = True

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def notifyStatus(self):
		printl("", self, "S")

		syncInfo = getSyncInfoInstance()
		printl("inProgress:" + str(syncInfo.inProgress), self, "D")

		if syncInfo.inProgress is True:
			pass
			#self["key_red"].setText(_("Hide"))
			#self["key_green"].setText(_("Abort"))
			#self["key_yellow"].setText("")
		else:
			pass
			#self["key_red"].setText(_("Manage"))
			#self["key_green"].setText(_("Complete Sync"))
			#self["key_yellow"].setText(_("Normal Sync"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyRed(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyYellow(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBlue(self):
		printl("", self, "S")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyGreen(self):
		printl("", self, "S")

		if self._serverSet:
			self.doMediaSync()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBouquetUp(self):
		printl("", self, "S")

		self["console"].pageUp()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBouquetDown(self):
		printl("", self, "S")

		self["console"].pageDown ()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def doMediaSync(self):
		printl("", self, "S")

		syncInfo = getSyncInfoInstance()

		if syncInfo.inProgress is False:
			syncInfo.start(MediaSyncer)
		else:
			syncInfo.abort()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def clearLog(self):
		printl("", self, "S")

		self["console"].setText("")
		self["console"].lastPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def appendLog(self, text):
		printl("", self, "S")

		self["console"].appendText(text + "\n")
		self["console"].lastPage()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setProgress(self, value):
		printl("", self, "S")

		self["progress"].setValue(value)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setRange(self, value):
		printl("", self, "S")

		self["progress"].range = (0, value)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyCancel(self):
		printl("", self, "S")

		self.close()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def close(self):
		printl("", self, "S")

		unregisterOutputInstance(self)

		Screen.close(self)

		printl("", self, "C")


#===========================================================================
#
#===========================================================================
class MediaSyncerInfo(object):
	outputInstance = []

	progress = 0
	range = 0
	log = []
	loglinesize = 40

	poster = None
	name = None
	year = None

	inProgress = False
	isFinished = False

	session = None

	thread = None

	#===========================================================================
	#
	#===========================================================================
	def start(self, myType):
		printl("", self, "S")

		try:
			if self.inProgress:
				return False
			self.reset()

			self.isFinished = False
			self.inProgress = True
			self.setOutput(None)
			self.thread = MediaSyncer(self.setOutput, self.setProgress, self.setRange, self.setInfo, self.finished, myType)
			self.thread.start()
			for outputInstance in self.outputInstance:
				outputInstance.notifyStatus()

			printl("", self, "C")
			return True
		except Exception, ex:
			printl("Exception: " + str(ex), self)

			printl("", self, "C")
			return False

	#===========================================================================
	#
	#===========================================================================
	def abort(self):
		printl("", self, "S")

		if not self.inProgress:

			printl("", self, "C")
			return False

		self.thread.abort()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def registerOutputInstance(self, instance, session):
		printl("", self, "S")

		try:
			if instance:
				self.outputInstance.append(instance)
			if session:
				self.session = session

			if self.inProgress:
				self.setRange(self.range)
				self.setProgress(self.progress)
				self.setInfo(self.poster, self.name, self.year)

				for outputInstance in self.outputInstance:
					outputInstance.clearLog()

				if len(self.log) > 0:
					for text in self.log:
						for outputInstance in self.outputInstance:
							outputInstance.appendLog(text)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def unregisterOutputInstance(self, instance):
		printl("", self, "S")

		try:
			if instance:
				self.outputInstance.remove(instance)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setOutput(self, text):
		printl("", self, "S")

		try:
			if text is None:
				del self.log[:]
				for outputInstance in self.outputInstance:
					outputInstance.clearLog()
			else :
				if len(self.log) >= self.loglinesize:
					del self.log[:]
					for outputInstance in self.outputInstance:
						outputInstance.clearLog()
						outputInstance.appendLog(text)
				else:
					for outputInstance in self.outputInstance:
						#pass
						outputInstance.appendLog(text)
				self.log.append(text)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setRange(self, value):
		printl("", self, "S")

		try:
			self.range = value
			for outputInstance in self.outputInstance:
				outputInstance.setRange(self.range)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setProgress(self, value):
		printl("", self, "S")

		try:
			self.progress = value
			for outputInstance in self.outputInstance:
				outputInstance.setProgress(self.progress)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setInfo(self, poster, name, year):
		printl("", self, "S")

		try:
			self.poster = poster
			self.name = name
			self.year = year
			for outputInstance in self.outputInstance:
				outputInstance.setPoster(self.poster)
				outputInstance.setName(self.name)
				outputInstance.setYear(self.year)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finished(self):
		printl("", self, "S")

		try:
			self.inProgress = False
			self.isFinished = True
			for outputInstance in self.outputInstance:
				outputInstance.notifyStatus()
			if len(self.outputInstance) == 0:
				pass
				#todo add screen after we are finished
				#self.session.open(ProjectValerieSyncFinished)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def reset(self):
		printl("", self, "S")

		try:
			self.linecount = 40
			self.progress = 0
			self.range = 0
			del self.log[:]

			self.poster = None
			self.name = None
			self.year = None

		except Exception, ex:
			printl("Exception: " + str(ex), self)

		printl("", self, "C")

#===========================================================================
#
#===========================================================================
class MediaSyncer(Thread):

	#===========================================================================
	#
	#===========================================================================
	def __init__ (self, output, progress, myRange, info, finished, mode):
		Thread.__init__(self)
		self.output = output
		self.progress = progress
		self.myRange = myRange
		self.info = info
		self.finished = finished
		self.mode = mode
		self.output(_("Thread running"))
		self.doAbort = False
		self.plexInstance = Singleton().getPlexInstance()

	#===========================================================================
	#
	#===========================================================================
	def abort(self):
		printl("", self, "S")

		self.doAbort = True
		self.output("Aborting sync! Saving and cleaning up!")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def run(self):
		printl("", self, "S")

		self.doAbort = False

		# get sections from server
		self.sectionList = self.plexInstance.displaySections()
		printl("sectionList: "+ str(self.sectionList),self, "D")
		movies = {}

		# get params
		params = getMovieViewDefaults()

		# get servername
		prefix = Singleton().getPlexInstance().getServerName().lower()

		b_height = params["elements"]["backdrop"]["height"]
		b_width = params["elements"]["backdrop"]["width"]
		b_postfix = params["elements"]["backdrop"]["postfix"]

		p_height = params["elements"]["poster"]["height"]
		p_width = params["elements"]["poster"]["width"]
		p_postfix = params["elements"]["poster"]["postfix"]

		l_height = "720"
		l_width = "1280"
		l_postfix = "_backdrop_1280x720.jpg"

		backdropVariants = [[b_height, b_width, b_postfix], [l_height, l_width, l_postfix]]
		posterVariants = [[p_height, p_width, p_postfix]]

		self.output("Reading section of the server ...")
		for section in self.sectionList:
			if section[2] == "movieEntry":
				printl("movie", self, "D")
				url = section[3]["t_url"] + "/all"
				self.output("got movie url: " + str(url))
				printl("url: " + str(url), self, "D")
				library, tmpAbc, tmpGenres = self.plexInstance.getMoviesFromSection(url)
				for movie in library:
					import time
					time.sleep(5)
					for variant in backdropVariants:
						t_height = variant[0]
						t_width = variant[1]
						t_postfix = variant[2]

						# location string
						location = config.plugins.dreamplex.mediafolderpath.value + str(prefix) + "_" +  str(movie[1]["ratingKey"]) + str(t_postfix)

						# check if backdrop exists
						if fileExists(location):
							self.output("backdrop exists under the location " + str(location))
							continue
						else:
							self.output("file does not exist ... start downloading")
							#download backdrop
							self.downloadMedia(movie[2]["fanart_image"], location, t_height, t_width)

					for variant in posterVariants:
						t_height = variant[0]
						t_width = variant[1]
						t_postfix = variant[2]

						# location string
						location = config.plugins.dreamplex.mediafolderpath.value + str(prefix) + "_" +  str(movie[1]["ratingKey"]) + str(t_postfix)

						# check if poster exists
						if fileExists(location):
							self.output("poster exists under the location " + str(location))
							continue
						else:
							self.downloadMedia(movie[2]["thumb"], location, t_height, t_width)

					movies[movie[0]] = (movie[2]["fanart_image"], movie[2]["thumb"])
				printl("movies: " + str(library), self, "D")

			#if section[2] == "showEntry":
			#	printl("tvshow", self, "D")
			#	url = section[3]["t_url"]
			#	printl("url: " + str(url), self, "D")
			#	shows = self.plexInstance.getShowsFromSection(url)
			#	printl("shows: " + str(shows), self, "D")


		self.finished()

		self.output(_("Done"))
		self.output("---------------------------------------------------")
		self.output(_("Press Exit / Back"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def downloadMedia(self, download_url, location, width, height):
		printl("", self, "S")

		if download_url:
			download_url = download_url.replace('&width=999&height=999', '&width=' + width + '&height=' + height)
			printl( "download url " + download_url, self, "D")

		if not download_url:
			printl("no pic data available", self, "D")
		else:
			printl("starting download", self, "D")
			downloadPage(download_url, location)

		return True

		printl("", self, "C")