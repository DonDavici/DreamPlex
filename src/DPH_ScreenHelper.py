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
from enigma import eSize, getDesktop

from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.VideoWindow import VideoWindow
from Components.Label import Label
from Components.Label import MultiColorLabel
from Components.config import NumericalTextInput

from Screens.Screen import Screen

from skin import parseColor

from DPH_Singleton import Singleton
from DP_ViewFactory import translateValues

from __common__ import printl2 as printl, addNewScreen, closePlugin, getSkinResolution, getSkinHighlightedColor, getSkinNormalColor

#===============================================================================
#
#===============================================================================
class DPH_ScreenHelper(object):
	width = "195"
	height = "268"
	#===============================================================================
	#
	#===============================================================================
	def __init__(self, forceMiniTv=False):
		printl("", self, "S")

		self.stopLiveTvOnStartup = config.plugins.dreamplex.stopLiveTvOnStartup.value

		# we use this e.g in DP_View to use miniTv for backdrops via libiframe
		self.forceMiniTv = forceMiniTv

		if not self.stopLiveTvOnStartup or self.forceMiniTv:
			self["miniTv"] = VideoWindow(decoder=0)
			self.miniTvInUse = True
		else:
			self["miniTv"] = Label()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def initMiniTv(self, width=None, height=None):
		"""
		the widht and height is in params files a param section on its own
		but for the views the settings located there for this reason
		we have both ways.
		"""
		printl("", self, "S")

		if not self.stopLiveTvOnStartup or self.forceMiniTv:
			if width is None or height is None:
				width, height = self.getMiniTvParams()
			desk = getDesktop(0)
			print str(self["miniTv"].instance)
			self["miniTv"].instance.setFBSize(desk.size())
			self["miniTv"].instance.resize(eSize(int(width), int(height)))
		else:
			self["miniTv"].hide()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getMiniTvParams(self):
		printl("", self, "S")

		width = 400
		height = 225
		printl("screenName: " + str(self.screenName), self, "D")

		if self.height is not None and self.width is not None:
			height = self.height
			width = self.width

		printl("width: " + str(width) + " - height: " + str(height), self, "D")
		printl("", self, "C")
		return int(width), int(height)

	#===============================================================================
	#
	#===============================================================================
	def initScreen(self, screenName):
		printl("", self, "S")

		tree = Singleton().getSkinParamsInstance()

		self.screenName = screenName

		for screen in tree.findall('screen'):
			name = str(screen.get('name'))

			if name == self.screenName:
				self.miniTv = translateValues(str(screen.get('miniTv')))
				if self.miniTv:
					self.width = screen.get('width')
					self.height = screen.get('height')
				else:
					self.Poster= translateValues(str(screen.get('usePoster')))
					if self.Poster:
						self.width = screen.get('width')
						self.height = screen.get('height')

		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPH_PlexScreen(object):

	#===============================================================================
	#
	#===============================================================================
	def __init__(self):

		self.skinResolution = getSkinResolution()

	#===============================================================================
	#
	#===============================================================================
	def setColorFunctionIcons(self):
		# first we set the pics for buttons if existing
		try:
			self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])

		except:
			pass

		try:
			self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])
		except:
			pass

		try:
			self["btn_yellow"].instance.setPixmapFromFile(self.guiElements["key_yellow"])
		except:
			pass

		try:
			self["btn_blue"].instance.setPixmapFromFile(self.guiElements["key_blue"])
		except:
			pass

#===============================================================================
#
#===============================================================================
class DPH_MultiColorFunctions(object):

	#===============================================================================
	#
	#===============================================================================
	def __init__(self):
		printl("", self, "S")

		self.colorFunctionContainer = {}
		self.colorFunctionContainer["red"] = {}
		self.colorFunctionContainer["green"] = {}
		self.colorFunctionContainer["yellow"] = {}
		self.colorFunctionContainer["blue"] = {}

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setColorFunction(self, color, level, functionList):
		#printl("", self, "S")

		self.colorFunctionContainer[color][level] = functionList

		#printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getColorFunction(self, color, level):
		printl("", self, "S")

		# we put this into try because if there is no function registered it will come a gs
		try:
			return self.colorFunctionContainer[color][level][1]
		except:
			return False

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def alterColorFunctionNames(self, level):
		printl("", self, "S")
		colorList = ["red", "green", "yellow", "blue"]

		for color in colorList:
			functionList = self.colorFunctionContainer[color][level]

			if functionList is not None:
				# if it is not already visible we change this now
				if self["btn_"+ color + "Text"].getVisible() == 0:
					self["btn_"+ color + "Text"].show()
					self["btn_"+ color].show()

				self["btn_"+ color + "Text"].setText(self.colorFunctionContainer[color][level][0])
			else:
				if self["btn_"+ color + "Text"].getVisible() == 1:
					self["btn_"+ color + "Text"].hide()
					self["btn_"+ color].hide()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setMultiLevelElements(self, levels):
		printl("", self, "S")
		self.levels = levels

		dp_highlighted = parseColor(getSkinHighlightedColor())
		dp_normal = parseColor(getSkinNormalColor())

		for i in range(1,int(levels)+1):
			self["L"+str(i)] = MultiColorLabel()
			self["L"+str(i)].foreColors = [dp_highlighted, dp_normal]
			self["L"+str(i)].setText(str(i))

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setLevelActive(self, currentLevel):
		printl("", self, "S")

		self.currentFunctionLevel = currentLevel
		printl("currentFunctionLevel: " + str(self.currentFunctionLevel), self, "D")

		for i in range(1,int(self.levels)+1):
			if int(self.currentFunctionLevel) == int(i):
				self["L" + str(i)].setForegroundColorNum(0)
			else:
				self["L" + str(i)].setForegroundColorNum(1)

		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPH_Screen(Screen):

	#===============================================================================
	#
	#===============================================================================
	def __init__(self, session):
		printl("", self, "S")

		Screen.__init__(self, session)

		self["globalActions"] = HelpableActionMap(self, "DP_PluginCloser",
			{
			    "stop":    (self.closePlugin, ""),
			}, -2)

		self.onLayoutFinish.append(self.addNewScreen)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def addNewScreen(self):
		printl("", self, "S")

		addNewScreen(self)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def closePlugin(self):
		printl("", self, "S")

		closePlugin(self.session)

		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPH_Filter(NumericalTextInput):

	#===============================================================================
	#
	#===============================================================================
	def __init__(self):
		printl("", self, "S")

		NumericalTextInput.__init__(self)

		self["number_key_popup"] = Label()
		self["number_key_popup"].hide()

		self["filterActions"] = HelpableActionMap(self, "DP_FilterMenuActions",
			{
			"1":			(self.onKey1, ""),
			"2":			(self.onKey2, ""),
			"3":			(self.onKey3, ""),
			"4":			(self.onKey4, ""),
			"5":			(self.onKey5, ""),
			"6":			(self.onKey6, ""),
			"7":			(self.onKey7, ""),
			"8":			(self.onKey8, ""),
			"9":			(self.onKey9, ""),
			"0":			(self.onKey0, ""),
			}, -2)

		# for number key input
		self.setUseableChars(u' 1234567890abcdefghijklmnopqrstuvwxyz')

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey1(self):
		printl("", self, "S")

		self.onNumberKey(1)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey2(self):
		printl("", self, "S")

		self.onNumberKey(2)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey3(self):
		printl("", self, "S")

		self.onNumberKey(3)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey4(self):
		printl("", self, "S")

		self.onNumberKey(4)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey5(self):
		printl("", self, "S")

		self.onNumberKey(5)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey6(self):
		printl("", self, "S")

		self.onNumberKey(6)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey7(self):
		printl("", self, "S")

		self.onNumberKey(7)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey8(self):
		printl("", self, "S")

		self.onNumberKey(8)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey9(self):
		printl("", self, "S")

		self.onNumberKey(9)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onKey0(self):
		printl("", self, "S")

		self.onNumberKey(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNumberKey(self, number):
		printl("", self, "S")

		printl(str(number), self, "I")

		key = self.getKey(number)
		if key is not None:
			keyvalue = key.encode("utf-8")
			if len(keyvalue) == 1:
				self.onNumberKeyLastChar = keyvalue[0].upper()
				self.onNumberKeyPopup(self.onNumberKeyLastChar, True)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def onNumberKeyPopup(self, value, visible):
		printl("", self, "S")

		if visible:
			self["number_key_popup"].setText(value)
			self["number_key_popup"].show()
		else:
			self["number_key_popup"].hide()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def timeout(self):
		"""
		onNumberKeyTimeout
		"""
		printl("", self, "S")

		printl(self.onNumberKeyLastChar, self, "I")
		if self.onNumberKeyLastChar != ' ':
			pass
			# filter
		else:
			pass
			# reset filter

		self.filter()

		self.onNumberKeyPopup(self.onNumberKeyLastChar, False)
		NumericalTextInput.timeout(self)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def filter(self):
		printl("", self, "S")

		if self.onNumberKeyLastChar == " ":
			self["menu"].setList(self.beforeFilterListViewList)

			# we also have to reset the variable because this one is passed to player
			self.listViewList = self.beforeFilterListViewList
		else:
			self.listViewList = [x for x in self.beforeFilterListViewList if x[0][0] == self.onNumberKeyLastChar]
			self["menu"].setList(self.listViewList)

		self.refreshMenu()

		printl("", self, "C")