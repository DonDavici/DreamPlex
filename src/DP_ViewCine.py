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
from DP_View import DP_View

from __common__ import printl2 as printl

#===============================================================================
# 
#===============================================================================
def getViewClass():
	"""
	@param: none
	@return: DP_View Class 
	"""
	printl("", __name__, "S")
	
	printl("", __name__, "C")
	return DP_ViewCine

#===========================================================================
#
#===========================================================================
class DP_ViewCine(DP_View):

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, cache=None):
		printl("", self , "S")

		DP_View.__init__(self, session, libraryName, loadLibrary, playEntry, viewName, select, cache)

		printl("", self, "C")