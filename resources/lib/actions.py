import os
import utils
import xbmc
import xbmcgui

import api


class Actions:
    def __init__(self):
        self.api = api.Api()
        self.lang = utils.addon.getLocalizedString

    def executeAction(self, action, params):
        if action == "play_all":
            utils.playAll(self._getSongs(params),
                          'shuffle' in params, params.get('videoId'))
        elif action == "add_to_queue":
            self.addToQueue(params)
            self.notify(self.lang(30110))
        elif action == "update_playlists":
            self.api.load_playlists()
        elif action == "clear_cache":
            utils.log("Clearing cache...")
            self.clearCache()
        elif action == "clear_oauth_cache":
            utils.log("Clearing auth cache...")
            self.api.clear_auth_cache()
        elif action == "add_favourite":
            self.addFavourite(params.pop("title"), params)
            self.notify(self.lang(30110))
        elif action == "add_library":
            self.api.addStoreTrack(params["videoId"])
            self.notify(self.lang(30103))
        elif action == "add_album_library":
            for track in self.api.getAlbum(params["album_id"]):
                self.api.addStoreTrack(track["videoId"])
            self.notify(self.lang(30103))
        elif action == "add_playlist":
            self.addToPlaylist(params["videoId"])
        elif action == "del_from_playlist":
            self.api.delFromPlaylist(params["playlist_id"], params["videoId"])
            self.notify(self.lang(30110))
        elif action == "update_library":
            self.clearCache()
            xbmc.executebuiltin("RunPlugin(%s)" % utils.addon_url)
        elif action == "search":
            xbmc.executebuiltin(
                "ActivateWindow(10502,%s/?path=search_result&query=%s)" % (utils.addon_url, params.get('filter_criteria')))
        elif action == "set_thumbs":
            self.setThumbs(params["videoId"])
        elif action == "create_playlist":
            keyboard = xbmc.Keyboard('', self.lang(30413))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                self.api.createPlaylist(keyboard.getText())
                self.notify(self.lang(30110))
        elif action == "delete_playlist":
            if xbmcgui.Dialog().yesno(self.lang(30405), self.lang(30406), '"' + params["title"] + '"'):
                self.api.deletePlaylist(params["playlist_id"])
                xbmc.executebuiltin("ActivateWindow(10502,%s/?path=library)" % utils.addon_url)
                self.notify(self.lang(30110))
        elif action == "artist_topsongs":
            artist_id = self.api.getApi().get_track_info(params["videoId"])['artistId'][0]
            xbmc.executebuiltin("ActivateWindow(10502,%s/?path=artist_topsongs&artistid=%s)" % (utils.addon_url, artist_id))
        else:
            utils.log("Invalid action: " + action)

    def notify(self, text):
        xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, text, utils.addon.getAddonInfo('icon')))

    def addToQueue(self, params):
        songs = self._getSongs(params)

        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

        for song in songs:
            playlist.add(utils.getUrl(song), utils.createItem(song['display_name'], song['albumart']))


    def clearCache(self):
        try:
            self.api.clearCache()
            self.notify(self.lang(30110))
        except Exception as e:
            utils.log(repr(e))
            self.notify(self.lang(30106))

    def addToPlaylist(self, videoId):
        playlists = self.api.getPlaylists()
        plist = [pl_name for pl_id, pl_name, pl_arturl in playlists]
        selected = xbmcgui.Dialog().select(self.lang(30401), plist)
        if selected > 0:
            self.api.addToPlaylist(playlists[selected][0], videoId)
            self.notify(self.lang(30110))

    def setThumbs(self, videoId):
        options = [self.lang(30410), self.lang(30412), self.lang(30411)]
        selected = xbmcgui.Dialog().select(self.lang(30409), options)
        if selected >= 0:
            thumbs = {'0': 'LIKE', '1': 'INDIFFERENT', '2': 'DISLIKE'}[str(selected)]
            self.api.set_rating(videoId, thumbs)
            self.notify(self.lang(30110))

    def _getSongs(self, params):
        get = params.get

        if get('playlist_id'):
            utils.log("Loading playlist: " + get('playlist_id'))
            songs = self.api.getPlaylistSongs(get('playlist_id'))
        elif get('album_id'):
            utils.log("Loading album: " + get('album_id'))
            songs = self.api.getAlbum(get('album_id'))
        elif get('artist_id'):
            utils.log("Loading artist top tracks: " + get('artist_id'))
            songs = self.api.getArtistInfo(get('artist_id'))['tracks']
        else:
            songs = self.api.getFilterSongs(get('filter_type'), get('filter_criteria'), get('artist'))

        return songs

