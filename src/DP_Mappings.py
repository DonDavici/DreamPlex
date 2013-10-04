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
import os.path

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, getDesktop
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
from Screens.LocationBox import MovieLocationBox
from Screens.InputBox import InputBox
from Screens.Console import Console as SConsole
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, testPlexConnectivity, testInetConnectivity, checkXmlFile, getXmlContent, writeXmlContent
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__init__ import initServerEntryConfig, getVersion

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DP_PathSelector import DPS_PathSelector
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from twisted.python.versions import getVersionString

#===============================================================================
# import cProfile
#===============================================================================
try:
# Python 2.5
	import xml.etree.cElementTree as etree
	#printl2("running with cElementTree on Python 2.5+", __name__, "D")
except ImportError:
	try:
		# Python 2.5
		import xml.etree.ElementTree as etree
		#printl2("running with ElementTree on Python 2.5+", __name__, "D")
	except ImportError:
		printl2("something weng wrong during xml parsing" + str(e), self, "E")


#===============================================================================
# class
# DPS_SystemCheck
#===============================================================================
class DPS_Mappings(Screen):
	
	remotePath = None
	localPath = None
	
	def __init__(self, session, serverID):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.session = session
		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		#"ok": self.startSelection,
		"cancel": self.cancel,
		"red": self.redKey,
		"green": self.greenKey,
		}, -1)
		
		
		self["content"] = DPS_MappingsEntryList([], serverID)
		self.updateList()
		
		self["key_red"] = StaticText(_("Delete Entry"))
		self["key_green"] = StaticText(_("Add Entry"))
		
		printl("", self, "C")
		
	
	#===========================================================================
	# 
	#===========================================================================
	def updateList(self):
		printl("", self, "S")
		
		self["content"].buildList()

		printl("", self, "C")
		
	#===================================================================
	# 
	#===================================================================
	def cancel(self):
		printl("", self, "S")

		self.close(False,self.session)
		
		printl("", self, "C")
		
	#===================================================================
	# 
	#===================================================================
	def greenKey(self):
		printl("", self, "S")
		
		self.session.openWithCallback(self.setLocalPathCallback, DPS_PathSelector,"/", "mapping")
		
		printl("", self, "C")
		
	
	#===================================================================
	# 
	#===================================================================
	def setLocalPathCallback(self, callback = None, type = None):
		printl("", self, "S")
		
		if callback is not None and len(callback):
			printl("localPath: " + str(callback), self, "D")
			self.localPath = str(callback)
			self.session.openWithCallback(self.setRemotePathCallback, VirtualKeyBoard, title = (_("Enter your remote path segment here:")), text = "C:\Vidoes or /volume1/vidoes or \\\\SERVER\\Videos\\")
		else:
			self.session.open(MessageBox,_("Adding new mapping was not completed"), MessageBox.TYPE_INFO)
			self.close()
	
	#===================================================================
	# 
	#===================================================================
	def setRemotePathCallback(self, callback = None):
		printl("", self, "S")
		
		if callback is not None and len(callback):
			printl("remotePath: " + str(callback), self, "D")
			self.remotePath = str(callback)
			
			self["content"].addNewMapping(self.remotePath, self.localPath)
		else:
			self.session.open(MessageBox,_("Adding new mapping was not completed"), MessageBox.TYPE_INFO)
		
		
		self.close()
		printl("", self, "C")	
		
	#===================================================================
	# 
	#===================================================================
	def redKey(self):
		printl("", self, "S")

		content = self["content"].getCurrent()
		if content is not None:
			currentId = content[1][7]
			printl("currentId: " + str(currentId), self, "D")
			
			self["content"].deleteSelectedMapping(currentId)
		self.close()
		
		printl("", self, "C")
		
#===============================================================================
# class
# DPS_ServerEntryList
#===============================================================================
class DPS_MappingsEntryList(MenuList):
	
	lastMappingId = 0 # we use this to find the next id if we add a new element
	location = None
	
	def __init__(self, menuList, serverID, enableWrapAround = True):
		printl("", self, "S")
		self.serverID = serverID
		MenuList.__init__(self, menuList, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.location = config.plugins.dreamplex.configfolderpath.value + "mountMappings"

		checkXmlFile(self.location)
		
		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def postWidgetCreate(self, instance):
		printl("", self, "S")
		
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

		printl("", self, "C")
		
	#===========================================================================
	# 
	#===========================================================================
	def buildList(self):
		printl("", self, "S")
		
		self.list=[]
		
		tree = getXmlContent(self.location)
		
		printl("serverID: " + str(self.serverID), self, "D")
		for server in tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(self.serverID):
				
				for mapping in server.findall('mapping'):
					self.lastMappingId = mapping.attrib.get("id")
					remotePathPart = mapping.attrib.get("remotePathPart")
					localPathPart = mapping.attrib.get("localPathPart")
					printl("self.lastMappingId: " + str(self.lastMappingId), self, "D")
					printl("remotePathPart: " + str(remotePathPart), self, "D")
					printl("localPathPart: " + str(localPathPart), self, "D")
					
					res = [mapping]
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(self.lastMappingId)))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 300, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(localPathPart)))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 355, 0, 300, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(remotePathPart)))
	
					self.list.append(res)
		
		self.l.setList(self.list)
		self.moveToIndex(0)
		
		#self.deleteSelectedMapping(1)
				
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def deleteSelectedMapping(self, mappingId):
		printl("", self, "S")
		tree = getXmlContent(self.location)
		printl("serverID: " + str(self.serverID), self, "D")
		for server in tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(self.serverID):
				
				for mapping in server.findall('mapping'):
					printl("mapping: " + str(mapping.get('id')), self, "D")
					if str(mapping.get('id')) == str(mappingId):
						server.remove(mapping)
						writeXmlContent(tree, self.location)
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================	
	def addNewMapping(self, remotePath, localPath):
		printl("", self, "S")

		tree = getXmlContent(self.location)
		
		newId = int(self.lastMappingId) + 1
		
		printl("newId: " + str(newId), self, "D")
		printl("remotePath: " + str(remotePath), self, "D")
		printl("localPath: " + str(localPath), self, "D")
		
		existingServer = False
		
		for server in tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(self.serverID):
				existingServer = True
				
				server.append(etree.Element('mapping id="' + str(newId) + '" remotePathPart="' + remotePath + '" localPathPart="' + localPath + '"'))
				writeXmlContent(tree, self.location)
		
		if existingServer == False: # this server has no node in the xml
			printl("expanding server list", self, "D")
			tree.append(etree.Element('server id="' + str(self.serverID) + '"'))
			writeXmlContent(tree, self.location)
			
			# now lets go through the xml again to add the mapping to the server
			self.addNewMapping(remotePath, localPath)
		
		printl("", self, "C")
