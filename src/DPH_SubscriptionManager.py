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
import re
import threading
import httplib
import traceback
import string

from __common__ import printl2 as printl, getUUID, timeToMillis, getPlexHeaders, getXMLHeader

#===========================================================================
#
#===========================================================================
class SubscriptionManager:
	def __init__(self):
		self.subscribers = {}
		self.info = {}
		self.lastkey = ""
		self.volume = 0
		self.guid = ""
		self.server = ""
		self.protocol = "http"
		self.port = ""
		self.playerprops = {}
		self.sentstopped = True
		self.progressFromEnigma2 = 0
		self.playerStateFromEnigma2 = "stopped"
		self.durationFromEnigma2 = 0
		self.players = None
		self.session = None

	#===========================================================================
	#
	#===========================================================================
	def getVolume(self):

		self.volume = self.session.current_dialog.getVolume()

	#===========================================================================
	#
	#===========================================================================
	def msg(self, players):
		msg = getXMLHeader()
		self.updatePlayerState()
		msg += '<MediaContainer commandID="INSERTCOMMANDID"'

		if players:
			self.getVolume()
			maintype = "music"
			for p in players.values():
				maintype = p.get('type')
			self.mainlocation = "fullScreen" + maintype[0:1].upper() + maintype[1:].lower()
		else:
			self.mainlocation = "navigation"
		msg += ' location="%s">' % self.mainlocation

		msg += "<Timeline seekRange='0-0' state='stopped' time='0' type='music'></Timeline>"
		msg += "<Timeline seekRange='0-0' state='stopped' time='0' type='photo'></Timeline>"
		msg += self.getTimelineXML(self.getVideoPlayerId(players), "video")
		msg += "\r\n</MediaContainer>"
		return msg

	#===========================================================================
	#
	#===========================================================================
	def updatePlayerState(self):
		try:
			e2params = self.session.current_dialog.getPlayerState()
			if e2params:
				self.progressFromEnigma2 = e2params['progress']
				self.playerStateFromEnigma2 = e2params["state"]
				self.durationFromEnigma2 = e2params["duration"]
				self.lastkey = e2params["lastKey"]
		except:
			pass

	#===========================================================================
	#
	#===========================================================================
	def getTimelineXML(self, playerid, ptype):
		if playerid > 0:
			state = self.playerStateFromEnigma2
			time = self.progressFromEnigma2
		else:
			state = "stopped"
			time = 0

		ret = "\r\n"+'<Timeline location="%s" state="%s" time="%s" type="%s"' % (self.mainlocation, state, time, ptype)

		if playerid > 0:
			ret += ' duration="%s"' % self.durationFromEnigma2
			ret += ' seekRange="0-%s"' % self.progressFromEnigma2
			ret += ' controllable="%s"' % self.controllable()
			ret += ' machineIdentifier="%s"' % getUUID() #serv.get('uuid', "")
			ret += ' protocol="%s"' % self.protocol
			ret += ' address="%s"' % self.server
			ret += ' port="%s"' % self.port
			ret += ' guid="%s"' % 11111 #info['guid']
			ret += ' containerKey="%s"' % (self.lastkey or "/library/metadata/900000")
			ret += ' key="%s"' % (self.lastkey or "/library/metadata/900000")
			m = re.search(r'(\d+)$', self.lastkey)
			if m:
				ret += ' ratingKey="%s"' % m.group()
			ret += ' volume="%s"' % 100
			ret += ' shuffle="%s"' % 0

		ret += '/>'
		return ret

	#===========================================================================
	#
	#===========================================================================
	def updateCommandID(self, uuid, commandID):
		if commandID and self.subscribers.get(uuid, False):
			self.subscribers[uuid].commandID = int(commandID)

	#===========================================================================
	#
	#===========================================================================
	def notify(self, players, event = False):
		self.cleanup()

		# fetch the message, subscribers or not, since the server
		# will need the info anyway
		msg = self.msg(players)

		if self.subscribers:
			with threading.RLock():
				for sub in self.subscribers.values():
					pass
					sub.send_update(msg, len(players)==0)

		return True

	#===========================================================================
	#
	#===========================================================================
	def controllable(self):
		return "playPause,play,stop,skipPrevious,skipNext,volume,stepBack,stepForward,seekTo"

	#===========================================================================
	#
	#===========================================================================
	def addSubscriber(self, protocol, host, port, uuid, commandID):
		sub = Subscriber(protocol, host, port, uuid, commandID)
		with threading.RLock():
			self.subscribers[sub.uuid] = sub
		return sub

	#===========================================================================
	#
	#===========================================================================
	def getSubscribersList(self):
		return self.subscribers

	#===========================================================================
	#
	#===========================================================================
	def removeSubscriber(self, uuid):
		with threading.RLock():
			for sub in self.subscribers.values():
				if sub.uuid == uuid or sub.host == uuid:
					sub.cleanup()
					del self.subscribers[sub.uuid]

	#===========================================================================
	#
	#===========================================================================
	def cleanup(self):
		with threading.RLock():
			for sub in self.subscribers.values():
				if sub.age > 30:
					sub.cleanup()
					del self.subscribers[sub.uuid]

	#===========================================================================
	#
	#===========================================================================
	def getPlayerProperties(self, playerid):
		info = {}
		try:
			# get info from the player
			props = {}#jsonrpc("Player.GetProperties", {"playerid": playerid, "properties": ["time", "totaltime", "speed", "shuffled"]})
			info['time'] = timeToMillis(props['time'])
			info['duration'] = timeToMillis(props['totaltime'])
			info['state'] = ("paused", "playing")[int(props['speed'])]
			info['shuffle'] = ("0","1")[props.get('shuffled', False)]
		except:
			info['time'] = 0
			info['duration'] = 0
			info['state'] = "stopped"
			info['shuffle'] = False
		# get the volume from the application
		info['volume'] = self.volume
		info['guid'] = self.guid

		return info

	#===========================================================================
	#
	#===========================================================================
	def getVideoPlayerId(self, players):
		return players.get("video", {}).get('playerid', 0)

	#===========================================================================
	#
	#===========================================================================
	def getAudioPlayerId(self, players):
		return players.get("music", {}).get('playerid', 0)

	#===========================================================================
	#
	#===========================================================================
	def getPhotoPlayerId(self, players):
		return players.get("photo", {}).get('playerid', 0)

#===========================================================================
#
#===========================================================================
class Subscriber:
	#===========================================================================
	#
	#===========================================================================
	def __init__(self, protocol, host, port, uuid, commandID):
		self.protocol = protocol or "http"
		self.host = host
		self.port = port or 32400
		self.uuid = uuid or host
		self.commandID = int(commandID) or 0
		self.navlocationsent = False
		self.age = 0

	#===========================================================================
	#
	#===========================================================================
	def __eq__(self, other):
		return self.uuid == other.uuid

	#===========================================================================
	#
	#===========================================================================
	def tostr(self):
		return "uuid=%s,commandID=%i" % (self.uuid, self.commandID)

	#===========================================================================
	#
	#===========================================================================
	def cleanup(self):
		requests.closeConnection(self.protocol, self.host, self.port)

	#===========================================================================
	#
	#===========================================================================
	def send_update(self, msg, is_nav):
		self.age += 1
		if not is_nav:
			self.navlocationsent = False
		elif self.navlocationsent:
			return True
		else:
			self.navlocationsent = True
		msg = re.sub(r"INSERTCOMMANDID", str(self.commandID), msg)
		printl("sending xml to subscriber %s: %s" % (self.tostr(), msg), self, "D")
		requests.post(self.host, self.port, "/:/timeline", msg, getPlexHeaders(), self.protocol)
		# if not requests.post(self.host, self.port, "/:/timeline", msg, getPlexHeaders(), self.protocol):
		# 	printl("removing subcriber ...", self, "D")
		# 	subMgr.removeSubscriber(self.uuid)

#===========================================================================
#
#===========================================================================
class RequestMgr:
	def __init__(self):
		self.conns = {}

	#===========================================================================
	#
	#===========================================================================
	def getConnection(self, protocol, host, port):
		conn = self.conns.get(protocol+host+str(port), False)
		if not conn:
			if protocol=="https":
				conn = httplib.HTTPSConnection(host, port)
			else:
				conn = httplib.HTTPConnection(host, port)
		return conn

	#===========================================================================
	#
	#===========================================================================
	def closeConnection(self, protocol, host, port):
		conn = self.conns.get(protocol+host+str(port), False)
		if conn:
			conn.close()
			self.conns.pop(protocol+host+str(port), None)

	#===========================================================================
	#
	#===========================================================================
	def dumpConnections(self):
		for conn in self.conns.values():
			conn.close()
		self.conns = {}

	#===========================================================================
	#
	#===========================================================================
	def post(self, host, port, path, body, header={}, protocol="http"):
		conn = None
		try:
			conn = self.getConnection(protocol, host, port)
			header['Connection'] = "keep-alive"
			conn.request("POST", path, body, header)
			data = conn.getresponse()

			if int(data.status) >= 400:
				print "HTTP response error: " + str(data.status)
				# this should return false, but I'm hacking it since iOS returns 404 no matter what
				return data or True
			elif int(data.status) == 200:
				print "got 200 OK"
				print "data: " + str(data.read())
			else:
				return data.read() or True
		except:
			print "Unable to connect to %s\nReason:" % host
			traceback.print_exc()
			self.conns.pop(protocol+host+str(port), None)
			if conn:
				conn.close()
			return False

	#===========================================================================
	#
	#===========================================================================
	def getwithparams(self, host, port, path, params, header={}, protocol="http"):
		newpath = path + '?'
		pairs = []
		for key in params:
			pairs.append(str(key)+'='+str(params[key]))
		newpath += string.join(pairs, '&')
		return self.get(host, port, newpath, header, protocol)

	#===========================================================================
	#
	#===========================================================================
	def get(self, host, port, path, header={}, protocol="http"):
		try:
			conn = self.getConnection(protocol, host, port)
			header['Connection'] = "keep-alive"
			conn.request("GET", path, headers=header)
			data = conn.getresponse()
			if int(data.status) >= 400:
				print "HTTP response error: " + str(data.status)
				return False
			else:
				return data.read() or True
		except:
			print "Unable to connect to %s\nReason: %s" % (host, traceback.print_exc())
			self.conns.pop(protocol+host+str(port), None)
			conn.close()
			return False

requests = RequestMgr()
