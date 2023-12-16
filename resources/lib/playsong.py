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
            song = wrapper.LibrarySong.wrap(storage.getSong(videoId))
            if not song:
                # fetch from web
                song = self.api.getTrack(videoId)

        # check if not expired before returning
        if url:
            import time
            # utils.log("TIME "+str(utils.paramsToDict(params['url']))+ " "+str(time.time()))
            if int(utils.paramsToDict(url).get('expire', 0)) < time.time():
                url = ''

        if not url:
            # try to fetch from web
            url = self.api.getSongStreamUrl(videoId)

        return song, url

    def __prefetchUrl(self):
        import json
        jsonGetPlaylistPos = '{"jsonrpc":"2.0", "method":"Player.GetProperties", "params":{"playerid":0,"properties":["playlistid","position","percentage"]},"id":1}'
        jsonGetPlaylistItems = '{"jsonrpc":"2.0", "method":"Playlist.GetItems",    "params":{"playlistid":0,"properties":["file","duration"]}, "id":1}'

        # get song position in playlist
        playerProperties = json.loads(xbmc.executeJSONRPC(jsonGetPlaylistPos))
        while 'result' not in playerProperties or playerProperties['result']['percentage'] < 5:
            utils.log("playerProperties: "+repr(playerProperties), xbmc.LOGDEBUG)
            # wait for song playing and playlist ready
            xbmc.sleep(1000)
            playerProperties = json.loads(xbmc.executeJSONRPC(jsonGetPlaylistPos))

        position = playerProperties['result']['position']
        utils.log("position:" + str(position) + " percentage:" + str(playerProperties['result']['percentage']))

        # get next song id and fetch url
        playlistItems = json.loads(xbmc.executeJSONRPC(jsonGetPlaylistItems))
        # utils.log("playlistItems: "+repr(playlistItems), xbmc.LOGDEBUG)

        if 'items' not in playlistItems['result']:
            utils.log("empty playlist")
            return

        if position + 1 >= len(playlistItems['result']['items']):
            utils.log("playlist end:: position " + repr(position) + " size " + repr(len(playlistItems['result']['items'])))
            return

        videoId_next = utils.paramsToDict(
            playlistItems['result']['items'][position + 1]['file']).get("videoId")

        stream_url = self.api.getSongStreamUrl(videoId_next)
        utils.set_mem_cache(videoId_next, stream_url)

