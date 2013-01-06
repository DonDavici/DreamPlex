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
from Components.config import config

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

    
#===========================================================================
# 
#===========================================================================
def getTranscodeUrl(picturePointer, selection, width, height):
    '''
    '''
    printl("",__name__ , "S")
    
    picUrl = "unknown"
    
    serverPicData = selection[1][picturePointer]
    printl("serverPicData: " + str(serverPicData), __name__, "D")
    
    try:
        if selection[1][picturePointer].split('/')[0] == "http:":
            picData =  serverPicData
        else:    
            picData= str("http://" + selection[1]["server"] + serverPicData)
        
        picUrl = 'http://%s/photo/:/transcode?url=%s&width=%s&height=%s' % (selection[1]["server"], urllib.quote_plus(picData), width, height)
    except:
        printl( "something is wrong with the picture", __name__, "W")

    

    printl("", __name__, "C")
    return picUrl

#===============================================================================
# 
#===============================================================================
def getPictureData(selection, postfix):
    '''
    '''
    printl("", __name__, "S")
    
    mediaPath = config.plugins.dreamplex.mediafolderpath.value
    
    if selection[1]["Id"] is None or selection[1]["Id"] == "None" or selection[1]["Id"] == "":
        target = "None"
    else:
        try:
            name = selection[1]["Id"]
            target = mediaPath + name + postfix
        except:
            target = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/all/picreset.png"
            printl( "something went wrong", __name__, "D")
    
    printl("", __name__, "C")
    return target    
    