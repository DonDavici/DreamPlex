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
from Components.config import config
from enigma import eSize, getDesktop

from Components.VideoWindow import VideoWindow
from Components.Label import Label

from __common__ import printl2 as printl

#===============================================================================
#
#===============================================================================
class DPH_ScreenHelper(object):

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
		else:
			self["miniTv"] = Label()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def initMiniTv(self):
		printl("", self, "S")

		if not self.stopLiveTvOnStartup or self.forceMiniTv:
			# TODO make this dynamik via skin params file
			w = 400
			h = 225
			desk = getDesktop(0)
			self["miniTv"].instance.setFBSize(desk.size())
			self["miniTv"].instance.resize(eSize(w, h))
		else:
			self["miniTv"].hide()

		printl("", self, "C")


