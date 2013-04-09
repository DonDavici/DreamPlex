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
#=================================
#IMPORT
#=================================
import sys
import time

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from os import system, popen

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Input import Input
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.Console import Console as SConsole

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, testPlexConnectivity, testInetConnectivity, getXmlContent
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__init__ import initServerEntryConfig, getVersion

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from twisted.python.versions import getVersionString

#===============================================================================
# class
# DPS_SystemCheck
#===============================================================================
class DPS_Mappings(Screen):
	
	def __init__(self, session, serverID):
		'''
		'''
		printl("", self, "S")
		
		Screen.__init__(self, session)
		self.session = session
		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		#"ok": self.startSelection,
		"cancel": self.cancel,
		"red": self.cancel,
		}, -1)
		
		
		self["content"] = DPS_MappingsEntryList([], serverID)
		self.updateList()
		
		self["key_red"] = StaticText(_("Exit"))
		
		printl("", self, "C")
		
	
	#===========================================================================
	# 
	#===========================================================================
	def updateList(self):
		'''
		'''
		printl("", self, "S")
		
		self["content"].buildList()

		printl("", self, "C")
		
	#===================================================================
	# 
	#===================================================================
	def cancel(self):
		'''
		'''
		printl("", self, "S")

		self.close(False,self.session)
		
		printl("", self, "C")
		


#===============================================================================
# class
# DPS_ServerEntryList
#===============================================================================
class DPS_MappingsEntryList(MenuList):
    
    def __init__(self, menuList, serverID, enableWrapAround = True):
        '''
        '''
        printl("", self, "S")
        self.serverID = serverID
        MenuList.__init__(self, menuList, enableWrapAround, eListboxPythonMultiContent)
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 18))
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def postWidgetCreate(self, instance):
        '''
        '''
        printl("", self, "S")
        
        MenuList.postWidgetCreate(self, instance)
        instance.setItemHeight(20)

        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def buildList(self):
        '''
        '''
        printl("", self, "S")
        
        self.list=[]

        
        tree = getXmlContent()
        
        # 'mapping' nodes that are children of nodes with entry='0'
        mappings = tree.findall(".//*[@id='" + str(self.serverID) + "']/mapping")
        
        for mapping in mappings:
            remotePathPart = mapping.findtext("remotePathPart")
            localPathPart = mapping.findtext("localPathPart")
        
            res = [mapping]
            res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(localPathPart)))
            res.append((eListboxPythonMultiContent.TYPE_TEXT, 200, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(remotePathPart)))
    
            self.list.append(res)
        
        self.l.setList(self.list)
        self.moveToIndex(0)
                
        printl("", self, "C")
