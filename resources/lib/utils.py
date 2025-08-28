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
client_id = addon.getSetting('youtube.api.id')
if client_id != '' and client_id[-27:] != ".apps.googleusercontent.com":
    client_id = client_id + ".apps.googleusercontent.com"    
client_secret = addon.getSetting('youtube.api.secret')
colored_titles = addon.getSetting('colored_titles') == 'true'
headless_mode = addon.getSetting('headless_mode') == 'true'
use_infoLabels = xbmc.getInfoLabel('System.BuildVersion').split()[0] < '21'
icon_path = os.path.join(
    xbmcaddon.Addon().getAddonInfo('path'),
    'resources', 'media', 'themes',
    addon.getSetting("icon_theme")
)


def enhance_thumbnail_quality(url):
    """
    Enhance thumbnail quality by modifying Google/YouTube thumbnail URLs
    Examples:
    - googleusercontent.com URLs: Remove size limits (=s0?imgmax=0)
    - YouTube URLs: Request maximum resolution
    """
    if not url:
        return url
        
    # Google Photos/YouTube thumbnails from googleusercontent.com
    if 'googleusercontent.com' in url:
        # Remove existing size parameters and add high-quality ones
        if '=' in url:
            base_url = url.split('=')[0]
        else:
            base_url = url
        # s0 = original size, imgmax=0 = no size limit
        return f"{base_url}=s0?imgmax=0"
    
    # YouTube direct thumbnails
    if 'ytimg.com' in url or 'youtube.com' in url:
        # Don't modify if already maxresdefault
        if 'maxresdefault.jpg' in url:
            return url
        # Try to get the highest quality version
        elif 'default.jpg' in url:
            return url.replace('default.jpg', 'maxresdefault.jpg')
        elif 'hqdefault.jpg' in url:
            return url.replace('hqdefault.jpg', 'maxresdefault.jpg')
        elif 'mqdefault.jpg' in url:
            return url.replace('mqdefault.jpg', 'maxresdefault.jpg')
        elif 'sddefault.jpg' in url:
            return url.replace('sddefault.jpg', 'maxresdefault.jpg')
    
    # Return original URL if no enhancement possible
    return url


def is_generic_thumbnail(url):
    """
    Check if thumbnail is a generic/low-quality YouTube thumbnail
    that should be replaced with YouTube v3 API data
    """
    if not url:
        return True
    
    # These are generic/low-quality thumbnails from ytimg.com
    generic_patterns = [
        'oardefault.jpg',  # Generic channel thumbnail
        'default.jpg',     # Very low quality
        'mqdefault.jpg',   # Medium quality but still low
        'hqdefault.jpg'    # High quality but not the best
    ]
    
    return any(pattern in url for pattern in generic_patterns)


# Global cache for batched YouTube API results
_youtube_thumbnail_cache = {}

def get_youtube_thumbnails_batch(video_ids):
    """
    Get thumbnails for multiple videos in a single YouTube v3 API request
    Returns dict: {video_id: best_thumbnail_url}
    """
    if not video_ids:
        return {}
    
    # Filter out IDs we already have cached
    uncached_ids = [vid for vid in video_ids if vid not in _youtube_thumbnail_cache]
    
    if uncached_ids:
        try:
            api_key = addon.getSetting('youtube_api_key')
            if api_key:
                import requests
                
                # YouTube API supports up to 50 IDs per request
                batch_size = 50
                for i in range(0, len(uncached_ids), batch_size):
                    batch_ids = uncached_ids[i:i + batch_size]
                    
                    url = "https://www.googleapis.com/youtube/v3/videos"
                    params = {
                        'part': 'snippet',
                        'id': ','.join(batch_ids),
                        'key': api_key,
                        'fields': 'items(id,snippet/thumbnails)'
                    }
                    
                    log(f"Fetching thumbnails for {len(batch_ids)} videos in single API request")
                    response = requests.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('items', [])
                        
                        for item in items:
                            video_id = item.get('id')
                            if video_id and 'snippet' in item:
                                thumbnails = item['snippet'].get('thumbnails', {})
                                
                                # Priority order: maxres > high > medium > default
                                best_url = None
                                for quality in ['maxres', 'high', 'medium', 'default']:
                                    if quality in thumbnails:
                                        best_url = thumbnails[quality]['url']
                                        break
                                
                                _youtube_thumbnail_cache[video_id] = best_url or f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                    
                    # Cache fallback URLs for failed requests
                    for video_id in batch_ids:
                        if video_id not in _youtube_thumbnail_cache:
                            _youtube_thumbnail_cache[video_id] = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            else:
                # No API key, use direct URLs
                for video_id in uncached_ids:
                    _youtube_thumbnail_cache[video_id] = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                    
        except Exception as e:
            log(f"YouTube batch API error: {e}")
            # Cache fallback URLs for failed requests
            for video_id in uncached_ids:
                _youtube_thumbnail_cache[video_id] = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    
    # Return results for requested IDs
    return {vid: _youtube_thumbnail_cache.get(vid, f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg") for vid in video_ids}

def get_youtube_thumbnail_fallback(video_id):
    """
    Get better thumbnail using YouTube v3 API (single video - uses cache)
    """
    if not video_id:
        return ""
    
    # Check cache first
    if video_id in _youtube_thumbnail_cache:
        return _youtube_thumbnail_cache[video_id]
    
    # If not cached, make a single request
    result = get_youtube_thumbnails_batch([video_id])
    return result.get(video_id, f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg")


def pre_fetch_thumbnails_for_items(items, get_video_id_func, get_thumbnails_func):
    """
    Pre-fetch YouTube thumbnails for a list of items to optimize batch loading
    
    Args:
        items: List of items (songs, albums, etc.)
        get_video_id_func: Function to extract video_id from an item
        get_thumbnails_func: Function to extract thumbnails from an item
    """
    video_ids_for_batch = []
    
    for item in items:
        video_id = get_video_id_func(item)
        if video_id:
            thumbnails = get_thumbnails_func(item)
            if thumbnails:
                # Check if this might need YouTube API fallback
                best_thumb = None
                max_pixels = 0
                for thumb in thumbnails:
                    if thumb and thumb.get('url'):
                        width = thumb.get('width', 0)
                        height = thumb.get('height', 0)
                        pixels = width * height
                        if pixels > max_pixels:
                            max_pixels = pixels
                            best_thumb = thumb
                
                if best_thumb and is_generic_thumbnail(best_thumb.get('url', '')):
                    video_ids_for_batch.append(video_id)
    
    # Pre-fetch all YouTube thumbnails in batches
    if video_ids_for_batch:
        log(f"Pre-fetching thumbnails for {len(video_ids_for_batch)} videos in batch requests")
        get_youtube_thumbnails_batch(video_ids_for_batch)
        return len(video_ids_for_batch)
    
    return 0


def get_best_thumbnail(thumbnails, video_id=None):
    """
    Get the best quality thumbnail from a thumbnails array, with smart fallback
    Works for both YTMusic API and YouTube v3 API ordering
    Uses YouTube v3 API fallback for generic thumbnails when video_id is available
    """
    if not thumbnails or len(thumbnails) == 0:
        # No thumbnails provided, try YouTube v3 API fallback
        if video_id:
            return get_youtube_thumbnail_fallback(video_id)
        return ""
    
    # Find the highest quality thumbnail by comparing width/height
    best_thumbnail = None
    max_pixels = 0
    
    for thumb in thumbnails:
        if thumb and thumb.get('url'):
            # Calculate total pixels (width * height)
            width = thumb.get('width', 0)
            height = thumb.get('height', 0)
            pixels = width * height
            
            if pixels > max_pixels:
                max_pixels = pixels
                best_thumbnail = thumb
    
    if best_thumbnail:
        url = best_thumbnail.get('url', '')
        
        # Check if this is a generic thumbnail that should be replaced
        if is_generic_thumbnail(url):
            if video_id:
                log(f"Replacing generic thumbnail with YouTube v3 API for video {video_id}")
                return get_youtube_thumbnail_fallback(video_id)
            # No video_id available, enhance what we have
            return enhance_thumbnail_quality(url)
        else:
            # Good thumbnail, just enhance it
            return enhance_thumbnail_quality(url)
    
    # Fallback: if no width/height data, use last thumbnail (works for YTMusic)
    fallback_url = thumbnails[-1]['url']
    if is_generic_thumbnail(fallback_url) and video_id:
        log(f"Replacing generic fallback thumbnail with YouTube v3 API for video {video_id}")
        return get_youtube_thumbnail_fallback(video_id)
    
    return enhance_thumbnail_quality(fallback_url)
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
    
    # Use new Kodi v21+ InfoTagMusic instead of deprecated setInfo
    music_tag = li.getMusicInfoTag()
    music_tag.setTitle(song.title)
    music_tag.setAlbum(song.album_title)
    music_tag.setArtist(song.artist_name)
    music_tag.setMediaType('song')
    
    # Debug: Log duration information
    duration_value = getattr(song, 'duration', None)
    log(f"DURATION DEBUG: {song.title} - duration: {duration_value}, type: {type(duration_value)}", xbmc.LOGINFO)
    
    if song.duration and song.duration > 0:
        music_tag.setDuration(song.duration)
        log(f"DURATION SET: {song.title} - {song.duration} seconds", xbmc.LOGINFO)
    else:
        log(f"DURATION NOT SET: {song.title} - duration is {song.duration}", xbmc.LOGWARNING)
    
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

    if not content:
        content = 'addon'
    if addon.getSetting('general.viewtype') == 'true':
        if addon.getSetting('general.viewidswitch') == 'true':
            # Use integer view types
            xbmc.executebuiltin('Container.SetViewMode(%d)' % int(addon.getSetting('general.%s.view.id' % content)))
        else:
            # Use optional view types
            xbmc.executebuiltin('Container.SetViewMode(%d)' % int(addon.getSetting('general.%s.view' % content)))

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