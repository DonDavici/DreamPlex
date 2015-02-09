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

from __common__ import printl2 as printl, testInetConnectivity, getUserAgentHeader, getBoxArch, getOeVersion

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
			vlist.append((_("Check for gst-plugin-fragmented"), "oe16"))

		elif self.archVersion == "mips32el":
			vlist.append((_("Check for gst-plugins-bad-fragmented"), "oe20"))

		else:
			printl("unknown oe version", self, "W")
			vlist.append((_("Check for gst-plugin-fragmented if you are using OE16."), "oe16"))
			vlist.append((_("Check for gst-plugins-bad-fragmented if you are using OE20."), "oe20"))

		vlist.append((_("Check openSSL installation data."), "check_Curl"))
		vlist.append((_("Check mjpegtools intallation data."), "check_jpegTools"))
		vlist.append((_("Check python imaging installation data."), "check_Pil"))
		vlist.append((_("Check python textutils installation data."), "check_textutils"))

		if config.plugins.dreamplex.showUpdateFunction.value:
			vlist.append((_("Check for update."), "check_Update"))

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

		if selection[1] == "oe16" or selection[1] == "oe20":
			self.checkLib(selection[1])

		if selection[1] == "check_Curl":
			self.checkOpensslInstallation()

		if selection[1] == "check_jpegTools":
			self.checkJpegToolsInstallation()

		if selection[1] == "check_Pil":
			self.checkPythonImagingInstallation()

		if selection[1] == "check_Update":
			self.checkForUpdate()

		if selection[1] == "check_textutils":
			self.checkPythonTextutils()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkForUpdate(self, silent=False):
		printl("", self, "S")

		if testInetConnectivity() and self.checkOpensslInstallation(True):
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
			cmd = "curl -o /tmp/temp.deb -L -k " + str(remoteUrl) + " && dpkg -i /tmp/temp.deb; rm /tmp/temp.deb"
			#bintray runing => cmd = "curl -o /tmp/temp.deb -L -k https://bintray.com/artifact/download/dondavici/Dreambox/enigma2-plugin-extensions-dreamplex_" + str(self.latestVersion) + "_all.deb && dpkg -i /tmp/temp.deb; rm /tmp/temp.deb"

		printl("cmd: " + str(cmd), self, "D")

		self.session.open(SConsole,"Excecuting command:", [cmd] , self.finishupdate)

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

	#===========================================================================
	# override is used to get bool as answer and not the plugin information
	#===========================================================================
	def checkOpensslInstallation(self, override=False):
		printl("", self, "S")

		if getOeVersion() != "oe22":
			command = "opkg status python-pyopenssl"
		else:
			command = "dpkg -s python-pyopenssl"

		self.check = "openssl"
		state = self.executeCommand(command, override)

		printl("", self, "C")
		return state

	#===========================================================================
	#
	#===========================================================================
	def checkJpegToolsInstallation(self):
		printl("", self, "S")

		if getOeVersion() != "oe22":
			command = "opkg status mjpegtools"
		else:
			command = "dpkg -s mjpegtools"

		self.check = "jpegTools"
		state = self.executeCommand(command)

		printl("", self, "C")
		return state

	#===========================================================================
	#
	#===========================================================================
	def checkPythonImagingInstallation(self):
		printl("", self, "S")

		if getOeVersion() != "oe22":
			command = "opkg status python-imaging"
		else:
			command = "dpkg -s python-imaging"

		self.check = "pythonImaging"
		state = self.executeCommand(command)

		printl("", self, "C")
		return state

	#===========================================================================
	#
	#===========================================================================
	def checkPythonTextutils(self):
		printl("", self, "S")

		if getOeVersion() != "oe22":
			command = "opkg status python-textutils"
		else:
			command = "dpkg -s python-textutils"

		self.check = "pythonTextutils"
		state = self.executeCommand(command)

		printl("", self, "C")
		return state

	#===============================================================================
	#
	#===============================================================================
	def checkLib(self, arch):
		printl("", self, "S")

		command = None

		if arch == "oe16":
			command = "opkg status gst-plugin-fragmented"
			self.archVersion = "mipsel"

		elif arch == "oe20":
			if getOeVersion() != "oe22":
				command = "opkg status gst-plugins-bad-fragmented"
			else:
				command = "dpkg -s gst-plugins-bad-fragmented"
			self.archVersion = "mips32el"

		else:
			printl("someting went wrong with arch type", self, "W")

		self.check = "gst"
		self.executeCommand(command)

		printl("", self, "C")


	#===============================================================================
	#
	#===============================================================================
	def executeCommand(self, command, override=False):
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
				# plugin is not install
				if self.check == "gst":
					self.session.openWithCallback(self.installStreamingLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "openssl":
					self.session.openWithCallback(self.installOpensslLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "jpegTools":
					self.session.openWithCallback(self.installJpegToolsLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "pythonImaging":
					self.session.openWithCallback(self.installPyhtonImagingLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "pythonTextutils":
					self.session.openWithCallback(self.installPyhtonTextutilsLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				else:
					printl("no proper value i self.check", self, "W")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installOpensslLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.archVersion == "mipsel":
				command = "opkg update; opkg install python-pyopenssl"

			elif self.archVersion == "mips32el":

				if getOeVersion() != "oe22":
					command = "opkg update; opkg install python-pyopenssl"
				else:
					command = "apt-get update && apt-get install python-pyopenssl --force-yes -y"

			else:
				printl("something went wrong finding out the oe-version", self, "W")

			if not system(command):
				# Successfully installed
				#defaultServer = plexServerConfig.getDefaultServer()
				#self.openSectionlist(defaultServer)
				pass
			else:
				# Fail, try again and report the output...
				pipe = popen(command)
				if pipe is not None:
					data = pipe.read(8192)
					if data is None:
						data = "Unknown Error"
					pipe.close()
					self.session.open(MessageBox, _("Could not install "+ command + ":\n") + data, MessageBox.TYPE_ERROR)
				# Failed to install
				self.cancel()
		else:
			# User said 'no'
			self.cancel()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installJpegToolsLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.archVersion == "mipsel":
				command = "opkg update; opkg install mjpegtools"

			elif self.archVersion == "mips32el":
				if getOeVersion() != "oe22":
					command = "opkg update; opkg install mjpegtools"
				else:
					command = "apt-get update && apt-get install mjpegtools --force-yes -y"

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
	def installPyhtonImagingLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.archVersion == "mipsel":
				command = "opkg update; opkg install python-imaging"

			elif self.archVersion == "mips32el":
				if getOeVersion() != "oe22":
					command = "opkg update; opkg install python-imaging"
				else:
					command = "apt-get update && apt-get install python-imaging --force-yes -y"

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
	def installPyhtonTextutilsLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.archVersion == "mipsel":
				command = "opkg update; opkg install python-textutils"

			elif self.archVersion == "mips32el":
				if getOeVersion() != "oe22":
					command = "opkg update; opkg install python-textutils"
				else:
					command = "apt-get update && apt-get install python-textutils --force-yes -y"

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
	def installStreamingLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.archVersion == "mipsel":
				command = "opkg update; opkg install gst-plugin-fragmented"

			elif self.archVersion == "mips32el":
				if getOeVersion() != "oe22":
					command = "opkg update; opkg install gst-plugins-bad-fragmented"
				else:
					command = "apt-get update && apt-get install gst-plugins-bad-fragmented --force-yes -y"

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