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
#from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
class Singleton(object):
	"""
	singlton config object
	"""
	__we_are_one = {}
	__plexInstance = ""
	__logFileInstance = ""
	__skinParamsInstance = ""

	def __init__(self):
		#implement the borg patter (we are one)
		self.__dict__ = self.__we_are_one

	def getPlexInstance(self, value=None):
		"""with value you can set the singleton content"""
		if value:
			#printl("generating Plex instance ...", self, "D")
			self.__plexInstance = value
		else:
			#printl("reusing Plex instance ...", self, "D")
			pass

		return self.__plexInstance

	def getLogFileInstance(self, value=None):
		"""with value you can set the singleton content"""
		if value:
			#printl("generating Logfile instance ...", self, "D")
			self.__logFileInstance = value
		else:
			#printl("reusing Logfile instance ...", self, "D")
			pass

		return self.__logFileInstance

	def getSkinParamsInstance(self, value=None):
		"""with value you can set the singleton content"""
		if value:
			#printl("generating skinParam instance ...", self, "D")
			self.__skinParamsInstance = value
		else:
			#printl("reusing skinParam instance ...", self, "D")
			pass

		return self.__skinParamsInstance
