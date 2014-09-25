# -*- coding: utf-8 -*-
"""
DreamPlex Plugin by DonDavici, 2012
 
https://github.com/DonDavici/DreamPlex

Based on XBMCLocalProxy 0.1 Copyright 2011 Torben Gerkensmeyer
Based on PleXBMC Remote Helper 0.2 Copyright 2013 Hippojay

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
#===============================================================================
# IMPORT
#===============================================================================
from enigma import ePythonMessagePump

from BaseHTTPServer import HTTPServer
from threading import Thread

from Components.config import config

from DPH_PlexGdm import PlexGdm
from DPH_RemoteHandler import RemoteHandler
from DP_Syncer import ThreadQueue

from __init__ import getVersion
from __common__ import printl2 as printl, getBoxInformation, getMyIp

#===============================================================================
#
#===============================================================================
class HttpDeamon(Thread):

	session = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, port, g_uuid):
		self.port = port
		self.g_uuid = g_uuid
		self.playerData = ThreadQueue()
		self.playerDataPump = ePythonMessagePump()

	#===========================================================================
	#
	#===========================================================================
	def getPlayerDataPump(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.playerDataPump

	#===========================================================================
	#
	#===========================================================================
	def getPlayerDataQueue(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.playerData

	#===========================================================================
	#
	#===========================================================================
	def setSession(self, session):
		self.session = session
		self.start()

	#===========================================================================
	#PROPERTIES
	#===========================================================================
	PlayerDataPump = property(getPlayerDataPump)
	PlayerData = property(getPlayerDataQueue)

	#===========================================================================
	#
	#===========================================================================
	def startDeamon(self):
		printl("", self, "S")

		Thread.__init__(self)

		self.HandlerClass = RemoteHandler
		self.ServerClass = HTTPServer
		self.protocol = "HTTP/1.0"
		self.myIp = getMyIp()

		# this starts updatemechanism to show up as player in devices like ios
		self.client = PlexGdm()
		version = str(getVersion())
		gBoxType = getBoxInformation()
		boxName = config.plugins.dreamplex.boxName.value

		self.client.clientDetails(self.g_uuid, boxName, self.port , gBoxType[1] + " (" + str(self.myIp) +")", version)
		self.client.start_registration()

		if self.client.check_client_registration():
			self.registered = True
			printl("Successfully registered", self, "D")
		else:
			self.registered = False
			printl("Unsuccessfully registered", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getDeamonState(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.registered, self.remoteListenerInformation

	#===========================================================================
	#
	#===========================================================================
	def stopRemoteDeamon(self):
		printl("", self, "S")

		self.client.stop_all()
		self.httpd.shutdown()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	#def runHttp(session, playerCallback, HandlerClass = MyHandler,ServerClass = HTTPServer, protocol="HTTP/1.0"):
	def run(self):
		printl("", __name__, "S")
		server_address = ("", self.port)#(self.myIp, self.port)

		self.HandlerClass.protocol_version = self.protocol
		self.HandlerClass.session = self.session
		self.HandlerClass.playerCallback = self.nowDoIt
		self.httpd = self.ServerClass(server_address, self.HandlerClass)

		sa = self.httpd.socket.getsockname()

		self.remoteListenerInformation = "Serving HTTP on " + str(sa[0]) + " port " + str(sa[1])

		printl(self.remoteListenerInformation, __name__, "D")
		self.httpd.serve_forever()

		printl("", __name__, "C")

	#===========================================================================
	#
	#===========================================================================
	def nowDoIt(self, data):

		self.playerData.push((data,))
		self.playerDataPump.send(0)

