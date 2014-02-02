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

from Screens.TaskView import JobView

from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Task import job_manager, Task, Job, Condition
from Components.config import config
from Components.ScrollLabel import ScrollLabel

from twisted.web.client import downloadPage

from Screens.Screen import Screen

from Tools.Directories import fileExists

from __plugin__ import Plugin
from DP_PlexLibrary import PlexLibrary
from DPH_Singleton import Singleton
from DP_ViewFactory import getMovieViewDefaults

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===========================================================================
#
#===========================================================================
class DPS_Syncer(Screen):

	_session = None
	_job = None
	_serverIsSet = False

	def __init__(self, session):
		Screen.__init__(self, session)

		self._session = session

		self["console"] = ScrollLabel()

		self["txt_filter"]		= Label()

		self["txt_red"] = Label()
		self["txt_green"] = Label()
		self["txt_yellow"] = Label()
		self["txt_blue"] = Label()

		self["btn_red"] = Pixmap()
		self["btn_green"] = Pixmap()
		self["btn_blue"] = Pixmap()
		self["btn_yellow"] = Pixmap()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyRed,
			"blue": self.keyBlue,
			"yellow": self.keyYellow,
			"green": self.keyGreen,
		    "cancel": self.keyCancel,
		    "ok": self.okbuttonClick,
		}, -2)

		self.getServerList()

		self["menu"]= List(self.mainMenuList, True)

		self.onLayoutFinish.append(self.toggleFunctions)

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
	def toggleFunctions(self):
		printl("", self, "S")

		if self._serverIsSet:
			self["txt_red"].show()
			self["txt_green"].show()
			self["txt_yellow"].show()
			self["txt_blue"].show()

			self["btn_red"].show()
			self["btn_green"].show()
			self["btn_blue"].show()
			self["btn_yellow"].show()
		else:
			self["txt_red"].hide()
			self["txt_green"].hide()
			self["txt_yellow"].hide()
			self["txt_blue"].hide()

			self["btn_red"].hide()
			self["btn_green"].hide()
			self["btn_blue"].hide()
			self["btn_yellow"].hide()

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
				self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))

				# functions and visus are only visible if server is set
				self._serverIsSet = True
				self.toggleFunctions()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyRed(self):
		printl("", self, "S")

		if self._serverIsSet:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyYellow(self):
		printl("", self, "S")

		if self._serverIsSet:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyBlue(self):
		printl("", self, "S")

		if self._serverIsSet:
			# show Jobview
			job_manager.in_background = False
			self.session.openWithCallback(self.JobViewCallback, JobView, self._job)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def JobViewCallback(self, in_background):
		printl("", self, "S")

		job_manager.in_background = in_background

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def keyGreen(self):
		printl("", self, "S")
		if self._serverIsSet:

			# prepare job tasks
			self.doMediaSync()

			# add jobs to jobmanager
			job_manager.AddJob(self._job)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def doMediaSync(self):
		printl("", self, "S")

		# get sections from server
		self.sectionList = self.plexInstance.displaySections()
		printl("sectionList: "+ str(self.sectionList),self, "D")
		movies = {}

		# build job
		self._job = Job(_("Media Syncer"))

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

		for section in self.sectionList:
			if section[2] == "movieEntry":
				printl("movie", self, "D")
				url = section[3]["t_url"] + "/all"
				printl("url: " + str(url), self, "D")
				library, tmpAbc, tmpGenres = self.plexInstance.getMoviesFromSection(url)
				for movie in library:
					for variant in backdropVariants:
						t_height = variant[0]
						t_width = variant[1]
						t_postfix = variant[2]

						# location string
						location = config.plugins.dreamplex.mediafolderpath.value + str(prefix) + "_" +  str(movie[1]["ratingKey"]) + str(t_postfix)

						# check if backdrop exists
						if fileExists(location):
							continue
						else:
							#download backdrop
							task = PythonTask(self._job, str(movie[0]))
							task.work = self.downloadMedia(movie[2]["fanart_image"], location, t_height, t_width)

					for variant in posterVariants:
						t_height = variant[0]
						t_width = variant[1]
						t_postfix = variant[2]

						# location string
						location = config.plugins.dreamplex.mediafolderpath.value + str(prefix) + "_" +  str(movie[1]["ratingKey"]) + str(t_postfix)

						# check if poster exists
						if fileExists(location):
							continue
						else:
							task = PythonTask(self._job, str(movie[0]))
							task.work = self.downloadMedia(movie[2]["thumb"], location, t_height, t_width)

					movies[movie[0]] = (movie[2]["fanart_image"], movie[2]["thumb"])
				printl("movies: " + str(library), self, "D")


		printl("resutl: " + str(movies), self, "D")
			#if section[2] == "showEntry":
			#	printl("tvshow", self, "D")
			#	url = section[3]["t_url"]
			#	printl("url: " + str(url), self, "D")
			#	shows = self.plexInstance.getShowsFromSection(url)
			#	printl("shows: " + str(shows), self, "D")


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

	#===========================================================================
	#
	#===========================================================================
	def keyCancel(self):
		printl("", self, "S")

		self.close()

		printl("", self, "C")


class PythonTask(Task):
	def _run(self):
		from twisted.internet import threads, task
		self.aborted = False
		self.pos = 0
		threads.deferToThread(self.work).addBoth(self.onComplete)
		self.timer = task.LoopingCall(self.onTimer)
		self.timer.start(5, False)

	def work(self):
		raise NotImplemented, "work"

	def abort(self):
		self.aborted = True
		if self.callback is None:
			self.finish(aborted = True)

	def onTimer(self):
		self.setProgress(self.pos)

	def onComplete(self, result):
		self.postconditions.append(FailedPostcondition(result))
		self.timer.stop()
		del self.timer
		self.finish()

class FailedPostcondition(Condition):
	def __init__(self, exception):
		self.exception = exception
	def getErrorMessage(self, task):
		if isinstance(self.exception, int):
			if hasattr(task, 'log'):
				log = ''.join(task.log).strip()
				log = log.split('\n')[-4:]
				log = '\n'.join(log)
				return log
		else:
			return _("Error code") + " %s" % self.exception

		return str(self.exception)

	def check(self, task):
		return (self.exception is None) or (self.exception == 0)