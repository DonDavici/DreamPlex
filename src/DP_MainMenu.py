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
import time

from Components.ActionMap import HelpableActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.Label import Label

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from DP_PlexLibrary import PlexLibrary
from DP_SystemCheck import DPS_SystemCheck
from DP_Settings import DPS_Settings
from DP_Server import DPS_Server
from DP_About import DPS_About
from DP_ServerMenu import DPS_ServerMenu

from DPH_Singleton import Singleton
from DPH_MovingLabel import DPH_HorizontalMenu
from DPH_WOL import wake_on_lan

from __common__ import printl2 as printl, testPlexConnectivity, testInetConnectivity
from __plugin__ import Plugin
from __init__ import _ # _ is translation
#===============================================================================
#
#===============================================================================	
class DPS_MainMenu(Screen, DPH_HorizontalMenu):

	g_horizontal_menu = False
	selectedEntry = None
	g_serverConfig = None
	nextExitIsQuit = True
	currentService = None
	plexInstance = None
	selectionOverride = None

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, session, allowOverride=True):
		printl("", self, "S")
		Screen.__init__(self, session)
		self.selectionOverride = None
		printl("selectionOverride:" +str(self.selectionOverride), self, "D")
		self.session = session

		self.setMenuType("main_menu")

		self["title"] = StaticText()
		self["txt_exit"] = Label()

		# get all our servers as list
		self.getServerList(allowOverride)
		
		self["menu"]= List(self.mainMenuList, True)
		
		self.menu_main_list = self["menu"].list

		self["actions"] = HelpableActionMap(self, "DP_MainMenuActions", 
			{
				"ok":		(self.okbuttonClick, ""),
				"left":		(self.left, ""),
				"right":	(self.right, ""),
				"up":		(self.up, ""),
				"down":		(self.down, ""),
				"cancel":	(self.cancel, ""),
			}, -2)
		
		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
			self.session.nav.stopService()

		if self.g_horizontal_menu:
			self.setHorMenuElements()
			self.translateNames()

		self.onFirstExecBegin.append(self.onExec)
		self.onFirstExecBegin.append(self.onExecRunDev)
		self.onLayoutFinish.append(self.finishLayout)
		self.onShown.append(self.checkSelectionOverride)

		printl("", self, "C")

	#===============================================================================
	# 
	#===============================================================================
	def finishLayout(self):
		printl("", self, "S")
		
		self.setTitle(_("Main Menu"))

		self["txt_exit"].setText(_("Exit"))

		if self.g_horizontal_menu:
			# init horizontal menu
			self.refreshOrientationHorMenu(0)

		printl("", self, "C")

	#===============================================================
	# 
	#===============================================================
	def okbuttonClick(self, selectionOverride = None):
		printl("", self, "S")

		# this is used to step in directly into a server when there is only one entry in the serverlist
		# todo check if this works
		if selectionOverride is not None:
			selection = selectionOverride
		else:
			selection = self["menu"].getCurrent()
		
		printl("selection = " + str(selection), self, "D")

		if selection is not None:
			
			self.selectedEntry = selection[1]
			printl("selected entry " + str(self.selectedEntry), self, "D")
			
			if type(self.selectedEntry) is int:
				printl("selected entry is int", self, "D")
				
				if self.selectedEntry == Plugin.MENU_MAIN:
					printl("found Plugin.MENU_MAIN", self, "D")
					self["menu"].setList(self.menu_main_list)
			
				elif self.selectedEntry == Plugin.MENU_SERVER:
					printl("found Plugin.MENU_SERVER", self, "D")

					self.g_serverConfig = selection[3]
					# now that we know the server we establish global plexInstance
					self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))

					# check if server is reachable
					self.checkServerState()

				elif self.selectedEntry == Plugin.MENU_SYSTEM:
					printl("found Plugin.MENU_SYSTEM", self, "D")
					self["menu"].setList(self.getSettingsMenu())
					self.setTitle(_("System"))
					self.refreshMenu(0)

					if self.g_horizontal_menu:
						self.refreshOrientationHorMenu(0)
				
			elif type(self.selectedEntry) is str:
				printl("selected entry is string", self, "D")

				if selection[1] == "DPS_Settings":
					self.session.open(DPS_Settings)
					
				elif selection[1] == "DPS_Server":
					self.session.open(DPS_Server)
					
				elif selection[1] == "DPS_SystemCheck":
					self.session.open(DPS_SystemCheck)
				
				elif selection[1] == "DPS_About":
					self.session.open(DPS_About)

			else:
				pass
					
			printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def getSettingsMenuList(self):
		printl("", self, "S")
		
		self["menu"].setList(self.getSettingsMenu())
		self.refreshMenu(0)

		printl("", self, "C")
	
	#==========================================================================
	# 
	#==========================================================================
	def up(self):
		printl("", self, "S")

		if self.g_horizontal_menu:
			self.left()
		else:
			self["menu"].selectPrevious()
		
		printl("", self, "C")	
	
	#===========================================================================
	# 
	#===========================================================================
	def down(self):
		printl("", self, "S")

		if self.g_horizontal_menu:
			self.right()
		else:
			self["menu"].selectNext()
		
		printl("", self, "C")
	
	#===============================================================================
	# 
	#===============================================================================
	def right(self):
		printl("", self, "S")
				
		try:
			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(+1)
			else:
				self["menu"].pageDown()
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")
			self["menu"].selectNext()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def left(self):
		printl("", self, "S")
		
		try:
			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(-1)
			else:
				self["menu"].pageUp()
		except Exception, ex:
			printl("Exception(" + str(type(ex)) + "): " + str(ex), self, "W")
			self["menu"].selectPrevious()
		
		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def exit(self):
		printl("", self, "S")

		if config.plugins.dreamplex.stopLiveTvOnStartup.value:
			printl("restoring liveTv", self, "D")
			self.session.nav.playService(self.currentService)

		self.close((True,) )

		printl("", self, "C")

	#===========================================================================
	# 
	#===========================================================================
	def cancel(self):
		printl("", self, "S")

		if self.nextExitIsQuit:
			self.exit()
		
		else:
			self.setTitle(_("Main Menu"))

			printl("selectedEntry " +  str(self.selectedEntry), self, "D")
			self.getServerList()

			self["menu"].setList(self.menu_main_list)
			self.nextExitIsQuit = True

			if self.g_horizontal_menu:
				self.refreshOrientationHorMenu(0)

		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def refreshMenu(self, value):
		printl("", self, "S")
		
		if value == 1:
			self["menu"].selectNext()
		elif value == -1:
			self["menu"].selectPrevious()

		printl("", self, "C")
		
#===============================================================================
# HELPER
#===============================================================================
		
	#===============================================================================
	# 
	#===============================================================================
	def Error(self, error):
		printl("", self, "S")
		
		self.session.open(MessageBox,_("UNEXPECTED ERROR:") + "\n%s" % error, MessageBox.TYPE_INFO)
		
		printl("", self, "C")
		
	#=======================================================================
	# 
	#=======================================================================
	def getSettingsMenu (self):
		printl("", self, "S")
		
		mainMenuList = []

		mainMenuList.append((_("Settings"), "DPS_Settings", "settingsEntry"))
		mainMenuList.append((_("Server"), "DPS_Server", "settingsEntry"))
		mainMenuList.append((_("Systemcheck"), "DPS_SystemCheck", "settingsEntry"))

		self.nextExitIsQuit = False
		
		printl("", self, "C")
		return mainMenuList

	#===============================================================================
	#
	#===============================================================================
	def checkSelectionOverride(self):
		printl("", self, "S")
		printl("self.selectionOverride: " + str(self.selectionOverride), self, "D")

		if self.selectionOverride is not None:
			self.okbuttonClick(self.selectionOverride)

		printl("", self, "C")
	#===============================================================================
	#
	#===============================================================================
	def getServerList(self, allowOverride=True):
			printl("", self, "S")

			self.mainMenuList = []

			# add servers to list
			for serverConfig in config.plugins.dreamplex.Entries:

				# only add the server if state is active
				if serverConfig.state.value:
					serverName = serverConfig.name.value

					self.mainMenuList.append((serverName, Plugin.MENU_SERVER, "serverEntry", serverConfig))

					# automatically enter the server if wanted
					if serverConfig.autostart.value and allowOverride:
						printl("here", self, "D")
						self.selectionOverride = [serverName, Plugin.MENU_SERVER, "serverEntry", serverConfig]

			self.mainMenuList.append((_("System"), Plugin.MENU_SYSTEM, "systemEntry"))
			self.mainMenuList.append((_("About"), "DPS_About", "aboutEntry"))

			printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkServerState(self):
		printl("", self, "S")

		self.g_wolon = self.g_serverConfig.wol.value
		self.g_wakeserver = str(self.g_serverConfig.wol_mac.value)
		self.g_woldelay = int(self.g_serverConfig.wol_delay.value)
		connectionType = str(self.g_serverConfig.connectionType.value)
		if connectionType == "0":
			ip = "%d.%d.%d.%d" % tuple(self.g_serverConfig.ip.value)
			port =  int(self.g_serverConfig.port.value)
			isOnline = testPlexConnectivity(ip, port)

		elif connectionType == "2":
			#state = testInetConnectivity("http://my.plexapp.com")
			isOnline = True
		else:
			isOnline = testInetConnectivity()

		if isOnline:
			stateText = "Online"
		else:
			stateText = "Offline"

		printl("Plexserver State: " + str(stateText), self, "I")
		if not isOnline:
			if self.g_wolon == True and connectionType == "0":
				self.showWakeMessage()

			else:
				self.showOfflineMessage()
		else:
			self.session.open(DPS_ServerMenu, self.g_serverConfig)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startServerMenu(self, answer):
		printl("", self, "S")
		printl("answer: " + str(answer), self, "D")

		if answer:
			self.checkServerState()
		else:
			self.session.open(DPS_ServerMenu, self.g_serverConfig)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showWakeMessage(self):
		printl("", self, "S")

		self.session.openWithCallback(self.executeWakeOnLan, MessageBox, _("Plexserver seems to be offline. Start with Wake on Lan settings? \n\nPlease note: \nIf you press yes the spinner will run for " + str(self.g_woldelay) + " seconds. \nAccording to your settings."), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def showOfflineMessage(self):
		printl("", self, "S")

		self.session.openWithCallback(self.startServerMenu,MessageBox,_("Plexserver seems to be offline. Please check your your settings or connection!\n Retry?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def executeWakeOnLan(self, confirm):
		printl("", self, "S")

		if confirm:
			# User said 'yes'
			printl("Wake On LAN: " + str(self.g_wolon), self, "D")

			for i in range(1,12):
				if not self.g_wakeserver == "":
					try:
						printl("Waking server " + str(i) + " with MAC: " + self.g_wakeserver, self, "D")
						wake_on_lan(self.g_wakeserver)
					except ValueError:
						printl("Incorrect MAC address format for server " + str(i), self, "D")
					except:
						printl("Unknown wake on lan error", self, "D")
			self.sleepNow()
		else:
			# User said 'no'
			self.refreshMenu(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def sleepNow (self):
		printl("", self, "S")

		time.sleep(int(self.g_woldelay))
		self.checkServerState()

		printl("", self, "C")

#===============================================================================
# ADDITIONAL STARTUPS
#===============================================================================
	
	#===============================================================================
	# 
	#===============================================================================
	def onExecRunDev(self):
		printl("", self, "S")
		
		printl("", self, "C")
	
	#===========================================================================
	# 
	#===========================================================================
	def onExec(self):
		printl("", self, "S")
		
		# activate this to develop plex player via ios or android app
		# state server is starting
		# test over: 127.0.0.1:8000/version
		# registration on plex server is working - player is showing up in handy app
		# next step is to find out what should happen if a button is pressed. 
		# for now we do not see any incoming traffic from the app :-(
		#HttpDeamon().startDeamon()
		
		if config.plugins.dreamplex.checkForUpdateOnStartup.value:
			DPS_SystemCheck(self.session).checkForUpdate()

		printl("", self, "C")
