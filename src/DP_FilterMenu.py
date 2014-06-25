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

from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

from Components.Label import Label

from Screens.Screen import Screen

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

from DPH_Singleton import Singleton
from DPH_MovingLabel import DPH_HorizontalMenu

#===============================================================================
#
#===============================================================================
class DPS_ServerMenu(Screen, DPH_HorizontalMenu):

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, filterData ):
		printl("", self, "S")
		Screen.__init__(self, session)

		self.session = session
		self.plexInstance = Singleton().getPlexInstance()

		self.setMenuType("server_menu")

		if self.g_horizontal_menu:
			self.setHorMenuElements(depth=2)
			self.translateNames()

		self["title"] = StaticText()
		self["txt_exit"] = Label()
		self["txt_menu"] = Label()
		self["menu"]= List(enableWrapAround=True)

		self.menu_main_list = self["menu"].list

		self["actions"] = HelpableActionMap(self, "DP_MainMenuActions",
			{
				"ok":		(self.okbuttonClick, ""),
				"left":		(self.left, ""),
				"right":	(self.right, ""),
				"up":		(self.up, ""),
				"down":		(self.down, ""),
				"cancel":	(self.cancel, ""),
			    "menu":		(self.onKeyMenu, ""),
			}, -2)

		self.onLayoutFinish.append(self.finishLayout)
		self.onShown.append(self.checkSelectionOverride)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle(_("Server Menu"))

		self["txt_exit"].setText(_("Exit"))
		self["txt_menu"].setText(_("Menu"))

		self.checkServerState()

		if self.g_horizontal_menu:
			# init horizontal menu
			self.refreshOrientationHorMenu(0)



		printl("", self, "C")
