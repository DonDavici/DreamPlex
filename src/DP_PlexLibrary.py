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
import urllib
import re
import httplib
import socket
import sys
import os
import datetime 
import time
import base64 
import hashlib
import random
import hmac
import uuid

#===============================================================================
# 
#===============================================================================
from Screens.Screen import Screen

from Components.config import config

from Plugins.Extensions.DreamPlex.__plugin__ import getPlugin, Plugin
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
#from DPH_bonjourFind import *

#===============================================================================
# import cProfile
#===============================================================================
try:
    from lxml import etree
    printl("running with lxml.etree", __name__, "D")
except ImportError:
    try:
    # Python 2.5
        import xml.etree.cElementTree as etree
        printl("running with cElementTree on Python 2.5+", __name__, "D")
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            printl("running with ElementTree on Python 2.5+", __name__, "D")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
                printl("running with cElementTree", __name__, "D")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    printl("running with ElementTree")
                except ImportError:
                    printl("Failed to import ElementTree from any known place", __name__, "W")

#===============================================================================
# 
#===============================================================================
#DEBUG ON/OFF
DEBUG = "true"

#Get the setting from the appropriate file.
DEFAULT_PORT="32400"
MYPLEX_SERVER="my.plexapp.com"

_MODE_GETCONTENT=0
_MODE_TVSHOWS=1
_MODE_MOVIES=2
_MODE_ARTISTS=3
_MODE_getSeasonsOfShow=4
_MODE_PLAYLIBRARY=5
_MODE_TVEPISODES=6
_MODE_PLEXPLUGINS=7
_MODE_PROCESSXML=8
_MODE_BASICPLAY=12
_MODE_ALBUMS=14
_MODE_TRACKS=15
_MODE_PHOTOS=16
_MODE_MUSIC=17
_MODE_VIDEOPLUGINPLAY=18
_MODE_PLEXONLINE=19
_MODE_CHANNELINSTALL=20
_MODE_CHANNELVIEW=21
_MODE_DISPLAYSERVERS=22
_MODE_PLAYLIBRARY_TRANSCODE=23
_MODE_MYPLEXQUEUE=24

_OVERLAY_XBMC_UNWATCHED=6  #Blank
_OVERLAY_XBMC_WATCHED=7    #Tick
_OVERLAY_PLEX_UNWATCHED=4  #Dot
_OVERLAY_PLEX_WATCHED=0    #Blank
_OVERLAY_PLEX_PARTIAL=5    #half - Reusing XBMC overlaytrained

#===============================================================================
# PlexLibrary
#===============================================================================
class PlexLibrary(Screen):
    g_sessionID=None
    g_serverDict=[]
    g_sections=[]
    g_name = "Plexserver"
    g_host = "192.168.45.190"
    g_port = "32400"
    g_connectionType = None
    g_showForeign = True
    g_address = None # is later the combination of g_host : g_port
    g_stream = "0" # 0 = autoselect, 1 = Selecting stream, 2 = Selecting smb/unc, 3 = unknown
    g_secondary = "true" # show filter for media
    g_streamControl = "3" # 1 unknown, 2 = unknown, 3 = All subs disabled
    g_channelview = "false" # unknown
    g_flatten = "0" # 0 = show seasons, 1 = show all
    g_playtheme = "false"
    g_forcedvd = "false"
    g_skipcontext = "true" # best understanding when looking getMoviesfromsection
    g_skipmetadata = "true" # best understanding when looking getMoviesfromsection
    g_skipmediaflags = "true" # best understanding when looking getMoviesfromsection
    g_skipimages = "false"
    g_loc = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/" # homeverzeichnis
    g_myplex_username = "" # "" = do not use
    g_myplex_password = "password"
    g_myplex_token = ""
    g_transcode = "false"
    g_transcodetype = "0" # 0 = m3u8, 1 = flv
    g_transcodefmt = "m3u8" # m3u8, flv
    g_wolon = "true"
    g_wakeserver = "00-11-32-12-C5-F9"
    g_woldelay = 10
    g_nasoverride = "false"
    g_nasoverrideip = "192.168.45.190"
    g_nasuserid = "userid"
    g_naspass = "naspass"
    g_nasroot = "/"
    g_bonjour = "0" # 0 = OFF, 1= ON
    g_quality = "4" # +3 laut zeile irgendwo todo checken
    g_capability = ""
    g_audioOutput = "2" #0 = "mp3,aac", 1 = "mp3,aac,ac3", 2 ="mp3,aac,ac3,dts"
    g_session = None
    
    #Create the standard header structure and load with a User Agent to ensure we get back a response.
    g_txheaders = {
                  'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',    
                  }
    
    #===========================================================================
    # 
    #===========================================================================
    def __init__(self, session, serverConfig=None):
        '''
        '''
        printl("", self, "S")
        
        Screen.__init__(self, session)
        self.g_session = session

        printl("running on " + str(sys.version_info), self, "I")
        
                
        # global settings
        self.g_secondary = str(config.plugins.dreamplex.showFilter.value).lower()
        
        # server settings
        self.g_name = str(serverConfig.name.value)
        self.g_connectionType = str(serverConfig.connectionType.value)
        self.g_port = str(serverConfig.port.value)

        if self.g_connectionType == "0":
            self.g_host = "%d.%d.%d.%d" % tuple(serverConfig.ip.value)
        else:
            try:
                self.g_host = str(socket.gethostbyname(serverConfig.dns.value))
            except Exception, e:
                printl("socket error: " + str(e), self, "W")
                printl("trying fallback to ip", self, "I")
                self.g_host = "%d.%d.%d.%d" % tuple(serverConfig.ip.value)
                
                

        printl("using this serverName: " +  self.g_name, self, "I")
        printl("using this serverIp: " +  self.g_host, self, "I")
        printl("using this serverPort: " +  self.g_port, self, "I")
        printl("using this connectionType: " +  self.g_connectionType, self, "I")
        
        #Next lets check if for this server nas override is activated
        self.checkNasOverride()
        
        #Fill serverdate to global g_serverDict
        self.discoverAllServers()

        #_PARAM_TOKEN
        global _PARAM_TOKEN
        #_PARAM_TOKEN = self.getNewMyPlexToken()
        _PARAM_TOKEN = None
                                   
        printl("", self, "C")

    #============================================================================
    # 
    #============================================================================
    def displaySections(self, filter=None ): # CHECKED unused!?!?
        '''
        '''
        printl("", self, "S")
        #===>
        mainMenuList = []
        self.g_sections = []
        #===>
        
        numOfServers=len(self.g_serverDict)
        printl( "Using list of "+str(numOfServers)+" servers: " +  str(self.g_serverDict), self, "I")
        self.getAllSections()
        
        for section in self.g_sections:
                
            details={'title' : section.get('title', 'Unknown') }
            
            if len(self.g_serverDict) > 1:
                details['title']=section.get('serverName')+": "+details['title']
            
            extraData={ 'fanart_image' : self.getFanart(section, section.get('address')) ,
                        'type'         : "Video" ,
                        'thumb'        : self.getFanart(section, section.get('address'), False) ,
                        'token'        : section.get('token',None) }
                                               
            #Determine what we are going to do process after a link is selected by the user, based on the content we find
            
            path = section['path']
            address =  section['address']
            
            if self.g_secondary == "true":
                printl( "_MODE_GETCONTENT detected", self, "D")
                mode=_MODE_GETCONTENT
            else:
                path=path+'/all'    
            
            params = {} 
            params['t_url'] = self.getSectionUrl(address, path)
            params['t_mode'] = str(section.get('type')) 
            
            if self.g_secondary == "true":      
                if section.get('type') == 'show':
                    printl( "_MODE_TVSHOWS detected", self, "D")
                    mainMenuList.append((_(section.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))
                        
                elif section.get('type') == 'movie':
                    
                    printl( "_MODE_MOVIES detected", self, "D")
                    mainMenuList.append((_(section.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))
    
                elif section.get('type') == 'artist':
                    printl( "_MODE_ARTISTS detected", self, "D")

                        
                elif section.get('type') == 'photo':
                    printl( "_MODE_PHOTOS detected", self, "D")

                else:
                    printl("Ignoring section "+details['title']+" of type " + section.get('type') + " as unable to process")
                    continue
            
            else: # lets start here we configured no filters          
                if section.get('type') == 'show':
                    printl( "_MODE_TVSHOWS detected", self, "D")
                    mode= _MODE_TVSHOWS
                    mainMenuList.append((_(section.get('title').encode('utf-8')), getPlugin("tvshows", Plugin.MENU_VIDEOS), params))
                    if (filter is not None) and (filter != "tvshow"):
                        continue
                        
                elif section.get('type') == 'movie':
                    printl( "_MODE_MOVIES detected", self, "D")
                    mode= _MODE_MOVIES
                    mainMenuList.append((_(section.get('title').encode('utf-8')), getPlugin("movies", Plugin.MENU_VIDEOS), params))
                    if (filter is not None) and (filter != "movies"):
                        continue
    
                elif section.get('type') == 'artist':
                    printl( "_MODE_ARTISTS detected", self, "D")
                    mode= _MODE_ARTISTS
                    if (filter is not None) and (filter != "music"):
                        continue
                        
                elif section.get('type') == 'photo':
                    printl( "_MODE_PHOTOS detected", self, "D")
                    mode= int(_MODE_PHOTOS)
                    if (filter is not None) and (filter != "photos"):
                        continue
                else:
                    printl("Ignoring section "+details['title']+" of type " + section.get('type') + " as unable to process")
                    continue
         
        #=======================================================================   
        # UNUSED FOR NOW
        #=======================================================================
        #    if self.g_skipcontext == "false":
        #        context=[]
        #        refreshURL="http://"+section.get('address')+section.get('path')+"/refresh"
        #        #libraryRefresh = "XBMC.RunScript("+self.g_loc+"/default.py, update ," + refreshURL + ")"
        #        context.append(('Refresh library section', libraryRefresh , ))
        #    else:
        #        context=None
        #    
        #    printl("mode: " + str(mode), self, "D")
        #         
        # #For each of the servers we have identified
        # allservers = self.resolveAllServers()
        # numOfServers = len(allservers)
        # 
        # if self.g_myplex_username != '':
        #    self.addGUIItem('http://myplexqueue&mode='+str(_MODE_MYPLEXQUEUE), {'title':'myplex Queue'},{'type':'Video'})
        # 
        # for server in allservers:
        #                                                                                      
        #    #Plex plugin handling 
        #    if (filter is not None) and (filter != "plugins"):
        #        continue 
        #              
        #    if numOfServers > 1:
        #        prefix=server['serverName']+": "
        #    else:
        #        prefix=""
        #    
        #    details={'title' : prefix+"Channels" }
        #    extraData={'type' : "Video",
        #               'token' : server.get('token',None) }    
        #        
        #    u="http://"+server['address']+"/system/plugins/all&mode="+str(_MODE_CHANNELVIEW)
        #    self.addGUIItem(u,details,extraData)
        #            
        #    #Create plexonline link
        #    details['title']=prefix+"Plex Online"
        #    extraData['type']="file"
        #    
        #    u="http://"+server['address']+"/system/plexonline&mode="+str(_MODE_PLEXONLINE)
        #    self.addGUIItem(u,details,extraData)
        #  
        # #=======================================================================
        # # #All XML entries have been parsed and we are ready to allow the user to browse around.  So end the screen listing.
        # # xbmcplugin.endOfDirectory(pluginhandle)  
        # #=======================================================================
        #=======================================================================
        
        printl("mainMenuList: " + str(mainMenuList), self, "D")
        printl("", self, "C")
        return mainMenuList  

    #=============================================================================
    # 
    #=============================================================================
    def getAllSections(self): # CHECKED
        '''
            from self.g_serverDict, get a list of all the available sections
            and deduplicate the sections list
            @input: None
            @return: MainMenu for DP_MainMenu and alters the global value g_sectionList for other functions
        '''
        printl("", self, "S")
          
        multiple = False
        multiple_list = []
        for server in self.g_serverDict:
                                                                            
            if server['discovery'] == "local" or server['discovery'] == "bonjour":                                                
                html = self.getURL('http://'+server['address']+'/library/sections')
            elif server['discovery'] == "myplex":
                html = self.getMyPlexURL('/pms/system/library/sections')
                
            if html is False:
                continue
                    
            tree = etree.fromstring(html).getiterator("Directory")
            
            for sections in tree:
                
                #we need this until we do not support music and photos
                type = sections.get('type', 'unknown')
                if type == "movie" or type == "show":
                    self.appendEntry(sections, server)
                else:
                    printl("excluded unsupported section: " + str(sections.get('title','Unknown').encode('utf-8')),self, "I")
                
        if multiple == True:
            printl("there are other plex servers in the network => " + str(multiple_list), self, "I")
            
        '''
        If we have more than one server source, then
        we need to ensure uniqueness amonst the
        seperate sections.
        
        If we have only one server source, then the assumption
        is that Plex will deal with this for us
        '''
        if len(self.g_serverDict) > 1:    
            oneCount=0
            for onedevice in self.g_sections:
            
                twoCount=0
                for twodevice in self.g_sections:
    
                    printl( "["+str(oneCount)+":"+str(twoCount)+"] Checking " + str(onedevice['title']) + " and " + str(twodevice['title']))
                    printl( "and "+ onedevice['uuid'] + " is equal " + twodevice['uuid'])
    
                    if oneCount == twoCount:
                        printl( "skip" )
                        twoCount+=1
                        continue
                        
                    if ( str(onedevice['title']) == str(twodevice['title']) ) and ( onedevice['uuid'] == twodevice['uuid'] ):
                        printl( "match")
                        if onedevice['local'] == "1":
                            printl ( "popping 2 " + str(self.g_sections.pop(twoCount)))
                        else:
                            printl ( "popping 1 " + str(self.g_sections.pop(oneCount)))
                    else:
                        printl( "no match")
                    
                    twoCount+=1
                 
                oneCount+=1
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def appendEntry(self, sections, server):
        '''
        '''
        #printl("", self, "S")
        
        self.g_sections.append({'title':sections.get('title','Unknown').encode('utf-8'), 
                               'address': self.g_host + ":" + self.g_port,
                               'serverName' : self.g_name.encode('utf-8'),
                               'uuid' : sections.get('machineIdentifier','Unknown') ,
                               'path' : '/library/sections/' + sections.get('key') ,
                               'token' : sections.get('accessToken',None) ,
                               'location' : server['discovery'] ,
                               'art' : sections.get('art') ,
                               #'local' : sections.get('local') ,
                               'type' : sections.get('type','Unknown') }) 
   
        #printl("", self, "C")

    #=============================================================================
    # 
    #=============================================================================
    def getSectionFilter(self, p_url, p_mode, p_final): # CHECKED
        '''
        '''
        printl("", self, "S")
        printl("p_url: " + str(p_url), self, "I")
        printl("p_mode: " + str(p_mode), self, "I")
        printl("p_final: " + str(p_final), self, "I")
        
        #===>
        mainMenuList = []
        #===>
        
        html = self.getURL(p_url)   
        tree = etree.fromstring(html)
        directories = tree.getiterator("Directory")
        viewGroup = str(tree.get("viewGroup"))
        
        printl("directories: " + str(directories), self, "D")
        printl("viewGroup: " + str(viewGroup),self, "D")

        viewGroupTypes = { "all":p_mode,
                         "unwatched":p_mode,
                         "newest":p_mode,
                         "recentlyAdded":p_mode,
                         "recentlyViewed":p_mode,
                         "onDeck":p_mode,
                         "folder":p_mode,
                         "recentlyViewedShows":p_mode,
                         "collection": "secondary",
                         "genre":"secondary",
                         "year":"secondary",
                         "decade":"secondary",
                         "director":"secondary",
                         "actor":"secondary",
                         "country":"secondary",
                         "contentRating":"secondary",
                         "rating":"secondary",
                         "resolution":"secondary",
                         "firstCharacter":"secondary"
                      }        

        for sections in directories:   
            
            isSearchFilter = False
            #sample = <Directory prompt="Search Movies - Teens" search="1" key="search?type=1" title="Search..." />
            prompt = str(sections.get('prompt', 'noSearch')) 
            
            if prompt != "noSearch": # prompt for search string
                isSearchFilter = True
                t_url = p_url
                t_mode = str(p_mode)
            
            elif p_final == True:
                printl("final", self, "D" )
                t_mode = p_mode
            
            else:
                t_mode = viewGroupTypes[sections.get('key')]
            
            t_url = p_url + "/" + str(sections.get('key'))
            
            printl("t_url: " + str(t_url), self, "D")
            printl("t_mode: " + str(t_mode),self, "D")
            printl("isSearchFilter: " + str(isSearchFilter), self, "D")  
            
            params = {}
            params["t_url"] = t_url
            params["t_mode"] = str(p_mode)
            params["isSearchFilter"] =isSearchFilter
            
            if t_mode != "secondary": #means that the next answer is again a filter cirteria
                
                if t_mode == 'show' or t_mode == 'episode':
                    printl( "_MODE_TVSHOWS detected", self, "X")
                    mainMenuList.append((_(sections.get('title').encode('utf-8')), getPlugin("tvshows", Plugin.MENU_VIDEOS), params))
                        
                elif t_mode == 'movie':
                    printl( "_MODE_MOVIES detected", self, "X")
                    mainMenuList.append((_(sections.get('title').encode('utf-8')), getPlugin("movies", Plugin.MENU_VIDEOS), params))
    
                elif t_mode == 'artist':
                    printl( "_MODE_ARTISTS detected", self, "X")
                        
                elif t_mode == 'photo':
                    printl( "_MODE_PHOTOS detected", self, "X")
                
                else:
                    printl("Ignoring section " + str(sections.get('title').encode('utf-8')) + " of type " + str(sections.get('type')) + " as unable to process", self, "I")
                    continue
            else:
                params["t_final"] = True
                mainMenuList.append((_(sections.get('title').encode('utf-8')), Plugin.MENU_FILTER, params))

            t_url = None
        
        #printl("mainMenuList: " + str(mainMenuList), self, "D")
        printl("", self, "C")
        return mainMenuList  
 
    #===============================================================================
    # 
    #===============================================================================
    def addGUIItem(self, url, details, extraData, context=None, folder=True ):
        '''
        '''
        printl("", self, "S")
        #==============================================================================
 #       if details.get('title','') == '':
 #           
 #           printl("", self, "C")
 #           return
 #             
 #       if (extraData.get('token',None) is None) and _PARAM_TOKEN:
 #           extraData['token']=_PARAM_TOKEN
 # 
 #       aToken=self.getAuthDetails(extraData)
 #       qToken=self.getAuthDetails(extraData, prefix='?')
        #==============================================================================
        
        #==============================================================================
 #       #Create the URL to pass to the item
 #       if ( not folder) and ( extraData['type'] =="Picture" ):
 #           u=url+qToken
 #       else:
 #           u=sys.argv[0]+"?url="+str(url)+aToken
 # 
 #       printl("URL to use for listing: " + u)
        #==============================================================================
    
        content = (url, details, extraData, context)
        
        #printl("content = " + str(content), self, "D")
        printl("", self, "C")
        return content
    
    
    #===============================================================================
    # 
    #===============================================================================
    def getSectionUrl(self, address, path):
        '''
        '''
        printl("", self, "S")

        sectionUrl = 'http://%s%s' % ( address, path)
        
        printl("sectionUrl = " + sectionUrl, self, "D")
        printl("", self, "C")
        return sectionUrl

    #====================================================================
    # 
    #====================================================================
    def getAuthDetails(self, details, url_format=True, prefix="&" ): # CHECKED
        '''
            Takes the token and creates the required arguments to allow
            authentication.  This is really just a formatting tools
            @input: token as dict, style of output [opt] and prefix style [opt]
            @return: header string or header dict
        '''
        printl("", self, "S")
        
        token = details.get('token', None)
            
        if url_format:
            if token:
                printl("", self, "C")
                return prefix+"X-Plex-Token="+str(token)
            else:
                printl("", self, "C")
                return ""
        else:
            if token:
                printl("", self, "C")
                return {'X-Plex-Token' : token }
            else:
                printl("", self, "C")
                return {}

    #===================================================================
    # 
    #===================================================================
    def getMyPlexServers(self): # CHECKED
        '''
            Connect to the myplex service and get a list of all known
            servers.
            @input: nothing
            @return: a list of servers (as Dict)
        '''
        printl("", self, "S")
        
        printl("== ENTER: self.getMyPlexServers ==", False)
        
        tempServers=[]
        url_path="/pms/servers"
        
        html = self.getMyPlexURL(url_path)
        
        if html is False:
            return
            
        server=etree.fromstring(html).findall('Server')
        count=0
        for servers in server:
            data=dict(servers.items())
            
            if data.get('owned',None) == "1":
                if count == 0:
                    master=1
                    count=-1
                accessToken=self.getMyPlexToken()
            else:
                master='0'
                accessToken=data.get('accessToken',None)
            
            tempServers.append({'serverName': data['name'].encode('utf-8') ,
                                'address'   : data['address']+":"+data['port'] ,
                                'discovery' : 'myplex' , 
                                'token'     : accessToken ,
                                'uuid'      : data['machineIdentifier'] ,
                                'owned'     : data.get('owned',0) ,  
                                'master'    : master })
        
        printl("tempServers = " + tempServers, self, "C") 
        printl("", self, "C")                       
        return tempServers                         
        
    #===========================================================================
    # 
    #===========================================================================
    def getLocalServers(self): # CHECKED
        '''
            Connect to the defined local server (either direct or via bonjour discovery)
            and get a list of all known servers.
            @input: nothing
            @return: a list of servers (as Dict)
        '''
        printl("", self, "S")
    
        tempServers=[]
        url_path="/servers"
        html=False
        
        for local in self.g_serverDict:
        
            if local.get('discovery') == "local" or local.get('discovery') == "bonjour":
                html = self.getURL(local['address']+url_path)
                break
            
        if html is False:
            return tempServers
                 
        server=etree.fromstring(html).findall('Server')
        count=0
        for servers in server:
            data=dict(servers.items())
            
            if count == 0:
                master=1
            else:
                master=0
            
            tempServers.append({'serverName': data['name'].encode('utf-8') ,
                                'address'   : data['address']+":"+data['port'] ,
                                'discovery' : 'local' , 
                                'token'     : data.get('accessToken',None) ,
                                'uuid'      : data['machineIdentifier'] ,
                                'owned'     : '1' ,
                                'master'    : master })
    
            count+=1 
            
        printl("tempServers = " + str(tempServers), self, "C")
        printl("", self, "C")                   
        return tempServers                         

    #===============================================================================
    # 
    #===============================================================================
    def getMyPlexURL(self, url_path, renew=False, suppress=True ): # CHECKED
        '''
            Connect to the my.plexapp.com service and get an XML pages
            A seperate function is required as interfacing into myplex
            is slightly different than getting a standard URL
            @input: url to get, whether we need a new token, whether to display on screen err
            @return: an xml page as string or false
        '''
        printl("", self, "S")                
        printl("url = " + MYPLEX_SERVER + url_path, self, "D")
    
        try:
            conn = httplib.HTTPSConnection(MYPLEX_SERVER) 
            conn.request("GET", url_path+"?X-Plex-Token=" + self.getMyPlexToken(renew)) 
            data = conn.getresponse() 
            if ( int(data.status) == 401 )  and not ( renew ):
                return self.getMyPlexURL(url_path,True)
                
            if int(data.status) >= 400:
                error = "HTTP response error: " + str(data.status) + " " + str(data.reason)
                #===============================================================
                # if suppress is False:
                #    xbmcgui.Dialog().ok("Error",error)
                #===============================================================
                printl (error, self, "I")
                printl("", self, "C")
                return False
            elif int(data.status) == 301 and type == "HEAD":
                
                printl("", self, "C")
                return str(data.status)+"@"+data.getheader('Location')
            else:      
                link=data.read()
                
                printl("====== XML returned =======", self, "I")
                printl("link = " + link, self, "I")
                printl("====== XML finished ======", self, "I")
                
        except socket.gaierror :
            error = 'Unable to lookup host: ' + MYPLEX_SERVER + "\nCheck host name is correct"
            #===================================================================
            # if suppress is False:
            #    xbmcgui.Dialog().ok("Error",error)
            #===================================================================
            printl (error, self, "I")
            printl("", self, "C")
            return False
        except socket.error, msg : 
            error="Unable to connect to " + MYPLEX_SERVER +"\nReason: " + str(msg)
            #===================================================================
            # if suppress is False:
            #    xbmcgui.Dialog().ok("Error",error)
            #===================================================================
            printl (error, self, "I")
            printl("", self, "C")
            return False
        else:
            
            printl("", self, "C")
            return link

    #=============================================================================
    # 
    #=============================================================================
    def getMyPlexToken(self, renew=False ): # CHECKED
        '''
            Get the myplex token.  If the user ID stored with the token
            does not match the current userid, then get new token.  This stops old token
            being used if plex ID is changed. If token is unavailable, then get a new one
            @input: whether to get new token
            @return: myplex token
        '''
        printl("", self, "S")
        
        try:
            #user,token = (__settings__.getSetting('self.g_myplex_token')).split('|')
            user,token = self.g_myplex_token
        except:
            token=""
        
        #if ( token == "" ) or (renew) or (user != __settings__.getSetting('myplex_user')):
        if ( token == "" ) or (renew) or (user != self.g_myplex_username):
            token = self.getNewMyPlexToken()
        
        printl("Using token: " + str(token) + "[Renew: " + str(renew) + "]", self, "D")
        printl("", self, "C")
        return token

    #============================================================================
    # 
    #============================================================================
    def getNewMyPlexToken(self): # CHECKED
        '''
            Get a new myplex token from myplex API
            @input: nothing
            @return: myplex token
        '''
        printl("", self, "S")
    
        printl("Getting New token", self, "I")
        #=======================================================================
        # self.g_myplex_username = __settings__.getSetting('myplex_user')
        # self.g_myplex_password = __settings__.getSetting('myplex_pass')
        #=======================================================================
            
        if ( self.g_myplex_username or self.g_myplex_password ) == "":
            printl("No myplex details in config..", self, "I")
            printl("", self, "")
            return False
        
        base64string = base64.encodestring('%s:%s' % (self.g_myplex_username, self.g_myplex_password)).replace('\n', '')
        txdata=""
        token=False
        
        #=======================================================================
        # myplex_headers={'X-Plex-Platform': "XBMC",
        #            'X-Plex-Platform-Version': "11.00",
        #            'X-Plex-Provides': "player",
        #            'X-Plex-Product': "PleXBMC",
        #            'X-Plex-Version': "2.0b",
        #            'X-Plex-Device': "Not Known",
        #            'X-Plex-Client-Identifier': "PleXBMC",
        #            'Authorization': "Basic %s" % base64string }
        #=======================================================================
        
        myplex_headers={'X-Plex-Platform': "XBMC",
                        'X-Plex-Platform-Version': "11.00",
                        'X-Plex-Provides': "player",
                        'X-Plex-Product': "PleXBMC",
                        'X-Plex-Version': "2.0b",
                        'X-Plex-Device': "Not Known",
                        'X-Plex-Client-Identifier': "PleXBMC",
                        'Authorization': "Basic %s" % base64string }
        
        printl( "[MyTube] MyTubePlayerService - Starting auth request", self, "I")
        token = os.popen('curl -s -k -X POST "%s" -d "%s"' % ("https://" + MYPLEX_SERVER + "/users/sign_in.xml", urllib.urlencode(myplex_headers))).read()
        
    #===========================================================================
    #    try:
    #        conn = httplib.HTTPSConnection(MYPLEX_SERVER)
    #        conn.request("POST", "/users/sign_in.xml", txdata, myplex_headers) 
    #        data = conn.getresponse() 
    #   
    #        if int(data.status) == 201:      
    #            link=data.read()
    #            printl("====== XML returned =======")
    # 
    #            try:
    #                token=etree.fromstring(link).findtext('authentication-token')
    #                #===========================================================
    #                # __settings__.setSetting('self.g_myplex_token',self.g_myplex_username+"|"+token)
    #                #===========================================================
    #                self.g_myplex_token = self.g_myplex_username + "|" + token
    #                #todo add function call to save token in config
    #            except:
    #                printl(link)
    #            
    #            printl("====== XML finished ======")
    #        else:
    #            error = "HTTP response error: " + str(data.status) + " " + str(data.reason)
    #            #===============================================================
    #            # if suppress is False:
    #            #    xbmcgui.Dialog().ok(title,error)
    #            #===============================================================
    #            print error
    #            return False
    #    except socket.gaierror :
    #        #===================================================================
    #        # error = 'Unable to lookup host: ' + server + "\nCheck host name is correct"
    #        #===================================================================
    #        error = 'Unable to lookup host: ' + MYPLEX_SERVER + "\nCheck host name is correct"
    #        #===================================================================
    #        # if suppress is False:
    #        #    xbmcgui.Dialog().ok(title,error)
    #        #===================================================================
    #        print error
    #        return False
    #    except socket.error, msg : 
    #        #===================================================================
    #        # error="Unable to connect to " + server +"\nReason: " + str(msg)
    #        #===================================================================
    #        error="Unable to connect to " + MYPLEX_SERVER +"\nReason: " + str(msg)
    #        #===================================================================
    #        # if suppress is False:
    #        #    xbmcgui.Dialog().ok(title,error)
    #        #===================================================================
    #        print error
    #        return False
    #===========================================================================
        printl ("token = " + token, self, "D")
        printl("", self, "C")
        return token
 
    #============================================================================
    # 
    #============================================================================
    def getURL(self, url, suppress=True, type="GET", popup=0 ): # CHECKED
        '''
        '''
        printl("", self, "S")

        try:        
            if url[0:4] == "http":
                serversplit=2
                urlsplit=3
            else:
                serversplit=0
                urlsplit=1
                
            server=url.split('/')[serversplit]
            urlPath="/"+"/".join(url.split('/')[urlsplit:])
            
            printl("server: " + str(server), self, "D")
            printl("urlPath: " + str(urlPath), self, "D")
                
            authHeader = self.getAuthDetails({'token':_PARAM_TOKEN}, False)
                
            #===================================================================
            # printl("url = "+url)
            # printl("header = "+str(authHeader))
            #===================================================================
            conn = httplib.HTTPConnection(server) 
            conn.request(type, urlPath, headers=authHeader) 
            data = conn.getresponse() 
    
            if ( int(data.status) == 301 ) or ( int(data.status) == 302 ): 
                printl("status 301 or 302 found", self, "I")
                
                data = data.getheader('Location')
                printl("data: " + str(data), self, "I")
                
                printl("", self, "C")
                return data
    
            elif int(data.status) >= 400:
                error = "HTTP response error: " + str(data.status) + " " + str(data.reason)
                printl( error, self, "I")
                #===============================================================
                # if suppress is False:
                #    if popup == 0:
                #        xbmc.executebuiltin("XBMC.Notification(URL error: "+ str(data.reason) +",)")
                #    else:
                #        xbmcgui.Dialog().ok("Error",server)
                #===============================================================
                
                printl("", self, "C")
                return False
            
            else:   
                link=data.read()
                
                #printl("====== XML returned =======", self, "D")
                #printl("data: " + link, self, "D")
                #printl("====== XML finished ======", self, "D")
                
                printl("", self, "C")
                return link
        
        except socket.gaierror :
            error = 'Unable to lookup host: ' + server + "\nCheck host name is correct"
            #===================================================================
            # if suppress is False:
            #    if popup==0:
            #        xbmc.executebuiltin("XBMC.Notification(\"DreamPlex\": URL error: Unable to find server,)")
            #    else:
            #        xbmcgui.Dialog().ok("","Unable to contact host")
            #===================================================================
            printl( error, self, "I")
            
            printl("", self, "C")
            return False
        
        except socket.error, msg : 
            error="Unable to connect to " + server +"\nReason: " + str(msg)
            #===================================================================
            # if suppress is False:
            #    if popup == 0:
            #        xbmc.executebuiltin("XBMC.Notification(\"DreamPlex\": URL error: Unable to connect to server,)")
            #    else:
            #        xbmcgui.Dialog().ok("","Unable to connect to host")
            #===================================================================
            printl( error, self, "I")
            printl("", self, "C")
            return False
   
    #========================================================================
    # 
    #========================================================================
    def mediaType(self, partData, server, dvdplayback=False ): # CHECKED
        '''
        '''
        printl("", self, "S")   
        stream = partData['key']
        file = partData['file']
        
        #First determine what sort of 'file' file is
        printl("physical file location: " + file, self, "I")   
        if file[0:2] == "\\\\":
            printl("Looks like a UNC",self, "I")
            type="UNC"
        elif file[0:1] == "/" or file[0:1] == "\\":
            printl("looks like a unix file", self, "I")
            type="nixfile"
        elif file[1:3] == ":\\" or file[1:2] == ":/":
            printl("looks like a windows file", self, "I")
            type="winfile"
        else:
            printl("uknown file type", self, "I")
            printl("file = " + str(file),self, "I")
            type="notsure"
        
        # 0 is auto select.  basically check for local file first, then stream if not found
        if self.g_stream == "0":
            #check if the file can be found locally
            if type == "nixfile" or type == "winfile":
                try:
                    printl("Checking for local file", self, "I")
                    exists = open(file, 'r')
                    printl("Local file found, will use this", self, "I")
                    exists.close()
                    
                    printl("", self, "C")
                    return "file:"+file
                except: 
                    pass
                    
            printl("No local file", self, "I")
            #===================================================================
            # global self.g_stream
            #===================================================================
            if dvdplayback:
                printl("Forcing SMB for DVD playback", self, "I")
                self.g_stream="2"
            else:
                self.g_stream="1"
            
        # 1 is stream no matter what
        if self.g_stream == "1":
            printl( "Selecting stream", self, "I")
            printl("", self, "C")
            return "http://"+server+stream
            
        # 2 is use SMB 
        elif self.g_stream == "2" or self.g_stream == "3":
            if self.g_stream == "2":
                protocol="smb"
            else:
                protocol="afp"
                
            printl( "Selecting smb/unc")
            if type=="UNC":
                filelocation=protocol+":"+file.replace("\\","/")
            else:
                #Might be OSX type, in which case, remove Volumes and replace with server
                server=server.split(':')[0]
                loginstring=""
    
                if self.g_nasoverride == "true":
                    if not self.g_nasoverrideip == "":
                        server=self.g_nasoverrideip
                        printl("Overriding server with: " + server, self, "I")
                        
                    #===========================================================
                    # nasuser = __settings__.getSetting('self.g_nasuserid')
                    #===========================================================
                    nasuser = self.g_nasuserid
                    if not nasuser == "":
                        #=======================================================
                        # loginstring=__settings__.getSetting('self.g_nasuserid')+":"+__settings__.getSetting('naspass')+"@"
                        #=======================================================
                        loginstring = self.g_nasuserid +":"+ self.g_naspass + "@"
                        printl("Adding AFP/SMB login info for user " + nasuser, self, "I")
                    
                    
                if file.find('Volumes') > 0:
                    filelocation=protocol+":/"+file.replace("Volumes",loginstring+server)
                else:
                    if type == "winfile":
                        filelocation=protocol+"://"+loginstring+server+"/"+file[3:]
                    else:
                        #else assume its a file local to server available over smb/samba (now we have linux PMS).  Add server name to file path.
                        filelocation=protocol+"://"+loginstring+server+file
                        
            if self.g_nasoverride == "true" and self.g_nasroot != "":
                #Re-root the file path
                printl("Altering path " + filelocation + " so root is: " +  self.g_nasroot, self, "I")
                if '/'+self.g_nasroot+'/' in filelocation:
                    components = filelocation.split('/')
                    index = components.index(self.g_nasroot)
                    for i in range(3,index):
                        components.pop(3)
                    filelocation='/'.join(components)
        else:
            printl( "No option detected, streaming is safest to choose", self, "I" )       
            filelocation="http://"+server+stream
        
        printl("Returning URL: " + filelocation, self, "I")
        printl("", self, "C")
        return filelocation
    
    
            
    #===========================================================================
    # 
    #===========================================================================
    def getMoviesFromSection(self, url, tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        printl("url: " + str(url), self, "D")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'movies')
        #=======================================================================
                
        #get the server name from the URL, which was passed via the on screen listing..
        if tree is None:
            #Get some XML and parse it
            html=self.getURL(url)
            
            if html is False:
                return
                
            tree = etree.fromstring(html)
    
        server=self.getServerFromURL(url)
                        
        randomNumber=str(random.randint(1000000000,9999999999))   
        #Find all the video tags, as they contain the data we need to link to a file.
        MovieTags=tree.findall('Video')
        
        
        fullList=[]
        
        for movie in MovieTags:
            
            #===================================================================
            # self.movieTag(url, server, tree, movie, randomNumber)
            #===================================================================
            
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
            #===>
            #Right, add that link...and loop around for another entry
            content = self.movieTag(url, server, tree, movie, randomNumber)
            #printl ("-> " + str(content), self)
            fullList.append(content)
            #printl ("-> " + str(result), self)
            #===>
        
        #printl ("fullList = " + str(fullList), self, "D")
        printl("", self, "C")
        return fullList
     
    #=======================================================================
    # 
    #=======================================================================
    def getShowsFromSection(self, url, tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'getShowsFromSection')
        #=======================================================================
                
        #Get the URL and server name.  Get the XML and parse
        if tree is None:
            html=self.getURL(url)
        
            if html is False:
                return
    
            tree=etree.fromstring(html)
    
        server=self.getServerFromURL(url)
    
        #For each directory tag we find
        ShowTags=tree.findall('Directory') 
        
        fullList=[]
        
        for show in ShowTags:
    
            tempgenre=[]
            
            for child in show:
                tempgenre.append(child.get('tag',''))
                
            watched=int(show.get('viewedLeafCount',0))
            
            #Create the basic data structures to pass up
            details={'title'      : show.get('title','Unknown').encode('utf-8') ,
                     'tvshowname' : show.get('title','Unknown').encode('utf-8') ,
                     'studio'     : show.get('studio','') ,
                     'plot'       : show.get('summary','') ,
                     'overlay'    : _OVERLAY_XBMC_UNWATCHED ,
                     'playcount'  : 0 , 
                     'season'     : 0 ,
                     'episode'    : int(show.get('leafCount',0)) ,
                     'mpaa'       : show.get('contentRating','') ,
                     'aired'      : show.get('originallyAvailableAt','') ,
                     'server'    : str(server) ,
                     'genre'      : " / ".join(tempgenre) }
                     
            extraData={'type'              : 'video' ,
                       'WatchedEpisodes'   : watched ,
                       'UnWatchedEpisodes' : details['episode'] - watched ,
                       'thumb'             : self.getThumb(show, server) ,
                       'fanart_image'      : self.getFanart(show, server) ,
                       'token'             : _PARAM_TOKEN ,
                       'key'               : show.get('key','') ,
                       'server'            : str(server) ,
                       'ratingKey'         : str(show.get('ratingKey',0)) }
    
            #banner art
            if show.get('banner',None) is not None:
                extraData['banner']='http://'+server+show.get('banner').split('?')[0]+"/banner.jpg"
             
            #===================================================================
            # #Set up overlays for watched and unwatched episodes
            # if extraData['WatchedEpisodes'] == 0:
            #    if g_skinwatched == "DreamPlex":
            #        details['overlay']=_OVERLAY_PLEX_UNWATCHED   
            # elif extraData['UnWatchedEpisodes'] == 0: 
            #    if g_skinwatched == "xbmc":
            #        details['overlay']=_OVERLAY_XBMC_WATCHED   
            #    elif g_skinwatched == "DreamPlex":
            #        details['overlay']=_OVERLAY_PLEX_WATCHED   
            # else:
            #    if g_skinwatched == "DreamPlex":
            #        details['overlay'] = _OVERLAY_PLEX_PARTIAL
            #===================================================================
            
            #Create URL based on whether we are going to flatten the season view
            if self.g_flatten == "2":
                printl("Flattening all shows", self, "I")
                u='http://%s%s&mode=%s'  % ( server, extraData['key'].replace("children","allLeaves"), str(_MODE_TVEPISODES))
            else:
                u='http://%s%s&mode=%s'  % ( server, extraData['key'], str(_MODE_getSeasonsOfShow))
                
            if self.g_skipcontext == "false":
                context=self.buildContextMenu(url, extraData)
            else:
                context=None
                
        #=======================================================================
        #    self.addGUIItem(u,details,extraData, context) 
        #    
        # #End the listing    
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
            #===>
            #Right, add that link...and loop around for another entry
            content = self.addGUIItem(u,details,extraData, context)
            printl ("-> " + str(content), self, "D")
            fullList.append(content)
            #printl ("-> " + str(result), self)
            #===>
    
        #printl ("fullList = " + fullList, self, "D")
        printl("", self, "C")
        return fullList
 
    #===========================================================================
    # 
    #===========================================================================
    def getSeasonsOfShow(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'seasons')
        #=======================================================================
    
        #Get URL, XML and parse
        server=self.getServerFromURL(url)
        html=self.getURL(url)
        
        if html is False:
            return
       
        tree=etree.fromstring(html)
        
        willFlatten=False
        if self.g_flatten == "1":
            #check for a single season
            if int(tree.get('size',0)) == 1:
                printl("Flattening single season show", self, "I")
                willFlatten=True
        
        sectionart=self.getFanart(tree, server)
              
        #For all the directory tags
        SeasonTags=tree.findall('Directory')
        
        fullList=[]
        
        for season in SeasonTags:
    
            if willFlatten:
                url='http://'+server+season.get('key')
                self.getEpisodesOfSeason(url)
                return
            
            watched=int(season.get('viewedLeafCount',0))
        
            #Create the basic data structures to pass up
            details={'title'      : season.get('title','Unknown').encode('utf-8') ,
                     'tvshowname' : season.get('title','Unknown').encode('utf-8') ,
                     'studio'     : season.get('studio','') ,
                     'plot'       : season.get('summary','') ,
                     'overlay'    : _OVERLAY_XBMC_UNWATCHED ,
                     'playcount'  : 0 , 
                     'season'     : 0 ,
                     'episode'    : int(season.get('leafCount',0)) ,
                     'mpaa'       : season.get('contentRating','') ,
                     'server'     : str(server) ,
                     'aired'      : season.get('originallyAvailableAt','') }
                     
            extraData={'type'              : 'video' ,
                       'WatchedEpisodes'   : watched ,
                       'UnWatchedEpisodes' : details['episode'] - watched ,
                       'thumb'             : self.getThumb(season, server) ,
                       'fanart_image'      : self.getFanart(season, server) ,
                       'token'             : _PARAM_TOKEN ,
                       'key'               : season.get('key','') ,
                       'server'            : str(server) ,
                       'ratingKey'         : str(season.get('ratingKey',0)) }
                         
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=sectionart
    
            #===================================================================
            # #Set up overlays for watched and unwatched episodes
            # if extraData['WatchedEpisodes'] == 0:
            #    if g_skinwatched == "DreamPlex":
            #        details['overlay']=_OVERLAY_PLEX_UNWATCHED   
            # elif extraData['UnWatchedEpisodes'] == 0: 
            #    if g_skinwatched == "xbmc":
            #        details['overlay']=_OVERLAY_XBMC_WATCHED   
            #    elif g_skinwatched == "DreamPlex":
            #        details['overlay']=_OVERLAY_PLEX_WATCHED   
            # else:
            #    if g_skinwatched == "DreamPlex":
            #        details['overlay'] = _OVERLAY_PLEX_PARTIAL
            #===================================================================
                
            url='http://%s%s&mode=%s' % ( server , extraData['key'], str(_MODE_TVEPISODES) )
    
            if self.g_skipcontext == "false":
                context=self.buildContextMenu(url, season)
            else:
                context=None
                
        #=======================================================================
        #    #Build the screen directory listing
        #    self.addGUIItem(url,details,extraData, context) 
        #    
        # #All done, so end the listing
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
            #===>
            #Right, add that link...and loop around for another entry
            content = self.addGUIItem(url, details, extraData, context)
            #printl ("-> " + str(content), self)
            fullList.append(content)
            #printl ("-> " + str(result), self)
            #===>
    
        #printl ("fullList = " + fullList, self, "D")
        printl("", self, "C")
        return fullList
    
    #===============================================================================
    # 
    #===============================================================================
    def getEpisodesOfSeason(self, url, tree=None ): # CHECKED    
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'episodes')
        #=======================================================================
                    
        if tree is None:
            #Get URL, XML and Parse
            html=self.getURL(url)
            
            if html is False:
                return
            
            tree=etree.fromstring(html)
        
        ShowTags=tree.findall('Video')
        server=self.getServerFromURL(url)
        
        if self.g_skipimages == "false":        
            sectionart=self.getFanart(tree, server)
         
        randomNumber=str(random.randint(1000000000,9999999999))   
        
        fullList=[]
         
        for episode in ShowTags:
            tempgenre=[]
            tempcast=[]
            tempdir=[]
            tempwriter=[]
            
            for child in episode:
                if child.tag == "Media":
                    mediaarguments = dict(child.items())
                elif child.tag == "Genre" and self.g_skipmetadata == "false":
                    tempgenre.append(child.get('tag'))
                elif child.tag == "Writer"  and self.g_skipmetadata == "false":
                    tempwriter.append(child.get('tag'))
                elif child.tag == "Director"  and self.g_skipmetadata == "false":
                    tempdir.append(child.get('tag'))
                elif child.tag == "Role"  and self.g_skipmetadata == "false":
                    tempcast.append(child.get('tag'))
            
            printl("Media attributes are " + str(mediaarguments), self, "I")
                                        
            #Gather some data 
            view_offset = episode.get('viewOffset',0)
            duration=int(mediaarguments.get('duration',episode.get('duration',0)))/1000
                                   
            #Required listItem entries for XBMC
            details={'plot'        : episode.get('summary','') ,
                     'title'       : episode.get('title','Unknown').encode('utf-8') ,
                     'playcount'   : int(episode.get('viewCount',0)) ,
                     'rating'      : float(episode.get('rating',0)) ,
                     'studio'      : episode.get('studio',tree.get('studio','')) ,
                     'mpaa'        : episode.get('contentRating', tree.get('grandparentContentRating','')) ,
                     'year'        : int(episode.get('year',0)) ,
                     'tagline'     : episode.get('tagline','') ,
                     'duration'    : str(datetime.timedelta(seconds=duration)) ,
                     'overlay'     : _OVERLAY_XBMC_UNWATCHED ,
                     'episode'     : int(episode.get('index',0)) ,
                     'aired'       : episode.get('originallyAvailableAt','') ,
                     'tvshowtitle' : episode.get('grandparentTitle',tree.get('grandparentTitle','')) ,
                     'server'      : str(server) ,
                     'season'      : episode.get('parentIndex',tree.get('parentIndex',0)) }
    
            details['title'] = str(details['episode']).zfill(2) + ". " + details['title']
                     
            if tree.get('mixedParents',0) == 1:
                details['title'] = details['tvshowtitle'] + ": " + details['title']
            
            #Extra data required to manage other properties
            extraData={'type'         : "Video" ,
                       'thumb'        : self.getThumb(episode, server) ,
                       'fanart_image' : self.getFanart(episode, server) ,
                       'token'        : _PARAM_TOKEN ,
                       'key'          : episode.get('key',''),
                       'server'       : str(server) ,
                       'ratingKey'    : str(episode.get('ratingKey',0)) }
    
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=sectionart
                              
            #===================================================================
            # #Determine what tupe of watched flag [overlay] to use
            # if details['playcount'] > 0:
            #    if g_skinwatched == "xbmc":
            #        details['overlay']=_OVERLAY_XBMC_WATCHED
            #    elif g_skinwatched == "DreamPlex":
            #        details['overlay']=_OVERLAY_PLEX_WATCHED
            # else: #if details['playcount'] == 0: 
            #    if g_skinwatched == "DreamPlex":
            #        details['overlay']=_OVERLAY_PLEX_UNWATCHED
            # 
            # if g_skinwatched == "DreamPlex" and int(view_offset) > 0:
            #    details['overlay'] = _OVERLAY_PLEX_PARTIAL
            #===================================================================
            
            #Extended Metadata
            if self.g_skipmetadata == "false":
                details['cast']     = tempcast
                details['director'] = " / ".join(tempdir)
                details['writer']   = " / ".join(tempwriter)
                details['genre']    = " / ".join(tempgenre)
                 
            #Add extra media flag data
            if self.g_skipmediaflags == "false":
                extraData['VideoResolution'] = mediaarguments.get('videoResolution','')
                extraData['VideoCodec']      = mediaarguments.get('videoCodec','')
                extraData['AudioCodec']      = mediaarguments.get('audioCodec','')
                extraData['AudioChannels']   = mediaarguments.get('audioChannels','')
                extraData['VideoAspect']     = mediaarguments.get('aspectRatio','')
    
            #Build any specific context menu entries
            if self.g_skipcontext == "false":
                context=self.buildContextMenu(url, extraData)    
            else:
                context=None
            
            # http:// <server> <path> &mode=<mode> &id=<media_id> &t=<rnd>
            u="http://%s%s&mode=%s&id=%s&t=%s" % (server, extraData['key'], _MODE_PLAYLIBRARY, extraData['ratingKey'], randomNumber)
    
        #=======================================================================
        #    self.addGUIItem(u,details,extraData, context, folder=False)        
        # 
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
            #===>
            #Right, add that link...and loop around for another entry
            content = self.addGUIItem(url, details, extraData, context)
            #printl ("-> " + str(content), self)
            fullList.append(content)
            #printl ("-> " + str(result), self)
            #===>
    
        #printl ("fullList = " + fullList, self, "D")
        printl("", self, "C")
        return fullList
 
    #===========================================================================
    # 
    #===========================================================================
    def getAudioSubtitlesMedia(self, server, id ): # CHECKED
        '''
        '''
        printl("", self, "S")
        printl("Gather media stream info", self, "I" ) 
                
        #get metadata for audio and subtitle
        suburl="http://"+server+"/library/metadata/"+id
                
        html=self.getURL(suburl)
        tree=etree.fromstring(html)
    
        parts=[]
        partsCount=0
        subtitle={}
        subCount=0
        audio={}
        audioCount=0
        external={}
        media={}
        subOffset=-1
        audioOffset=-1
        selectedSubOffset=-1
        selectedAudioOffset=-1
        
        timings = tree.find('Video')
    
        media['viewOffset']=timings.get('viewOffset',0)       
        media['duration']=timings.get('duration',0)
        
        options = tree.getiterator('Part')    
        
        contents="type"
        
        #Get the Parts info for media type and source selection 
        for stuff in options:
            try:
                bits=stuff.get('key'), stuff.get('file')
                parts.append(bits)
                partsCount += 1
            except: pass
            
        if self.g_streamControl == "1" or self.g_streamControl == "2":
    
            contents="all"
            tags=tree.getiterator('Stream')
            
            for bits in tags:
                stream=dict(bits.items())
                if stream['streamType'] == '2':
                    audioCount += 1
                    audioOffset += 1
                    try:
                        if stream['selected'] == "1":
                            printl("Found preferred audio id: " + str(stream['id']), self, "I" ) 
                            audio=stream
                            selectedAudioOffset=audioOffset
                    except: pass
                         
                elif stream['streamType'] == '3':
                    subOffset += 1
                    try:
                        if stream['key']:
                            printl( "Found external subtitles id : " + str(stream['id']),self, "I")
                            external=stream
                            external['key']='http://'+server+external['key']
                    except: 
                        #Otherwise it's probably embedded
                        try:
                            if stream['selected'] == "1":
                                printl( "Found preferred subtitles id : " + str(stream['id']), self, "I")
                                subCount += 1
                                subtitle=stream
                                selectedSubOffset=subOffset
                        except: pass
              
        else:
                printl( "Stream selection is set OFF", self, "I")
                  
        
        streamData={'contents'   : contents ,
                    'audio'      : audio , 
                    'audioCount' : audioCount , 
                    'subtitle'   : subtitle , 
                    'subCount'   : subCount ,
                    'external'   : external , 
                    'parts'      : parts , 
                    'partsCount' : partsCount , 
                    'media'      : media , 
                    'subOffset'  : selectedSubOffset , 
                    'audioOffset': selectedAudioOffset }
        
        printl ("streamData = " + str(streamData), self, "D" )
        printl("", self, "C")
        return streamData
    
    #========================================================================
    # 
    #========================================================================
    def playLibraryMedia(self, id, vids, override=False ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        self.getTranscodeSettings(override)
      
        server = self.getServerFromURL(vids)
        
        streams=self.getAudioSubtitlesMedia(server,id)     
        url = self.selectMedia(streams['partsCount'],streams['parts'], server)
        
        #=======================================================================
        # #so läufts aber mal sehen ob wir das hinbekommen ohne das wir etliche zeile code zu überspringen
        # test = url
        # printl("TEST URL: " + test, False)
        #=======================================================================
    
        if url is None:
            return
            
        protocol=url.split(':',1)[0]
    
        if protocol == "file":
            printl( "We are playing a local file", self, "I")
            playurl=url.split(':',1)[1]
        elif protocol == "http":
            printl( "We are playing a stream", self, "I")
            if self.g_transcode == "true":
                printl( "We will be transcoding the stream", self, "I")
                playurl = self.transcode(id,url)+self.getAuthDetails({'token':_PARAM_TOKEN})
    
            else:
                playurl=url+self.getAuthDetails({'token':_PARAM_TOKEN},prefix="?")
        else:
            playurl=url
    
        try:
            resume=int(int(streams['media']['viewOffset']))
        except:
            resume=0
        
        printl("Resume has been set to " + str(resume),self, "I")
        
        #=======================================================================
        # item = xbmcgui.ListItem(path=playurl)
        #=======================================================================
        result=1
    
        if resume > 0:       
            #===================================================================
            # displayTime = str(datetime.timedelta(seconds=int(resume)))
            # dialogOptions = [ "Resume from " + displayTime , "Start from beginning"]
            # printl( "We have part way through video.  Display resume dialog")
            # startTime = xbmcgui.Dialog()
            # result = startTime.select('Resuming playback..',dialogOptions)
            #===================================================================
    
            if result == -1:
                printl("", self, "C")
                return
        
    #===========================================================================
    #    printl("handle is " + str(pluginhandle))
    #    #item.setProperty('ResumeTime', '300' )
    #    #item.setProperty('TotalTime', '1200' )
    # 
    #    if override:
    #        start=xbmc.Player().play(listitem=item)
    #    else:
    #        start = xbmcplugin.setResolvedUrl(pluginhandle, True, item)
    #    
    #    #Set a loop to wait for positive confirmation of playback
    #    count = 0
    #    while not xbmc.Player().isPlaying():
    #        printl( "Not playing yet...sleep for 2")
    #        count = count + 2
    #        if count >= 20:
    #            return
    #        else:
    #            time.sleep(2)
    #               
    #    #If we get this far, then XBMC must be playing
    #    
    #    #If the user chose to resume...
    #    if result == 0:
    #        #Need to skip forward (seconds)
    #        printl("Seeking to " + str(resume))
    #        xbmc.Player().pause()
    #        xbmc.Player().seekTime((resume)) 
    #        time.sleep(1)
    #        seek=xbmc.Player().getTime()
    # 
    #        while not ((seek - 10) < resume < (seek + 10)):
    #            printl( "Do not appear to have seeked correctly. Try again")
    #            xbmc.Player().seekTime((resume)) 
    #            time.sleep(1)
    #            seek=xbmc.Player().getTime()
    #        
    #        xbmc.Player().pause()
    #===========================================================================
    
        if not (self.g_transcode == "true" ): 
            self.setAudioSubtitles(streams)
     
        self.monitorPlayback(id,server)
        
        #TODO return playurl
        #=======================================================================
        # printl("TEST URL: " + test, False)
        #=======================================================================
        printl("PLAYURL => " + playurl, self, "I")
        printl("RESUME => " + str(resume), self, "I")
        printl("", self, "C")
        
        playerData = {}
        playerData["playUrl"] = playurl
        playerData["resumeStamp"] = resume
        playerData["server"] = server
        playerData["id"] = id
        
        return playerData
    
    #===========================================================================
    # 
    #===========================================================================
    def setAudioSubtitles(self, stream ): # CHECKED
        '''
        '''
        printl("", self, "S")
            
        if stream['contents'] == "type":
            printl ("No streams to process.", self, "I")
            
            if self.g_streamControl == "3":
                #===============================================================
                # xbmc.Player().showSubtitles(False)    
                #===============================================================
                printl ("All subs disabled", self, "I")
            
            printl("", self, "C")   
            return True
    
        if self.g_streamControl == "1" or  self.g_streamControl == "2":
            audio=stream['audio']
            printl("Attempting to set Audio Stream", self, "I")
            #Audio Stream first        
            if stream['audioCount'] == 1:
                printl ("Only one audio stream present - will leave as default", self, "I")
            elif stream['audioCount'] > 1:
                printl ("Multiple audio stream. Attempting to set to local language", self, "I")
                try:
                    if audio['selected'] == "1":
                        printl ("Found preferred language at index " + str(stream['audioOffset']), self, "I")
                        #=======================================================
                        # xbmc.Player().setAudioStream(stream['audioOffset'])
                        #=======================================================
                        printl ("Audio set", self, "I")
                except: pass
          
        #Try and set embedded subtitles
        if self.g_streamControl == "1":
            subtitle=stream['subtitle']
            printl("Attempting to set subtitle Stream", self, "I")
            try:
                if stream['subCount'] > 0 and subtitle['languageCode']:
                    printl ("Found embedded subtitle for local language", self, "I" )
                    printl ("Enabling embedded subtitles", self, "I")
                    #===========================================================
                    # xbmc.Player().showSubtitles(False)
                    # xbmc.Player().setSubtitleStream(stream['subOffset'])
                    #===========================================================
                    printl("", self, "C")   
                    return True
                else:
                    printl ("No embedded subtitles to set", self, "I")
            except:
                printl("Unable to set subtitles", self, "I")
      
        if self.g_streamControl == "1" or self.g_streamControl == "2":
            external=stream['external']
            printl("Attempting to set external subtitle stream", self, "I")
        
            try:   
                if external:
                    try:
                        printl ("External of type ["+external['codec']+"]", self, "I")
                        if external['codec'] == "idx" or external['codec'] =="sub":
                            printl ("Skipping IDX/SUB pair - not supported yet", self, "I")
                        else:    
                            #===================================================
                            # xbmc.Player().setSubtitles(external['key'])
                            #===================================================
                            printl("", self, "C")   
                            return True
                    except: pass                    
                else:
                    printl ("No external subtitles available. Will turn off subs", self, "I")
            except:
                printl ("No External subs to set", self, "I")
                
        #=======================================================================
        # xbmc.Player().showSubtitles(False)    
        #=======================================================================
        printl("", self, "C")   
        return False
            
    #===============================================================================
    # 
    #===============================================================================
    def codeToCountry(self, id ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        languages = { "None": "none"            ,
                    "alb" : "Albanian"          ,
                    "ara" : "Arabic"            ,
                    "arm" : "Belarusian"        ,
                    "bos" : "Bosnian"           ,
                    "bul" : "Bulgarian"         ,
                    "cat" : "Catalan"           ,
                    "chi" : "Chinese"           ,
                    "hrv" : "Croatian"          ,
                    "cze" : "Czech"             ,
                    "dan" : "Danish"            ,
                    "dut" : "Dutch"             ,
                    "eng" : "English"           ,
                    "epo" : "Esperanto"         ,
                    "est" : "Estonian"          ,
                    "per" : "Farsi"             ,
                    "fin" : "Finnish"           ,
                    "fre" : "French"            ,
                    "glg" : "Galician"          ,
                    "geo" : "Georgian"          ,
                    "ger" : "German"            ,
                    "ell" : "Greek"             ,
                    "heb" : "Hebrew"            ,
                    "hin" : "Hindi"             ,
                    "hun" : "Hungarian"         ,
                    "ice" : "Icelandic"         ,
                    "ind" : "Indonesian"        ,
                    "ita" : "Italian"           ,
                    "jpn" : "Japanese"          ,
                    "kaz" : "Kazakh"            ,
                    "kor" : "Korean"            ,
                    "lav" : "Latvian"           ,
                    "lit" : "Lithuanian"        ,
                    "ltz" : "Luxembourgish"     ,
                    "mac" : "Macedonian"        ,
                    "may" : "Malay"             ,
                    "nor" : "Norwegian"         ,
                    "oci" : "Occitan"           ,
                    "pol" : "Polish"            ,
                    "por" : "Portuguese"        ,
                    "pob" : "Portuguese (Brazil)" ,
                    "rum" : "Romanian"          ,
                    "rus" : "Russian"           ,
                    "scc" : "SerbianLatin"      ,
                    "scc" : "Serbian"           ,
                    "slo" : "Slovak"            ,
                    "slv" : "Slovenian"         ,
                    "spa" : "Spanish"           ,
                    "swe" : "Swedish"           ,
                    "syr" : "Syriac"            ,
                    "tha" : "Thai"              ,
                    "tur" : "Turkish"           ,
                    "ukr" : "Ukrainian"         ,
                    "urd" : "Urdu"              ,
                    "vie" : "Vietnamese"        ,
                    "all" : "All" }
        
        printl("", self, "C")   
        return languages[ id ]        
 
    #===========================================================
    # 
    #===========================================================
    def selectMedia(self, count, options, server ):   # CHECKED
        '''
        '''
        printl("", self, "S")
        
        #if we have two or more files for the same movie, then present a screen
        result=0
        dvdplayback=False
        
        if count > 1:
            printl("count higher than 1 SOLVE THIS", self, "I") 
    #==========================================================================
    #       dialogOptions=[]
    #       dvdIndex=[]
    #       indexCount=0
    #       for items in options:
    # 
    #           name=items[1].split('/')[-1]
    #       
    #           if self.g_forcedvd == "true":
    #               if '.ifo' in name.lower():
    #                   printl( "Found IFO DVD file in " + name )
    #                   name="DVD Image"
    #                   dvdIndex.append(indexCount)
    #                   
    #           dialogOptions.append(name)
    #           indexCount+=1
    #   
    #       printl("Create selection dialog box - we have a decision to make!") 
    #       startTime = xbmcgui.Dialog()
    #       result = startTime.select('Select media to play',dialogOptions)
    #       if result == -1:
    #           return None
    #       
    #       if result in dvdIndex:
    #           printl( "DVD Media selected")
    #           dvdplayback=True
    #==========================================================================
         
        else:
            if self.g_forcedvd == "true":
                if '.ifo' in options[result]:
                    dvdplayback=True
       
        newurl=self.mediaType({'key': options[result][0] , 'file' : options[result][1]},server,dvdplayback)
       
        printl("We have selected media at " + newurl, self, "I")
        printl("", self, "C")   
        return newurl

    #=================================================================
    # 
    #=================================================================
    def remove_html_tags(self, data): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        p = re.compile(r'<.*?>')
        
        printl("", self, "C")   
        return p.sub('', data)

    #===============================================================================
    # 
    #===============================================================================
    def monitorPlayback(self, id, server ): # CHECKED
        '''
        '''
        printl("", self, "S")

    #===========================================================================
    # 
    #    if len(server.split(':')) == 1:
    #        server=server
    #        
    #    monitorCount = 0
    #    progress = 0
    #    complete = 0
    #    #Whilst the file is playing back
    #    while xbmc.Player().isPlaying():
    #        #Get the current playback time
    #      
    #        currentTime = int(xbmc.Player().getTime())
    #        totalTime = int(xbmc.Player().getTotalTime())
    #        try:      
    #            progress = int(( float(currentTime) / float(totalTime) ) * 100)
    #        except:
    #            progress = 0
    #        
    #        if currentTime < 30:
    #            printl("Less that 30 seconds, will not set resume")
    #        
    #        #If we are less than 95% completem, store resume time
    #        elif progress < 95:
    #            printl( "self.Movies played time: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress) )
    #            self.getURL("http://"+server+"/:/progress?key="+id+"&identifier=com.plexapp.plugins.library&time="+str(currentTime*1000),suppress=True)
    #            complete=0
    # 
    #        #Otherwise, mark as watched
    #        else:
    #            if complete == 0:
    #                printl( "Movie marked as watched. Over 95% complete")
    #                self.getURL("http://"+server+"/:/scrobble?key="+id+"&identifier=com.plexapp.plugins.library",suppress=True)
    #                complete=1
    # 
    #        time.sleep(5)
    #          
    #    #If we get this far, playback has stopped
    #    printl("Playback Stopped")
    #    
    #    if self.g_sessionID is not None:
    #        printl("Stopping PMS self.transcode job with session " + self.g_sessionID)
    #        stopURL='http://'+server+'/video/:/self.transcode/segmented/stop?session='+self.g_sessionID          
    #        html=self.getURL(stopURL)
    #===========================================================================
        printl("", self, "C")       
        return
     
    #============================================================================
    # 
    #============================================================================
    def PLAY(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
              
        if url[0:4] == "file":
            printl( "We are playing a local file")
            #Split out the path from the URL
            playurl=url.split(':',1)[1]
        elif url[0:4] == "http":
            printl( "We are playing a stream", self, "I")
            if '?' in url:
                playurl=url+self.getAuthDetails({'token':_PARAM_TOKEN})
            else:
                playurl=url+self.getAuthDetails({'token':_PARAM_TOKEN},prefix="?")
        else:
            playurl=url
      
        #===================================================================
        # item = xbmcgui.ListItem(path=playurl)
        # return xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        #===================================================================
        printl("", self, "C")   
        return playurl
    
    #===============================================================================
    # 
    #===============================================================================
    def videoPluginPlay(self, vids, prefix=None ): # CHECKED
        '''
            Plays Plugin Videos, which do not require library feedback 
            but require further processing
            @input: url of video, plugin identifier
            @return: nothing. End of Script
        '''
        printl("", self, "S")
               
        server=self.getServerFromURL(vids)
        
        #If we find the url lookup service, then we probably have a standard plugin, but possibly with resolution choices
        if '/services/url/lookup' in vids:
            printl("URL Lookup service", self, "I")
            html=self.getURL(vids, suppress=False)
            if not html:
                printl("", self, "C")   
                return
            tree=etree.fromstring(html)
            
            mediaCount=0
            mediaDetails=[]
            for media in tree.getiterator('Media'):
                mediaCount+=1
                tempDict={'videoResolution' : media.get('videoResolution',"Unknown")}
                
                for child in media:
                    tempDict['key']=child.get('key','')
                
                tempDict['identifier']=tree.get('identifier','')
                mediaDetails.append(tempDict)
                        
            printl( str(mediaDetails), self, "I" )            
                        
            #If we have options, create a dialog menu
            result=0
            if mediaCount > 1:
                printl ("Select from plugin video sources", self, "I")
                dialogOptions=[x['videoResolution'] for x in mediaDetails ]
                #===============================================================
                # videoResolution = xbmcgui.Dialog()
                #===============================================================
                
                #===============================================================
                # result = videoResolution.select('Select resolution..',dialogOptions)
                #===============================================================
                
                if result == -1:
                    printl("", self, "C")   
                    return
    
            self.videoPluginPlay(self.getLinkURL('',mediaDetails[result],server))
            printl("", self, "C")   
            return  
            
        #Check if there is a further level of XML required
        if '&indirect=1' in vids:
            printl("Indirect link", self, "I")
            html=self.getURL(vids, suppress=False)
            if not html:
                printl("", self, "C")   
                return
            tree=etree.fromstring(html)
            
            for bits in tree.getiterator('Part'):
                self.videoPluginPlay(self.getLinkURL(vids,bits,server))
                break
            
            printl("", self, "C")       
            return
        
        #if we have a plex URL, then this is a transcoding URL
        if 'plex://' in vids:
            printl("found webkit video, pass to self.transcoder", self, "I")
            self.getTranscodeSettings(True)
            if not (prefix):
                prefix="system"
            vids=self.transcode(0, vids, prefix)
            session=vids
        
        #Everything else should be this
        #else:
        #    printl("Direct link")
        #    output=self.getURL(vids, type="HEAD", suppress=False)
        #    if not output:
        #        return
        #        
        #    printl(str(output))
        #    if ( output[0:4] == "http" ) or ( output[0:4] == "plex" ):
        #        printl("Redirect.  Getting new URL")
        #        vids=output
        #        printl("New URL is: "+ vids)
        #        parameters=self.get_params(vids)
        #        
        #        prefix=parameters.get("prefix",'')
        #        extraData={'key'        : vids ,
        #                   'identifier' : prefix }
        #
        #        vids=self.getLinkURL(vids, extraData ,server)  
        
        printl("URL to Play: " + vids, self, "I")
        printl("Prefix is: " + str(prefix), self, "I")
            
        #If this is an Apple movie trailer, add User Agent to allow access
        if 'trailers.apple.com' in vids:
            url=vids+"|User-Agent=QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)"
        elif server in vids:
            url=vids+self.getAuthDetails({'token': _PARAM_TOKEN})
        else:
            url=vids
       
        printl("Final URL is : " + url, self, "I")
        
        #=======================================================================
        # item = xbmcgui.ListItem(path=url)
        # start = xbmcplugin.setResolvedUrl(pluginhandle, True, item)        
        #=======================================================================
    
        if 'self.transcode' in url:
            try:
                self.pluginTranscodeMonitor(self.g_sessionID,server)
            except: 
                printl("Unable to start self.transcode monitor", self, "I")
        else:
            printl("Not starting monitor", self, "I")
            
        printl("", self, "C")   
        return
    
    #===============================================================================
    # 
    #===============================================================================
    def pluginTranscodeMonitor(self, sessionID, server ): # CHECKED
        '''
        '''
        printl("", self, "S")
    
        #Logic may appear backward, but this does allow for a failed start to be detected
        #First while loop waiting for start
    #=========================================================================== 
    #    count=0
    #
    #    while not xbmc.Player().isPlaying():
    #        printl( "Not playing yet...sleep for 2")
    #        count = count + 2
    #        if count >= 40:
    #            #Waited 20 seconds and still no movie playing - assume it isn't going to..
    #            return
    #        else:
    #            time.sleep(2)
    # 
    #    while xbmc.Player().isPlaying():
    #        printl("Waiting for playback to finish")
    #        time.sleep(4)
    #    
    #    printl("Playback Stopped")
    #    printl("Stopping PMS self.transcode job with session: " + sessionID)
    #    stopURL='http://'+server+'/video/:/self.transcode/segmented/stop?session='+sessionID
    #        
    #    html=self.getURL(stopURL)
    #===========================================================================
        printl("", self, "C")   
        return

    #===============================================================================
    # 
    #===============================================================================
    def get_params(self, paramstring ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        printl("Parameter string: " + paramstring, self, "I")
        param={}
        if len(paramstring)>=2:
                params=paramstring
                
                if params[0] == "?":
                    cleanedparams=params[1:] 
                else:
                    cleanedparams=params
                    
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                
                pairsofparams=cleanedparams.split('&')
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                        elif (len(splitparams))==3:
                                param[splitparams[0]]=splitparams[1]+"="+splitparams[2]
        printl("Returning: " + str(param), self, "I")                        
        printl("", self, "C")   
        return param
 
    #============================================================================
    # 
    #============================================================================
    def getContent(self, url ):  # CHECKED
        '''
            This function takes teh URL, gets the XML and determines what the content is
            This XML is then redirected to the best processing function.
            If a search term is detected, then show keyboard and run search query
            @input: URL of XML page
            @return: nothing, redirects to another function
        '''
        printl("", self, "S")
            
        server = self.getServerFromURL(url)
        lastbit=url.split('/')[-1]
        printl("URL suffix: " + str(lastbit), self, "I")
        
        #=======================================================================
        # #Catch search requests, as we need to process input before getting results.
        # if lastbit.startswith('search'):
        #    printl("This is a search URL.  Bringing up keyboard", self, "I")
        #    kb = xbmc.Keyboard('', 'heading')
        #    kb.setHeading('Enter search term')
        #    kb.doModal()
        #    if (kb.isConfirmed()):
        #        text = kb.getText()
        #        printl("Search term input: "+ text, self, "I")
        #        url=url+'&query='+text
        #    else:
        #        return
        #=======================================================================
         
        html=self.getURL(url, suppress=False, popup=1 )
        
        if html is False:
            printl("", self, "C")   
            return
            
        tree=etree.fromstring(html)
     
        if lastbit == "folder":
            self.processXML(url,tree)
            return
     
        view_group=tree.get('viewGroup',None)
    
        if view_group == "movie":
            printl( "This is movie XML, passing to self.Movies", self, "I")
            #===================================================================
            # if not (lastbit.startswith('recently') or lastbit.startswith('newest')):
            #    xbmcplugin.addSortMethod(pluginhandle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
            #===================================================================
            self.getMoviesFromSection(url, tree)
        elif view_group == "show":
            printl( "This is tv show XML", self, "I")
            self.getShowsFromSection(url,tree)
        elif view_group == "episode":
            printl("This is TV episode XML", self, "I")
            self.getEpisodesOfSeason(url,tree)
        elif view_group == 'artist':
            printl( "This is music XML", self, "I")
            self.artist(url, tree)
        elif view_group== 'album' or view_group == 'albums':
            self.albums(url,tree)
        elif view_group == "track":
            printl("This is track XML", self, "I")
            self.tracks(url, tree)
        elif view_group =="photo":
            printl("This is a photo XML", self, "I")
            self.photo(url,tree)
        else:
            self.processDirectory(url,tree)
        
        printl("", self, "C")       
        return

    #===========================================================================
    # 
    #===========================================================================
    def processDirectory(self, url, tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        printl("Processing secondary menus", self, "I")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'movies')
        #=======================================================================
    
        server=self.getServerFromURL(url)
        
        for directory in tree:
            details={'title' : directory.get('title','Unknown').encode('utf-8') }
            extraData={'thumb'        : self.getThumb(directory, server) ,
                       'fanart_image' : self.getFanart(tree, server, False) } 
            
            if extraData['thumb'] == '':
                extraData['thumb']=extraData['fanart_image']
            
            u='%s&mode=%s' % ( self.getLinkURL(url,directory,server), _MODE_GETCONTENT )
    
            self.addGUIItem(u,details,extraData)
            
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
        printl("", self, "C")   
        
    #===============================================================================
    # 
    #===============================================================================
    def getMasterServer(self):
        '''
        '''
        printl("", self, "S")
        
        self.discoverAllServers()
        possibleServers=[]
        for serverData in self.resolveAllServers():
            print str(serverData)
            if serverData['master'] == 1:
                possibleServers.append({'address' : serverData['address'] ,
                                        'discovery' : serverData['discovery'] })
        print str(possibleServers)
        if len(possibleServers) > 1:
            preferred="local"
            for serverData in possibleServers:
                if preferred == "any":
                    return serverData['address']
                else:
                    if serverData['discovery'] == preferred:
                        return serverData['address']
        
        printl("", self, "C")                   
        return possibleServers[0]['address']                

    #===========================================================================
    # 
    #===========================================================================
    def transcode(self, id, url, identifier=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
     
        server=self.getServerFromURL(url)
        
        #Check for myplex user, which we need to alter to a master server
        if 'plexapp.com' in url:
            server=self.getMasterServer()
        
        printl("Using preferred transcosing server: " + server, self, "I")
            
        filestream=urllib.quote_plus("/"+"/".join(url.split('/')[3:]))
      
        if identifier is not None:
            baseurl=url.split('url=')[1]
            myurl="/video/:/self.transcode/segmented/start.m3u8?url="+baseurl+"&webkit=1&3g=0&offset=0&quality="+self.g_quality+"&session="+self.g_sessionID+"&identifier="+identifier
        else:
      
            if self.g_transcodefmt == "m3u8":
                myurl = "/video/:/self.transcode/segmented/start.m3u8?identifier=com.plexapp.plugins.library&ratingKey=" + id + "&offset=0&quality="+self.g_quality+"&url=http%3A%2F%2Flocalhost%3A32400" + filestream + "&3g=0&httpCookies=&userAgent=&session="+self.g_sessionID
            elif self.g_transcodefmt == "flv":
                myurl="/video/:/self.transcode/generic.flv?format=flv&videoCodec=libx264&vpre=video-embedded-h264&videoBitrate=5000&audioCodec=libfaac&apre=audio-embedded-aac&audioBitrate=128&size=640x480&fakeContentLength=2000000000&url=http%3A%2F%2Flocalhost%3A32400"  + filestream + "&3g=0&httpCookies=&userAgent="
            else:
                printl( "Woah!!  Barmey settings error....Bale.....", self, "I")
                printl("", self, "C")   
                return url
        
        now=str(int(round(time.time(),0)))
        
        msg = myurl+"@"+now
        printl("Message to hash is " + msg, self, "I")
        
        #These are the DEV API keys - may need to change them on release
        publicKey="KQMIY6GATPC63AIMC4R2"
        privateKey = base64.decodestring("k3U6GLkZOoNIoSgjDshPErvqMIFdE0xMTx8kgsrhnC0=")
           
        #=======================================================================
        # import hmac
        #=======================================================================
        hash = hmac.new(privateKey,msg,digestmod=hashlib.sha256)
        
        printl("HMAC after hash is " + hash.hexdigest(), self, "I")
        
        #Encode the binary hash in base64 for transmission
        token=base64.b64encode(hash.digest())
        
        #Send as part of URL to avoid the case sensitive header issue.
        fullURL="http://"+server+myurl+"&X-Plex-Access-Key="+publicKey+"&X-Plex-Access-Time="+str(now)+"&X-Plex-Access-Code="+urllib.quote_plus(token)+"&"+self.g_capability
           
        printl("Transcoded media location URL " + fullURL, self, "I")
        
        printl("", self, "C")   
        return fullURL

    #===============================================================================
    # 
    #===============================================================================
    def artist(self, url, tree=None ): # CHECKED
        '''
            Process artist XML and display data
            @input: url of XML page, or existing tree of XML page
            @return: nothing
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'artists')
        #=======================================================================
        
        #Get the URL and server name.  Get the XML and parse
        if tree is None:      
            html=self.getURL(url)
            if html is False:
                return
       
            tree=etree.fromstring(html)
        
        server=self.getServerFromURL(url)
        
        ArtistTag=tree.findall('Directory')
        for artist in ArtistTag:
        
            details={'plot'    : artist.get('summary','') ,
                     'artist'  : artist.get('title','').encode('utf-8') }
            
            details['title']=details['artist']
              
            extraData={'type'         : "Music" ,
                       'thumb'        : self.getThumb(artist, server) ,
                       'fanart_image' : self.getFanart(artist, server) ,
                       'ratingKey'    : artist.get('title','') ,
                       'key'          : artist.get('key','') }
    
            url='http://%s%s&mode=%s' % (server, extraData['key'], str(_MODE_ALBUMS) )
            
            self.addGUIItem(url,details,extraData) 
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
    
    #===============================================================================
    # 
    #===============================================================================
    def albums(self, url, tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'albums')
        #=======================================================================
       
        #Get the URL and server name.  Get the XML and parse
        if tree is None:
            html=self.getURL(url)
            if html is False:
                return
       
            tree=etree.fromstring(html)
        
        server=self.getServerFromURL(url)        
        sectionart=self.getFanart(tree, server)
        
        AlbumTags=tree.findall('Directory')
        for album in AlbumTags:
         
            details={'album'   : album.get('title','').encode('utf-8') ,
                     'year'    : int(album.get('year',0)) ,
                     'artist'  : tree.get('parentTitle', album.get('parentTitle','')) ,
                     'plot'    : album.get('summary','') }
    
            details['title']=details['album']
    
            extraData={'type'         : "Music" ,
                       'thumb'        : self.getThumb(album, server) ,
                       'fanart_image' : self.getFanart(album, server) ,
                       'key'          : album.get('key','') }
    
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=sectionart
                                        
            url='http://%s%s&mode=%s' % (server, extraData['key'], str(_MODE_TRACKS) )
    
            self.addGUIItem(url,details,extraData) 
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================
    
    #===========================================================================
    # 
    #===========================================================================
    def tracks(self, url,tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'songs')
        #=======================================================================
                    
        if tree is None:       
            html=self.getURL(url)          
            if html is False:
                return
      
            tree=etree.fromstring(html)
        
        server = self.getServerFromURL(url)                               
        sectionart = self.getFanart(tree,server) 
        TrackTags = tree.findall('Track')      
        for track in TrackTags:        
            self.trackTag(server, tree, track)
        
        printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================

    #===========================================================================
    # 
    #===========================================================================
    def PlexPlugins(self, url, tree=None ): # CHECKED
        '''
            Main function to parse plugin XML from PMS
            Will create dir or item links depending on what the 
            main tag is.
            @input: plugin page URL
            @return: nothing, creates XBMC GUI listing
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'movies')
        #=======================================================================
        server=self.getServerFromURL(url)
        if tree is None:
    
            html=self.getURL(url)
        
            if html is False:
                return
    
            tree=etree.fromstring(html)
        
        for plugin in tree:
    
            details={'title'   : plugin.get('title','Unknown').encode('utf-8') }
    
            if details['title'] == "Unknown":
                details['title']=plugin.get('name',"Unknown").encode('utf-8')
    
            extraData={'thumb'        : self.getThumb(plugin, server) , 
                       'fanart_image' : self.getFanart(plugin, server) ,
                       'identifier'   : tree.get('identifier','') ,
                       'type'         : "Video" ,
                       'key'          : plugin.get('key','') }
            
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=self.getFanart(tree, server)
                
            p_url=self.getLinkURL(url, extraData, server)
          
            if plugin.tag == "Directory" or plugin.tag == "Podcast":
                self.addGUIItem(p_url+"&mode="+str(_MODE_PLEXPLUGINS), details, extraData)
                    
            elif plugin.tag == "Video":
                self.addGUIItem(p_url+"&mode="+str(_MODE_VIDEOPLUGINPLAY), details, extraData, folder=False)
            
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)        
        #=======================================================================

    #============================================================================
    # 
    #============================================================================
    def processXML(self, url, tree=None ):
        '''
            Main function to parse plugin XML from PMS
            Will create dir or item links depending on what the 
            main tag is.
            @input: plugin page URL
            @return: nothing, creates XBMC GUI listing
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'movies')
        #=======================================================================
        server=self.getServerFromURL(url)
        if tree is None:
    
            html=self.getURL(url)
        
            if html is False:
                printl("", self, "C")   
                return
    
            tree=etree.fromstring(html)
        
        for plugin in tree:
    
            details={'title'   : plugin.get('title','Unknown').encode('utf-8') }
    
            if details['title'] == "Unknown":
                details['title']=plugin.get('name',"Unknown").encode('utf-8')
    
            extraData={'thumb'        : self.getThumb(plugin, server) , 
                       'fanart_image' : self.getFanart(plugin, server) ,
                       'identifier'   : tree.get('identifier','') ,
                       'type'         : "Video" }
            
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=self.getFanart(tree, server)
                
            p_url=self.getLinkURL(url, plugin, server)
          
            if plugin.tag == "Directory" or plugin.tag == "Podcast":
                self.addGUIItem(p_url+"&mode="+str(_MODE_PROCESSXML), details, extraData)
    
            elif plugin.tag == "Track":
                self.trackTag(server, tree, plugin)
                    
            elif tree.get('viewGroup') == "movie":
                self.getMoviesFromSection(url, tree)
                printl("", self, "C")   
                return
    
            elif tree.get('viewGroup') == "episode":
                self.getEpisodesOfSeason(url, tree)
                printl("", self, "C")   
                return
           
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle) 
        #=======================================================================
    
    #===============================================================================
    # 
    #===============================================================================
    def movieTag(self, url, server, tree, movie, randomNumber):
        '''
        '''
        printl("", self, "S")
        
        tempgenre=[]
        tempcast=[]
        tempdir=[]
        tempwriter=[]
        
        #Lets grab all the info we can quickly through either a dictionary, or assignment to a list
        #We'll process it later
        for child in movie:
            if child.tag == "Media":
                mediaarguments = dict(child.items())
            elif child.tag == "Genre" and self.g_skipmetadata == "false":
                tempgenre.append(child.get('tag'))
            elif child.tag == "Writer"  and self.g_skipmetadata == "false":
                tempwriter.append(child.get('tag'))
            elif child.tag == "Director"  and self.g_skipmetadata == "false":
                tempdir.append(child.get('tag'))
            elif child.tag == "Role"  and self.g_skipmetadata == "false":
                tempcast.append(child.get('tag'))

        printl("Media attributes are " + str(mediaarguments), self, "D")

                                    
        #Gather some data 
        view_offset=movie.get('viewOffset',0)
        duration=int(mediaarguments.get('duration',movie.get('duration',0)))/1000
                 
        #Required listItem entries for XBMC
        details={'plot'      : movie.get('summary','') ,
                 'title'     : movie.get('title','Unknown').encode('utf-8') ,
                 'playcount' : int(movie.get('viewCount',0)) ,
                 'rating'    : movie.get('rating',0) ,
                 'studio'    : movie.get('studio','') ,
                 'mpaa'      : "Rated " + movie.get('contentRating', 'unknown') ,
                 'year'      : int(movie.get('year',0)) ,
                 'tagline'   : movie.get('tagline','') ,
                 'duration'  : str(datetime.timedelta(seconds=duration)) ,
                 'server'    : str(server) ,
                 'overlay'   : _OVERLAY_XBMC_UNWATCHED }
        
        #Extra data required to manage other properties
        extraData={'type'         : "Video" ,
                   'thumb'        : self.getThumb(movie, server) ,
                   'fanart_image' : self.getFanart(movie, server) ,
                   'token'        : _PARAM_TOKEN ,
                   'key'          : movie.get('key',''),
                   'ratingKey'    : str(movie.get('ratingKey',0)) }
    
        #=======================================================================
        # #Determine what tupe of watched flag [overlay] to use
        # if details['playcount'] > 0:
        #    if g_skinwatched == "xbmc":
        #        details['overlay']=_OVERLAY_XBMC_WATCHED
        #    elif g_skinwatched == "DreamPlex":
        #        details['overlay']=_OVERLAY_PLEX_WATCHED
        # elif details['playcount'] == 0: 
        #    if g_skinwatched == "DreamPlex":
        #        details['overlay']=_OVERLAY_PLEX_UNWATCHED
        # 
        # if g_skinwatched == "DreamPlex" and int(view_offset) > 0:
        #    details['overlay'] = _OVERLAY_PLEX_PARTIAL
        #=======================================================================
        
        #Extended Metadata
        if self.g_skipmetadata == "false":
            details['cast']     = tempcast
            details['director'] = " / ".join(tempdir)
            details['writer']   = " / ".join(tempwriter)
            details['genre']    = " / ".join(tempgenre)
             
        #Add extra media flag data
        if self.g_skipmediaflags == "false":
            extraData['VideoResolution'] = mediaarguments.get('videoResolution','')
            extraData['VideoCodec']      = mediaarguments.get('videoCodec','')
            extraData['AudioCodec']      = mediaarguments.get('audioCodec','')
            extraData['AudioChannels']   = mediaarguments.get('audioChannels','')
            extraData['VideoAspect']     = mediaarguments.get('aspectRatio','')
    
        #Build any specific context menu entries
        if self.g_skipcontext == "false":
            context=self.buildContextMenu(url, extraData)    
        else:
            context=None
        # http:// <server> <path> &mode=<mode> &id=<media_id> &t=<rnd>
        u="http://%s%s&mode=%s&id=%s&t=%s" % (server, extraData['key'], _MODE_PLAYLIBRARY, extraData['ratingKey'], randomNumber)
        
        printl("", self, "C")   
        return self.addGUIItem(url,details,extraData,context,folder=False)        
        
    #===============================================================================
    # 
    #===============================================================================
    def trackTag(self, server, tree, track ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'songs')
        #=======================================================================
                                  
        for child in track:
            for babies in child:
                if babies.tag == "Part":
                    partDetails=(dict(babies.items()))
        
        printl( "Part is " + str(partDetails), self, "I")
    
        details={'TrackNumber' : int(track.get('index',0)) ,
                 'title'       : str(track.get('index',0)).zfill(2)+". "+track.get('title','Unknown').encode('utf-8') ,
                 'rating'      : float(track.get('rating',0)) ,
                 'album'       : track.get('parentTitle', tree.get('parentTitle','')) ,
                 'artist'      : track.get('grandparentTitle', tree.get('grandparentTitle','')) ,
                 'duration'    : int(track.get('duration',0))/1000 }
                                   
        extraData={'type'         : "Music" ,
                   'fanart_image' : self.getFanart(track, server) ,
                   'thumb'        : self.getThumb(track, server) ,
                   'ratingKey'    : track.get('key','') }
    
        if '/resources/plex.png' in extraData['thumb']:
            printl("thumb is default", self, "I")
            extraData['thumb']=self.getThumb(tree, server)
            
        if extraData['fanart_image'] == "":
            extraData['fanart_image']=self.getFanart(tree, server)
        
        #If we are streaming, then get the virtual location
        url=self.mediaType(partDetails,server)
    
        u="%s&mode=%s&id=%s" % (url, str(_MODE_BASICPLAY), str(extraData['ratingKey']))
            
        self.addGUIItem(u,details,extraData,folder=False)        
        printl("", self, "C")   
    #===============================================================================
    # 
    #===============================================================================
    def photo(self, url,tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        server=url.split('/')[2]

        
        if tree is None:
            html=self.getURL(url)
            
            if html is False:
                return
            
            tree=etree.fromstring(html)
        
        sectionArt=self.getFanart(tree,server)
     
        for picture in tree:
            
            details={'title' : picture.get('title',picture.get('name','Unknown')).encode('utf-8') } 
            
            extraData={'thumb'        : self.getThumb(picture, server) ,
                       'fanart_image' : self.getFanart(picture, server) ,
                       'type'         : "Picture" }
    
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=sectionArt
    
            u=self.getLinkURL(url, picture, server)   
                    
            if picture.tag == "Directory":
                u=u+"&mode="+str(_MODE_PHOTOS)
                self.addGUIItem(u,details,extraData)
        
            elif picture.tag == "Photo":
            
                if tree.get('viewGroup','') == "photo":
                    for photo in picture:
                        if photo.tag == "Media":
                            for images in photo:
                                if images.tag == "Part":
                                    print "found part tag"
                                    extraData['key']="http://"+server+images.get('key','')
                                    u=extraData['key']
                
                self.addGUIItem(u,details,extraData,folder=False)
            
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================

    #============================================================================
    # 
    #============================================================================
    def music(self, url, tree=None ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'artists')
        #=======================================================================
    
        server=self.getServerFromURL(url)
        
        if tree is None:
            html=self.getURL(url)
        
            if html is False:
                return
       
            tree=etree.fromstring(html)
      
        for grapes in tree:
           
            if grapes.get('key',None) is None:
                continue
    
            details={'genre'       : grapes.get('genre','') ,
                     'artist'      : grapes.get('artist','') ,
                     'year'        : int(grapes.get('year',0)) ,
                     'album'       : grapes.get('album','') ,
                     'tracknumber' : int(grapes.get('index',0)) ,
                     'title'       : "Unknown" }
    
            
            extraData={'type'        : "Music" ,                          
                       'thumb'       : self.getThumb(grapes, server) ,
                       'fanart_image': self.getFanart(grapes, server) }
    
            if extraData['fanart_image'] == "":
                extraData['fanart_image']=self.getFanart(tree, server)
    
            u=self.getLinkURL(url, grapes, server)
            
            if grapes.tag == "Track":
                printl("Track Tag", self, "I")
                #===============================================================
                # xbmcplugin.setContent(pluginhandle, 'songs')
                #===============================================================
                
                details['title']=grapes.get('track','Unknown').encode('utf-8')
                details['duration']=int(grapes.get('totalTime',0)/1000)
        
                u=u+"&mode="+str(_MODE_BASICPLAY)
                self.addGUIItem(u,details,extraData,folder=False)
    
            else: 
            
                if grapes.tag == "Artist":
                    printl("Artist Tag", self, "I")
                    #===========================================================
                    # xbmcplugin.setContent(pluginhandle, 'artists')
                    #===========================================================
                    details['title']=grapes.get('artist','Unknown')
                 
                elif grapes.tag == "Album":
                    printl("Album Tag", self, "I")
                    #===========================================================
                    # xbmcplugin.setContent(pluginhandle, 'albums')
                    #===========================================================
                    details['title']=grapes.get('album','Unknown')
    
                elif grapes.tag == "Genre":
                    details['title']=grapes.get('genre','Unknown')
                
                else:
                    printl("Generic Tag: " + grapes.tag, self, "I")
                    details['title']=grapes.get('title','Unknown')
                
                u=u+"&mode="+str(_MODE_MUSIC)
                self.addGUIItem(u,details,extraData)
            
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)    
        #=======================================================================

    #=============================================================================
    # 
    #=============================================================================
    def getThumb(self,  data, server ): # CHECKED
        '''
            Simply take a URL or path and determine how to format for images
            @ input: elementTree element, server name
            @ return formatted URL
        '''
        printl("", self, "S")
        
        thumbnail=data.get('thumb','').split('?t')[0]
        
        if thumbnail == '':
            printl("", self, "C")   
            return self.g_loc+'/resources/plex.png'
            
        elif thumbnail[0:4] == "http" :
            printl("", self, "C")   
            return thumbnail
        
        elif thumbnail[0] == '/':
            printl("", self, "C")   
            return 'http://'+server+thumbnail
        
        else: 
            printl("", self, "C")   
            return self.g_loc+'/resources/plex.png'
 
    #============================================================================
    # 
    #============================================================================
    def getFanart(self, data, server, transcode=True ): # CHECKED
        '''
            Simply take a URL or path and determine how to format for fanart
            @ input: elementTree element, server name
            @ return formatted URL for photo resizing
        '''
        printl("", self, "S")
        
        fanart=data.get('art','')
        
        if fanart == '':
            printl("", self, "C")   
            return ''
    
        elif fanart[0:4] == "http" :
            printl("", self, "C")   
            return fanart
            
        elif fanart[0] == '/':
            if transcode:
                printl("", self, "C")   
                return self.photoTranscode(server,'http://localhost:32400'+fanart)
            else:
                printl("", self, "C")   
                return 'http://%s%s' % (server, fanart)
            
        else: 
            printl("", self, "C")    
            return ''

    #===========================================================================
    # 
    #===========================================================================
    def getServerFromURL(self, url ): # CHECKED
        '''
        Simply split the URL up and get the server portion, sans port
        @ input: url, woth or without protocol
        @ return: the URL server
        '''
        printl("", self, "S")

        if url[0:4] == "http" or url[0:4] == "plex":
            printl("", self, "C")   
            return url.split('/')[2]
        else:
            printl("", self, "C")   
            return url.split('/')[0]
 
    
    #============================================================================
    # 
    #============================================================================
    def getLinkURL(self, url, pathData, server ): # CHECKED
        '''
            Investigate the passed URL and determine what is required to 
            turn it into a usable URL
            @ input: url, XML data and PM server address
            @ return: Usable http URL
        '''
        printl("", self, "S")

        path=pathData.get('key','')
        printl("Path is " + path, self, "I")
        
        if path == '':
            printl("Empty Path", self, "I")
            printl("", self, "C")   
            return
        
        #If key starts with http, then return it
        if path[0:4] == "http":
            printl("Detected http link", self, "I")
            printl("", self, "C")   
            return path
            
        #If key starts with a / then prefix with server address    
        elif path[0] == '/':
            printl("Detected base path link", self, "I")
            printl("", self, "C")   
            return 'http://%s%s' % ( server, path )
    
        #If key starts with plex:// then it requires transcoding 
        elif path[0:5] == "plex:":
            printl("Detected plex link", self, "I")    
            components=path.split('&')
            for i in components:
                if 'prefix=' in i:
                    del components[components.index(i)]
                    break
            if pathData.get('identifier',None):
                components.append('identifier='+pathData['identifier'])
            
            path='&'.join(components)
            printl("", self, "C")           
            return 'plex://'+server+'/'+'/'.join(path.split('/')[3:])
            
        #Any thing else is assumed to be a relative path and is built on existing url        
        else:
            printl("Detected relative link", self, "I")
            printl("", self, "C")   
            return "%s/%s" % ( url, path )
         
        printl("", self, "C")   
        return url

    #===============================================================================
    # 
    #===============================================================================
    def plexOnline(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # xbmcplugin.setContent(pluginhandle, 'files')
        #=======================================================================
    
        server=self.getServerFromURL(url)
        
        html=self.getURL(url)
        
        if html is False:
            return
        
        tree=etree.fromstring(html)
            
        for plugin in tree:
           
            details={'title' : plugin.get('title',plugin.get('name','Unknown')).encode('utf-8') }
            extraData={'type'      : "Video" , 
                       'installed' : int(plugin.get('installed',2)) ,
                       'key'       : plugin.get('key','') ,
                       'thumb'     : self.getThumb(plugin,server)} 
                       
            mode=_MODE_CHANNELINSTALL
            
            if extraData['installed'] == 1:
                details['title']=details['title']+" (installed)"
                
            elif extraData['installed'] == 2:      
                mode=_MODE_PLEXONLINE
            
            u=self.getLinkURL(url, plugin, server)
            
            u=u+"&mode="+str(mode)+"&name="+urllib.quote_plus(details['title'])
            self.addGUIItem(u, details, extraData)
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)    
        #=======================================================================

    #==========================================================================
    # 
    #==========================================================================
    def install(self, url, name ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        html=self.getURL(url)
    #===========================================================================
    #    if html is False:
    #        return
    #    tree = etree.fromstring(html)
    #    
    #    operations={}
    #    i=0
    #    for plums in tree.findall('Directory'):
    #        operations[i]=plums.get('title')
    #        
    #        #If we find an install option, switch to a yes/no dialog box
    #        if operations[i].lower() == "install":
    #            printl("Not installed.  Print dialog")
    #            ret = xbmcgui.Dialog().yesno("Plex Online","About to install " + name)
    # 
    #            if ret:
    #                printl("Installing....")
    #                installed = self.getURL(url+"/install")
    #                tree = etree.fromstring(installed)
    # 
    #                msg=tree.get('message','(blank)')
    #                printl(msg)
    #                xbmcgui.Dialog().ok("Plex Online",msg)
    #            return
    # 
    #        i+=1
    #     
    #    #Else continue to a selection dialog box
    #    ret = xbmcgui.Dialog().select("This plugin is already installed..",operations.values())
    #    
    #    if ret == -1:
    #        printl("No option selected, cancelling")
    #        return
    #    
    #    printl("Option " + str(ret) + " selected.  Operation is " + operations[ret])
    #    u=url+"/"+operations[ret].lower()
    # 
    #    action = self.getURL(u)
    #    tree = etree.fromstring(action)
    # 
    #    msg=tree.get('message')
    #    printl(msg)
    #    xbmcgui.Dialog().ok("Plex Online",msg)
    #    xbmc.executebuiltin("Container.Refresh")
    #===========================================================================
    
        printl("", self, "C")   
        return   
    
    #=============================================================================
    # 
    #=============================================================================
    def channelView(self, url ): # CHECKED 
        '''
        '''
        printl("", self, "S")

        html=self.getURL(url)
        if html is False:
            return
        tree = etree.fromstring(html)    
        server=self.getServerFromURL(url)   
        for channels in tree.getiterator('Directory'):
        
            if channels.get('local','') == "0":
                continue
                
            arguments=dict(channels.items())
    
            extraData={'fanart_image' : self.getFanart(channels, server) ,
                       'thumb'        : self.getThumb(channels, server) }
            
            details={'title' : channels.get('title','Unknown') }
    
            suffix=channels.get('path').split('/')[1]
            
            if channels.get('unique','')=='0':
                details['title']=details['title']+" ("+suffix+")"
                   
            p_url=self.getLinkURL(url, channels, server)  
            
            if suffix == "photos":
                mode=_MODE_PHOTOS
            elif suffix == "video":
                mode=_MODE_PLEXPLUGINS
            elif suffix == "music":
                mode=_MODE_MUSIC
            else:
                mode=_MODE_GETCONTENT
            
            self.addGUIItem(p_url+'&mode='+str(mode),details,extraData)
            
            printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)
        #=======================================================================

    #===========================================================================
    # 
    #===========================================================================
    def photoTranscode(self, server, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
        
        new_url = 'http://%s/photo/:/transcode?url=%s&width=1280&height=720' % (server, urllib.quote_plus(url))
        
        printl("", self, "C")   
        return new_url
                  
    #===============================================================================
    # 
    #===============================================================================
    def skin(self ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #Get the global host variable set in settings
    #===========================================================================
    #    WINDOW = xbmcgui.Window( 10000 )
    #  
    #    self.getAllSections()
    #    sectionCount=0
    #    serverCount=0
    #    
    #    #For each of the servers we have identified
    #    for section in self.g_sections:
    # 
    #        extraData={ 'fanart_image' : self.getFanart(section, section['address']) ,
    #                    'thumb'        : self.getFanart(section, section['address'], False) }
    #                                                                                  
    #        #Determine what we are going to do process after a link is selected by the user, based on the content we find
    #        
    #        path=section['path']
    #        
    #        if section['type'] == 'show':
    #            window="VideoLibrary"
    #            mode=_MODE_TVSHOWS
    #        if  section['type'] == 'movie':
    #            window="VideoLibrary"
    #            mode=_MODE_MOVIES
    #        if  section['type'] == 'artist':
    #            window="MusicFiles"
    #            mode=_MODE_ARTISTS
    #        if  section['type'] == 'photo':
    #            window="Pictures"
    #            mode=_MODE_PHOTOS
    #               
    #        aToken=self.getAuthDetails(section)
    #        qToken=self.getAuthDetails(section, prefix='?')
    # 
    #        if self.g_secondary == "true":
    #            mode=_MODE_GETCONTENT
    #        else:
    #            path=path+'/all'
    # 
    #        s_url='http://%s%s&mode=%s%s' % ( section['address'], path, mode, aToken)
    # 
    #        #Build that listing..
    #        WINDOW.setProperty("DreamPlex.%d.title"    % (sectionCount) , section['title'])
    #        WINDOW.setProperty("DreamPlex.%d.subtitle" % (sectionCount) , section['serverName'])
    #        WINDOW.setProperty("DreamPlex.%d.path"     % (sectionCount) , "ActivateWindow("+window+",plugin://plugin.video.DreamPlex/?url="+s_url+",return)")
    #        WINDOW.setProperty("DreamPlex.%d.art"      % (sectionCount) , extraData['fanart_image']+qToken)
    #        WINDOW.setProperty("DreamPlex.%d.type"     % (sectionCount) , section['type'])
    #        WINDOW.setProperty("DreamPlex.%d.icon"     % (sectionCount) , extraData['thumb']+qToken)
    #        WINDOW.setProperty("DreamPlex.%d.thumb"    % (sectionCount) , extraData['thumb']+qToken)
    #        WINDOW.setProperty("DreamPlex.%d.partialpath" % (sectionCount) , "ActivateWindow("+window+",plugin://plugin.video.DreamPlex/?url=http://"+section['address']+section['path'])
    #  
    #        printl("Building window properties index [" + str(sectionCount) + "] which is [" + section['title'] + "]")
    #        printl("PATH in use is: ActivateWindow("+window+",plugin://plugin.video.DreamPlex/?url="+s_url+",return)")
    #        sectionCount += 1
    #    
    #    #For each of the servers we have identified
    #    allservers=self.resolveAllServers()
    #    numOfServers=len(allservers)
    #    
    #    for server in allservers:
    #    
    #        if self.g_channelview == "true":
    #            WINDOW.setProperty("DreamPlex.channel", "1")
    #            WINDOW.setProperty("DreamPlex.%d.server.channel" % (serverCount) , "ActivateWindow(VideoLibrary,plugin://plugin.video.DreamPlex/?url=http://"+server['address']+"/system/plugins/all&mode=21"+aToken+",return)")
    #        else:
    #            WINDOW.clearProperty("DreamPlex.channel")
    #            WINDOW.setProperty("DreamPlex.%d.server.video" % (serverCount) , "http://"+server['address']+"/video&mode=7"+aToken)
    #            WINDOW.setProperty("DreamPlex.%d.server.music" % (serverCount) , "http://"+server['address']+"/music&mode=17"+aToken)
    #            WINDOW.setProperty("DreamPlex.%d.server.photo" % (serverCount) , "http://"+server['address']+"/photos&mode=16"+aToken)
    #                
    #        WINDOW.setProperty("DreamPlex.%d.server.online" % (serverCount) , "http://"+server['address']+"/system/plexonline&mode=19"+aToken)
    # 
    #        WINDOW.setProperty("DreamPlex.%d.server" % (serverCount) , server['serverName'])
    #        printl ("Name mapping is :" + server['serverName'])
    #            
    #        serverCount+=1
    #                   
    #    #Clear out old data
    #    try:
    #        printl("Clearing properties from [" + str(sectionCount) + "] to [" + WINDOW.getProperty("DreamPlex.sectionCount") + "]")
    # 
    #        for i in range(sectionCount, int(WINDOW.getProperty("DreamPlex.sectionCount"))+1):
    #            WINDOW.clearProperty("DreamPlex.%d.title"    % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.subtitle" % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.url"      % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.path"     % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.window"   % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.art"      % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.type"     % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.icon"     % ( i ) )
    #            WINDOW.clearProperty("DreamPlex.%d.thumb"    % ( i ) )
    #    except:
    #        pass
    # 
    #    printl("Total number of skin sections is [" + str(sectionCount) + "]")
    #    printl("Total number of servers is ["+str(numOfServers)+"]")
    #    WINDOW.setProperty("DreamPlex.sectionCount", str(sectionCount))
    #    WINDOW.setProperty("DreamPlex.numServers", str(numOfServers))
    #    if __settings__.getSetting('myplex_user') != '':
    #        WINDOW.setProperty("DreamPlex.queue" , "ActivateWindow(VideoLibrary,plugin://plugin.video.DreamPlex/?url=http://myplexqueue&mode=24,return)")
    #        WINDOW.setProperty("DreamPlex.myplex",  "1" )     
    #===========================================================================
        printl("", self, "C")   
        return

    #============================================================================
    # 
    #============================================================================
    def myPlexQueue(self): # CHECKED
        '''
        '''
        printl("", self, "S")    
    #===========================================================================
    #    if __settings__.getSetting('myplex_user') == '':
    #        xbmc.executebuiltin("XBMC.Notification(myplex not configured,)")      
    #        return
    # 
    #    html=self.getMyPlexURL('/pms/playlists/queue/all')
    #    tree=etree.fromstring(html)
    #    
    #    self.PlexPlugins('http://my.plexapp.com/playlists/queue/all', tree)
    #===========================================================================
        printl("", self, "C")   
        return
        
    #===============================================================================
    # 
    #===============================================================================
    def libraryRefresh(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # printl("== ENTER: libraryRefresh ==", False)
        # html=self.getURL(url)
        # printl ("Library refresh requested")
        # xbmc.executebuiltin("XBMC.Notification(\"DreamPlex\",Library Refresh started,100)")
        #=======================================================================
        printl("", self, "C")   
        return
 
    #============================================================================
    # 
    #============================================================================
    def watched(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
    
        if url.find("unscrobble") > 0:
            printl ("Marking as unwatched with: " + url, self, "I")
        else:
            printl ("Marking as watched with: " + url, self, "I")
        
        html=self.getURL(url)
        #=======================================================================
        # xbmc.executebuiltin("Container.Refresh")
        #=======================================================================
        printl("", self, "C")   
        return

    #==========================================================================
    # 
    #==========================================================================
    def displayServers(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")

        type=url.split('/')[2]
        printl("Displaying entries for " + type, self, "I")
        Servers = self.resolveAllServers()
    
        #For each of the servers we have identified
        for mediaserver in Servers:
        
            details={'title' : mediaserver.get('serverName','Unknown') }
    
            if type == "video":
                s_url='http://%s/video&mode=%s' % ( mediaserver.get('address','') , _MODE_PLEXPLUGINS )
                
            elif type == "online":
                s_url='http://%s/system/plexonline&mode=%s' % ( mediaserver.get('address','') , _MODE_PLEXONLINE )
                
            elif type == "music":
                s_url='http://%s/music&mode=%s' % ( mediaserver.get('address','') , _MODE_MUSIC )
                
            elif type == "photo":
                s_url='http://%s/photos&mode=%s' % ( mediaserver.get('address','') , _MODE_PHOTOS )
                    
            self.addGUIItem(s_url, details, {} )
        
        printl("", self, "C")   
        #=======================================================================
        # xbmcplugin.endOfDirectory(pluginhandle)  
        #=======================================================================

    #===============================================================================
    # 
    #===============================================================================
    def getTranscodeSettings(self, override=False ): # CHECKED
        '''
        '''
        printl("", self, "S")
        #=======================================================================
        # global self.g_transcode 
        # self.g_transcode = __settings__.getSetting('self.transcode')
        #=======================================================================
    
        if override is True:
            printl( "Transcode override.  Will play media with addon transcoding settings", self, "I")
            self.g_transcode="true"
    
        if self.g_transcode == "true":
            #If self.transcode is set, ignore the stream setting for file and smb:
            #===================================================================
            # global self.g_stream
            # self.g_stream = "1"
            #===================================================================
            printl( "We are set to Transcode, overriding stream selection", self, "I")
            #===================================================================
            # global self.g_transcodetype 
            # global self.g_transcodefmt
            #===================================================================
            #===================================================================
            # self.g_transcodetype = __settings__.getSetting('self.transcodefmt')
            #===================================================================
            #===================================================================
            # self.g_transcodetype = __settings__.getSetting('self.transcodefmt')
            # if self.g_transcodetype == "0":
            #    self.g_transcodefmt="m3u8"
            # elif self.g_transcodetype == "1":
            #    self.g_transcodefmt="flv"
            #===================================================================
            
            #===================================================================
            # global self.g_quality
            # self.g_quality = str(int(__settings__.getSetting('quality'))+3)
            #===================================================================
            printl( "Transcode format is " + self.g_transcodefmt, self, "I")
            printl( "Transcode quality is " + self.g_quality, self, "I")
            
            baseCapability="http-live-streaming,http-mp4-streaming,http-streaming-video,http-mp4-video"
            if int(self.g_quality) >= 3:
                baseCapability+=",http-streaming-video-240p,http-mp4-video-240p"
            if int(self.g_quality) >= 4:
                baseCapability+=",http-streaming-video-320p,http-mp4-video-320p"
            if int(self.g_quality) >= 5:
                baseCapability+=",http-streaming-video-480p,http-mp4-video-480p"
            if int(self.g_quality) >= 6:
                baseCapability+=",http-streaming-video-720p,http-mp4-video-720p"
            if int(self.g_quality) >= 9:
                baseCapability+=",http-streaming-video-1080p,http-mp4-video-1080p"
                
            #===================================================================
            # self.g_audioOutput=__settings__.getSetting("audiotype")
            #===================================================================
       
            if self.g_audioOutput == "0":
                audio="mp3,aac"
            elif self.g_audioOutput == "1":
                audio="mp3,aac,ac3"
            elif self.g_audioOutput == "2":
                audio="mp3,aac,ac3,dts"
        
            #===================================================================
            # global self.g_capability   
            #===================================================================
            self.g_capability="X-Plex-Client-Capabilities="+urllib.quote_plus("protocols="+baseCapability+";videoDecoders=h264{profile:high&resolution:1080&level:51};audioDecoders="+audio)              
            printl("Plex Client Capability = " + self.g_capability, self, "I")
            
            #===================================================================
            # import uuid
            #===================================================================
            #===================================================================
            # global self.g_sessionID
            #===================================================================
            self.g_sessionID = str(uuid.uuid4())
            
            printl("", self, "C")   
            
    #===============================================================================
    # 
    #===============================================================================
    def deleteMedia(self, url ): # CHECKED
        '''
        '''
        printl("", self, "S")
        printl ("deleteing media at: " + url, self, "I")
        
        #=======================================================================
        # return_value = xbmcgui.Dialog().yesno("Confirm file delete?","Delete this item? This action will delete media and associated data files.")
        #=======================================================================
        return_value = True
        if return_value:
            printl("Deleting....")
            installed = self.getURL(url,type="DELETE")    
            #===================================================================
            # xbmc.executebuiltin("Container.Refresh")
            #===================================================================
        
        printl("", self, "C")   
        return True
    
    #===========================================================================
    # ##So this is where we really start the plugin.
    # printl( "DreamPlex -> Script argument is " + str(sys.argv[1]), False)
    # 
    # try:
    #    params=self.get_params(sys.argv[2])
    # except:
    #    params={}
    #        
    # #Now try and assign some data to them
    # param_url = params.get('url',None)
    # param_name = urllib.unquote_plus(params.get('name',""))
    # mode = int(params.get('mode',-1))
    # param_id=params.get('id',None)
    # param_transcodeOverride = int(params.get('self.transcode',0))
    # param_identifier = params.get('identifier',None)
    # _PARAM_TOKEN = params.get('X-Plex-Token',None)
    # 
    # if str(sys.argv[1]) == "skin":
    #    self.discoverAllServers()
    #    self.skin()
    # elif sys.argv[1] == "update":
    #    url=sys.argv[2]
    #    self.libraryRefresh(url)
    # elif sys.argv[1] == "watch":
    #    url=sys.argv[2]
    #    self.watched(url)
    # elif sys.argv[1] == "setting":
    #    __settings__.openSettings()
    # elif sys.argv[1] == "delete":
    #    url=sys.argv[2]
    #    self.deleteMedia(url)
    # elif sys.argv[1] == "refresh":
    #    xbmc.executebuiltin("Container.Refresh")
    # else:
    #   
    #    pluginhandle = int(sys.argv[1])
    #                    
    #    if DEBUG == "true":
    #        print "DreamPlex -> Mode: "+str(mode)
    #        print "DreamPlex -> URL: "+str(param_url)
    #        print "DreamPlex -> Name: "+str(param_name)
    #        print "DreamPlex -> ID: "+ str(param_id)
    #        print "DreamPlex -> identifier: " + str(param_identifier)
    #        print "DreamPlex -> token: " + str(_PARAM_TOKEN)
    # 
    #    #Run a function based on the mode variable that was passed in the URL       
    #    if ( mode == None ) or ( param_url == None ) or ( len(param_url)<1 ):
    #        self.discoverAllServers()
    #        self.displaySections()
    #    elif mode == 0:
    #        self.getContent(param_url)
    #    elif mode == 1:
    #        self.getShowsFromSection(param_url)
    #    elif mode == 2:
    #        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    #        self.getMoviesFromSection(param_url)
    #    elif mode == 3:
    #        self.artist(param_url)
    #    elif mode == 4:
    #        self.getSeasonsOfShow(param_url)
    #    elif mode == 5:
    #        self.playLibraryMedia(param_id,param_url)
    #    elif mode == 6:
    #        self.getEpisodesOfSeason(param_url)
    #    elif mode == 7:
    #        self.PlexPlugins(param_url)
    #    elif mode == _MODE_PROCESSXML:
    #        self.processXML(param_url)
    #    elif mode == 12:
    #        self.PLAY(param_url)
    #    elif mode == 14:
    #        self.albums(param_url)
    #    elif mode == 15:
    #        self.tracks(param_url)
    #    elif mode == 16:
    #        self.photo(param_url)
    #    elif mode == 17:
    #        self.music(param_url)
    #    elif mode == 18:
    #        self.videoPluginPlay(param_url,param_identifier)
    #    elif mode == 19:
    #        self.plexOnline(param_url)
    #    elif mode == 20:
    #        self.install(param_url,param_name)
    #    elif mode == 21:
    #        self.channelView(param_url)
    #    elif mode == 22:
    #        self.discoverAllServers()
    #        self.displayServers(param_url)
    #    elif mode == 23:
    #        self.playLibraryMedia(param_id,param_url,override=True)
    #    elif mode == 24:
    #        self.myPlexQueue()
    # 
    # print "===== DreamPlex STOP ====="
    #   
    # #clear done and exit.        
    # sys.modules.clear()
    #===========================================================================

    #===============================================================================
    # 
    #===============================================================================
    def buildContextMenu(self, url, itemData ): # CHECKED
        '''
        '''
        printl("", self, "S")
        context=[]
        server=self.getServerFromURL(url)
        refreshURL=url.replace("/all", "/refresh")
        plugin_url="XBMC.RunScript("+self.g_loc+"/default.py, "
        ID=itemData.get('ratingKey','0')
    
        #Initiate Library refresh 
        libraryRefresh = plugin_url+"update, " + refreshURL.split('?')[0]+self.getAuthDetails(itemData,prefix="?") + ")"
        context.append(('Rescan library section', libraryRefresh , ))
        
        #Mark media unwatched
        unwatchURL="http://"+server+"/:/unscrobble?key="+ID+"&identifier=com.plexapp.plugins.library"+self.getAuthDetails(itemData)
        unwatched=plugin_url+"watch, " + unwatchURL + ")"
        context.append(('Mark as Unwatched', unwatched , ))
                
        #Mark media watched        
        watchURL="http://"+server+"/:/scrobble?key="+ID+"&identifier=com.plexapp.plugins.library"+self.getAuthDetails(itemData)
        watched=plugin_url+"watch, " + watchURL + ")"
        context.append(('Mark as Watched', watched , ))
    
        #Delete media from Library
        deleteURL="http://"+server+"/library/metadata/"+ID+self.getAuthDetails(itemData)
        removed=plugin_url+"delete, " + deleteURL + ")"
        context.append(('Delete media', removed , ))
    
        #Display plugin setting menu
        settingDisplay=plugin_url+"setting)"
        context.append(('DreamPlex settings', settingDisplay , ))
    
        #Reload media section
        listingRefresh=plugin_url+"refresh)"
        context.append(('Reload Section', listingRefresh , ))
    
        printl("Using context menus " + str(context), self, "I")
        
        printl("", self, "C")   
        return context
  
#===============================================================================
# HELPER FUNCTIONS
#===============================================================================
  
    #===============================================================================
    # 
    #===============================================================================
    def checkNasOverride(self):
        '''
        '''
        printl("", self, "S")
        
        #NAS Override
        #===========================================================================
        # self.g_nasoverride = __settings__.getSetting('nasoverride')
        #===========================================================================
        printl("DreamPlex -> check SMB IP Override: " + self.g_nasoverride, self, "I")
        
        if self.g_nasoverride == "true":
            #===================================================================
            # self.g_nasoverrideip = __settings__.getSetting('nasoverrideip')
            #===================================================================
            if self.g_nasoverrideip == "":
                printl("DreamPlex -> No NAS IP Specified.  Ignoring setting", self, "I")
            else:
                printl("DreamPlex -> NAS IP: " + self.g_nasoverrideip, self, "I")
                
            #===================================================================
            # self.g_nasroot = __settings__.getSetting('nasroot')
            #===================================================================
      
    #===========================================================================
    # #Get look and feel
    # if __settings__.getSetting("contextreplace") == "true":
    #    g_contextReplace=True
    # else:
    #    g_contextReplace=False
    #===========================================================================
    
    #===========================================================================
    # self.g_skipcontext = __settings__.getSetting("skipcontextmenus")    
    # self.g_skipmetadata= __settings__.getSetting("skipmetadata")
    # self.g_skipmediaflags= __settings__.getSetting("skipflags")
    # self.g_skipimages= __settings__.getSetting("skipimages")
    # 
    # self.g_loc = "special://home/addons/plugin.video.DreamPlex"
    #===========================================================================
    
    #===========================================================================
    # #Create the standard header structure and load with a User Agent to ensure we get back a response.
    # g_txheaders = {
    #              'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',    
    #              }
    #===========================================================================
    
    #===========================================================================
    # #Set up holding variable for session ID
    # global self.g_sessionID
    # self.g_sessionID=None
    #===========================================================================
        
        printl("", self, "C")
        
    def discoverAllServers(self): # CHECKED
        '''
            Take the users settings and add the required master servers
            to the server list.  These are the devices which will be queried
            for complete library listings.  There are 3 types:
                local server - from IP configuration
                bonjour server - from a bonjour lookup
                myplex server - from myplex configuration
            Alters the global self.g_serverDict value
            @input: None
            @return: None       
        '''
        printl("", self, "S")
        #=======================================================================
        # self.g_bonjour = __settings__.getSetting('bonjour')
        #=======================================================================
    
        #Set to Bonjour
        if self.g_bonjour == "1":
            printl("DreamPlex -> local Bonjour discovery setting enabled.", self, "I")
    #===========================================================================
    #        try:
    #            printl("Attempting bonjour lookup on _plexmediasvr._tcp")
    #            bonjourServer = bonjourFind("_plexmediasvr._tcp")
    #                                                
    #            if bonjourServer.complete:
    #                printl("Bonjour discovery completed")
    #                #Add the first found server to the list - we will find rest from here
    #                
    #                bj_server_name = bonjourServer.bonjourName[0].encode('utf-8')
    #                
    #                self.g_serverDict.append({'name'      : bj_server_name.split('.')[0] ,
    #                                     'address'   : bonjourServer.bonjourIP[0]+":"+bonjourServer.bonjourPort[0] ,
    #                                     'discovery' : 'bonjour' , 
    #                                     'token'     : None ,
    #                                     'uuid'      : None })
    #                                     
    #                                     
    #            else:
    #                printl("BonjourFind was not able to discovery any servers")
    # 
    #        except:
    #            print "DreamPlex -> Bonjour Issue.  Possibly not installed on system"
    #            #TODO add message dialog to ask if it should be installed
    #            #===============================================================
    #            # xbmcgui.Dialog().ok("Bonjour Error","Is Bonojur installed on this system?")
    #            #===============================================================
    #===========================================================================
    
        #Set to Disabled       
        else:
            #===================================================================
            # self.g_host = __settings__.getSetting('ipaddress')
            # self.g_port =__settings__.getSetting('port')
            #===================================================================
            
            #!!!!
            self.g_serverDict=[] #we clear g_serverDict because we use plex for now only with one server to seperate them within the plugin
            #!!!!
            
            if not self.g_host or self.g_host == "<none>":
                self.g_host = None
            
            elif not self.g_port:
                printl( "No port defined.  Using default of " + DEFAULT_PORT, self, "I")
                self.g_address = self.g_host + ":" + DEFAULT_PORT
            
            else:
                self.g_address = self.g_host + ":" + self.g_port
                printl( "Settings hostname and port: " + self.g_address, self, "I")
        
            if self.g_address is not None:
                self.g_serverDict.append({'serverName': self.g_name ,
                                     'address'   : self.g_address ,
                                     'discovery' : 'local' , 
                                     'token'     : None ,
                                     'uuid'      : None ,
                                     'role'      : 'master' })    
            
        #=======================================================================
        # if __settings__.getSetting('myplex_user') != "":
        #=======================================================================
        if self.g_myplex_username != "":
            printl( "DreamPlex -> Adding myplex as a server location", self, "I")
            self.g_serverDict.append({'serverName': 'MYPLEX' ,
                                 'address'   : "my.plex.app" ,
                                 'discovery' : 'myplex' , 
                                 'token'     : None ,
                                 'uuid'      : None ,
                                 'role'      : 'master' })
        
        
        printl("DreamPlex -> serverList is " + str(self.g_serverDict), self, "I")
        printl("", self, "C")
 
    #===========================================================================
    # 
    #===========================================================================
    def resolveAllServers(self): # CHECKED
        '''
          Return list of all media sections configured
          within DreamPlex
          @input: None
          @Return: unique list of media sections
        '''
        printl("", self, "C")

        localServers=[]
          
        for servers in self.g_serverDict:
        
            if ( servers['discovery'] == 'local' ) or ( servers['discovery'] == 'bonjour' ):
                localServers += self.getLocalServers()
            elif servers['discovery'] == 'myplex':
                localServers += self.getMyPlexServers()
        
            printl ("Resolved server List: " + str(localServers), self, "I")
        
        '''If we have more than one server source, then
           we need to ensure uniqueness amonst the
           seperate servers.
           
           If we have only one server source, then the assumption
           is that Plex will deal with this for us.
        '''
        
        if len(self.g_serverDict) > 1:
            oneCount=0
            for onedevice in localServers:
            
                twoCount=0
                for twodevice in localServers:
    
                    printl( "["+str(oneCount)+":"+str(twoCount)+"] Checking " + onedevice['uuid'] + " and " + twodevice['uuid'])
    
                    if oneCount == twoCount:
                        printl( "skip" )
                        twoCount+=1
                        continue
                        
                    if onedevice['uuid'] == twodevice['uuid']:
                        printl ( "match" )
                        if onedevice['discovery'] == "local":
                            localServers.pop(twoCount)
                        else:
                            localServers.pop(oneCount)
                    else:
                        printl( "no match" )
                    
                    twoCount+=1
                 
                oneCount+=1
        
        printl("Unique server List: " + str(localServers), self, "I")
        printl("", self, "C")
        return localServers   
