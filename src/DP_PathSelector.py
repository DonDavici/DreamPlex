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
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap

from Components.FileList import FileList
from Components.Label import Label

from DP_ViewFactory import getGuiElements

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===========================================================================
# 
#===========================================================================
class DPS_PathSelector(Screen):

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, initDir, myType):
		printl("", self, "S")
		
		Screen.__init__(self, session)

		self.guiElements = getGuiElements()

		self.myType = myType
		inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		inhibitMounts = []
		self["filelist"] = FileList(initDir, showFiles=False, inhibitMounts=inhibitMounts, inhibitDirs=inhibitDirs)
		self["target"] = Label()
		self["target"].setText(initDir)
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"green": self.green,
			"red": self.cancel
			
		}, -1)

		self["targetText"] = Label()

		self["btn_red"]			= Pixmap()
		self["btn_redText"]		= Label()

		self["btn_green"]		= Pixmap()
		self["btn_greenText"]   = Label()

		self.onLayoutFinish.append(self.finishLayout)
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_redText"].setText(_("Cancel"))

		self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])
		self["btn_greenText"].setText(_("Ok"))

		self["targetText"].setText(_("Target: "))

		self.setTitle(_("Pathselector"))

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def cancel(self):
		printl("", self, "S")
		
		self.close(self["filelist"].getSelection()[0], self.myType)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def green(self):
		printl("", self, "S")
		
		self.close(self["filelist"].getSelection()[0], self.myType)
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def up(self):
		printl("", self, "S")
		
		self["filelist"].up()
		self.updateTarget()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def down(self):
		printl("", self, "S")
		
		self["filelist"].down()
		self.updateTarget()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def left(self):
		printl("", self, "S")
		
		self["filelist"].pageUp()
		self.updateTarget()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def right(self):
		printl("", self, "S")
		
		self["filelist"].pageDown()
		self.updateTarget()
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def ok(self):
		printl("", self, "S")
		
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateTarget()
			
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def updateTarget(self):
		printl("", self, "S")
		
		currFolder = self["filelist"].getSelection()[0]
		if currFolder is not None:
			self["target"].setText(currFolder)
		else:
			self["target"].setText(_("Invalid Location"))
			
		printl("", self, "C")