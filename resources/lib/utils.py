import os
import sys
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import urllib.parse

# xbmc hooks
addon = xbmcaddon.Addon()

# plugin constants
plugin = 'YtMusicEXP-' + addon.getAddonInfo('version')
dbg = addon.getSetting('debug') == 'true'
addon_url = sys.argv[0]
handle = int(sys.argv[1])
song_url = sys.argv[0] + "?action=play_song&videoId=%s&title=%s&artist=%s&albumart=%s&album=%s&duration=%s&isVideo=%s    "
colored_titles = addon.getSetting('colored_titles') == 'true'
use_infoLabels = xbmc.getInfoLabel('System.BuildVersion').split()[0] < '21'
icon_path = os.path.join(
    xbmcaddon.Addon().getAddonInfo('path'),
    'resources', 'media', 'themes',
    addon.getSetting("icon_theme")
) if xbmc.getCondVisibility('System.HasAddon()') else None

def debug():
    import web_pdb; web_pdb.set_trace()


# utility functions
def log(message, log_level=xbmc.LOGINFO, log_object=None):
    if dbg or log_level >= xbmc.LOGWARNING:
        if log_object:
            xbmc.log("[%s] %s %s" % (plugin, message, repr(log_object)), log_level)
        else:
            xbmc.log("[%s] %s" % (plugin, message), log_level)


def paramsToDict(parameters):
    """ Convert parameters encoded in a URL to a dict. """
    paramDict = {}
    if parameters:
        paramPairs = parameters.split('?')[1].split('&')
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            # try:
            paramDict[paramSplits[0]] = urllib.parse.unquote_plus(
                paramSplits[1])
            # except IndexError:
            #    pass
    return paramDict


def createItem(song):  # , fanart):
    li = xbmcgui.ListItem(song.title, offscreen=True)
    li.setArt({'thumb': song.thumbnail})  # , 'fanart': fanart})
    li.setProperties({'IsPlayable': 'true'}) 
    li.setContentLookup(False)
    infoLabels = {'album': song.album_title, 'title': song.title}
    if song.duration and song.duration > 0:
        infoLabels['duration'] = song.duration
    # if song.is_video:
    #     infoLabels['mediatype'] = 'musicvideo'
    #     infoLabels['artist'] = [song.artist_name]
    #     li.setInfo(type='Video', infoLabels=infoLabels)
    # else:
    infoLabels['mediatype'] = 'song'
    infoLabels['artist'] = song.artist_name
    li.setInfo(type='Music', infoLabels=infoLabels)
    return li


def setResolvedUrl(list_item):
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=list_item)


def setDirectory(list_items, content, sort_methods):
    # log("SETDIRECTORY "+repr(list_items))
    xbmcplugin.addDirectoryItems(handle, list_items, len(list_items))
    if handle > 0:
        xbmcplugin.setContent(handle, content)

    for sorts in sort_methods:
        xbmcplugin.addSortMethod(int(sys.argv[1]), sorts)

    xbmcplugin.endOfDirectory(handle, succeeded=True)


def tryEncode(text, encoding='utf-8'):
    try:
        if sys.platform.startswith('linux'):
            return text.encode('latin1', errors='ignore')
        return text.encode(encoding, errors='ignore')
    except UnicodeEncodeError:
        # log(" ENCODING FAIL!!! " + encoding + " " + repr(text))
        return repr(text)


def getUrl(song):
    # log(repr(song))
    url = song_url % (song.video_id, urllib.parse.quote_plus(song.title), urllib.parse.quote_plus(song.artist_name), song.thumbnail,
                      urllib.parse.quote_plus(song.album_title), song.duration, song.is_video)
    return url


def playAll(songs, shuffle=False, fromhere=''):
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()

    fromhereSong = None
    for song in songs:
        if song.video_id != fromhere:
            playlist.add(getUrl(song), createItem(song))
        else:
            fromhereSong = song

    if shuffle or fromhere:
        playlist.shuffle()

    if fromhere:
        playlist.add(getUrl(fromhereSong), createItem(fromhereSong), 0)

    xbmc.executebuiltin('Playlist.Playoffset(music,0)')


def get_mem_cache(key):
    try:
        # log("MEM CACHE "+repr(xbmcgui.getCurrentWindowId())+" "+xbmcgui.Window(xbmcgui.getCurrentWindowId()).getProperty('gpmusic_' + key))
        return eval(xbmcgui.Window(10000).getProperty('ytmusic_' + key))
    except SyntaxError as se:
        # log("ERROR "+repr(se))
        return None


def set_mem_cache(key, value):
    xbmcgui.Window(10000).setProperty('ytmusic_' + key, repr(value))


def get_system_version():
    try:
        import json
        json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", '
                                         '"params": {"properties": ["version", "name"]}, "id": 1 }')
        json_query = str(json_query)
        json_query = json.loads(json_query)

        version_installed = json_query['result']['version']
        return (version_installed.get('major', 1), version_installed.get('minor', 0))
    except:
        return (1, 0)  # Frodo
    
def getTitle(text, isFolder = False):
    if colored_titles:
        return "[COLOR orange]*** %s ***[/COLOR]%s" % (text, ' +>' if isFolder else '')

    else:
        return "*** %s ***%s" % (str.upper(text), ' +>' if isFolder else '')

def get_icon_path(icon):
    return os.path.join(icon_path, icon)