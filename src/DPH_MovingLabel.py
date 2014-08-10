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

#noinspection PyUnresolvedReferences
from enigma import eTimer
from Components.Label import MultiColorLabel
from skin import parseColor
from __common__ import printl2 as printl
from DPH_Singleton import Singleton


class DPH_HorizontalMenu(object):

	#===============================================================================
	#
	#===============================================================================
	def setHorMenuElements(self, depth):
		printl("", self, "S")
		self.depth = depth

		self.setRangeList()

		highlighted = parseColor("#e69405")
		normal = parseColor("#ffffff")

		for i in self.rangeList:
			self[str(i)] = MultiColorLabel()
			self[str(i)].foreColors = [highlighted, normal]
			self[str(i)].show()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setRangeList(self):
		printl("", self, "S")

		rangeList = []
		for i in range(1,(self.depth+1)):
			rangeList.append("-" + str(i))
			rangeList.append("+" + str(i))

		rangeList.append("0")

		self.rangeList = rangeList

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def translateNames(self):
		printl("", self, "S")

		for i in self.rangeList:
			self.translatePositionToName(int(i), str(i))

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def refreshOrientationHorMenu(self, value=None):
		printl("", self, "S")
		printl("value: " + str(value), self, "D")

		if value == 1:
			self["menu"].selectNext()
		elif value == -1:
			self["menu"].selectPrevious()

		currentIndex = self["menu"].index
		content = self["menu"].list
		count = len(content)

		self[self.translatePositionToName(0)].setText(content[currentIndex][0])
		self[self.translatePositionToName(0)].setForegroundColorNum(0)
		for i in range(1,(self.depth+1)):
			targetIndex = currentIndex + i
			if targetIndex < count:
				self[self.translatePositionToName(+i)].setText(content[targetIndex][0])
			else:
				firstResult = targetIndex - count
				printl("firstResult: " + str(firstResult), self, "D")
				if firstResult >= count:
					firstResult = currentIndex

				self[self.translatePositionToName(+i)].setText(content[firstResult][0])

			targetIndex = currentIndex - i
			if targetIndex >= 0:
				self[self.translatePositionToName(-i)].setText(content[targetIndex][0])
			else:
				secondResult = count + targetIndex
				printl("secondResult: " + str(secondResult), self, "D")
				self[self.translatePositionToName(-i)].setText(content[secondResult][0])

		self.hideUnusedElementsFromMenu(count)

		printl("", self, "C")
		return True

	_translatePositionToName = {}
	#===============================================================================
	#
	#===============================================================================
	def translatePositionToName(self, name, value=None):
		#printl("", self, "S")

		if value is None:
			printl("", self, "C")
			return self._translatePositionToName[name]
		else:
			self._translatePositionToName[name] = value

		#printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def initMenu(self):
		printl("", self, "S")

		tree = Singleton().getSkinParamsInstance()

		for orientation in tree.findall('orientation'):
			name = str(orientation.get('name'))
			if name == self.menuType:
				myType = str(orientation.get('type'))
				if myType == "horizontal":
					self.g_horizontal_menu = True

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def hideUnusedElementsFromMenu(self, count):
		printl("", self, "S")

		if count == 1:
			self["-2"].hide()
			self["-1"].hide()
			self["+1"].hide()
			self["+2"].hide()

		elif count == 2:
			self["-2"].hide()
			self["-1"].hide()
			self["+2"].hide()

		elif count == 3:
			self["-2"].hide()
			self["+2"].hide()

		elif count == 4:
			pass
			#self["-2"].hide()

		elif count >= 5:
			self["-2"].show()
			self["-1"].show()
			self["+1"].show()
			self["+2"].show()

		else:
			# this should not happen
			raise Exception

		printl("", self, "C")