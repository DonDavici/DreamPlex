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
import sys
import time

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from os import system, popen

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Input import Input
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, testPlexConnectivity
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__init__ import initServerEntryConfig

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

#===============================================================================
# class
# DPS_SystemCheck
#===============================================================================
class DPS_SystemCheck(Screen):
	oeVersion = None
	check = None
	
	def __init__(self, session):
		'''
		'''
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.session = session
		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		"ok": self.startSelection,
		"cancel": self.cancel,
		"red": self.cancel,
		}, -1)
		
		vlist = []
		
		self.oeVersion = self.getBoxArch()
		
		if self.oeVersion == "mipsel":
			vlist.append((_("found mipsel (OE 1.6) => Check for 'gst-plugin-fragmented"), "oe16"))
		
		elif self.oeVersion == "mips32el":
			vlist.append((_("found mips32el (OE 2.0) => Check for 'gst-plugins-bad-fragmented"), "oe20"))
		
		else:
			printl("unknown oe version", self, "W")
			vlist.append((_("Check for 'gst-plugin-fragmented if you are using OE16."), "oe16"))
			vlist.append((_("Check for 'gst-plugins-bad-fragmented if you are using OE20."), "oe20"))
		
		vlist.append((_("Check curl installation data."), "check_Curl"))
		vlist.append((_("Check DreamPlex installation data."), "check_DP"))
		
		self["content"] = MenuList(vlist)
		
		self["key_red"] = StaticText(_("Exit"))
		
		printl("", self, "C")
		
	
	#===========================================================================
	# 
	#===========================================================================
	def startSelection(self):
		'''
		'''
		printl("", self, "S")
		
		selection = self["content"].getCurrent()
		
		if selection[1] == "oe16" or selection[1] == "oe20":
			self.checkLib(selection[1])
		
		if selection[1] == "check_DP":
			self.checkDreamPlexInstallation()
			
		if selection[1] == "check_Curl":
			self.checkCurlInstallation()	
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def checkCurlInstallation(self):
		'''
		'''
		printl("", self, "S")
		
		command = "opkg status curl"
		
		self.check = "curl"
		self.executeCommand(command)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def checkDreamPlexInstallation(self):
		'''
		'''
		printl("", self, "S")
		
		command = "opkg status DreamPlex"
		
		self.check = "dreamplex"
		self.executeCommand(command)
		
		printl("", self, "C")
	
	#===============================================================================
	# 
	#===============================================================================	
	def checkLib(self, arch):
		'''
		'''
		printl("", self, "S")
		
		command = None
		
		if arch == "oe16":
			command = "opkg status gst-plugin-fragmented"
			self.oeVersion = "mipsel"
		
		elif arch == "oe20":
			command = "opkg status gst-plugins-bad-fragmented"
			self.oeVersion = "mips32el"
		
		else:
			printl("someting went wrong with arch type", self, "W")
		
		self.check = "gst"
		self.executeCommand(command)
		
		printl("", self, "C")
		

	#===============================================================================
	# 
	#===============================================================================
	def executeCommand(self, command):
		'''
		'''
		printl("", self, "S")
		
		pipe = popen(command, "r")
		
		if pipe:
			data = pipe.read(8192)
			pipe.close()
			if data is not None and data != "":
				# plugin is installed
				self.session.open(MessageBox, _("Information:\n") + data, MessageBox.TYPE_INFO)
			else:
				# plugin is not install
				if self.check == "gst":
					self.session.openWithCallback(self.installStreamingLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)
				
				elif self.check == "curl":
					self.session.openWithCallback(self.installCurlLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)
				
				elif self.check == "dreamplex":
					# for now we do nothing at this point
					pass
				
				else:
					printl("no proper value i self.check", self, "W")
		
		printl("", self, "C")
		
	#===============================================================================
	# 
	#===============================================================================
	def installCurlLibs(self, confirm):
		'''
		'''
		printl("", self, "S")
		
		if confirm:
			# User said 'Yes'
			
			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install curl"
		
			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install curl"
		
			else:
				printl("something went wrong finding out the oe-version", self, "W")
			
			if not system(command):
				# Successfully installed
				#defaultServer = plexServerConfig.getDefaultServer()
				#self.openSectionlist(defaultServer)
				pass
			else:
				# Fail, try again and report the output...
				pipe = popen(command, "r")
				if pipe is not None:
					data = pipe.read(8192)
					if data is None:
						data = "Unknown Error"
					pipe.close()
					self.session.open(MessageBox, _("Could not install "+ command + ":\n") + data, MessageBox.TYPE_ERROR)
				# Failed to install
				self.cancel()
		else:
			# User said 'no' 
			self.cancel()
		
		printl("", self, "C")
	
	#===============================================================================
	# 
	#===============================================================================
	def installStreamingLibs(self, confirm):
		'''
		'''
		printl("", self, "S")
		
		if confirm:
			# User said 'Yes'
			
			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install gst-plugin-fragmented"
		
			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install gst-plugins-bad-fragmented"
		
			else:
				printl("something went wrong finding out the oe-version", self, "W")
			
			if not system(command):
				# Successfully installed
				#defaultServer = plexServerConfig.getDefaultServer()
				#self.openSectionlist(defaultServer)
				pass
			else:
				# Fail, try again and report the output...
				pipe = popen(command, "r")
				if pipe is not None:
					data = pipe.read(8192)
					if data is None:
						data = "Unknown Error"
					pipe.close()
					self.session.open(MessageBox, _("Could not install "+ command + ":\n") + data, MessageBox.TYPE_ERROR)
				# Failed to install
				self.cancel()
		else:
			# User said 'no' 
			self.cancel()
		
		printl("", self, "C")

	#===================================================================
	# 
	#===================================================================
	def cancel(self):
		'''
		'''
		printl("", self, "S")

		self.close(False,self.session)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def getBoxArch(self):
		'''
		'''
		printl("", self, "S")
		
		ARCH = "unknown"
		
		if (sys.version_info < (2, 6, 8) and sys.version_info > (2, 6, 6)):
			ARCH = "mipsel"
				
		if (sys.version_info < (2, 7, 4) and sys.version_info > (2, 7, 0)):
			ARCH = "mips32el"
				
		printl("", self, "C")
		return ARCH