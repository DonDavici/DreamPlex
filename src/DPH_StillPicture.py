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
import sys

#noinspection PyUnresolvedReferences
from enigma import eWidget, eServiceReference, iPlayableService, eTimer
from Components.Renderer.Renderer import Renderer
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.config import config

from __common__ import printl2 as printl, getBoxInformation

#===============================================================================
#
#===============================================================================
class Showiframe(object):

	#===========================================================================
	#
	#===========================================================================
	def __init__(self):
		printl("", self , "S")

		try:
			self.load()
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "E")

		printl("", self , "C")

	#===========================================================================
	#
	#===========================================================================
	def load(self):
		printl("", self , "S")

		# we append here to have ctype.so also for sh4 boxes
		libsFolder = config.plugins.dreamplex.pluginfolderpath.value + "libs"
		sys.path.append(libsFolder)

		#try:
			#self.ctypes = __import__("_ctypes")
			#printl("self.ctypes import worked", self, "D")
		#except Exception, ex:
			#printl("self.ctypes import failed", self, "E")
			#printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "E")
			#self.ctypes = None

			#printl("", self, "C")
			#return False
		import _ctypes
		self.ctypes = _ctypes
		libname = "libshowiframe.so.0.0.oe20"
		self.finishShowSinglePic = None


		libsi = libsFolder + "/" + libname
		printl("LIB_PATH=" + str(libsi), self, "I")
		self.showiframe = self.ctypes.dlopen(libsi)
		printl("showiframe" + str(self.showiframe), self, "D")

		try:
			self.showSinglePic = self.ctypes.dlsym(self.showiframe, "showSinglePic")
			self.finishShowSinglePic = self.ctypes.dlsym(self.showiframe, "finishShowSinglePic")
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")
			printl("self.ctypes.dlsym - FAILED!!! trying next ...", self, "W")
			try:
				self.showSinglePic = self.ctypes.dlsym(self.showiframe, "_Z13showSinglePicPKc")
				self.finishShowSinglePic = self.ctypes.dlsym(self.showiframe, "_Z19finishShowSinglePicv")
			except Exception, ex2:
				printl("Exception(" + str(type(ex2)) + "): " + str(ex2), self, "E")
				printl("self.ctypes.dlsym - FAILED AGAIN !!!", self, "E")

				printl("", self, "C")
				return False

		printl("", self, "C")
		return True

	#===========================================================================
	#
	#===========================================================================
	def showStillpicture(self, pic):
		printl("", self , "S")

		if self.ctypes is not None:
			self.ctypes.call_function(self.showSinglePic, (pic, ))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishStillPicture(self):
		printl("", self , "S")

		if self.ctypes is not None and self.finishShowSinglePic is not None:
			self.ctypes.call_function(self.finishShowSinglePic, ())

		printl("", self, "C")

#===========================================================================
#
#===========================================================================
class eStillPicture(eWidget):

	#===========================================================================
	#
	#===========================================================================
	#noinspection PyUnresolvedReferences
	def __init__(self, parent):
		printl("", self , "S")

		eWidget.__init__(self, parent)
		self.setTransparent(True)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setText(self):
		printl("", self , "S")

		pass

		printl("", self, "C")

#===========================================================================
#
#===========================================================================
class StillPicture(Renderer, InfoBarBase):
	GUI_WIDGET = eStillPicture

	element = False

	stillpicture = ""
	stillpictureDefault = ""
	isLoop = False
	session = None
	poll_timer = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session):
		printl("", self , "S")

		Renderer.__init__(self)

		self.showiframe = Showiframe()
		self.session = session
		self.poll_timer = eTimer()
		self.poll_timer.callback.append(self.poll)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def addEventTracker(self):
		printl("", self , "S")

		if self.session is not None and self.session.nav is not None:
			self.session.nav.event.append(self.event)
		else:
			printl("ARGGHHHH!!! self.session is not None and self.session.nav is not None", self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def removeEventTracker(self):
		printl("", self , "S")

		if self.session is not None and self.session.nav is not None:
			self.session.nav.event.remove(self.event)
		else:
			printl("ARGGHHHH!!! self.session is not None and self.session.nav is not None", self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def event(self, myType):
		printl("", self , "S")

		if myType == iPlayableService.evEOF:
			self.__evEOF()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def poll(self):
		printl("", self , "S")

		if self.session is not None and self.session.nav is not None:
			service = self.session.nav.getCurrentService()
			seek = service and service.seek()
			if seek is not None:
				seek.getPlayPosition()
		else:
			printl("ARGGHHHH!!! self.session is not None and self.session.nav is not None", self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def pollStart(self):
		printl("", self , "S")

		self.addEventTracker()
		self.poll_timer.start(500)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def pollStop(self):
		printl("", self , "S")

		self.removeEventTracker()
		self.poll_timer.stop()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def __evEOF(self):
		printl("", self , "S")

		if self.session is not None and self.session.nav is not None:
			service = self.session.nav.getCurrentService()

			boxInformation = getBoxInformation()

			if boxInformation[0] != "sh4" and service and service.seek():
				service.seek().seekTo(0)
			else:
				self.session.nav.playService(eServiceReference(4097, 0, self.getStillpicture()), forceRestart=True)
		else:
			printl("ARGGHHHH!!! self.session is not None and self.session.nav is not None", self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def elementExists(self):
		printl("", self , "S")

		printl("", self, "C")
		return self.element

	#===========================================================================
	#
	#===========================================================================
	def getStillpicture(self):
		printl("", self , "S")

		printl("", self, "C")
		return self.stillpicture

	#===========================================================================
	#
	#===========================================================================
	def getStillpictureDefault(self):
		printl("", self , "S")

		printl("", self, "C")
		return self.stillpictureDefault

	#===========================================================================
	#
	#===========================================================================
	def setStillPicture(self, value, default=False, refresh=True, isLoop=False):
		printl("", self , "S")

		if default is True:
			self.stillpictureDefault = config.plugins.dreamplex.mediafolderpath.value + "/bootlogo.m1v"

		if self.stillpicture != value:
			self.stillpicture = value
			self.isLoop = isLoop
			if refresh is True:
				self.changed()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setStillPictureToDefault(self):
		printl("", self , "S")

		if self.stillpicture != self.stillpictureDefault:
			self.stillpicture = self.stillpictureDefault
			self.changed()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def postWidgetCreate(self, instance):
		printl("", self , "S")

		self.sequence = None

		if self.skinAttributes is not None:
			self.element = True
			for (attrib, value) in self.skinAttributes:
				if attrib == "text":
					self.setStillPicture(value, True, False)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showStillPicture(self):
		printl("", self , "S")

		if self.elementExists():
			try:
				if self.isLoop is False:
					self.showiframe.showStillpicture(self.getStillpicture())
				elif self.isLoop is True:
					if self.session is not None and self.session.nav is not None:
						printl("loop: " + str(self.getStillpicture()), self)
						ServiceEventTracker.setActiveInfoBar(self, None, None)
						self.session.nav.playService(eServiceReference(4097, 0, self.getStillpicture()))
						self.pollStart()
					else:
						printl("ARGGHHHH!!! self.session is not None and self.session.nav is not None", self, "E")
			except Exception, ex:
				printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishStillPicture(self):
		printl("", self , "S")

		if self.elementExists():
			try:
				if self.isLoop is False:
					self.showiframe.finishStillPicture()
				elif self.isLoop is True:
					self.pollStop()
					if self.session is not None and self.session.nav is not None:
						self.session.nav.stopService()
						ServiceEventTracker.popActiveInfoBar()
					else:
						printl("ARGGHHHH!!! self.session is not None and self.session.nav is None", self, "E")
			except Exception, ex:
				printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "E")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onShow(self):
		printl("", self , "S")

		self.showStillPicture()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onHide(self):
		printl("", self , "S")

		# We could close the still picutre here, but keep it open for a neatless expereience
		pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def changed(self):
		printl("", self , "S")

		self.showStillPicture()

		printl("", self, "C")
