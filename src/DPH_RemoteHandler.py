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
from BaseHTTPServer import BaseHTTPRequestHandler
import traceback
import re

from DPH_Singleton import Singleton
from DP_PlexLibrary import PlexLibrary

from __common__ import printl2 as printl, getVersion

#===============================================================================
#
#===============================================================================
class RemoteHandler(BaseHTTPRequestHandler):
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
				self.end_headers()
				self.wfile.write("DreamPlex Helper Remote Redirector: Running\r\n")
				self.wfile.write("Version: " + getVersion())
				self.send_response(200)

			elif request_path == "player/playback/playMedia":
				from Components.config import config

				from urlparse import urlparse, parse_qs
				params = parse_qs(urlparse(self.path).query)

				address = params["address"][0]
				port = params["port"][0]
				protocol = params["protocol"][0]
				key = params["key"][0]
				machineIdentifier = params["machineIdentifier"][0]
				printl("target machineIdentifier: " + str(machineIdentifier), self, "D")

				for serverConfig in config.plugins.dreamplex.Entries:
					printl("current machineIdentifier: " + str(serverConfig.machineIdentifier.value), self, "D")

					if serverConfig.machineIdentifier.value == machineIdentifier:
						printl("we have a match ...", self, "D")
						self.g_serverConfig = serverConfig

						self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig))

						listViewList, mediaContainer = self.plexInstance.getMoviesFromSection(protocol + "://" + address + ":" + port + key)

						autoPlayMode = False
						resumeMode = False
						playbackType = self.g_serverConfig.playbackType.value
						whatPoster = None
						currentIndex = 0
						libraryName = "Mixed"

						data = {"listViewList": listViewList, "mediaContainer": mediaContainer, "autoPlayMode": autoPlayMode, "resumeMode": resumeMode, "playbackMode": playbackType, "whatPoster": whatPoster, "currentIndex": currentIndex, "libraryName": libraryName}

						self.playerCallback(data)

					else:
						printl("no match ...", self, "D")

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