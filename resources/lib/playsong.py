import api
import utils
import xbmc
import wrapper
from storage import storage


class PlaySong:

    def __init__(self):
        self.api = api.Api()

    def play(self, params):

        song, url = self.__getSongStreamUrl(wrapper.SongFromParams(params))
        utils.log("Playing Song: %s - %r " % (song.title, url))

        mime = utils.paramsToDict(url).get('mime', 'audio/mpeg')

        li = utils.createItem(song)
        li.setProperty('mimetype', mime)
        li.setContentLookup(False)
        li.setPath(url)

        utils.setResolvedUrl(li)

        self.__prefetchUrl()
 
    def __getSongStreamUrl(self, song):
        # try to fetch from memory first
        videoId = song.video_id
        url = utils.get_mem_cache(videoId)

        # if no metadata
        if not song.title:
            song = self.api.getSong(videoId)

        # check if not expired before returning
        if url:
            import time
            # utils.log("TIME "+str(utils.paramsToDict(params['url']))+ " "+str(time.time()))
            expire_time = int(utils.paramsToDict(url).get('expire', 0))
            current_time = time.time()
            # Add buffer time (60 seconds) to prevent URLs from expiring during playback
            if expire_time < (current_time + 60):
                utils.log("Stream URL expired or will expire soon for " + videoId + ", refreshing...")
                url = ''

        if not url:
            # try to fetch from web with retry mechanism for improved reliability
            max_retries = 2
            retry_count = 0
            while retry_count < max_retries and not url:
                try:
                    url = self.api.getSongStreamUrl(videoId)
                    if url:
                        utils.log("Successfully fetched stream URL for: " + videoId + " (attempt " + str(retry_count + 1) + ")")
                    else:
                        utils.log("Failed to fetch stream URL for: " + videoId + " (attempt " + str(retry_count + 1) + ")")
                except Exception as e:
                    utils.log("Error fetching stream URL for " + videoId + " (attempt " + str(retry_count + 1) + "): " + str(e))
                
                retry_count += 1
                if retry_count < max_retries and not url:
                    utils.log("Retrying in 1 second...")
                    import time
                    time.sleep(1)

        return song, url

    def __prefetchUrl(self):
        import json
        jsonGetPlaylistPos = '{"jsonrpc":"2.0", "method":"Player.GetProperties", "params":{"playerid":0,"properties":["playlistid","position","percentage"]},"id":1}'
        jsonGetPlaylistItems = '{"jsonrpc":"2.0", "method":"Playlist.GetItems",    "params":{"playlistid":0,"properties":["file","duration"]}, "id":1}'

        # get song position in playlist
        playerProperties = json.loads(xbmc.executeJSONRPC(jsonGetPlaylistPos))
        while 'result' not in playerProperties or playerProperties['result']['percentage'] < 5:
            utils.log(message="playerProperties: ", log_object=playerProperties, log_level=xbmc.LOGDEBUG)
            # wait for song playing and playlist ready
            xbmc.sleep(1000)
            playerProperties = json.loads(xbmc.executeJSONRPC(jsonGetPlaylistPos))

        # Add delay to ensure stability across all platforms
        utils.log("Adding delay for prefetch stability")
        xbmc.sleep(2000)

        position = playerProperties['result']['position']
        utils.log("position:" + str(position) + " percentage:" + str(playerProperties['result']['percentage']))

        # get next song id and fetch url
        playlistItems = json.loads(xbmc.executeJSONRPC(jsonGetPlaylistItems))
        utils.log(message="playlistItems: ", log_object=playlistItems, log_level=xbmc.LOGDEBUG)

        if 'items' not in playlistItems['result']:
            utils.log("empty playlist")
            return

        if position + 1 >= len(playlistItems['result']['items']):
            utils.log("playlist end:: position " + repr(position) + " size " + repr(len(playlistItems['result']['items'])))
            return

        next_item = playlistItems['result']['items'][position + 1]['file']
        if next_item[:len(utils.addon_url)] == utils.addon_url:
            videoId_next = utils.paramsToDict(next_item).get("videoId")
            # Retry mechanism for improved reliability across all platforms
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    stream_url = self.api.getSongStreamUrl(videoId_next)
                    if stream_url:
                        utils.set_mem_cache(videoId_next, stream_url)
                        utils.log("Successfully prefetched URL for: " + videoId_next + " (attempt " + str(retry_count + 1) + ")")
                        break
                    else:
                        utils.log("Failed to get stream URL for: " + videoId_next + " (attempt " + str(retry_count + 1) + ")")
                except Exception as e:
                    utils.log("Error prefetching URL for " + videoId_next + " (attempt " + str(retry_count + 1) + "): " + str(e))
                
                retry_count += 1
                if retry_count < max_retries:
                    utils.log("Retrying in 2 seconds...")
                    xbmc.sleep(2000)
