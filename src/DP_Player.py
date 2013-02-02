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

from time import sleep
from urllib2 import urlopen, Request

from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox

from enigma import eServiceReference, eConsoleAppContainer, iPlayableService, eTimer, eServiceCenter, iServiceInformation #@UnresolvedImport

from thread import start_new_thread

from Tools.Directories import fileExists
from Tools import Notifications

from Components.config import config
from Components.ActionMap import ActionMap
from Components.Slider import Slider
from Components.Language import language
from Components.Sources.StaticText import StaticText
from Components.ServiceEventTracker import ServiceEventTracker

from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
# class
#===============================================================================    
class DP_Player(MoviePlayer):
    '''
    '''
    
    ENIGMA_SERVICE_ID = None
    ENIGMA_SERVICETS_ID = 0x1         #1
    ENIGMA_SERVICEGS_ID = 0x1001     #4097
    
    seek = None
    resume = False
    resumeStamp = 0
    server = None
    id = None
    url = None
    transcodingSession = None
    nTracks = False
    switchedLanguage = False
    startNewServiceOnPlay = False
  
    def __init__(self, session, playerData, resume=False):
        '''
        '''
        printl("", self, "S")
        
        self.session = session
                
        self.startNewServiceOnPlay = False
        
        # go through the data out of the function call
        self.resume = resume
        self.resumeStamp = int(playerData['resumeStamp']) / 1000 # plex stores seconds * 1000
        self.server = str(playerData['server'])
        self.id = str(playerData['id'])
        self.url = str(playerData['playUrl'])
        self.transcodingSession = str(playerData['transcodingSession'])


        # check for playable services
        printl( "Checking for usable gstreamer service (builtin)... ",self, "I")
        
        gstreamer = False
        
        if self.isValidServiceId(self.ENIGMA_SERVICEGS_ID):
            printl("we are able to stream over 4097", self, "I")
            gstreamer = True
        
        # lets built the sref for the movieplayer out of the gathered information            
        if self.url[:4] == "http": #this means we are in streaming mode so we will use sref 4097
            self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVICEGS_ID
        
        elif self.url[-3:] == ".ts": # seems like we have a real ts file so we will use sref 1
            self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVICETS_ID
        
        else: # if we have a real file but no ts but for eg mkv we will also use sref 4097
            self.ENIGMA_SERVICE_ID = self.ENIGMA_SERVICEGS_ID
        
        printl("self.ENIGMA_SERVICE_ID = " + str(self.ENIGMA_SERVICE_ID), self, "I")
        
        sref = eServiceReference(self.ENIGMA_SERVICE_ID, 0, self.url)
        sref.setName("DreamPlex")
        
        # lets call the movieplayer
        MoviePlayer.__init__(self, session, sref)
        
        self.skinName = "DPS_PlexPlayer"
        
        self.service = sref
        self.bufferslider = Slider(0, 100)
        self["bufferslider"] = self.bufferslider
        self["bufferslider"].setValue(0)
        self["label_buffer"] = StaticText("Buffer")
        self["label_update"] = StaticText("")
        self.bufferSeconds = 0
        self.bufferPercent = 0
        self.bufferSecondsLeft = 0
        self.bitrate = 0
        self.endReached = False
        self.buffersize = 1
        self.localCache = False
        self.dlactive = False
        #self.url = self.service.getPath()
        self.localsize = 0
 
        self["actions"] = ActionMap(["InfobarInstantRecord", "MoviePlayerActions"],
        {
         "leavePlayer": self.leavePlayer,
        }, -2)
 
        self.useBufferControl = config.plugins.dreamplex.useBufferControl.value
 
        if config.plugins.dreamplex.setBufferSize.value:
            bufferSize = int(config.plugins.dreamplex.bufferSize.value) * 1024 * 1024
            session.nav.getCurrentService().streamed().setBufferSize(bufferSize)
            
        service1 = self.session.nav.getCurrentService()
        self.seek = service1 and service1.seek()
        
        if self.seek != None:
            rLen = self.getPlayLength()
            rPos = self.getPlayPosition()
            printl("rLen: " + str(rLen), self, "I")
            printl("rPos: " + str(rPos), self, "I")
            
        if self.resume == True and self.resumeStamp != None and self.resumeStamp > 0.0:
            start_new_thread(self.seekWatcher,(self,))
        
        if config.plugins.dreamplex.autoLanguage.value: 
            start_new_thread(self.audioTrackWatcher,(self,))
        
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evUser+10: self.__evAudioDecodeError,
                iPlayableService.evUser+11: self.__evVideoDecodeError,
                iPlayableService.evUser+12: self.__evPluginError,
                iPlayableService.evBuffering: self.__evUpdatedBufferInfo,
                iPlayableService.evEOF: self.__evEOF,
            })
       
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def getPlayLength(self):
        '''
        '''
        printl("", self, "S")
        
        length = self.seek.getLength()
        
        printl("", self, "C")
        return length    
    
    #===========================================================================
    # 
    #===========================================================================
    def getPlayPosition(self):
        '''
        '''
        printl("", self, "S")
        
        position = self.seek.getPlayPosition()
        
        printl("", self, "C")
        return position
    
    #===========================================================================
    # 
    #===========================================================================
    def isValidServiceId(self, id):
        '''
        '''
        printl("", self, "S")
        
        testSRef = eServiceReference(id, 0, "Just a TestReference")
        info = eServiceCenter.getInstance().info(testSRef)
        
        printl("", self, "C")
        return info is not None

    #===========================================================================
    # 
    #===========================================================================
    def UpdateStatus(self):
        '''
        '''
        printl("", self, "S")

        if not self.dlactive:
            
            printl("", self, "C")
            return
        
        lastSize = 0;
        if fileExists(config.plugins.dreamplex.playerTempPath.value + self.filename, 'r'):
            lastSize = self.localsize
            self.localsize = os.path.getsize(config.plugins.dreamplex.playerTempPath.value + self.filename)
        else:
            self.localsize = 0
        
        self["label_buffer"].setText("Cache: "+self.formatKB(self.localsize,"B",1))
        
        if self.localsize > 0 and self.filesize >0:
            percent = float(float(self.localsize)/float(self.filesize))
            percent = percent * 100.0
            self["bufferslider"].setValue(int( percent ))
        
        self.StatusTimer.start(1000, True)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def DLfinished(self,retval):
        '''
        '''
        printl("", self, "S")
        
        self.dlactive = False
        printl( "download finished", self, "I")
        
        self["label_buffer"].setText("Download: Done")
        self["bufferslider"].setValue(int( 100 ))
        self.setSeekState(self.SEEK_STATE_PLAY) # this plays the file

        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def __evUpdatedBufferInfo(self):
        '''
        '''
        #printl("", self, "S")
        
        if self.localCache:
            printl("", self, "C")
            return
        
        bufferInfo = self.session.nav.getCurrentService().streamed().getBufferCharge()
        self.buffersize = bufferInfo[4]
        self.bufferPercent = bufferInfo[0]
        #printl("bufferPercent: " + str(self.bufferPercent), self, "D")
        self["bufferslider"].setValue(int(self.bufferPercent))

        if(self.bufferPercent > 95):
            self.bufferFull()
                
        if(self.bufferPercent == 0 and not self.endReached and (bufferInfo[1] != 0 and bufferInfo[2] !=0)):
            self.bufferEmpty()
        
        #printl("self.buffersize: " + str(self.buffersize), self, "D")
        #printl("self.bufferPercent: " + str(self.bufferPercent), self, "D")
        
        #printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def __evAudioDecodeError(self):
        '''
        '''
        printl("", self, "S")
        
        try:
            currPlay = self.session.nav.getCurrentService()
            sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
            printl( "audio-codec %s can't be decoded by hardware" % (sTagAudioCodec), self, "I")
            Notifications.AddNotification(MessageBox, _("This Box can't decode %s streams!") % sTagAudioCodec, type=MessageBox.TYPE_INFO, timeout=10)
        
        except Exception, e:
            printl("exception: " + str(e), self, "W")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def __evVideoDecodeError(self):
        '''
        '''
        printl("", self, "S")
        
        try:
            currPlay = self.session.nav.getCurrentService()
            sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
            printl( "video-codec %s can't be decoded by hardware" % (sTagVideoCodec), self, "I")
            Notifications.AddNotification(MessageBox, _("This Box can't decode %s streams!") % sTagVideoCodec, type=MessageBox.TYPE_INFO, timeout=10)
        
        except Exception, e:
            printl("exception: " + str(e), self, "W")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def __evPluginError(self):
        '''
        '''
        printl("", self, "S")
        
        try:
            currPlay = self.session.nav.getCurrentService()
            message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
            printl( "[PlexPlayer] PluginError " + message, self, "I")
            Notifications.AddNotification(MessageBox, _("Your Box can't decode this video stream!\n%s") % message, type=MessageBox.TYPE_INFO, timeout=10)
        
        except Exception, e:
            printl("exception: " + str(e), self, "W")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def __evEOF(self):
        '''
        '''
        printl("", self, "S")
        
        printl( "got evEOF", self, "W")
        
        try:
            err = self.session.nav.getCurrentService().info().getInfoString(iServiceInformation.sUser+12)
            printl( "Error: " + str(err), self, "W")
            
            if err != "":
                Notifications.AddNotification(MessageBox, _("Your Box can't decode this video stream!\n%s") % err, type=MessageBox.TYPE_INFO, timeout=10)
        
        except Exception, e:
            printl("exception: " + str(e), self, "W")
            
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def seekWatcher(self,*args):
        '''
        '''
        printl("", self, "S")
        
        printl( "seekWatcher started", self, "I")
        try:
            while self is not None and self.resumeStamp is not None:
                self.seekToStartPos()
                sleep(0.2)
        except Exception, e:
            printl("exception: " + str(e), self, "W")
        
        printl( "seekWatcher finished ", self, "I")
        printl("", self, "C")
            
    #===========================================================================
    # 
    #===========================================================================
    def seekToStartPos(self):
        '''
        '''
        printl("", self, "S")
        
        time = 0
        try:
            if self.resumeStamp is not None and config.plugins.dreamplex.setSeekOnStart.value:
                service = self.session.nav.getCurrentService()
                seek = service and service.seek()
                if seek != None:
                    r = seek.getLength()
                    if not r[0]:
                        printl ("got duration", self, "I")
                        if r[1] == 0:
                            printl( "duration 0", self, "I")
                            return
                        length = r[1]
                        r = seek.getPlayPosition()
                        if not r[0]:
                            printl( "playbacktime " + str(r[1]), self, "I")
                            if r[1] < 90000:# ~2 sekunden
                                printl( "do not seek yet " + str(r[1]), self, "I")
                                printl("", self, "C")
                                return
                        else:
                            printl("", self, "C")
                            return
                        
                        #time = length * self.start
                        #time = int(139144271)
                        time = self.resumeStamp * 90000
                        printl( "seeking to " + str(time) + " length " + str(length) + " ", self, "I")
                        self.resumeStamp = None
                        if time < 90000:
                            printl( "skip seeking < 10s", self, "I")
                            printl("", self, "C")
                            return
                        #if config.plugins.dreamplex.setBufferSize.value:
                            #self.session.nav.getCurrentService().streamed().setBufferSize(config.plugins.dreamplex.bufferSize.value)
                        self.doSeek(int(time))
        
        except Exception, e:
            printl("exception: " + str(e), self, "W")
            
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def formatKBits(self, value, ending="Bit/s", roundNumbers=2):
        '''
        '''
        #printl("", self, "S")
        
        bits = value * 8
        
        if bits > (1024*1024):
            return str(    round(float(bits)/float(1024*1024),roundNumbers)  )+" M"+ending
        if bits > 1024:
            return str(    round(float(bits)/float(1024),roundNumbers)       )+" K"+ending
        else:
            return str(bits)+" "+ending
        
        #printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def formatKB(self, value, ending="B", roundNumbers=2):
        '''
        '''
        #printl("", self, "S")
        
        byte = value

        if byte > (1024*1024):
            return str(    round(float(byte)/float(1024*1024),roundNumbers) ) +" M"+ending
        if byte > 1024:
            return str(    round(float(byte)/float(1024),roundNumbers)      ) +" K"+ending
        else:
            return str(byte)+" "+ending
        
        #printl("", self, "C")
                         
    #===========================================================================
    # 
    #===========================================================================
    def bufferFull(self):
        '''
        '''
        #printl("", self, "S")
        
        if self.useBufferControl:
            if self.seekstate != self.SEEK_STATE_PLAY :
                printl( "Buffer filled start playing", self, "I")
                self.setSeekState(self.SEEK_STATE_PLAY)
        
        #hide infobar to indicate buffer is ready
        self.hide()
        
        #printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def bufferEmpty(self):
        '''
        '''
        #printl("", self, "S")
        
        #show infobar to indicate buffer is empty 
        self.show()
        
        if self.useBufferControl:
            if self.seekstate != self.SEEK_STATE_PAUSE :
                printl( "Buffer drained pause", self, "I")
                self.setSeekState(self.SEEK_STATE_PAUSE)
        
        #printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def setSeekState(self, state, unknow=False):
        '''
        '''
        printl("", self, "S")
        
        if not self.startNewServiceOnPlay:
            super(DP_Player, self).setSeekState(state)
        else:
            printl( "start downloaded file now", self, "I")
            self.startNewServiceOnPlay = False
            super(DP_Player, self).setSeekState(self.SEEK_STATE_PLAY)
            sref = eServiceReference(self.ENIGMA_SERVICE_ID, 0, config.plugins.dreamplex.playerTempPath.value + self.filename)
            sref.setName("DreamPlex")
            self.session.nav.playService(sref)
        #self.session.openWithCallback(self.MoviePlayerCallback, DP_Player, sref, self)
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def leavePlayer(self):
        '''
        '''
        printl("", self, "S")
        
        self.leavePlayerConfirmed(True)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def leavePlayerConfirmed(self, answer):
        '''
        '''
        printl("", self, "S")
        
        if answer:
            self.handleProgress()
            self.stopTranscoding()
            self.close()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def doEofInternal(self, playing):
        '''
        '''
        printl("", self, "S")
        
        self.handleProgress()
        self.stopTranscoding()
        #check this
        #self.stop()
        self.close()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def handleProgress(self):
        '''
        '''
        printl("", self, "S")
        
        currentTime = self.getPlayPosition()[1] / 90000
        totalTime = self.getPlayLength()[1] / 90000
        progress = currentTime / (totalTime/100)
        #progress = 0
        printl( "played time is %s secs of %s @ %s%%" % ( currentTime, totalTime, progress),self, "I" )
        
        instance = Singleton()
        plexInstance = instance.getPlexInstance()
        
        
        if currentTime < 30:
            printl("Less that 30 seconds, will not set resume", self, "I")
        
        #If we are less than 95% complete, store resume time
        elif progress < 95:
            printl("Less than 95% progress, will store resume time", self, "I" )
            plexInstance.getURL("http://"+self.server+"/:/progress?key="+self.id+"&identifier=com.plexapp.plugins.library&time="+str(currentTime*1000))

        #Otherwise, mark as watched
        else:
            printl( "Movie marked as watched. Over 95% complete", self, "I")
            plexInstance.getURL("http://"+self.server+"/:/scrobble?key="+self.id+"&identifier=com.plexapp.plugins.library")
            
        
        printl("", self, "C")       
        
    
    #===========================================================================
    # stopTranscoding
    #===========================================================================
    def stopTranscoding(self):
        '''
        '''
        printl("", self, "S")
        
        instance = Singleton()
        plexInstance = instance.getPlexInstance()
        
        #sample from log /video/:/transcode/segmented/stop?session=0EBD197D-389A-4784-8CC5-709BAD5E1137&X-Plex-Client-Capabilities=protocols%3Dhttp-live-streaming%2Chttp-mp4-streaming%2Chttp-streaming-video%2Chttp-streaming-video-720p%2Chttp-mp4-video%2Chttp-mp4-video-720p%3BvideoDecoders%3Dh264%7Bprofile%3Ahigh%26resolution%3A1080%26level%3A41%7D%3BaudioDecoders%3Dmp3%2Caac%7Bbitrate%3A160000%7D&X-Plex-Client-Platform=iOS&X-Plex-Product=Plex%2FiOS&X-Plex-Version=3.0.2&X-Plex-Device-Name=DDiPhone [192.168.45.6:62662] (4 live)
        plexInstance.getURL("http://"+self.server+"/video/:/transcode/segmented/stop?session=" + self.transcodingSession)
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def isPlaying(self):
        '''
        '''
        printl("", self, "S")
        
        if self.seekstate != self.SEEK_STATE_PLAY:
            return False
        else:
            return True
        
        printl("", self, "C")

    
    #===========================================================================
    # audioTrackWatcher
    #===========================================================================
    def audioTrackWatcher(self,*args):
        '''
        '''
        printl("", self, "S")
        
        try:
            while self.nTracks == False and self is not None:
                self.setAudioTrack()
                sleep(1)
        
        except Exception, e:    
            printl("exception: " + str(e), self, "E")
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def setAudioTrack(self):
        '''
        '''
        printl("", self, "S")
        if self.switchedLanguage == False:
            try:
                service = self.session.nav.getCurrentService()
        
        
                tracks = service and self.getServiceInterface("audioTracks")
                nTracks = tracks and tracks.getNumberOfTracks() or 0
                
                if not nTracks:
                    printl("no tracks found yet ... retrying later", self, "D")
                    return
                
                self.nTracks = True
                trackList = []
                
                for i in xrange(nTracks):
                    audioInfo = tracks.getTrackInfo(i)
                    lang = audioInfo.getLanguage()
                    printl("lang: " + str(lang), self, "D")
                    trackList += [str(lang)]
                
                systemLanguage = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
                printl("found systemLanguage: " +  systemLanguage, self, "I")
                #systemLanguage = "en"
                
                self.tryAudioEnable(trackList, systemLanguage, tracks)
            
            except Exception, e:
                printl("audioTrack exception: " + str(e), self, "W") 
        
        printl("", self, "C")   
        
    
    #===========================================================================
    # tryAudioEnable
    #===========================================================================
    def tryAudioEnable(self, alist, match, tracks):
        '''
        '''
        printl("", self, "S")
        printl("alist: " + str(alist), self, "D")
        printl("match: " + str(match), self, "D")
        index = 0
        for e in alist:
            e.lower()
            if e.find(match) >= 0:
                printl("audio track match: " + str(e), self, "I")
                sleep(2)
                tracks.selectTrack(index)
                
                printl("", self, "S")
                index += 1
            else:
                printl("no audio track match with " + str(e), self, "I")
        
        self.switchedLanguage = True
        printl("", self, "S")
        
    
    #===========================================================================
    # getServiceInterface
    #===========================================================================
    def getServiceInterface(self, iface):
        '''
        '''
        printl("", self, "S")
        service = self.session.nav.getCurrentService() # self.service
        if service:
            attr = getattr(service, iface, None)
            if callable(attr):
                printl("", self, "C")   
                return attr()
        
        printl("", self, "C")   
        return None
