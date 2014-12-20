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
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.config import config
from Components.Pixmap import Pixmap
from Components.Label import Label

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from __common__ import printl2 as printl, checkXmlFile, getXmlContent, writeXmlContent
from __init__ import _ # _ is translation

from DP_ViewFactory import getGuiElements

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
		etree = None
		raise Exception
		#printl2("something weng wrong during xml parsing" + str(e), self, "E")


#===============================================================================
#
#===============================================================================
class DPS_Users(Screen):
	
	editMode = False
	
	def __init__(self, session, serverID, plexInstance):
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		#"ok": self.startSelection,
		"cancel": self.cancel,
		"red": self.redKey,
		"green": self.greenKey,
		"yellow": self.yellowKey,
		}, -1)
		
		self.guiElements = getGuiElements()
		self.plexInstance = plexInstance

		self.location = config.plugins.dreamplex.configfolderpath.value + "homeUsers"

		checkXmlFile(self.location)

		tree = getXmlContent(self.location)

		if tree is not None:
			self["content"] = DPS_UsersEntryList([], serverID, tree)
			self.updateList()
			self.error = False
		else:
			self.error = True

		self["btn_red"]			= Pixmap()
		self["btn_redText"]		= Label()

		self["btn_green"]		= Pixmap()
		self["btn_greenText"]   = Label()

		self["btn_yellow"]		= Pixmap()
		self["btn_yellowText"]   = Label()

		self.onShown.append(self.finishLayout)
		
		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		self["btn_red"].instance.setPixmapFromFile(self.guiElements["key_red"])
		self["btn_redText"].setText(_("Delete User"))

		self["btn_green"].instance.setPixmapFromFile(self.guiElements["key_green"])
		self["btn_greenText"].setText(_("Add User"))

		self["btn_yellow"].instance.setPixmapFromFile(self.guiElements["key_yellow"])
		self["btn_yellowText"].setText(_("Edit User"))

		if self.error:
			self.session.open(MessageBox,_("Something went wrong while opening users xml!"), MessageBox.TYPE_INFO)
			self.close()

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
		
		self.session.openWithCallback(self.setUsernameCallback, VirtualKeyBoard, title = (_("Enter the username here:")), text = "")
		
		printl("", self, "C")

	#===================================================================
	#
	#===================================================================
	def yellowKey(self):
		printl("", self, "S")

		content = self["content"].getCurrent()
		currentName = content[2][7]
		self.editMode = True

		self.session.openWithCallback(self.setUsernameCallback, VirtualKeyBoard, title = (_("Enter the username here:")), text = currentName)

		printl("", self, "C")
		
	
	#===================================================================
	# 
	#===================================================================
	def setUsernameCallback(self, callback = None, myType = None):
		printl("", self, "S")
		printl("myType: " + str(myType), self, "S")
		
		if callback is not None and len(callback):
			printl("username: " + str(callback), self, "D")
			self.username = str(callback)

			if self.editMode:
				content = self["content"].getCurrent()
				currentPin = content[3][7]
			else:
				currentPin = ""
			self.session.openWithCallback(self.setPinCallback, VirtualKeyBoard, title = (_("Enter the pin here:")), text = currentPin)
		else:
			self.session.open(MessageBox,_("Adding new user was not completed"), MessageBox.TYPE_INFO)
			self.close()
	
	#===================================================================
	# 
	#===================================================================
	def setPinCallback(self, callback = None):
		printl("", self, "S")
		
		if callback is not None:
			self.pin = str(callback)
		else:
			self.pin = ""

		printl("pin: " + str(self.pin), self, "D")

		xmlResponse = self.plexInstance.getHomeUsersFromPlex()

		users = xmlResponse.findall('User')

		for user in users:
			entryData = (dict(user.items()))
			title = entryData["title"]
			if self.username == title:
				printl("", self, "C")
				userId = entryData["id"]

				xmlResponse = self.plexInstance.switchHomeUser(userId, self.pin)

				entryData = (dict(xmlResponse.items()))
				self.authenticationToken = entryData["authenticationToken"]

				self.finishUserEntry()

		printl("", self, "C")

	#===================================================================
	#
	#===================================================================
	def finishUserEntry(self):
		printl("", self, "S")

		content = self["content"].getCurrent()
		currentId = content[1][7]
		self["content"].deleteSelectedUser(currentId)

		self["content"].addNewUser(self.username, self.pin, self.authenticationToken)

		self.editMode = False

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
			
			self["content"].deleteSelectedUser(currentId)
		self.close()
		
		printl("", self, "C")
		
#===============================================================================
#
#===============================================================================
class DPS_UsersEntryList(MenuList):
	
	lastMappingId = 0 # we use this to find the next id if we add a new element
	location = None
	
	def __init__(self, menuList, serverID, tree, enableWrapAround = True):
		printl("", self, "S")
		self.serverID = serverID
		self.tree = tree
		MenuList.__init__(self, menuList, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))

		self.location = config.plugins.dreamplex.configfolderpath.value + "homeUsers"

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

		printl("serverID: " + str(self.serverID), self, "D")
		for server in self.tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(self.serverID):

				for user in server.findall('user'):
					self.lastUserId = user.attrib.get("id")
					username = user.attrib.get("username")
					pin = user.attrib.get("pin")
					token = user.attrib.get("token")
					printl("self.lastUserId: " + str(self.lastUserId), self, "D")
					printl("username: " + str(username), self, "D")
					printl("pin: " + str(pin), self, "D")
					printl("token: " + str(token), self, "D")

					res = [user]
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(self.lastUserId)))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 50, 0, 300, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(username)))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 355, 0, 300, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(pin)))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, 655, 0, 300, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(token)))

					self.list.append(res)

		self.l.setList(self.list)
		self.moveToIndex(0)

		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def deleteSelectedUser(self, userId):
		printl("", self, "S")
		tree = getXmlContent(self.location)
		printl("serverID: " + str(self.serverID), self, "D")
		for server in tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(self.serverID):
				
				for user in server.findall('user'):
					printl("user: " + str(user.get('id')), self, "D")
					if str(user.get('id')) == str(userId):
						server.remove(user)
						writeXmlContent(tree, self.location)
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================	
	def addNewUser(self, username, pin, authenticationToken):
		printl("", self, "S")

		tree = getXmlContent(self.location)

		newId = int(self.lastMappingId) + 1

		printl("newId: " + str(newId), self, "D")
		printl("username: " + str(username), self, "D")
		printl("pin: " + str(pin), self, "D")
		printl("token: " + str(authenticationToken), self, "D")

		existingServer = False
		
		for server in tree.findall("server"):
			printl("servername: " + str(server.get('id')), self, "D")
			if str(server.get('id')) == str(self.serverID):
				existingServer = True
				
				server.append(etree.Element('user id="' + str(newId) + '" username="' + username + '" pin="' + pin + '" token="' + authenticationToken + '"'))
				writeXmlContent(tree, self.location)
		
		if not existingServer: # this server has no node in the xml
			printl("expanding server list", self, "D")
			tree.append(etree.Element('server id="' + str(self.serverID) + '"'))
			writeXmlContent(tree, self.location)
			
			# now lets go through the xml again to add the mapping to the server
			self.addNewUser(username, pin, authenticationToken)

		printl("", self, "C")
