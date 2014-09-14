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
import traceback
import re
import urllib
from threading import currentThread
from enigma import ePythonMessagePump

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

from DPH_PlexGdm import PlexGdm
from DP_Syncer import ThreadQueue

from __init__ import getVersion
from __common__ import printl2 as printl, getBoxInformation

#===============================================================================
#
#===============================================================================
class HttpDeamon(Thread):

	session = None

	#===========================================================================
	#
	#===========================================================================
	def __init__(self):
		self.playerData = ThreadQueue()
		self.playerDataPump = ePythonMessagePump()

	#===========================================================================
	#
	#===========================================================================
	def setCallbacks(self, playerCallback):

		self.playerCallback = playerCallback

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


		self.HandlerClass = MyHandler
		self.ServerClass = HTTPServer
		self.protocol = "HTTP/1.0"

		self.start()

		# this starts updatemechanism to show up as player in devices like ios
		client = PlexGdm(debug=3)
		version = str(getVersion())
		gBoxType = getBoxInformation()
		clientBox = "8000"
		printl("clientBox: " + str(gBoxType), self, "D")
		client.clientDetails(clientBox, "192.168.45.80", "8000", "DreamPlex", version)
		client.start_registration()

		if client.check_client_registration():
			printl("Successfully registered", self, "D")
		else:
			printl("Unsuccessfully registered", self, "D")


		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	#def runHttp(session, playerCallback, HandlerClass = MyHandler,ServerClass = HTTPServer, protocol="HTTP/1.0"):
	def run(self):
		"""
		Test the HTTP request handler class.

		This runs an HTTP server on port 8000 (or the first command line
		argument).
		"""
		printl("", __name__, "S")

		port = 8000
		server_address = ('', port)

		self.HandlerClass.protocol_version = self.protocol
		self.HandlerClass.session = self.session
		self.HandlerClass.playerCallback = self.nowDoIt
		httpd = self.ServerClass(server_address, self.HandlerClass)

		sa = httpd.socket.getsockname()
		printl("Serving HTTP on" + str(sa[0]) + "port " + str(sa[1]) + "...", __name__, "D")
		httpd.serve_forever()

		printl("", __name__, "C")

	#===========================================================================
	#
	#===========================================================================
	def nowDoIt(self, data):
		print "nowDoIt =>"
		print currentThread()

		self.playerData.push((data,))
		self.playerDataPump.send(0)

#===============================================================================
#
#===============================================================================
class MyHandler(BaseHTTPRequestHandler):
	"""
	Serves a HEAD request
	"""
	session = None
	playerCallback = None


	#===========================================================================
	#
	#===========================================================================
	def do_HEAD(self):
		printl("", self, "S")

		printl("Serving HEAD request...", self, "D")
		self.answer_request()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def do_GET(self):
		printl("", self, "S")

		printl("Serving GET request...", self, "D")
		self.answer_request()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def answer_request(self):
		printl("", self, "S")

		try:
			self.send_response(200)
			request_path=self.path[1:]
			request_path=re.sub(r"\?.*","",request_path)
			printl("request path is: [%s]" % request_path, self, "D")

			if request_path=="version":
				from DP_Player import DP_Player
				#def __init__(self, session, listViewList, currentIndex, libraryName, autoPlayMode, resumeMode, playbackMode, poster):
				self.session.open(DP_Player)
				# self.end_headers()
				# self.wfile.write("DreamPlex Helper Remote Redirector: Running\r\n")
				# self.wfile.write("Version: 0.1")
				# self.send_response(200)

			elif request_path == "player/playback/playMedia":
				from Components.config import config
				self.g_serverConfig = config.plugins.dreamplex.Entries[0]
				from DPH_Singleton import Singleton
				from DP_PlexLibrary import PlexLibrary
				self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))


				from urlparse import urlparse, parse_qs
				params = parse_qs(urlparse(self.path).query)

				address = params["address"][0]
				port = params["port"][0]
				protocol = params["protocol"][0]
				key = params["key"][0]


				#response = self.plexInstance.doRequest(protocol + "://" + address + ":" + port + key)
				listViewList, mediaContainer = self.plexInstance.getMoviesFromSection(protocol + "://" + address + ":" + port + key)

				autoPlayMode = False
				resumeMode = False
				playbackMode = "0" # STREAMED
				whatPoster = None
				currentIndex = 0
				libraryName = "test"

				data = {"listViewList": listViewList, "mediaContainer": mediaContainer, "autoPlayMode": autoPlayMode, "resumeMode": resumeMode, "playbackMode": playbackMode, "whatPoster": whatPoster, "currentIndex": currentIndex, "libraryName": libraryName}


				self.playerCallback(data)


			elif request_path=="verify":
				printl("DreamPlex Helper -> listener -> detected remote verification request", self, "D")
				self.send_response(200)

			elif request_path == "xbmcCmds/xbmcHttp":
				self.wfile.write("<html><li>OK</html>")
				self.send_response(200)
				printl("DreamPlex Helper -> listener -> Detected remote application request", self, "D")
				printl("Path: %s" % self.path, self, "D")
				command_path=self.path.split('?')[1]

				printl("Request: %s " % urllib.unquote(command_path), self, "D")

				if command_path.split('=')[0] == 'command':
					printl("Command: Sending a json to Plex", self, "D")
			else:
				self.send_response(200)
		except:
				traceback.print_exc()
				self.wfile.close()

				printl("", self, "C")
				return
		try:
			self.wfile.close()
		except:
			pass

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def address_string(self):
		printl("", self, "S")

		host, port = self.client_address[:2]
		#return socket.getfqdn(host)

		printl("", self, "C")
		return host 

