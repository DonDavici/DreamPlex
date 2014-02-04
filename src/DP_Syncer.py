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
#noinspection PyUnresolvedReferences
from enigma import eTimer, ePythonMessagePump

from threading import Thread
from threading import Lock

from Components.Label import Label
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.config import config
from Components.ScrollLabel import ScrollLabel

from twisted.web.client import downloadPage

from Screens.Screen import Screen

from Tools.Directories import fileExists

from __plugin__ import Plugin
from DP_PlexLibrary import PlexLibrary
from DPH_Singleton import Singleton
from DP_ViewFactory import getMovieViewDefaults
from DPH_Singleton import Singleton

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===========================================================================
#
#===========================================================================
class DPS_Syncer(Screen):

	_session = None
	_serverSet = False

	def __init__(self, session):
		Screen.__init__(self, session)

		self.mediaSyncerInfo = Singleton().getMediaSyncInstance() #MediaSyncerInfo().instance
		printl("self.mediaSyncer: " + str(self.mediaSyncerInfo), self, "D")
		self.mediaSyncerInfo.setCallbacks(self.callback_infos, self.callback_finished)

		self._session = session
		self["output"] = ScrollLabel()

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
		}, -2)

		self.getServerList()

		self["menu"]= List(self.mainMenuList, True)

		self.onFirstExecBegin.append(self.startup)
		self.onLayoutFinish.append(self.readyToRun)
		self.onClose.append(self.__onClose)

	#===============================================================================
	#
	#===============================================================================
	def __onClose(self):
		printl("", self, "S")

		self.mediaSyncerInfo.setCallbacks(None, None)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def startup(self):
		printl("", self, "S")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def readyToRun(self):
		printl("", self, "S")

		self["output"].setText("Starting ...")

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

	#===========================================================================
	#
	#===========================================================================
	def keyRed(self):
		printl("", self, "S")

		self.cancel()

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

		if self.mediaSyncerInfo.isRunning():
			self.close(1)
		else:
			self.close(0)

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

		self["output"].pageUp()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBouquetDown(self):
		printl("", self, "S")

		self["output"].pageDown ()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def doMediaSync(self):
		printl("", self, "S")

		self.mediaSyncerInfo.startSyncing()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def callback_infos(self, info):
		printl("", self, "S")

		self["output"].setText(info)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def callback_finished(self):
		printl("", self, "S")

		self["output"].setText(_("Finished"))
		self["txt_green"].setText(_("Close"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def cancel(self):
		printl("", self, "S")

		self.mediaSyncerInfo.cancel()
		self["output"].setText(_("Cancelled!"))

		printl("", self, "C")

#===========================================================================
#
#===========================================================================
class MediaSyncerInfo(object):
	instance = None

	def __init__(self):
		printl("", self, "S")

		assert not MediaSyncerInfo.instance, "only one MediaSyncerInfo instance is allowed!"
		MediaSyncerInfo.instance = self # set instance
		self.syncer = None
		self.running = False
		self.backgroundMediaSyncer = None

		self.callback_infos = None
		self.callback_finished = None

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startSyncing(self, arg = None):
		printl("", self, "S")

		if not self.running:
			self.backgroundMediaSyncer = BackgroundMediaSyncer()
			self.backgroundMediaSyncer.MessagePump.recv_msg.get().append(self.gotThreadMsg)

			if arg:
				self.backgroundMediaSyncer.setArg(arg)

			self.backgroundMediaSyncer.startSyncing()
			self.running = True

		printl("", self, "C")

	#===========================================================================
	# msg as second params is needed -. do not remove even if it is not used
	# form outside!!!!
	#===========================================================================
	# noinspection PyUnusedLocal
	def gotThreadMsg(self, msg):
		printl("", self, "S")

		msg = self.backgroundMediaSyncer.Message.pop()
		self.infoCallBack(msg[1])

		if msg[0] == THREAD_FINISHED:
			# clean up
			self.backgroundMediaSyncer.MessagePump.recv_msg.get().remove(self.gotThreadMsg)
			self.callback = None
			self.backgroundMediaSyncer = None
			self.running = False
			self.done()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setCallbacks(self, callback_infos, callback_finished):
		printl("", self, "S")

		self.callback_infos = callback_infos
		self.callback_finished = callback_finished

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def isRunning(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.running

	#===========================================================================
	#
	#===========================================================================
	def infoCallBack(self,text):
		printl("", self, "S")

		printl("text: " + str(text), self, "D")
		if text and self.callback_infos:
			self.callback_infos(text)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def done(self):
		printl("", self, "S")

		if self.callback_finished:
			self.callback_finished()

		self.running = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def cancel(self):
		printl("", self, "S")

		if self.backgroundMediaSyncer and self.running:
			self.backgroundMediaSyncer.Cancel()

		printl("", self, "C")

#===========================================================================
#
#===========================================================================
class BackgroundMediaSyncer(Thread):

	def __init__ (self):
		Thread.__init__(self)
		self.cancel = False
		self.arg = None
		self.messages = ThreadQueue()
		self.messagePump = ePythonMessagePump()
		self.running = False

		self.plexInstance = Singleton().getPlexInstance()

	#===========================================================================
	#
	#===========================================================================
	def getMessagePump(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.messagePump

	#===========================================================================
	#
	#===========================================================================
	def getMessageQueue(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.messages

	#===========================================================================
	#
	#===========================================================================
	def setArg(self, arg):
		printl("", self, "S")

		self.arg = arg

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def Cancel(self):
		printl("", self, "S")

		self.cancel = True

		printl("", self, "C")

	#===========================================================================
	#PROPERTIES
	#===========================================================================
	MessagePump = property(getMessagePump)
	Message = property(getMessageQueue)

	#===========================================================================
	#
	#===========================================================================
	def startSyncing(self):
		printl("", self, "S")

		# Once a thread object is created, its activity must be started by calling the thread’s start() method.
		# This invokes the run() method in a separate thread of control.
		self.start()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def run(self):
		printl("", self, "S")

		mp = self.messagePump

		self.running = True
		self.cancel = False

		msg_text = _("some text here")
		self.messages.push((THREAD_WORKING, msg_text))
		mp.send(0)

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

		try:
			msg_text = _("Reading section of the server ...")
			self.messages.push((THREAD_WORKING, msg_text))
			mp.send(0)

			for section in self.sectionList:
				# interupt if needed
				if self.cancel:
					break

				if section[2] == "movieEntry":
					printl("movie", self, "D")
					url = section[3]["t_url"] + "/all"

					msg_text = _("got movie url: " + str(url))
					self.messages.push((THREAD_WORKING, msg_text))
					mp.send(0)

					printl("url: " + str(url), self, "D")
					library, tmpAbc, tmpGenres = self.plexInstance.getMoviesFromSection(url)
					for movie in library:
						import time
						time.sleep(5)
						# interupt if needed
						if self.cancel:
							break

						for variant in backdropVariants:
							# interupt if needed
							if self.cancel:
								break

							t_height = variant[0]
							t_width = variant[1]
							t_postfix = variant[2]

							# location string
							location = config.plugins.dreamplex.mediafolderpath.value + str(prefix) + "_" +  str(movie[1]["ratingKey"]) + str(t_postfix)

							# check if backdrop exists
							if fileExists(location):
								msg_text = _("backdrop exists under the location " + str(location))
								self.messages.push((THREAD_WORKING, msg_text))
								mp.send(0)
								continue
							else:
								msg_text = _("file does not exist ... start downloading")
								self.messages.push((THREAD_WORKING, msg_text))
								mp.send(0)
								#download backdrop
								self.downloadMedia(movie[2]["fanart_image"], location, t_height, t_width)

						for variant in posterVariants:
							# interupt if needed
							if self.cancel:
								break

							t_height = variant[0]
							t_width = variant[1]
							t_postfix = variant[2]

							# location string
							location = config.plugins.dreamplex.mediafolderpath.value + str(prefix) + "_" +  str(movie[1]["ratingKey"]) + str(t_postfix)

							# check if poster exists
							if fileExists(location):
								msg_text = _("poster exists under the location " + str(location))
								self.messages.push((THREAD_WORKING, msg_text))
								mp.send(0)
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

			if self.cancel:
				self.messages.push((THREAD_FINISHED, _("Process aborted.\nPress OK to close.") ))
			else:
				self.messages.push((THREAD_FINISHED, _("We did it :-)")))

		except Exception, e:
			self.messages.push((THREAD_FINISHED, _("Error!\nError-message:%s\nPress OK to close." % e) ))
		finally:
			mp.send(0)

		self.running = False

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



THREAD_WORKING = 1
THREAD_FINISHED = 2
THREAD_ERROR = 3
#===========================================================================
#
#===========================================================================
class ThreadQueue:
	def __init__(self):
		self.__list = [ ]
		self.__lock = Lock()

	#===========================================================================
	#
	#===========================================================================
	def push(self, val):
		lock = self.__lock
		lock.acquire()
		self.__list.append(val)
		lock.release()

	#===========================================================================
	#
	#===========================================================================
	def pop(self):
		lock = self.__lock
		lock.acquire()
		ret = self.__list.pop()
		lock.release()
		return ret