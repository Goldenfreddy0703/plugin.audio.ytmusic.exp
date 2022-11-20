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
song_url = sys.argv[0] + "?action=play_song&videoId=%s&title=%s&artist=%s&albumart=%s&album=%s"

def debug():
    import web_pdb; web_pdb.set_trace()

# utility functions
def log(message):
    if dbg:
        xbmc.log("[%s] %s" % (plugin, message), xbmc.LOGINFO)


def paramsToDict(parameters):
    """ Convert parameters encoded in a URL to a dict. """
    paramDict = {}
    if parameters:
        paramPairs = parameters.split('?')[1].split('&')
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            #try:
            paramDict[paramSplits[0]] = urllib.parse.unquote_plus(
                paramSplits[1])
            #except IndexError:
            #    pass
    return paramDict


def createItem(title, thumb): #, fanart):
    li = xbmcgui.ListItem(title, offscreen=True)
    li.setArt({'thumb': thumb})#, 'fanart': fanart})
    li.setProperties({'IsPlayable': 'true'}) 
    li.setContentLookup(False)
    return li


def setResolvedUrl(list_item):
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=list_item)


def setDirectory(list_items, content, sort_methods):
    #log("SETDIRECTORY "+repr(list_items))
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
    #log(repr(song))
    url = song_url % (song['videoId'], urllib.parse.quote_plus(song['title']), urllib.parse.quote_plus(song['artist']), song['albumart'],
                      urllib.parse.quote_plus(song['album']['name'] if not isinstance(song['album'],str) else song['album']))
    return url


def playAll(songs, shuffle=False, fromhere=''):
    player = xbmc.Player()
    if player.isPlaying():
        player.stop()

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()

    fromhereSong = None
    for song in songs:
        if song['videoId'] != fromhere:
            item = createItem(song['display_name'], song['albumart'])
            item.setInfo(type='music', infoLabels={'artist': song['artist'], 'title': song['title']})
            playlist.add(getUrl(song), item)
        else:
            fromhereSong = song

    if shuffle or fromhere:
        playlist.shuffle()

    if fromhere:
        item = createItem(fromhereSong['display_name'], fromhereSong['albumart'])
        item.setInfo(type='music', infoLabels={'artist': fromhereSong['artist'], 'title': fromhereSong['title']})
        playlist.add(getUrl(fromhereSong), item, 0)

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

