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
import os
import cPickle as pickle

from Screens.Screen import Screen

from DP_View import DP_View, getViews
from DP_Player import DP_Player

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugins, Plugin

#------------------------------------------------------------------------------------------

class DP_LibMain(Screen):

    checkFileCreationDate = True

    def __init__(self, session, libraryName):
        printl("", self, "S")
        Screen.__init__(self, session)
        self._session = session
        self._libraryName = libraryName
        
        self._views = getViews()
        self.currentViewIndex = 0
        
        self.defaultPickle = ""
        self.onFirstExecBegin.append(self.showDefaultView)

    def getDefault(self):
        try:
            fd = open(self.defaultPickle, "rb")
            default = pickle.load(fd)
            fd.close()
        except:
            default = {
            "view": self.currentViewIndex, 
            "selection": None, 
            "sort": None, 
            "filter": None, 
        }
        return default

    def setDefault(self, selection, sort, filter):
        if selection is None and sort is None and filter is None:
            try:
                os.remove(self.defaultPickle)
            except:
                printl("Could not remove " + str(self.defaultPickle), self, "E")
            return
        default = {
            "view": self.currentViewIndex, 
            "selection": selection, 
            "sort": sort, 
            "filter": filter, 
        }
        
        fd = open(self.defaultPickle, "wb")
        pickle.dump(default, fd, 2) #pickle.HIGHEST_PROTOCOL)
        fd.close()

    def showDefaultView(self):
        default = self.getDefault()
        self.currentViewIndex = default["view"]
        self.showView(default["selection"], default["sort"], default["filter"])

    # Displays the selected View
    def showView(self, selection=None, sort=None, filter=None):
        printl("", self, "D")
        m = __import__(self._views[self.currentViewIndex][1], globals(), locals(), [], -1)
        self._session.openWithCallback(self.onViewClosed, m.getViewClass(), self._libraryName, self.loadLibrary, self.playEntry, self._views[self.currentViewIndex], select=selection, sort=sort, filter=filter)

    # Called if View has closed, react on cause for example change to different view
    def onViewClosed(self, cause=None):
        printl("cause: %s" % str(cause), self, "D")
        if cause is not None:
            if cause[0] == DP_View.ON_CLOSED_CAUSE_SAVE_DEFAULT:
                selection = None
                sort = None
                filter = None
                if len(cause) >= 2 and cause[1] is not None:
                    #self.currentViewIndex = cause[1]
                    selection = cause[1]
                if len(cause) >= 3 and cause[2] is not None:
                    sort = cause[2]
                if len(cause) >= 4 and cause[3] is not None:
                    filter = cause[3]
                self.setDefault(selection, sort, filter)
                self.close()
            elif cause[0] == DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW:
                selection = None
                sort = None
                filter = None
                self.currentViewIndex += 1
                if len(self._views) <= self.currentViewIndex:
                    self.currentViewIndex = 0
                
                if len(cause) >= 2 and cause[1] is not None:
                    #self.currentViewIndex = cause[1]
                    selection = cause[1]
                if len(cause) >= 3 and cause[2] is not None:
                    sort = cause[2]
                if len(cause) >= 4 and cause[3] is not None:
                    filter = cause[3]
                if len(cause) >= 5 and cause[4] is not None:
                    for i in range(len(self._views)):
                        if cause[4]== self._views[i][1]:
                            self.currentViewIndex = i
                            break
                self.showView(selection, sort, filter)
            else:
                self.close()
        else:
            self.close()

    # prototype for library loading, is called by the view
    def loadLibrary(self, params=None):
        #dict({'root': None})
        return []

    # starts playback, is called by the view
    def playEntry(self, entry, flags={}):
        printl("", self, "D")
        playbackPath = entry["Path"]
        if playbackPath[0] == "/" and os.path.isfile(playbackPath) is False:
            return False
        else:
            self.notifyEntryPlaying(entry, flags)
            
            isDVD, dvdFilelist, dvdDevice = self.checkIfDVD(playbackPath)
            if isDVD:
                self.playDVD(dvdDevice, dvdFilelist)
            else:
                self.playFile(entry, flags)
            return True

    # tries to determin if media entry is a dvd
    def checkIfDVD(self, playbackPath):
        printl("", self, "D")
        isDVD = False
        dvdFilelist = [ ]
        dvdDevice = None
        
        if playbackPath.lower().endswith(u"ifo"): # DVD
            isDVD = True
            dvdFilelist.append(str(playbackPath.replace(u"/VIDEO_TS.IFO", "").strip()))
        elif playbackPath.lower().endswith(u"iso"): # DVD
            isDVD = True
            dvdFilelist.append(str(playbackPath))
        return (isDVD, dvdFilelist, dvdDevice, )

    # playbacks a dvd by callinf dvdplayer plugin
    def playDVD(self, dvdDevice, dvdFilelist):
        printl("", self, "D")
        try:
            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
            # when iso -> filelist, when folder -> device
            self.session.openWithCallback(self.leaveMoviePlayer, DVDPlayer, \
                dvd_device = dvdDevice, dvd_filelist = dvdFilelist)
        except Exception, ex:
            printl("Exception: " + str(ex), self, "E")

    # playbacks a file by calling DP_player
    def playFile(self, entry, flags):
        printl("", self, "D")
        playbackList = self.getPlaybackList(entry)
        printl("playbackList: " + str(playbackList), self, "D")
        
        if len(playbackList) == 1:
            self.session.openWithCallback(self.leaveMoviePlayer, DP_Player, playbackList, flags=flags)
        elif len(playbackList) >= 2:
            self.session.openWithCallback(self.leaveMoviePlayer, DP_Player, playbackList, self.notifyNextEntry, flags=flags)

    # After calling this the view should auto reappear
    def leaveMoviePlayer(self, flags={}): 
        self.notifyEntryStopped(flags)
        
        self.session.nav.playService(None) 

    # prototype fore playbacklist creation
    def getPlaybackList(self, entry):
        printl("", self, "D")
        playbackList = []
        playbackList.append( (entry["Path"], entry["Title"], entry, ))
        return playbackList

    def buildInfoPlaybackArgs(self, entry):
        return {}

    # called on start of playback
    def notifyEntryPlaying(self, entry, flags):
        printl("", self, "D")
        args = self.buildInfoPlaybackArgs(entry)
        args["status"]  = "playing"
        plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
        for plugin in plugins:
            printl("plugin.name=" + str(plugin.name), self, "D")
            plugin.fnc(args, flags)

    # called on end of playback
    def notifyEntryStopped(self, flags):
        printl("", self, "D")
        args = {}
        args["status"] = "stopped"
        plugins = getPlugins(where=Plugin.INFO_PLAYBACK)
        for plugin in plugins:
            printl("plugin.name=" + str(plugin.name), self, "D")
            plugin.fnc(args, flags)

    # called if the next entry in the playbacklist is being playbacked
    def notifyNextEntry(self, entry, flags):
        printl("", self, "D")
        self.notifyEntryStopped(flags)
        self.notifyEntryPlaying(entry, flags)

