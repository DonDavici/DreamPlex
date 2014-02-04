# -*- coding: utf-8 -*-
#
# VideoDB E2
#
# Coded by Dr.Best (c) 2013
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.config import config
from TMDb import TMDb
from TVDb import TVDb



from enigma import ePythonMessagePump, eServiceReference
from threading import Thread
from os import path as os_path, walk as os_walk, listdir as os_listdir
from DatabaseConnection import OpenDatabaseForWriting
from DatabaseFunctions import isMounted, addToDatabase, getVideoDataFilterDirectories, EXTENSIONS, NewScanLog
from ThreadQueue import ThreadQueue, THREAD_WORKING, THREAD_FINISHED
from time import time as time_time


class BackgroundFileScanner(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.cancel = False
		self.path = None
		self.recursive = False
		self.messages = ThreadQueue()
		self.messagePump = ePythonMessagePump()
		self.running = False

	def getMessagePump(self):
		return self.messagePump

	def getMessageQueue(self):
		return self.messages

	def Cancel(self):
		self.cancel = True

	MessagePump = property(getMessagePump)
	Message = property(getMessageQueue)

	def setPath(self, path):
		self.path = path

	def startScanning(self, path, recursive):
		if not self.running:
			self.path = path
			self.recursive = recursive
			self.start()

	def run(self):
		self.running = True
		mp = self.messagePump
		self.cancel = False

		i = 0
		connection, error = OpenDatabaseForWriting()
		try: #so many things  can go wrong here, I need this, otherside the thread will not send the finished flag
			if connection is not None:
				cursor = connection.cursor()
				dirCursor = None
				counter = 0
				checkTime = 0
				addedRows = 0
				updatedRows = 0
				deletedRows = 0
				if self.path:
					# scan path was set by user, scan for files incl. subfolders
					directory = self.path
					for root, subFolders, files in os_walk(directory):
						if self.cancel:
							break
						if not root.endswith("/"):
							root += "/"
						msg_text =  _("scanning for media files in %s...") % root
						self.messages.push((THREAD_WORKING, msg_text))
						mp.send(0)
						for filename in files:
							extension = os_path.splitext(filename)[1].lower()
							if extension in EXTENSIONS:
								if self.cancel:
									break
								msg_text =  _("scanning %s...") % os_path.join(root, filename)
								self.messages.push((THREAD_WORKING, msg_text))
								mp.send(0)
								result = addToDatabase(cursor, root, filename)
								if result and result[0]:
									addedRows += 1
								elif result and not result[0]:
									updatedRows += 1
						i += 1
						if not self.recursive and i == 1:
							break
				if not self.cancel:
					connection.commit()
				cursor.close()
				connection.close()
				if self.cancel:
					self.messages.push((THREAD_FINISHED, _("Process aborted.\nPress OK to close.") ))
				else:
					self.messages.push((THREAD_FINISHED, _("%d files added,\n%d files updated,\n%d files removed in database!" % (addedRows, updatedRows, deletedRows))))
			else:
				self.messages.push((THREAD_FINISHED, _("Error!\nCan not open database!\n%s" %error) ))
		except Exception, e:
			if connection:
				connection.close()
			self.messages.push((THREAD_FINISHED, _("Error!\nError-message:%s\nPress OK to close." % e) ))
		finally:
			mp.send(0)
		self.running = False


class MovieDataUpdater(object):
	instance = None
	TMDB_MODE = 0
	TVDB_MODE = 1
	def __init__(self):
		assert not MovieDataUpdater.instance, "only one MovieDataUpdater instance is allowed!"
		MovieDataUpdater.instance = self # set instance
		self.movielist = None
		self.callback_infos = None
		self.callback_finished = None
		self.dataService = None
		self.movie = None
		self.mode = None
		self.displayService = None
		self.dbVideoScanner = None
		self.dbVideoScannerRunning = False
		self.running = False

		self.path = None
		self.recursive = False

		self.usepathdata = False


	def startVideoScanning(self, path, recursive, mode, usepathdata = False):
		if not self.running:
			self.path = path
			self.recursive = recursive
			self.dbVideoScanner = BackgroundFileScanner()
			self.dbVideoScanner.MessagePump.recv_msg.get().append(self.gotThreadMsg)
			self.dbVideoScanner.startScanning(path, recursive)
			self.running = self.dbVideoScannerRunning = True
			self.mode = mode
			self.usepathdata = usepathdata

	def gotThreadMsg(self, msg):
		msg = self.dbVideoScanner.Message.pop()
		self.infoCallBack(msg[1])
		if msg[0] == THREAD_FINISHED:
			self.dbVideoScanner.MessagePump.recv_msg.get().remove(self.gotThreadMsg)
			self.dbVideoScannerRunning = False
			if self.dbVideoScanner.cancel == False:
				directory = os_path.realpath(self.path)
				movielist = getVideoDataFilterDirectories(directory, self.mode,self.recursive)
			else:
				movielist = None
			if movielist:
				self.start(movielist, self.mode)
			else:
				self.done()

	def start(self, movielist, mode):
		self.mode = mode
		if self.mode == self.TMDB_MODE:
			self.displayService = "TMDb"
			self.dataService = TMDb(True)
		else:
			self.displayService = "TVDb"
			self.dataService = TVDb()
		self.movielist = movielist
		self.running = True
		self.getMovieData()

	def cancel(self):
		if self.dbVideoScannerRunning:
			self.dbVideoScanner.Cancel()
		else:
			self.movielist = None

	def isRunning(self):
		return self.running

	def setCallbacks(self, callback_infos, callback_finished):
		self.callback_infos = callback_infos
		self.callback_finished = callback_finished

	def getMovieData(self):
		self.movie = self.getNextMovie()
		if self.movie:
			text = _("Preparing %s for %s search...") % (os_path.join(self.movie["mountpoint"],self.movie["path"],self.movie["filename"]), self.displayService)
			print text
			if self.callback_infos:
				self.callback_infos(text)
			if self.mode == self.TMDB_MODE:
				indicator3D = config.plugins.videodb.Indicator3D.value
				if self.usepathdata == False:
					filename = self.movie["name"]
				else:
					filename = os_path.join(self.movie["mountpoint"],self.movie["path"],self.movie["name"])
				self.dataService.searchMovie(filename.replace(indicator3D,''),self.movie["serviceid"], self.searchMovieCallback)
			else:
				if self.usepathdata == False:
					path = ""
				else:
					path = self.movie["path"]
				self.dataService.searchForSerie(path, self.movie["name"], self.movie["description"], self.infoCallBack, self.callbackTMDbError, self.searchForSeriesNameEpisodeNameCallback)
		else:
			self.done()

	def done(self):
		if self.callback_finished:
			self.callback_finished()
		self.running = False
		self.dataService = None
		self.mode = None
		self.displayService = None
		self.movielist = None
		self.path = None
		self.recursive = False
		self.dbVideoScanner = None

	def searchForSeriesNameEpisodeNameCallback(self, seriesDataList, episodeDataList, error):
		if len(seriesDataList) == 1:
			self.dataService.setStatusList(1)
		if len(seriesDataList) == 1 and len(episodeDataList) == 1:
			seriesData = seriesDataList[0]
			episodeData = episodeDataList[0]
			text = _("Updating %s with TVDb-Data...") % (self.movie["name"])
			print text
			if self.callback_infos:
				self.callback_infos(text)
			self.dataService.saveTVDbDataToDatabase(seriesData, episodeData, self.movie["movie_id"], self.movie["event_id"], self.movie["begin"], self.callbackTMDbDataSaved)
		else:
			NewScanLog(self.movie["movie_id"], 1, 0, _("No unique data found"))
			text = _("No unique data found for %s found in TVDb...") % os_path.join(self.movie["mountpoint"],self.movie["path"],self.movie["filename"])
			print text
			if self.callback_infos:
				self.callback_infos(text)
			self.getMovieData()

	def infoCallBack(self,text):
		print text
		if text and self.callback_infos:
			self.callback_infos(text)

	def callbackTMDbError(self, text):
		self.infoCallBack(text)
		self.getMovieData()

	def callbackTMDbDataSaved(self, text, finished, error = False):
		self.getMovieData()

	def searchMovieCallback(self, movie, infostring):
		if movie is not None:
			text = _("Updating %s with TMDb-Data...") % (self.movie["name"])
			print text
			if self.callback_infos:
				self.callback_infos(text)
			self.dataService.saveTMBbDataToDatabase(movie, self.movie["movie_id"], self.movie["event_id"], self.movie["begin"], self.saveDataToDatabaseCallback)
		else:
			NewScanLog(self.movie["movie_id"], 2, 0, _("No unique data found"))
			if infostring:
				print infostring
				if self.callback_infos:
					self.callback_infos(infostring)
			self.getMovieData()

	def getNextMovie(self):
		if self.movielist and len(self.movielist) >0:
			return self.movielist.pop(0)[0]
		else:
			return None

	def saveDataToDatabaseCallback(self, error, result):
		self.getMovieData()


class MovieDataUpdaterScreen(Screen):
	skin = """<screen name="MovieDataUpdaterScreen" position="center,center" size="560,320" title="Update movie data">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget name="output" position="10,60" size="540,250" valign="center" halign="center" font="Regular;22" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.movieUpdater = MovieDataUpdater.instance
		self.movieUpdater.setCallbacks(self.callback_infos, self.callback_finished)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"green": self.green,
			"red": self.cancel,
		}, -1)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Background"))
		self["output"] = Label()
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.movieUpdater.setCallbacks(None, None)

	def green(self):
		if self.movieUpdater.isRunning():
			self.close(1)
		else:
			self.close(0)

	def cancel(self):
			self.movieUpdater.cancel()
			self["output"].setText(_("Cancelled!"))

	def callback_infos(self, info):
		self["output"].setText(info)

	def callback_finished(self):
		self["output"].setText(_("Finished"))
		self["key_green"].setText(_("Close"))

