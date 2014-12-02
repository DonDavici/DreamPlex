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
from DPH_SubscriptionManager import SubscriptionManager

from __common__ import printl2 as printl, getMyIp

#===============================================================================
#
#===============================================================================
class HttpDeamon(Thread):

	session = None
	httpd = None
	deamonState = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self):
		self.playerData = ThreadQueue()
		self.playerDataPump = ePythonMessagePump()
		self.subMgr = SubscriptionManager()

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
		self.subMgr.session = session
		self.start()

	#===========================================================================
	#PROPERTIES
	#===========================================================================
	PlayerDataPump = property(getPlayerDataPump)
	PlayerData = property(getPlayerDataQueue)

	#===========================================================================
	#
	#===========================================================================
	def notifySubscribers(self, players):
		self.subMgr.notify(players)

	#===========================================================================
	#
	#===========================================================================
	def addSubscriber(self, protocol, host, port, uuid, commandID):
		self.subMgr.addSubscriber(protocol, host, port, uuid, commandID)

	#===========================================================================
	#
	#===========================================================================
	def getSubscribersList(self):
		return self.subMgr.getSubscribersList()

	#===========================================================================
	#
	#===========================================================================
	def removeSubscriber(self, uuid):
		self.subMgr.removeSubscriber(uuid)

	#===========================================================================
	#
	#===========================================================================
	def updateCommandID(self, uuid, commandID):
		self.subMgr.updateCommandID(uuid, commandID)

	#===========================================================================
	#
	#===========================================================================
	def prepareDeamon(self):
		printl("", self, "S")

		Thread.__init__(self)

		self.HandlerClass = RemoteHandler
		self.ServerClass = HTTPServer
		self.protocol = "HTTP/1.0"
		self.myIp = getMyIp()

		if not self.myIp:
			self.deamonState = False
			return

		try:
			# this starts updatemechanism to show up as player in devices like ios
			self.client = PlexGdm()
			self.client.setClientDetails()
			self.client.start_registration()
		except:
			self.deamonState = False
			return

		if self.client.check_client_registration():
			self.registered = True
			printl("Successfully registered", self, "D")
		else:
			self.registered = False
			printl("Unsuccessfully registered", self, "D")

		self.deamonState = True

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getDeamonState(self):
		printl("", self, "S")

		printl("", self, "C")
		return self.registered, self.deamonState

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
		server_address = ("", config.plugins.dreamplex.remotePort.value)

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

