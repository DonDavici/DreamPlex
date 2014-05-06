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
from enigma import eTimer, ePythonMessagePump, eConsoleAppContainer

from threading import Thread
from threading import Lock

from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap

from twisted.web.client import downloadPage

from Screens.Screen import Screen

from Tools.Directories import fileExists

from DP_PlexLibrary import PlexLibrary
from DP_ViewFactory import getMovieViewDefaults
from DPH_Singleton import Singleton

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===========================================================================
#
#===========================================================================
class DPS_Syncer(Screen):

	_session = None
	_mode = None

	def __init__(self, session, serverConfig, mode):
		Screen.__init__(self, session)

		# now that we know the server we establish global plexInstance
		self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self._session, serverConfig))

		# we are "sync" or "render"
		self._mode = mode

		# we use the global g_mediaSyncerInfo.instance to take care only having one instance
		self.mediaSyncerInfo = g_mediaSyncerInfo.instance
		printl("self.mediaSyncer: " + str(self.mediaSyncerInfo), self, "D")
		self.mediaSyncerInfo.setCallbacks(self.callback_infos, self.callback_finished)
		self.mediaSyncerInfo.setMode(self._mode)

		self._session = session
		self["output"] = ScrollLabel()
		self["output"].setText(_("HURRA"))

		self["txt_green"] = Label()
		self["txt_green"].setText("Start Sync")
		self["btn_green"] = Pixmap()

		self["txt_blue"] = Label()
		self["txt_blue"].setText("run in Background")
		self["btn_blue"] = Pixmap()

		self["txt_red"] = Label()
		self["txt_red"].setText("Abort Sync")
		self["btn_red"] = Pixmap()

		self["txt_exit"] = Label()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyRed,
			"blue": self.keyBlue,
			"yellow": self.keyYellow,
			"green": self.keyGreen,
			"bouquet_up": self.keyBouquetUp,
			"bouquet_down": self.keyBouquetDown,
			"cancel": self.exit,
		}, -2)

		self.onFirstExecBegin.append(self.startup)
		self.onLayoutFinish.append(self.finishLayout)
		self.onClose.append(self.__onClose)

	#===============================================================================
	#
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle("Server - Syncer")

		if self.mediaSyncerInfo.isRunning():
			self["txt_green"].hide()
			self["btn_green"].hide()
			self["txt_exit"].hide()

		else:
			self["txt_exit"].setText(_("Exit"))

			self["txt_red"].hide()
			self["btn_red"].hide()

			self["txt_blue"].hide()
			self["btn_blue"].hide()


		printl("", self, "C")

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

	#===========================================================================
	#
	#===========================================================================
	def keyRed(self):
		printl("", self, "S")

		if self.mediaSyncerInfo.isRunning():
			self.cancel()
			self["txt_green"].show()
			self["btn_green"].show()

			self["txt_blue"].hide()
			self["btn_blue"].hide()

			self["txt_red"].hide()
			self["btn_red"].hide()

			self["txt_exit"].show()


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

		if not self.mediaSyncerInfo.isRunning():
			self.doMediaSync()
			self["txt_blue"].show()
			self["btn_blue"].show()
			self["btn_red"].show()
			self["txt_red"].show()
			self["btn_green"].hide()
			self["txt_green"].hide()
			self["txt_exit"].hide()

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
		self["txt_blue"].hide()
		self["btn_blue"].hide()

		self["txt_exit"].show()

		self["txt_red"].hide()
		self["btn_red"].hide()

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
	def exit(self):
		printl("", self, "S")

		if not self.mediaSyncerInfo.isRunning():
			self.close(0)

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
		self.mode = None

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startSyncing(self):
		printl("", self, "S")

		if not self.running:
			self.backgroundMediaSyncer = BackgroundMediaSyncer()
			self.backgroundMediaSyncer.MessagePump.recv_msg.get().append(self.gotThreadMsg)
			self.backgroundMediaSyncer.setMode(self.mode)

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
	def setMode(self, mode):
		printl("", self, "S")

		self.mode = mode

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

# !!! important !!!!
# this is a singleton implementation so that there is only one instance of this class
# it can be also imported from other classes with from file import g_mediaSyncerInfo
g_mediaSyncerInfo = MediaSyncerInfo()

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
	def setMode(self, mode):
		printl("", self, "S")

		self.mode = mode

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
		printl("mode: " + str(self.mode), self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def run(self):
		printl("", self, "S")

		if self.mode == "render":
			self.renderBackdrops()

		elif self.mode == "sync":
			self.syncMedia()

		else:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def renderBackdrops(self):

		printl("", self, "S")

		self.running = True
		self.cancel = False
		msg_text = _("some text here")
		self.messages.push((THREAD_WORKING, msg_text))
		self.messagePump.send(0)
		import os
		try:
			for myFile in os.listdir(config.plugins.dreamplex.mediafolderpath.value):
				if self.cancel:
					break

				# firt we check for images in the right size
				if "1280x720.jpg" in myFile:
					# if we got one we remove the .jpg at the end to check if there was a backdropmovie generated already
					myFileWoExtension = myFile[:-4]

					# location string
					location = config.plugins.dreamplex.mediafolderpath.value + myFileWoExtension + ".m1v"
					# check if backdrop video exists
					if fileExists(location):
						msg_text = _("backdrop video exists under the location " + str(location))
						self.messages.push((THREAD_WORKING, msg_text))
						self.messagePump.send(0)
						continue
					else:
						msg_text = _("started rendering backdrop video: " + str(location))
						self.messages.push((THREAD_WORKING, msg_text))
						self.messagePump.send(0)

						printl("started rendering myFile: " + str(location),self, "D")

						cmd = "jpeg2yuv -v 0 -f 25 -n1 -I p -j " + config.plugins.dreamplex.mediafolderpath.value + str(myFile) + " | mpeg2enc -v 0 -f 12 -x 1280 -y 720 -a 3 -4 1 -2 1 -q 1 -H --level high -o " + location
						printl("cmd: " + str(cmd), self, "D")

						os.system(cmd)

						msg_text = _("finished rendering myFile: " + str(myFile))
						self.messages.push((THREAD_WORKING, msg_text))
						self.messagePump.send(0)

					printl("finished rendering myFile: " + str(myFile),self, "D")

			if self.cancel:
				self.messages.push((THREAD_FINISHED, _("Process aborted.\nPress OK to close.") ))
			else:
				self.messages.push((THREAD_FINISHED, _("We did it :-)")))

		except Exception, e:
			self.messages.push((THREAD_FINISHED, _("Error!\nError-message:%s\nPress OK to close." % e) ))
		finally:
			self.messagePump.send(0)

		self.running = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def prepareMediaVariants(self):
		# get params
		params = getMovieViewDefaults()

		b_height = params["elements"]["backdrop"]["height"]
		b_width = params["elements"]["backdrop"]["width"]
		b_postfix = params["elements"]["backdrop"]["postfix"]

		p_height = params["elements"]["poster"]["height"]
		p_width = params["elements"]["poster"]["width"]
		p_postfix = params["elements"]["poster"]["postfix"]

		l_height = "1280"
		l_width = "720"
		l_postfix = "_backdrop_1280x720.jpg"

		self.backdropVariants = [[b_height, b_width, b_postfix], [l_height, l_width, l_postfix]]
		self.posterVariants = [[p_height, p_width, p_postfix]]

	#===========================================================================
	#
	#===========================================================================
	def syncMedia(self):
		printl("", self, "S")

		self.running = True
		self.cancel = False
		msg_text = _("some text here")
		self.messages.push((THREAD_WORKING, msg_text))
		self.messagePump.send(0)

		# get sections from server
		self.sectionList = self.plexInstance.getAllSections()
		printl("sectionList: "+ str(self.sectionList),self, "D")

		# get servername
		self.prefix = Singleton().getPlexInstance().getServerName().lower()

		# prepare variants
		self.prepareMediaVariants()

		try:
			msg_text = _("Reading section of the server ...")
			self.messages.push((THREAD_WORKING, msg_text))
			self.messagePump.send(0)

			for section in self.sectionList:
				# interupt if needed
				if self.cancel:
					break

				if section[2] == "movieEntry":
					printl("movie", self, "D")
					url = section[3]["t_url"]

					if str(config.plugins.dreamplex.showFilter.value).lower() == "true":
						url += "/all"

					msg_text = _("got movie url: " + str(url))
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)

					printl("url: " + str(url), self, "D")
					library, tmpAbc = self.plexInstance.getMoviesFromSection(url)

					self.syncThrougMediaLibrary(library)


				if section[2] == "showEntry":
					printl("tvshow", self, "D")
					url = section[3]["t_url"] + "/all"

					msg_text = _("got show url: " + str(url))
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)

					printl("url: " + str(url), self, "D")
					library, tmpAbc, tmpGenres = self.plexInstance.getShowsFromSection(url)

					self.syncThrougMediaLibrary(library)

			if self.cancel:
				self.messages.push((THREAD_FINISHED, _("Process aborted.\nPress OK to close.") ))
			else:
				self.messages.push((THREAD_FINISHED, _("We did it :-)")))

		except Exception, e:
			self.messages.push((THREAD_FINISHED, _("Error!\nError-message:%s\nPress OK to close." % e) ))
		finally:
			self.messagePump.send(0)

		self.running = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def syncThrougMediaLibrary(self, library):
		printl("", self, "S")

		for media in library:

			# interupt if needed
			if self.cancel:
				break

			for variant in self.backdropVariants:
				# interupt if needed
				if self.cancel:
					break

				t_height = variant[0]
				t_width = variant[1]
				t_postfix = variant[2]

				# location string
				location = config.plugins.dreamplex.mediafolderpath.value + str(self.prefix) + "_" +  str(media[1]["ratingKey"]) + str(t_postfix)

				# check if backdrop exists
				if fileExists(location):
					msg_text = _("backdrop exists under the location " + str(location))
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)
					continue
				else:
					msg_text = _("file does not exist ... start downloading")
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)
					#download backdrop
					self.downloadMedia(media[2]["fanart_image"], location, t_height, t_width)

			for variant in self.posterVariants:
				# interupt if needed
				if self.cancel:
					break

				t_height = variant[0]
				t_width = variant[1]
				t_postfix = variant[2]

				# location string
				location = config.plugins.dreamplex.mediafolderpath.value + str(self.prefix) + "_" +  str(media[1]["ratingKey"]) + str(t_postfix)

				# check if poster exists
				if fileExists(location):
					msg_text = _("poster exists under the location " + str(location))
					self.messages.push((THREAD_WORKING, msg_text))
					self.messagePump.send(0)
					continue
				else:
					self.downloadMedia(media[2]["thumb"], location, t_height, t_width)

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