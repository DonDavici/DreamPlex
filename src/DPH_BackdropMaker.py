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
#===============================================================================
# IMPORT
#===============================================================================
import time
import os

from threading import Thread

from __common__ import printl2 as printl
from __init__ import _ # _ is translation

#===============================================================================
# IMPORT
#===============================================================================
class backdropMaker(Thread):

	#===========================================================================
	#
	#===========================================================================
	def __init__ (self, output, progress, myRange, info, finished):
		Thread.__init__(self)
		self.output = output
		self.progress = progress
		self.range = myRange
		self.info = info
		self.finished = finished
		self.output(_("Thread running"))
		self.doAbort = False

	#===========================================================================
	#
	#===========================================================================
	def abort(self):
		self.doAbort = True
		self.output("Aborting sync! Saving and cleaning up!")

	#===========================================================================
	#
	#===========================================================================
	def run(self):

		self.output(_("Loading Filesystem"))
		printl("Loading Filesystem", self, "D")

		self.output(_("Searching for backdrop files"))
		start_time = time.time()

		elementListFileCounter = 0
		path = None

		if not os.path.isdir(path) is False:
			return

		elapsed_time = time.time() - start_time
		printl("Searching for backdrop files took: " + str(elapsed_time), self, "D")

		if elementListFileCounter == 0:
			self.output(_("Found") + ' ' + str(0) + ' ' + _("media files"))
			printl("Found 0 backdrop files", self, "D")
		else:
			self.output(_("Found") + ' ' + str(elementListFileCounter) + ' ' + _("backdrop files"))
			printl("Found " + str(elementListFileCounter) + " backdrop files", self, "D")

			self.range(elementListFileCounter)

		self.output(_("Done"))
		printl("Done", self, "D")
		self.output("---------------------------------------------------")
		self.output(_("Press Exit / Back"))

		self.finished(True)