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

from time import sleep
from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler

from Components.config import config

from DPH_Singleton import Singleton
from DP_PlexLibrary import PlexLibrary

from __common__ import printl2 as printl, getUUID, getVersion, getMyIp

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
	def do_OPTIONS(self):
		printl("", self, "S")

		printl("Serving OPTIONS request...", self, "D")
		self.send_response(200)
		self.setAccessControlHeaders()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def answer_request(self):
		printl("", self, "S")

		try:
			self.send_response(200)
			self.setAccessControlHeaders()

			request_path=self.path[1:]
			request_path=re.sub(r"\?.*","",request_path)

			printl("request path is: [%s]" % request_path, self, "D")

			if request_path == "player/timeline/poll":
				sleep(10)
				xml = "<MediaContainer location='navigation' commandID='10'><Timeline state='stopped' time='0' type='music' /><Timeline state='stopped' time='0' type='video' /><Timeline state='stopped' time='0' type='photo' /></MediaContainer>"
				self.setXmlHeader(xml)
				self.end_headers()
				self.wfile.write(xml)

			elif request_path == "resources":
				xml = self.getResourceXml()
				self.setXmlHeader(xml)
				self.end_headers()
				self.wfile.write(xml)

			elif request_path == "player/timeline/subscribe":
				xml = "<MediaContainer location='navigation' commandID='10'><Timeline state='stopped' time='0' type='music' /><Timeline state='stopped' time='0' type='video' /><Timeline state='stopped' time='0' type='photo' /></MediaContainer>"
				self.setXmlHeader(xml)
				self.end_headers()
				self.wfile.write(xml)

			elif request_path == "player/playback/seekTo":
				params = self.getParams()
				offset =  params["offset"][0]

			elif request_path == "player/playback/setParameters":
				params = self.getParams()
				volume = params["volume"][0]

				url = "http://localhost/web/vol?set=set" + str(volume)

				urllib.urlopen(url)
				self.send_response(200)

			elif request_path == "/player/playback/pause":
				url = "http://localhost/web/remotecontrol?command=400"

				urllib.urlopen(url)
				xml = "<MediaContainer location='navigation' commandID='10'><Timeline state='paused' time='0' type='music' /><Timeline state='paused' time='0' type='video' /><Timeline state='paused' time='0' type='photo' /></MediaContainer>"
				self.setXmlHeader(xml)
				self.end_headers()
				self.wfile.write(xml)

			elif request_path == "player/playback/stop":
				url = "http://localhost/web/remotecontrol?command=377"

				urllib.urlopen(url)
				self.send_response(200)

			elif request_path == "player/playback/skipNext":
				url = "http://localhost/web/remotecontrol?command=407"

				urllib.urlopen(url)
				self.send_response(200)

			elif request_path == "player/playback/stepForward":
				url = "http://localhost/web/remotecontrol?command=10"

				urllib.urlopen(url)
				self.send_response(200)

			elif request_path == "player/playback/stepBack":
				url = "http://localhost/web/remotecontrol?command=8"
				urllib.urlopen(url)
				self.send_response(200)

			elif request_path == "player/playback/skipPrevious":
				url = "http://localhost/web/remotecontrol?command=412"

				urllib.urlopen(url)
				self.send_response(200)

			elif request_path == "player/playback/playMedia":

				url = "http://localhost/web/powerstate?newstate=4"
				urllib.urlopen(url)

				params = self.getParams()

				address = params["address"][0]
				port = params["port"][0]
				completeAddress = address+":"+port
				protocol = params["protocol"][0]
				key = params["key"][0]

				if "offset" in params:
					offset = int(params["offset"][0])
				else:
					offset = 0

				machineIdentifier = params["machineIdentifier"][0]
				printl("target machineIdentifier: " + str(machineIdentifier), self, "D")

				for serverConfig in config.plugins.dreamplex.Entries:
					printl("current machineIdentifier: " + str(serverConfig.machineIdentifier.value), self, "D")

					if machineIdentifier in serverConfig.machineIdentifier.value:

						printl("we have a match ...", self, "D")
						self.g_serverConfig = serverConfig

						self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig, completeAddress, machineIdentifier))

						listViewList, mediaContainer = self.plexInstance.getMoviesFromSection(protocol + "://" + address + ":" + port + key)

						autoPlayMode = False

						if offset > 0:
							forceResume = True
						else:
							forceResume = False

						resumeMode = False # this is always false because the ios and android app ask itself if we want to resume :-) no need to ask second time

						playbackMode = self.g_serverConfig.playbackType.value
						currentIndex = 0
						libraryName = "Mixed"

						data = {"listViewList": listViewList, "mediaContainer": mediaContainer, "autoPlayMode": autoPlayMode, "forceResume":  forceResume, "resumeMode": resumeMode, "playbackMode": playbackMode, "currentIndex": currentIndex, "libraryName": libraryName}

						self.playerCallback(data)

						xml = "<MediaContainer location='navigation' commandID='10'><Timeline state='stopped' time='0' type='music' /><Timeline state='stopped' time='0' type='video' /><Timeline state='stopped' time='0' type='photo' /></MediaContainer>"
						self.setXmlHeader(xml)
						self.end_headers()
						self.wfile.write(xml)

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

	#===========================================================================
	#
	#===========================================================================
	def getResourceXml(self):
		printl("", self, "S")

		xml = "<MediaContainer><Player protocolCapabilities='playback, navigation' product='"+ getMyIp() +"' platformVersion='"+ getVersion() +"' platform='Enigma2' machineIdentifier='"+ getUUID() +"' title='"+ config.plugins.dreamplex.boxName.value +"' protocolVersion='1' deviceClass='stb'/></MediaContainer>"

		printl("", self, "C")
		return xml

	#===========================================================================
	#
	#===========================================================================
	def setXmlHeader(self, xml):
		printl("", self, "S")

		self.send_header('Content-type', 'text/xml; charset="utf-8"')
		self.send_header('Content-Length', str(len(xml)))

		printl("", self, "S")

	#===========================================================================
	#
	#===========================================================================
	def setAccessControlHeaders(self):
		printl("", self, "S")

		self.send_header('Access-Control-Allow-Credentials', 'true')
		self.send_header('Access-Control-Allow-Origin', '*')
		self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		self.send_header("Access-Control-Allow-Headers", "x-plex-client-identifier,x-plex-device,x-plex-device-name,x-plex-platform,x-plex-platform-version,x-plex-product,x-plex-target-client-identifier,x-plex-username,x-plex-version")

		printl("", self, "S")

	#===========================================================================
	#
	#===========================================================================
	def getParams(self):
		printl("", self, "S")

		printl("", self, "C")
		return parse_qs(urlparse(self.path).query)