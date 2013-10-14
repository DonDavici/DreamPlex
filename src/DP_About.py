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
from Components.Input import Input
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.HelpMenu import HelpableScreen

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
from Plugins.Extensions.DreamPlex.__init__ import getVersion

#===============================================================================
# class
# DPS_Settings
#===============================================================================		
class DPS_About(Screen):
	_session = None
	
	def __init__(self, session):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		
		self._session = session
		
		self["about"] = Label()
		
		
		self["key_red"] = StaticText(_("Close"))
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyCancel,
			"cancel": self.keyCancel,
		}, -2)
		
		self.onLayoutFinish.append(self.setContent)
		
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def setContent(self):
		printl("", self, "S")
		
		self.setTitle(_("About"))
		self["about"].setText(self.getText())
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
		
		content = ""
		content += "Information\n\n"
		content += "DreamPlex - a plex client for Enigma2 \n" 
		content += "Version: \t" + getVersion() + "\n\n"
		content += "Autor: \t DonDavici\n"
		content += "\n"
		content += "Contributors: \t wezhunter\n"
		content += "\t andyblac \n"
		content += "\n"
		content += "Skinner: \t IPMAN\n"
		content += "\n\nIf you like my work you can buy me a beer :-) \n\ndondavici@gmail.com"
		
		printl("", self, "C")
		return content
