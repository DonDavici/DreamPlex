# -*- coding: utf-8 -*-
'''
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
'''
#=================================
#IMPORT
#=================================
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Tools.BoundFunction import boundFunction

from Components.FileList import FileList
from Components.Label import Label

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===========================================================================
# 
#===========================================================================
class DPS_PathSelector(Screen):

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, initDir):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		inhibitMounts = []
		self["filelist"] = FileList(initDir, showDirectories = True, showMountpoints = True, showFiles = False, inhibitMounts = inhibitMounts, inhibitDirs = inhibitDirs)
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
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def cancel(self):
		printl("", self, "S")
		
		self.close(None)
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def green(self):
		printl("", self, "S")
		
		self.close(self["filelist"].getSelection()[0])
		
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