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
from Components.Label import Label
from __common__ import printl2 as printl
from DPH_Singleton import Singleton

class DPH_HorizontalMenu(object):

	def __init__(self):
		pass

	#===============================================================================
	#
	#===============================================================================
	def setHorMenuElements(self):
		printl("", self, "S")

		self["-2"] = DPH_MovingLabel()
		self["-1"] = DPH_MovingLabel(self["-2"].getTimer())
		self["0"]  = DPH_MovingLabel(self["-2"].getTimer())
		self["+1"] = DPH_MovingLabel(self["-2"].getTimer())
		self["+2"] = DPH_MovingLabel(self["-2"].getTimer())

		self["-3"] = Label()
		self["+3"] = Label()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def translateNames(self):
		printl("", self, "S")

		self.translatePositionToName(-2, "-2")
		self.translatePositionToName(-1, "-1")
		self.translatePositionToName( 0, "0")
		self.translatePositionToName(+1, "+1")
		self.translatePositionToName(+2, "+2")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def refreshOrientationHorMenu(self, value):
		printl("", self, "S")

		if self["-2"].moving is True or self["+2"].moving is True:

				printl("", self, "C")
				return False

		self.refreshMenu(value)
		currentIndex = self["menu"].index
		content = self["menu"].list
		count = len(content)

		howManySteps = 1
		doStepEveryXMs = 100

		if value == 0:
			self[self.translatePositionToName(0)].setText(content[currentIndex][0])
			for i in range(1,3): # 1, 2
				targetIndex = currentIndex + i
				if targetIndex < count:
					self[self.translatePositionToName(+i)].setText(content[targetIndex][0])
				else:
					self[self.translatePositionToName(+i)].setText(content[targetIndex - count][0])

				targetIndex = currentIndex - i
				if targetIndex >= 0:
					self[self.translatePositionToName(-i)].setText(content[targetIndex][0])
				else:
					self[self.translatePositionToName(-i)].setText(content[count + targetIndex][0])


		elif value == 1:
			self[self.translatePositionToName(-1)].moveTo(self[self.translatePositionToName(-2)].getPosition(), howManySteps)
			self[self.translatePositionToName( 0)].moveTo(self[self.translatePositionToName(-1)].getPosition(), howManySteps)
			self[self.translatePositionToName(+1)].moveTo(self[self.translatePositionToName( 0)].getPosition(), howManySteps)
			self[self.translatePositionToName(+2)].moveTo(self[self.translatePositionToName(+1)].getPosition(), howManySteps)

			# He has to jump | This works but leaves us with an ugly jump
			pos = self["+3"].getPosition()
			self[self.translatePositionToName(-2)].move(pos[0], pos[1])
			#self[self.translatePositionToName(-2)].moveTo(pos, 1)
			self[self.translatePositionToName(-2)].moveTo(self[self.translatePositionToName(+2)].getPosition(), howManySteps)

			# We have to change the conten of the most right
			i = 2
			targetIndex = currentIndex + i
			if targetIndex < count:
				self[self.translatePositionToName(-2)].setText(content[targetIndex][0])
			else:
				self[self.translatePositionToName(-2)].setText(content[targetIndex - count][0])

			rM2 = self.translatePositionToName(-2)
			self.translatePositionToName(-2, self.translatePositionToName(-1))
			self.translatePositionToName(-1, self.translatePositionToName( 0))
			self.translatePositionToName( 0, self.translatePositionToName(+1))
			self.translatePositionToName(+1, self.translatePositionToName(+2))
			self.translatePositionToName(+2, rM2)

			self["-1"].startMoving(doStepEveryXMs)
			self["0"].startMoving(doStepEveryXMs)
			self["+1"].startMoving(doStepEveryXMs)
			self["+2"].startMoving(doStepEveryXMs)

			# GroupTimer
			self["-2"].startMoving(doStepEveryXMs)

		elif value == -1:
			self[self.translatePositionToName(+1)].moveTo(self[self.translatePositionToName(+2)].getPosition(), howManySteps)
			self[self.translatePositionToName( 0)].moveTo(self[self.translatePositionToName(+1)].getPosition(), howManySteps)
			self[self.translatePositionToName(-1)].moveTo(self[self.translatePositionToName( 0)].getPosition(), howManySteps)
			self[self.translatePositionToName(-2)].moveTo(self[self.translatePositionToName(-1)].getPosition(), howManySteps)

			# He has to jump | This works but leaves us with an ugly jump
			pos = self["-3"].getPosition()
			self[self.translatePositionToName(+2)].move(pos[0], pos[1])
			#self[self.translatePositionToName(+2)].moveTo(pos, 1)
			self[self.translatePositionToName(+2)].moveTo(self[self.translatePositionToName(-2)].getPosition(), howManySteps)

			# We have to change the conten of the most left
			i = -2
			targetIndex = currentIndex + i
			if targetIndex >= 0:
				self[self.translatePositionToName(+2)].setText(content[targetIndex][0])
			else:
				self[self.translatePositionToName(+2)].setText(content[count + targetIndex][0])

			rP2 = self.translatePositionToName(+2)
			self.translatePositionToName(+2, self.translatePositionToName(+1))
			self.translatePositionToName(+1, self.translatePositionToName( 0))
			self.translatePositionToName( 0, self.translatePositionToName(-1))
			self.translatePositionToName(-1, self.translatePositionToName(-2))
			self.translatePositionToName(-2, rP2)

			self["-1"].startMoving(doStepEveryXMs)
			self["0"].startMoving(doStepEveryXMs)
			self["+1"].startMoving(doStepEveryXMs)
			self["+2"].startMoving(doStepEveryXMs)

			# GroupTimer
			self["-2"].startMoving(doStepEveryXMs)

		printl("", self, "C")
		return True

	_translatePositionToName = {}
	#===============================================================================
	#
	#===============================================================================
	def translatePositionToName(self, name, value=None):
		printl("", self, "S")

		if value is None:
			printl("", self, "C")
			return self._translatePositionToName[name]
		else:
			self._translatePositionToName[name] = value

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def setMenuType(self, menuType):
		printl("", self, "S")

		tree = Singleton().getSkinParamsInstance()

		for orientation in tree.findall('orientation'):
			name = str(orientation.get('name'))
			if name == menuType:
				myType = str(orientation.get('type'))
				if myType == "horizontal":
					self.g_horizontal_menu = True

		printl("", self, "C")

#===============================================================================
#
#===============================================================================
class DPH_MovingLabel(Label):

	def __init__ (self, groupTimer=None):
		printl("", self, "S")

		Label.__init__(self)

		self.moving = False

		# TODO: get real values
		self.x = 0.0
		self.y = 0.0

		self.xDest = 0.0
		self.yDest = 0.0

		self.clearPath()

		self.isGroupTimer = groupTimer is not None
		if self.isGroupTimer:
			self.moveTimer = groupTimer
		else:
			self.moveTimer = eTimer()
		self.moveTimer.callback.append(self.doMove)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def getTimer (self):
		printl("", self, "S")

		printl("", self, "C")
		return self.moveTimer

	#===============================================================================
	#
	#===============================================================================
	def clearPath (self, repeated=False):
		printl("", self, "S")

		if self.moving:
			self.moving = False
			if not self.isGroupTimer:
				self.moveTimer.stop()

		self.path = []
		self.currDest = 0
		self.repeated = repeated

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def addMovePoint (self, pos, time=20):
		printl("", self, "S")

		self._addMovePoint(pos[0], pos[1], time)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def _addMovePoint (self, x, y, time=20):
		printl("", self, "S")

		self.path.append((x, y, time))

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def moveTo (self, pos, time=20):
		printl("", self, "S")

		self._moveTo(pos[0], pos[1], time)

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def _moveTo (self, x, y, time=20):
		printl("", self, "S")

		self.clearPath()

		pos = self.getPosition()
		self.x = pos[0]
		self.y = pos[1]

		self._addMovePoint(x, y, time)

		printl("", self, "C")

	#===============================================================================
	# time meens in how many steps we move
	# periode means every X ms to a step
	#===============================================================================
	def startMoving (self, period=100):
		printl("", self, "S")

		if not self.moving:
			self.time = self.path[self.currDest][2]
			self.stepX = (self.path[self.currDest][0] - self.x) / float(self.time)
			self.stepY = (self.path[self.currDest][1] - self.y) / float(self.time)

			self.moving = True
			if not self.isGroupTimer:
				self.moveTimer.start(period)

		printl("", self, "C")

	#===============================================================================
	# time meens in how many steps we move
	# periode means every X ms to a step
	#===============================================================================
	def stopMoving (self):
		printl("", self, "S")

		self.moving = False
		if not self.isGroupTimer:
			self.moveTimer.stop()

		printl("", self, "C")

	#===============================================================================
	# time meens in how many steps we move
	# periode means every X ms to a step
	#===============================================================================
	def doMove (self):
		printl("", self, "S")

		self.x += self.stepX
		self.y += self.stepY
		self.time -= 1
		try:
			self.move(int(self.x), int(self.y))
		except: # moving not possible... widget not there any more... stop moving
			if not self.isGroupTimer:
				self.stopMoving()

		if self.time == 0:
			self.currDest += 1
			if not self.isGroupTimer:
				self.moveTimer.stop()
			self.moving = False
			if self.currDest >= len(self.path): # end of path
				if self.repeated:
					self.currDest = 0
					self.moving = False
					self.startMoving()
			else:
				self.moving = False
				self.startMoving()

		printl("", self, "C")
