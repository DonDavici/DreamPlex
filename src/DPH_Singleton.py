# -*- coding: utf-8 -*-
'''
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
'''
#===============================================================================
# IMPORT
#===============================================================================

#===============================================================================
# 
#===============================================================================
class Singleton:
	"""
	singlton config object
	"""
	__we_are_one = {}
	__plexInstance = ""
	__logFileInstance = ""

	def __init__(self):
		#implement the borg patter (we are one)
		self.__dict__ = self.__we_are_one

	def getPlexInstance(self, value=None):
		'''with value you can set the singleton content'''
		if value:
			self.__plexInstance = value
		return self.__plexInstance
	
	def getLogFileInstance(self, value=None):
		'''with value you can set the singleton content'''
		if value:
			self.__logFileInstance = value
		return self.__logFileInstance