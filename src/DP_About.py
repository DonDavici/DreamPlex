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
from Components.ActionMap import ActionMap
from Components.Label import Label

from Screens.Screen import Screen

from __common__ import printl2 as printl
from __init__ import getVersion, _ # _ is translation

#===============================================================================
#
#===============================================================================		
class DPS_About(Screen):
	_session = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		
		self._session = session
		
		self["leftText"] = Label()
		self["rightText"] = Label()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"cancel": self.keyCancel,
		}, -2)
		
		self.onLayoutFinish.append(self.finishLayout)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle(_("About"))
		
		self["leftText"].setText(self.getLeftText())
		self["rightText"].setText(self.getRightText())

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
	def getLeftText(self):
		printl("", self, "S")
		
		content = ""
		content += "Information\n\n"
		content += "DreamPlex - a plex client for Enigma2 \n" 
		content += "Version: \t" + getVersion() + "\n\n"
		content += "Autor: \t DonDavici\n"
		content += "\n"
		content += "Skin: \t Ipman alias Yipman\n"
		content += "\n"
		content += "Contributors: \t wezhunter\n"
		content += "\t andyblac \n"
		content += "\n\nIf you like my work you can buy me a beer :-) \n\ndondavici@gmail.com"
		
		printl("", self, "C")
		return content

		#===========================================================================
	#
	#===========================================================================
	def getRightText(self):
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
