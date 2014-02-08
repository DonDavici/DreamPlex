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
from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
# class
# DPS_Settings
#===============================================================================        
class DPS_Help(Screen):
	_session = None

	def __init__(self, session):
		printl("", self, "S")

		Screen.__init__(self, session)

		self._session = session

		self["help"] = Label()

		self["key_red"] = StaticText(_("Close"))

		self["setupActions"] = HelpableActionMap(self, "DP_View",
		{
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"bouquet_up": (self.bouquetUp, ""),
			"bouquet_down": (self.bouquetDown, ""),
		}, -2)

		self.onLayoutFinish.append(self.setContent)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setContent(self):
		printl("", self, "S")

		self["help"].text = self.getText()

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
	def getText(self):
		printl("", self, "S")

		content = "Visit the DreamPlex Wiki!"
		content += "\n\n   https://github.com/DonDavici/DreamPlex/wiki"
		content += "\n\n\nGet support in one of the following forums!"
		content += "\n\n   http://www.i-have-a-dreambox.com"
		content += "\n\n   http://www.vuplus-support.org/wbb3"
		content += "\n\n\nFind the git repository here!"
		content += "\n\n   https://github.com/DonDavici/DreamPlex"
		content += "\n\n\nDownload Dreamplex here!"
		content += "\n\n   https://bintray.com/dondavici/Dreambox"


		printl("", self, "C")
		return content

	#===========================================================================
	#
	#===========================================================================
	def bouquetUp(self):
		printl("", self, "S")

		self["help"].pageUp()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def bouquetDown(self):
		printl("", self, "S")

		self["help"].pageDown()

		printl("", self, "C")
