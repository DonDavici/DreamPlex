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
import os
import sys


#noinspection PyUnresolvedReferences
from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.config import *

from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText

from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
from Plugins.Extensions.DreamPlex.DPH_BackdropMaker import backdropMaker
#===============================================================================
# IMPORT
#===============================================================================
gSyncInfo = None

#===========================================================================
#
#===========================================================================
def getSyncInfoInstance():
	global gSyncInfo
	if gSyncInfo is None:
		gSyncInfo = dreamplexMovieMakerInfo()
	return gSyncInfo

#===========================================================================
#
#===========================================================================
def autostart(session):
	syncInfo = getSyncInfoInstance()
	syncInfo.registerOutputInstance(None, session)
	syncInfo.start(backdropMaker)

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
class dreamplexMovieMakerInfo(object):
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
	def start(self, type):
		printl("", self, "D")
		try:
			if self.inProgress:
				return False
			self.reset()

			isFinished = False
			self.inProgress = True
			self.setOutput(None)
			self.thread = backdropMaker(self.setOutput, self.setProgress, self.setRange, self.setInfo, self.finished, type)
			self.thread.start()
			for outputInstance in self.outputInstance:
				outputInstance.notifyStatus()
			return True
		except Exception, ex:
			printl("Exception: " + str(ex), self)
			return False

	#===========================================================================
	#
	#===========================================================================
	def abort(self):
		printl("", self, "D")
		if not self.inProgress:
			return False

		self.thread.abort()

	#===========================================================================
	#
	#===========================================================================
	def registerOutputInstance(self, instance, session):
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

	#===========================================================================
	#
	#===========================================================================
	def unregisterOutputInstance(self, instance):
		try:
			if instance:
				self.outputInstance.remove(instance)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	#===========================================================================
	#
	#===========================================================================
	def setOutput(self, text):
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
						outputInstance.appendLog(text)
				self.log.append(text)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	#===========================================================================
	#
	#===========================================================================
	def setRange(self, value):
		try:
			self.range = value
			for outputInstance in self.outputInstance:
				outputInstance.setRange(self.range)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	#===========================================================================
	#
	#===========================================================================
	def setProgress(self, value):
		try:
			self.progress = value
			for outputInstance in self.outputInstance:
				outputInstance.setProgress(self.progress)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	#===========================================================================
	#
	#===========================================================================
	def setInfo(self, poster, name, year):
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

	#===========================================================================
	#
	#===========================================================================
	def finished(self):
		try:
			self.inProgress = False
			self.isFinished = True
			for outputInstance in self.outputInstance:
				outputInstance.notifyStatus()
			if len(self.outputInstance) == 0:
				self.session.open(ProjectValerieSyncFinished)
		except Exception, ex:
			printl("Exception: " + str(ex), self)

	#===========================================================================
	#
	#===========================================================================
	def reset(self):
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

#===========================================================================
#
#===========================================================================
class ProjectValerieSyncFinished(Screen):
	skin = """
		<screen position="center,center" size="300,100" title=" ">
			<widget name="info" position="10,10" size="280,80" font="Regular;30" halign="center" valign="center"/>
		</screen>"""

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)

		self["info"] = Label(_("Synchronize finished"))

		self["ProjectValerieSyncFinishedActionMap"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"ok": self.close,
			"cancel": self.close
		}, -1)

		timeout = 8

		self.timerRunning = False
		self.initTimeout(timeout)

		self.onLayoutFinish.append(self.setCustomTitle)

	#===========================================================================
	#
	#===========================================================================
	def setCustomTitle(self):
		self.setTitle(_("Sync Manager"))

	#===========================================================================
	#
	#===========================================================================
	def initTimeout(self, timeout):
		self.timeout = timeout
		if timeout > 0:
			self.timer = eTimer()
			self.timer.callback.append(self.timerTick)
			self.onExecBegin.append(self.startTimer)
			self.origTitle = None
			if self.execing:
				self.timerTick()
			else:
				self.onShown.append(self.__onShown)
			self.timerRunning = True
		else:
			self.timerRunning = False

	#===========================================================================
	#
	#===========================================================================
	def __onShown(self):
		self.onShown.remove(self.__onShown)
		self.timerTick()

	#===========================================================================
	#
	#===========================================================================
	def startTimer(self):
		self.timer.start(1000)

	#===========================================================================
	#
	#===========================================================================
	def stopTimer(self):
		if self.timerRunning:
			del self.timer
			self.onExecBegin.remove(self.startTimer)
			self.setTitle(self.origTitle)
			self.timerRunning = False

	#===========================================================================
	#
	#===========================================================================
	def timerTick(self):
		if self.execing:
			self.timeout -= 1
			if self.origTitle is None:
				self.origTitle = self.instance.getTitle()
			self.setTitle(self.origTitle + " (" + str(self.timeout) + ")")
			if self.timeout == 0:
				self.timer.stop()
				self.timerRunning = False
				self.timeoutCallback()

	#===========================================================================
	#
	#===========================================================================
	def timeoutCallback(self):
		print "Timeout!"
		self.close()

#===========================================================================
#
#===========================================================================
class ProjectValerieSync(Screen):
	skinDeprecated = """
		<screen position="center,center" size="620,476" title="ProjectValerieSync" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />

			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />

			<eLabel text="Log:" position="10,50" size="400,20" font="Regular;18" />
			<widget name="console" position="10,70" size="400,360" font="Regular;15" />
			<eLabel text="Progress:" position="10,426" size="400,20" font="Regular;18" />
			<widget name="progress" position="10,446" size="400,20" borderWidth="1" borderColor="#bbbbbb" transparent="1" />

			<eLabel text="" position="420,50" size="1,416" backgroundColor="#bbbbbb" />

			<eLabel text="Last:" position="430,50" size="400,20" font="Regular;18" />
			<widget name="poster" position="430,70" size="156,214" />

			<eLabel text="Year:" position="430,350" size="180,20" font="Regular;18" />
			<widget name="year" position="440,370" size="170,20" font="Regular;16"/>

			<eLabel text="Name:" position="430,390" size="180,20" font="Regular;18" />
			<widget name="name" position="440,410" size="170,60" font="Regular;16"/>
		</screen>"""

	ShowStillPicture = False

	def __init__(self, session, autoSync=False):
		Screen.__init__(self, session)

		self.session = session

		self.autoSync = autoSync
		printl("Session: " + str(self.session), self, "H")
		printl("AutoSync: " + str(self.autoSync), self, "H")

		self.APILevel = getAPILevel(self)
		printl("APILevel=" + str(self.APILevel), self)
		if self.APILevel >= 2:
			self["API"] = DataElement()

		if self.APILevel >= 2:
			try:
				from Plugins.Extensions.ProjectValerie.StillPicture import StillPicture
				self["showiframe"] = StillPicture(session)
				self.ShowStillPicture = True
			except Exception, ex:
				printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")

		if self.APILevel == 1:
			self.skin = self.skinDeprecated

		self["key_red"] = StaticText(_("Manage"))
		self["key_green"] = StaticText(_("Complete Sync"))
		self["key_yellow"] = StaticText(_("Normal Sync"))
		self["key_blue"] = StaticText(_("Settings"))

		self["console"] = ScrollLabel(_("Please press the green button to start synchronize!\n"))
		self["progress"] = ProgressBar()
		self["poster"] = Pixmap()
		self["name"] = Label()
		self["year"] = Label()

		self["logtxt"] = StaticText(_("Log:"))
		self["progresstxt"] = StaticText(_("Progress:"))
		self["lasttxt"] = StaticText(_("Last:"))
		self["yeartxt"] = StaticText(_("Year:"))
		self["nametxt"] = StaticText(_("Name:"))

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MenuActions"],
		{
			"green": self.go,
			"yellow": self.gofast,
			"red": self.manage,
			"blue": self.menu,
			"menu": self.update,
			"cancel": self.close,
		}, -1)

		printl("PYTHONPATH=" + str(sys.path), self)
		sys.path.append(resolveFilename(SCOPE_PLUGINS, "Extensions/ProjectValerieSync") )

		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.startup)

	def setCustomTitle(self):
		self.setTitle(_("Sync Manager"))

	def startup(self):
		syncInfo = getSyncInfoInstance()
		registerOutputInstance(self, self.session)

		self.notifyStatus()

		printl("syncInfo.inProgress: " + str(syncInfo.inProgress), self)
		if syncInfo.inProgress is False:
			self.checkDefaults()

		if self.autoSync:
			self.delayedTimer = eTimer()
			self.delayedTimer.callback.append(self.startupDelayed)
			self.delayedTimer.start(5000)

	def startupDelayed(self):
		printl("->", self, "H")
		self.delayedTimer.stop()
		self.gofast()
		printl("<-", self, "H")

	def checkDefaults(self):
		SyncCheckDefaults()

	def close(self):
		unregisterOutputInstance(self)
		Screen.close(self)

	def notifyStatus(self):
		syncInfo = getSyncInfoInstance()
		printl("inProgress:" + str(syncInfo.inProgress), self, "D")
		if syncInfo.inProgress is True:
			self["key_red"].setText(_("Hide"))
			self["key_green"].setText(_("Abort"))
			self["key_yellow"].setText("")
		else:
			self["key_red"].setText(_("Manage"))
			self["key_green"].setText(_("Complete Sync"))
			self["key_yellow"].setText(_("Normal Sync"))

			if self.autoSync and syncInfo.isFinished is True:
				self.delayedTimer = eTimer()
				self.delayedTimer.callback.append(self.closeDelayed)
				self.delayedTimer.start(5000)

	def closeDelayed(self):
		printl("->", self, "H")
		self.delayedTimer.stop()
		self.close()
		printl("<-", self, "H")

	def menu(self):
		syncInfo = getSyncInfoInstance()
		if syncInfo.inProgress is False:
			self.session.open(ProjectValerieSyncSettings)

	def update(self):
		syncInfo = getSyncInfoInstance()
		if syncInfo.inProgress is False:
			syncInfo.start(pyvalerie.UPDATE)
		else:
			syncInfo.abort()

	def manage(self):
		syncInfo = getSyncInfoInstance()
		if syncInfo.inProgress is False:
			self.session.open(ProjectValerieSyncManager)
		else:
			self.close()

	def go(self):
		syncInfo = getSyncInfoInstance()
		if syncInfo.inProgress is False:
			syncInfo.start(pyvalerie.NORMAL)
		else:
			syncInfo.abort()

	def gofast(self):
		syncInfo = getSyncInfoInstance()
		if syncInfo.inProgress is False:
			syncInfo.start(pyvalerie.FAST)

	def clearLog(self):
		self["console"].setText("")
		self["console"].lastPage()

	def appendLog(self, text):
		self["console"].appendText(text + "\n")
		self["console"].lastPage()

	def setProgress(self, value):
		self["progress"].setValue(value)

	def setRange(self, value):
		self["progress"].range = (0, value)

	def setPoster(self, poster):
		if poster is not None and len(poster) > 0 and os.access(config.plugins.pvmc.mediafolderpath.value + poster, os.F_OK) is True:
			self["poster"].instance.setPixmapFromFile(config.plugins.pvmc.mediafolderpath.value + poster)
		else:
			self["poster"].instance.setPixmapFromFile(config.plugins.pvmc.mediafolderpath.value + "defaultposter.png")

	def setName(self, name):
		if name is not None and len(name) > 0:
			self["name"].setText(Utf8.utf8ToLatin(name))
		else:
			self["name"].setText("")

	def setYear(self, year):
		if year is not None and year > 0:
			self["year"].setText(str(year))
		else:
			self["year"].setText("")
