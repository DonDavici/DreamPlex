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

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, testPlexConnectivity
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__init__ import initServerEntryConfig

from Plugins.Extensions.DreamPlex.DP_PlexLibrary import PlexLibrary
from Plugins.Extensions.DreamPlex.DP_SystemCheck import DPS_SystemCheck

from Plugins.Extensions.DreamPlex.DPH_WOL import wake_on_lan
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

#===============================================================================
# class
# DPS_Settings
#===============================================================================        
class DPS_Settings(Screen, ConfigListScreen):
    _hasChanged = False
    _session = None
    
    def __init__(self, session):
        '''
        '''
        printl("", self, "S")
        
        Screen.__init__(self, session)
        
        ConfigListScreen.__init__(
            self,
            [
                getConfigListEntry(_("Debug Mode"), config.plugins.dreamplex.debugMode, _("fill me")),
                getConfigListEntry(_("Show Plugin in Main Menu"), config.plugins.dreamplex.showInMainMenu, _("fill me")),
                getConfigListEntry(_("Show Filter for Section"), config.plugins.dreamplex.showFilter, _("fill me")),
                getConfigListEntry(_("Log Folder Path"), config.plugins.dreamplex.logfolderpath, _("fill me")),
                getConfigListEntry(_("Media Folder Path"), config.plugins.dreamplex.mediafolderpath, _("fill me")),
                getConfigListEntry(_("Player Temp Path"), config.plugins.dreamplex.playerTempPath, _("fill me")),
                getConfigListEntry(_("Play Themes in TV Shows"), config.plugins.dreamplex.playTheme, _("fill me")),
                getConfigListEntry(_("Use fastScroll as default"), config.plugins.dreamplex.fastScroll, _("fill me")),
                getConfigListEntry(_("Summerize Sections"), config.plugins.dreamplex.summerizeSections, _("fill me")),
                
            ],
            session = self.session,
            on_change = self._changed
        )
        
        #getConfigListEntry(_("Use Autolanguage in Movieplayer"), config.plugins.dreamplex.autoLanguage, _("fill me")),
        
        self._session = session
        self._hasChanged = False

            
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Save"))
        
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.keySave,
            "red": self.keyCancel,
            "cancel": self.keyCancel,
            "ok": self.ok,
        }, -2)
        self.onLayoutFinish.append(self.setCustomTitle)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def setCustomTitle(self):
        '''
        '''
        printl("", self, "S")
        
        self.setTitle(_("Settings"))

        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def _changed(self):
        '''
        '''
        printl("", self, "S")
        
        self._hasChanged = True

        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def ok(self):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def keySave(self):
        '''
        '''
        printl("", self, "S")

        self.saveAll()
        self.close(None)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def restartGUI(self, answer):
        '''
        '''
        printl("", self, "S")
        if answer is True:
            from Screens.Standby import TryQuitMainloop
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()
        
        printl("", self, "C")

#===============================================================================
# class
# DPS_ServerEntriesListConfigScreen
#===============================================================================
class DPS_ServerEntriesListConfigScreen(Screen):

    def __init__(self, session, what = None):
        '''
        '''
        printl("", self, "S")
        
        Screen.__init__(self, session)
        self.session = session
        
        self["state"] = StaticText(_("State"))
        self["name"] = StaticText(_("Name"))
        self["ip"] = StaticText(_("IP"))
        self["port"] = StaticText(_("Port"))
        
        self["key_red"] = StaticText(_("Add"))
        self["key_yellow"] = StaticText(_("Edit"))
        self["key_blue"] = StaticText(_("Delete"))
        self["entrylist"] = DPS_ServerEntryList([])
        self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
            {
             "ok"    :    self.keyYellow,
             "back"    :    self.keyClose,
             "red"    :    self.keyRed,
             "yellow":    self.keyYellow,
             "blue":     self.keyDelete,
             }, -1)
        self.what = what
        self.updateList()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def updateList(self):
        '''
        '''
        printl("", self, "S")
        
        self["entrylist"].buildList()

        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def keyClose(self):
        '''
        '''
        printl("", self, "S")
        
        self.close(self.session, self.what, None)

        printl("", self, "C")
    
    #=======================================================================
    # 
    #=======================================================================
    def keyRed(self):
        '''
        '''
        printl("", self, "S")
        
        self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, None)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def keyOK(self): #not in use for now
        '''
        '''
        printl("", self, "S")
        
        try:
            sel = self["entrylist"].l.getCurrentSelection()[0]
        except Exception, ex:
            printl("Exception: " + str(ex), self, "W")
            sel = None
        
        self.close(self.session, self.what, sel)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def keyYellow(self):
        '''
        '''
        printl("", self, "S")
        
        try:
            sel = self["entrylist"].l.getCurrentSelection()[0]
        
        except Exception, ex:
            printl("Exception: " + str(ex), self, "W")
            sel = None
        
        if sel is None:
            return
        
        printl("config selction: " +  str(sel), self, "D")
        self.session.openWithCallback(self.updateList, DPS_ServerEntryConfigScreen, sel)
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def keyDelete(self):
        '''
        '''
        printl("", self, "S")
        
        try:
            sel = self["entrylist"].l.getCurrentSelection()[0]
        
        except Exception, ex:
            printl("Exception: " + str(ex), self, "W")
            sel = None
        
        if sel is None:
            return
        
        self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Server Entry?"))
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def deleteConfirm(self, result):
        '''
        '''
        printl("", self, "S")
        
        if not result:
            return
        
        sel = self["entrylist"].l.getCurrentSelection()[0]
        config.plugins.dreamplex.entriescount.value = config.plugins.dreamplex.entriescount.value - 1
        config.plugins.dreamplex.entriescount.save()
        config.plugins.dreamplex.Entries.remove(sel)
        config.plugins.dreamplex.Entries.save()
        config.plugins.dreamplex.save()
        configfile.save()
        self.updateList()
        
        printl("", self, "C")

#===============================================================================
# class
# DPS_ServerEntryConfigScreen
#===============================================================================
class DPS_ServerEntryConfigScreen(ConfigListScreen, Screen):

    def __init__(self, session, entry):
        printl("", self, "S")
        
        self.session = session
        Screen.__init__(self, session)

        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.keySave,
            "red": self.keyCancel,
            "blue": self.keyDelete,
            "cancel": self.keyCancel,
            "yellow": self.keyYellow
        }, -2)

        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("OK"))
        self["key_blue"] = StaticText(_("Delete"))
        self["key_yellow"] = StaticText(_("check myPlex token"))

        if entry is None:
            self.newmode = 1
            self.current = initServerEntryConfig()
        else:
            self.newmode = 0
            self.current = entry

        cfglist = [
            getConfigListEntry(_("State"), self.current.state),
            getConfigListEntry(_("Name"), self.current.name),
            getConfigListEntry(_("[Connection Type] Selection"), self.current.connectionType),
            getConfigListEntry(_("[Connection Type] IP"), self.current.ip),
            getConfigListEntry(_("[Connection Type] DNS"), self.current.dns),
            getConfigListEntry(_("[Connection Type] Port"), self.current.port),
            getConfigListEntry(_("[Connection Type > myPLEX] URL"), self.current.myplexUrl),
            getConfigListEntry(_("[Connection Type > myPLEX] Username"), self.current.myplexUsername),
            getConfigListEntry(_("[Connection Type > myPLEX] Password"), self.current.myplexPassword),
            getConfigListEntry(_("[Connection Type > myPLEX] renew myPlex token"), self.current.renewMyplexToken),
            getConfigListEntry(_("[Playback Type] Selection"), self.current.playbackType),
            getConfigListEntry(_("[Playback Type > TRANSCODED] Transcoding quality"), self.current.quality),
            getConfigListEntry(_("[Playback Type > DIRECT LOCAL] Overwrite within remote path part"), self.current.remotePathPart),
            getConfigListEntry(_("[Playback Type > DIRECT LOCAL] Override with local path part"), self.current.localPathPart),
            #getConfigListEntry(_("[Playback Type > DIRECT REMOTE] Username"), self.current.smbUser),
            #getConfigListEntry(_("[Playback Type > DIRECT REMOTE] Password"), self.current.smbPassword),
            #getConfigListEntry(_("[Playback Type > DIRECT REMOTE] Server override IP"), self.current.nasOverrideIp),
            #getConfigListEntry(_("[Playback Type > DIRECT REMOTE] Servers root"), self.current.nasRoot),
            getConfigListEntry(_("[WOL] Use Wake on Lan (WoL)"), self.current.wol),
            getConfigListEntry(_("[WOL] Mac address (Size: 12 alphanumeric no seperator) only for WoL"), self.current.wol_mac),
            getConfigListEntry(_("[WOL] Wait for server delay (max 180 seconds) only for WoL"), self.current.wol_delay),
        ]
            #===================================================================
            # 
            # getConfigListEntry(_("Transcode Type (no function yet but soon ;-)"), self.current.transcodeType),
            # getConfigListEntry(_("Quality (no function yet but soon ;-)"), self.current.quality),
            # getConfigListEntry(_("Audio Output (no function yet but soon ;-)"), self.current.audioOutput),
            # getConfigListEntry(_("Stream Mode (no function yet but soon ;-)"), self.current.streamMode),
            #===================================================================

        ConfigListScreen.__init__(self, cfglist, session)

        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def keySave(self):
        '''
        '''
        printl("", self, "S")
        
        if self.newmode == 1:
            config.plugins.dreamplex.entriescount.value = config.plugins.dreamplex.entriescount.value + 1
            config.plugins.dreamplex.entriescount.save()
        ConfigListScreen.keySave(self)
        config.plugins.dreamplex.save()
        configfile.save()
        self.close()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def keyCancel(self):
        '''
        '''
        printl("", self, "S")
        
        if self.newmode == 1:
            config.plugins.dreamplex.Entries.remove(self.current)
        ConfigListScreen.cancelConfirm(self, True)
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def keyYellow(self):
        '''
        '''
        printl("", self, "S")
        
        self.session.open(MessageBox,_("myPlex Token:\n%s \nfor the user:\n%s") % (self.current.myplexToken.value, self.current.myplexTokenUsername.value), MessageBox.TYPE_INFO)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def keyDelete(self):
        '''
        '''
        printl("", self, "S")
        
        if self.newmode == 1:
            self.keyCancel()
        else:        
            self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Server Entry?"))
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def deleteConfirm(self, result):
        '''
        '''
        printl("", self, "S")
        
        if not result:
            return
        
        config.plugins.dreamplex.entriescount.value = config.plugins.dreamplex.entriescount.value - 1
        config.plugins.dreamplex.entriescount.save()
        config.plugins.dreamplex.Entries.remove(self.current)
        config.plugins.dreamplex.Entries.save()
        config.plugins.dreamplex.save()
        configfile.save()
        self.close()
        
        printl("", self, "C")

#===============================================================================
# class
# DPS_ServerEntryList
#===============================================================================
class DPS_ServerEntryList(MenuList):
    
    def __init__(self, menuList, enableWrapAround = True):
        '''
        '''
        printl("", self, "S")
        
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

        
        for c in config.plugins.dreamplex.Entries:
            res = [c]
            #res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.state.value)))
            res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 0, 200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.name.value)))
            
            if c.connectionType.value == "2":
                text1 = c.myplexUrl.value
                text2 = c.myplexUsername.value
            else:
                text1 = "%d.%d.%d.%d" % tuple(c.ip.value)
                text2 = "%d"%(c.port.value)
                
            res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(text1)))
            res.append((eListboxPythonMultiContent.TYPE_TEXT, 450, 0, 80, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(text2)))
            self.list.append(res)
        
        
        self.l.setList(self.list)
        self.moveToIndex(0)
                
        printl("", self, "C")
