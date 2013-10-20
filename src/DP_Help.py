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
from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Input import Input
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.HelpMenu import HelpableScreen

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# class
# DPS_Settings
#===============================================================================        
class DPS_Help(Screen):
    _session = None
    
    def __init__(self, session):
        """
        """
        printl("", self, "S")
        
        Screen.__init__(self, session)
        
        self._session = session
        
        self["help"] = ScrollLabel()
        
            
        self["key_red"] = StaticText(_("Close"))
        
        self["setupActions"] = HelpableActionMap(self, "DP_View", 
        {
            "red": self.keyCancel,
            "cancel": self.keyCancel,
            "bouquet_up":       (self.bouquetUp, ""),
            "bouquet_down":     (self.bouquetDown, ""),
        }, -2)
        
        self.onLayoutFinish.append(self.setContent)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def setContent(self):
        """
        """
        printl("", self, "S")
        
        self.setTitle(_("Help"))
        self["help"].setText(self.getText())

        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def keyCancel(self):
        """
        """
        printl("", self, "S")
        
        self.close()
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def getText(self):
        """
        """
        printl("", self, "S")

        content = "Direct Local"
        content += "\n   Advantages:\tThe medias are played directly from E2."
        content += "\n   Prequesits:\tThis mode works if your plex library is mounted on your Dreambox and accessable."
        content += "\n   Functions:\tSeeking is working"
        content += "\n   HowTo:\tYou can use Windows or Linux based Plexserver."
        content += "\n\tSample content for Library location: movies | tvshows | music"
        content += "\n\tMedia location in Plex for Windows (sample): C:\path\of\library\root\movies\movie.mkv"
        content += "\n\tMedia location Plex for Linux (sample): /path/of/library/root/movies\movie.mkv"
        content += "\n\tMedia location on the Dreambox (sample): /media/net/mountpoint/movies\movie.mkv"
        content += "\n\tAs you can see movies/\movie.mkv is identical."
        content += "\n\tAccording to this just set up the following:"
        content += "\n\tRemote Path Part >>> C:\path\of\library\root\ or /path/of/library/root/"
        content += "\n\tLocal Path Part >>> /media/net/mountpoint/"
        content += "\n\n Transcoded"
        content += "\n   Advantages:\tThe medias go through the plex transcoder. So it is possible to set the quality."
        content += "\n   Prequesits:\tYou have to install gst-fragemented"
        content += "\n   Functions:\tSeeking is working"
        content += "\n\n Streamed"
        content += "\n   Advantages:\tIf you cant setup direct local and you dont have gst-fragmented"
        content += "\n   Prequesits:\tNothing"
        content += "\n   Functions:\tSeeking is not working"
        content += "\n\n myPlex"
        content += "\n   Advantages:\tYou can access shared libraries of friends."
        content += "\n   Prequesits:\tYou need a myPlex account."
        content += "\n   Note:\tThis is only neccessary to connect to shared libs. No need to use this in you local network"  
        printl("", self, "C")
        return content
    
    #===========================================================================
    # 
    #===========================================================================
    def bouquetUp(self):
        """
        """
        printl("", self, "S")
        
        self["help"].pageUp()
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def bouquetDown(self):
        """
        """
        printl("", self, "S")
        
        self["help"].pageDown()
        
        printl("", self, "C")