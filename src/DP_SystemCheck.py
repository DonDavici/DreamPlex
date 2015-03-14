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
import sys
import time
import httplib

from os import system, popen
from Screens.Standby import TryQuitMainloop

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.config import config
from Components.Label import Label

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Console import Console as SConsole

from __common__ import printl2 as printl, testInetConnectivity, getUserAgentHeader, getBoxArch, getOeVersion, revokeCacheFiles

from __init__ import getVersion, _ # _ is translation

#===============================================================================
#
#===============================================================================
class DPS_SystemCheck(Screen):

	archVersion = None
	check = None
	latestVersion = None

	def __init__(self, session):
		printl("", self, "S")

		Screen.__init__(self, session)

		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		"ok": self.startSelection,
		"cancel": self.cancel,
		"red": self.cancel,
		}, -1)

		vlist = []

		self.archVersion = getBoxArch()

		if self.archVersion == "mipsel":
			vlist.append((_("Check for gst-plugin-fragmented"), "gst-plugin-fragmented"))

		elif self.archVersion == "mips32el":
			vlist.append((_("Check for gst-plugins-bad-fragmented"), "gst-plugins-bad-fragmented"))

		else:
			printl("unknown oe version", self, "W")
			vlist.append((_("Check for gst-plugin-fragmented if you are using OE16."), "gst-plugin-fragmented"))
			vlist.append((_("Check for gst-plugins-bad-fragmented if you are using OE20."), "gst-plugins-bad-fragmented"))

		vlist.append((_("Check openSSL installation data."), "python-pyopenssl"))
		vlist.append((_("Check mjpegtools intallation data."), "mjpegtools"))
		vlist.append((_("Check python imaging installation data."), "python-imaging"))
		vlist.append((_("Check python textutils installation data."), "check_textutils"))
		vlist.append((_("Check curl installation data."), "curl"))

		if config.plugins.dreamplex.showUpdateFunction.value:
			vlist.append((_("Check for update."), "check_Update"))

		vlist.append((_("Revoke cache files manually"), "revoke_cache"))

		self["header"] = Label()
		self["content"] = MenuList(vlist)

		self.onLayoutFinish.append(self.finishLayout)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle(_("System - Systemcheck"))

		self["header"].setText(_("Functions List:"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startSelection(self):
		printl("", self, "S")

		selection = self["content"].getCurrent()

		# set package name for object
		content = selection[1]

		if content == "check_Update":
			self.checkForUpdate()
		elif content == "revoke_cache":
			revokeCacheFiles()
			self.session.openWithCallback(self.close, MessageBox,_("Cache files successfully deleted."), MessageBox.TYPE_INFO)
		else:
			self.package = content

			# first we check the state
			self.checkInstallationState()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkForUpdate(self, silent=False):
		printl("", self, "S")
		self.package = "python-pyopenssl"

		if testInetConnectivity() and self.checkInstallationState(True):
			printl( "Starting request", self, "D")

			conn = httplib.HTTPSConnection("api.github.com",timeout=10, port=443)
			conn.request(url="/repos/DonDavici/DreamPlex/tags", method="GET", headers=getUserAgentHeader())
			data = conn.getresponse()
			self.response = data.read()

			printl("response: " + str(self.response), self, "D")
			starter = 19
			closer = self.response.find('",', 0, 50)
			printl("closer: " + str(closer), self, "D")
			latestVersion = self.response[starter:closer] # is a bit dirty but better than forcing users to install simplejson
			printl("latestVersion: " + str(latestVersion), self, "D")

			installedVersion = getVersion()
			printl("InstalledVersion: " + str(installedVersion), self, "D")

			isBeta = self.checkIfBetaVersion(latestVersion)
			printl("isBeta: " + str(isBeta), self, "D")

			if config.plugins.dreamplex.updateType.value == "1" and isBeta == True: # Stable
				latestVersion = self.searchLatestStable()

			if latestVersion > installedVersion:
				self.latestVersion = latestVersion
				self.session.openWithCallback(self.startUpdate, MessageBox,_("Your current Version is " + str(installedVersion) + "\nUpdate to revision " + str(latestVersion) + " found!\n\nDo you want to update now?"), MessageBox.TYPE_YESNO)

			else:
				if not silent:
					self.session.openWithCallback(self.close, MessageBox,_("No update available"), MessageBox.TYPE_INFO)

		else:
			if not silent:
				self.session.openWithCallback(self.close, MessageBox,_("No internet connection available or openssl is not installed!"), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkIfBetaVersion(self, foundVersion):
		printl("", self, "S")

		isBeta = foundVersion.find("beta")
		if isBeta != -1:

			printl("", self, "C")
			return True
		else:

			printl("", self, "C")
			return False

	#===========================================================================
	#
	#===========================================================================s
	def searchLatestStable(self):
		printl("", self, "S")

		isStable = False
		latestStabel = ""
		leftLimiter = 0

		while not isStable:
			starter = self.response.find('},', leftLimiter)
			printl("starter: " + str(starter), self, "D")
			end = starter + 50
			closer = self.response.find('",', starter, end)
			printl("closer: " + str(closer), self, "D")
			# is a bit dirty but better than forcing users to install simplejson
			start = (self.response.find('": "', starter, end)) + 4 # we correct the string here right away => : "1.09-beta.9 becomes 1.09.beta.9
			latestStabel = self.response[start:closer]
			printl("found version: " + str(latestStabel), self, "D")
			isBeta = self.checkIfBetaVersion(latestStabel)
			if not isBeta:
				isStable = True
			else:
				leftLimiter = closer

		printl("latestStable: " + str(latestStabel), self, "D")

		printl("", self, "C")
		return latestStabel

	#===========================================================================
	#
	#===========================================================================
	def startUpdate(self, answer):
		printl("", self, "S")

		if answer is True:
			self.updateToLatestVersion()
		else:
			self.close()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def updateToLatestVersion(self):
		printl("", self, "S")

		if config.plugins.dreamplex.updateType.value == "1":
			updateType = "Stable"
		else:
			updateType = "Beta"

		if getOeVersion() != "oe22":
			remoteUrl = "http://sourceforge.net/projects/dreamplex/files/" + str(updateType) + "/ipk/enigma2-plugin-extensions-dreamplex_" + str(self.latestVersion) + "_all.ipk/download"
			cmd = "curl -o /tmp/temp.ipk -L -k " + str(remoteUrl) + " && opkg install --force-overwrite --force-depends /tmp/temp.ipk; rm /tmp/temp.ipk"
			#bintray runing => cmd = "curl -o /tmp/temp.ipk -L -k https://bintray.com/artifact/download/dondavici/Dreambox/enigma2-plugin-extensions-dreamplex_" + str(self.latestVersion) + "_all.ipk && opkg install --force-overwrite --force-depends /tmp/temp.ipk; rm /tmp/temp.ipk"

		else:
			remoteUrl = "http://sourceforge.net/projects/dreamplex/files/" + str(updateType) + "/deb/enigma2-plugin-extensions-dreamplex_" + str(self.latestVersion) + "_all.deb/download"
			cmd = "curl -o /tmp/temp.deb -L -k " + str(remoteUrl) + " && dpkg -i /tmp/temp.deb; apt-get update && apt-get -f install; rm /tmp/temp.deb"
			#bintray runing => cmd = "curl -o /tmp/temp.deb -L -k https://bintray.com/artifact/download/dondavici/Dreambox/enigma2-plugin-extensions-dreamplex_" + str(self.latestVersion) + "_all.deb && dpkg -i /tmp/temp.deb; rm /tmp/temp.deb"

		printl("cmd: " + str(cmd), self, "D")

		self.session.open(SConsole,"Excecuting command:", [cmd] , self.finishupdate)

		printl("", self, "C")

	#===========================================================================
	# override is used to get bool as answer and not the plugin information
	#===========================================================================
	def checkInstallationState(self, override=False):
		printl("", self, "S")

		if getOeVersion() != "oe22":
			command = "opkg status " + str(self.package)
		else:
			command = "dpkg -s " + str(self.package)

		state = self.executeStateCheck(command, override)

		printl("", self, "C")
		return state

	#===============================================================================
	#
	#===============================================================================
	def executeStateCheck(self, command, override=False):
		printl("", self, "S")

		pipe = popen(command)

		if pipe:
			data = pipe.read(8192)
			pipe.close()
			if data is not None and data != "":
				if override:
					return True
				# plugin is installed
				self.session.open(MessageBox, _("Information:\n") + data, MessageBox.TYPE_INFO)
			else:
				if override:
					return False

				# if plugin is not installed
				self.session.openWithCallback(self.installPackage, MessageBox, _("The selected lib/package/plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installPackage(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.archVersion == "mipsel":
				command = "opkg update; opkg install " + str(self.package)

			elif self.archVersion == "mips32el":
				if getOeVersion() != "oe22":
					command = "opkg update; opkg install " + str(self.package)
				else:
					command = "apt-get update && apt-get install " + str(self.package) + " --force-yes -y"

			else:
				printl("something went wrong finding out the oe-version", self, "W")

			self.executeInstallationCommand(command)
		else:
			# User said 'no'
			self.cancel()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def executeInstallationCommand(self, command):
		printl("", self, "S")

		self.session.open(SConsole,"Excecuting command:", [command] , self.finishupdate)

		printl("", self, "C")

	#===================================================================
	#
	#===================================================================
	def cancel(self):
		printl("", self, "S")

		self.close(False,self.session)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishupdate(self):
		printl("", self, "S")

		time.sleep(2)
		self.session.openWithCallback(self.e2restart, MessageBox,_("Enigma2 must be restarted!\nShould Enigma2 now restart?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def e2restart(self, answer):
		printl("", self, "S")

		if answer is True:
			try:
				self.session.open(TryQuitMainloop, 3)
			except Exception, ex:
				printl("Exception: " + str(ex), self, "W")
				data = "TryQuitMainLoop is not implemented in your OS.\n Please restart your box manually."
				self.session.open(MessageBox, _("Information:\n") + data, MessageBox.TYPE_INFO)
		else:
			self.close()

		printl("", self, "C")