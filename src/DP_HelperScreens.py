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
#=================================
#IMPORT
#=================================
from Screens.InputBox import InputBox
from Screens.Screen import Screen

from DPH_ScreenHelper import DPH_ScreenHelper

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
#
#===============================================================================
class DPS_InputBox(InputBox, DPH_ScreenHelper):

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, *args, **kwargs):
		Screen.__init__(self, session)
		InputBox.__init__(self, session, **kwargs)
		DPH_ScreenHelper.__init__(self)
		self.entryData = args

		self.setMenuType("input_box")

		printl("entryData: " + str(self.entryData), self, "D")

		self.setTitle(_("Search ..."))

		self.onLayoutFinish.append(self.finishLayout)

	#===============================================================================
	#
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.initMiniTv()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def go(self):
		printl("", self, "S")

		self.close(self.entryData, self["input"].getText())

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def cancel(self):
		printl("", self, "S")

		self.close(self.entryData)

		printl("", self, "C")
