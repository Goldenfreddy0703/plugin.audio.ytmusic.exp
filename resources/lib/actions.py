import os
import utils
import wrapper
import xbmc
import xbmcgui

import api


class Actions:
    def __init__(self):
        self.api = api.Api()
        self.lang = utils.addon.getLocalizedString

    def executeAction(self, action, params, return_params):
        utils.log("action called with return_params: ", xbmc.LOGDEBUG, log_object=return_params)
        if action == "play_all":
            utils.playAll(self._getSongs(params),
                          'shuffle' in params, params.get('videoId'))
        elif action == "add_to_queue":
            self.addToQueue(params)
            self.notify(self.lang(30425))
        elif action == "play_next":
            self.playNext(params)
            self.notify(self.lang(30425))
        elif action == "update_playlists":
            self.api.load_playlists()
        elif action == "clear_cache":
            utils.log("Clearing cache...")
            self.clearCache()
        elif action == "clear_playlist_cache":
            utils.log("Clearing playlist cache...")
            from storage import storage
            storage.curs.execute("DELETE FROM playlists_songs")
            storage.conn.commit()
            self.api.load_playlists()
            self.notify("Playlist cache cleared. All songs will now be loaded.")
            xbmc.executebuiltin('Container.Refresh')
        elif action == "clear_oauth_cache":
            utils.log("Clearing auth cache...")
            self.api.clear_auth_cache()
        elif action == "add_library":
            self.api.getApi().edit_song_library_status(params["token"])
            if utils.addon.getSetting('auto_update') == 'true':
                self.clearCache()
                xbmc.executebuiltin("RunPlugin(%s)" % utils.addon_url)
            else:
                self.notify(self.lang(30418))
        elif action == "remove_library":
            self.api.delSongFromLibrary(params['video_id'], params['token'])
            self.notify(self.lang(30425))
            xbmc.executebuiltin('Container.Refresh')
        elif action == "add_album_library":
            for track in self.api.getAlbum(params["album_id"]):
                if track.add_token:
                    self.api.getApi().edit_song_library_status(track.add_token)
                else:
                    self.notify(self.lang(30427))
            if utils.addon.getSetting('auto_update') == 'true':
                self.clearCache()
                xbmc.executebuiltin("RunPlugin(%s)" % utils.addon_url)
            else:
                self.notify(self.lang(30418))
        elif action == "remove_album_library":
            if self.api.delAlbumFromLibrary(params['album_id']):
                xbmc.executebuiltin('Container.Refresh')
            else:
                self.notify(self.lang(30427))
        elif action == "add_to_playlist":
            self.addToPlaylist(params["videoId"])
            self.notify(self.lang(30425))
        elif action == "del_from_playlist":
            self.api.delFromPlaylist(params["playlist_id"], params["videoId"])
            xbmc.executebuiltin('Container.Refresh')
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
                self.notify(self.lang(30425))
        elif action == "delete_playlist":
            if xbmcgui.Dialog().yesno(self.lang(30405), self.lang(30406), '"' + params["title"] + '"'):
                self.api.deletePlaylist(params["playlist_id"])
                xbmc.executebuiltin("ActivateWindow(10502,%s/?path=library)" % utils.addon_url)
                self.notify(self.lang(30425))
        elif action == "subscribe_artist":
            self.api.getApi().subscribe_artists([params["artist_id"]])
            self.notify(self.lang(30425))
        elif action == "unsubscribe_artist":
            self.api.getApi().unsubscribe_artists([params["artist_id"]])
            xbmc.executebuiltin('Container.Refresh')
        elif action == "artist_topsongs":
            #artist_id = self.api.getApi().get_track_info(params["videoId"])['artistId'][0]
            #artist_id = self.api.getApi().get_song(params["videoId"])['videoDetails']['channelId']
            xbmc.executebuiltin("ActivateWindow(10502,%s/?path=artist_topsongs&artistid=%s)" % (utils.addon_url, params.get('artistid')))
        elif action == "goto_album":
            xbmc.executebuiltin(
                "ActivateWindow(10502,%s/?path=store_album&album_id=%s)" % (utils.addon_url, params.get('album_id')))
        elif action == "goto_artist":
            xbmc.executebuiltin(
                "ActivateWindow(10502,%s/?path=search_result&query=%s&artistid=%s)" % (utils.addon_url, params.get('query'), params.get('artistid')))
        elif action == "add_playlist":
            self.api.getApi().rate_playlist(params["playlist_id"],"LIKE")
            self.api.load_playlists()
            self.notify(self.lang(30425))
        elif action == "remove_playlist":
            self.api.removePlaylist(params["playlist_id"])
            xbmc.executebuiltin('Container.Refresh')
        elif action == "start_radio":
            # Start radio based on song, artist, album, or playlist
            radio_type = params.get('type', 'song')
            if radio_type == 'song':
                # Start song radio using watch playlist
                videoId = params.get('videoId')
                watch_playlist = self.api.getApi().get_watch_playlist(videoId=videoId, radio=True)
                if watch_playlist and 'tracks' in watch_playlist:
                    songs = wrapper.Song.wrap(watch_playlist['tracks'])
                    utils.playAll(songs, shuffle=True)
                    self.notify("Started song radio")
            elif radio_type == 'artist':
                # Start artist radio
                artist_id = params.get('id')
                watch_playlist = self.api.getApi().get_watch_playlist(radioId=f"RDAO{artist_id}")
                if watch_playlist and 'tracks' in watch_playlist:
                    songs = wrapper.Song.wrap(watch_playlist['tracks'])
                    utils.playAll(songs, shuffle=True)
                    self.notify("Started artist radio")
            elif radio_type == 'playlist':
                # Start playlist radio
                playlist_id = params.get('id')
                watch_playlist = self.api.getApi().get_watch_playlist(playlistId=playlist_id, radio=True)
                if watch_playlist and 'tracks' in watch_playlist:
                    songs = wrapper.Song.wrap(watch_playlist['tracks'])
                    utils.playAll(songs, shuffle=True)
                    self.notify("Started playlist radio")
        elif action == "view_lyrics":
            # Get and display song lyrics
            videoId = params.get('videoId')
            try:
                lyrics_browse_id = self.api.getApi().get_watch_playlist(videoId=videoId).get('lyrics')
                if lyrics_browse_id:
                    lyrics_data = self.api.getApi().get_lyrics(lyrics_browse_id)
                    if lyrics_data and 'lyrics' in lyrics_data:
                        lyrics_text = lyrics_data['lyrics']
                        # Display lyrics in a text viewer
                        dialog = xbmcgui.Dialog()
                        dialog.textviewer(f"Lyrics: {params.get('display_name', 'Unknown')}", lyrics_text)
                    else:
                        self.notify("No lyrics available")
                else:
                    self.notify("No lyrics available")
            except Exception as e:
                utils.log(f"Error getting lyrics: {str(e)}")
                self.notify("Error loading lyrics")
        elif action == "edit_playlist":
            # Edit playlist details (name and description)
            playlist_id = params["playlist_id"]
            current_title = params.get("title", "")
            
            # Get new title
            keyboard = xbmc.Keyboard(current_title, self.lang(30438))  # Edit playlist name
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                new_title = keyboard.getText()
                try:
                    self.api.getApi().edit_playlist(playlist_id, title=new_title)
                    self.notify("Playlist updated")
                    xbmc.executebuiltin('Container.Refresh')
                except Exception as e:
                    utils.log(f"Error editing playlist: {str(e)}")
                    self.notify("Error updating playlist")
        elif action == "share_playlist":
            # Generate shareable link for playlist
            playlist_id = params["playlist_id"]
            share_url = f"https://music.youtube.com/playlist?list={playlist_id}"
            # Copy to clipboard (if possible) or show dialog
            dialog = xbmcgui.Dialog()
            dialog.ok("Share Playlist", f"Playlist URL:\n{share_url}")
        elif action == "play_song":
            # Play single song (different from play_all)
            from playsong import PlaySong
            PlaySong().play(params)
        elif action == "view_artist_albums":
            # Navigate to artist albums page
            artist_id = params.get('artist_id')
            xbmc.executebuiltin(f"ActivateWindow(10502,{utils.addon_url}/?path=artist_albums&artistid={artist_id})")
        elif action == "view_artist_singles":
            # Navigate to artist singles page
            artist_id = params.get('artist_id')
            xbmc.executebuiltin(f"ActivateWindow(10502,{utils.addon_url}/?path=artist_singles&artistid={artist_id})")
        elif action == "view_related_artists":
            # Navigate to related artists page
            artist_id = params.get('artist_id')
            xbmc.executebuiltin(f"ActivateWindow(10502,{utils.addon_url}/?path=related_artists&artistid={artist_id})")
        else:
            utils.log("Invalid action: " + action, xbmc.LOGERROR)

        if utils.headless_mode and return_params:
            from navigation import Navigation; Navigation(return_params, {}).listMenu() # shows previous Menu


    def notify(self, text):
        xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, text, utils.addon.getAddonInfo('icon')))

    def addToQueue(self, params):
        songs = self._getSongs(params)

        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

        for song in songs:
            playlist.add(utils.getUrl(song), utils.createItem(song))

    def playNext(self, params):
        songs = self._getSongs(params)

        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        position = playlist.getposition() + 1

        for song in songs:
            playlist.add(utils.getUrl(song), utils.createItem(song), position)

    def clearCache(self):
        try:
            self.api.clearCache()
            self.notify(self.lang(30425))
        except Exception as e:
            utils.log(repr(e), xbmc.LOGERROR)
            self.notify(self.lang(30421))

    def addToPlaylist(self, videoId):
        playlists = list(self.api.get_playlists())
        playlist_names = [playlist.playlist_name for playlist in playlists]
        selected = xbmcgui.Dialog().select(self.lang(30401), playlist_names)
        if selected > 0:
            self.api.addToPlaylist(playlists[selected].playlist_id, videoId)
            self.notify(self.lang(30425))

    def setThumbs(self, videoId):
        options = [self.lang(30410), self.lang(30412), self.lang(30411)]
        selected = xbmcgui.Dialog().select(self.lang(30409), options)
        if selected >= 0:
            thumbs = {'0': 'LIKE', '1': 'INDIFFERENT', '2': 'DISLIKE'}[str(selected)]
            self.api.set_rating(videoId, thumbs)
            self.notify(self.lang(30425))

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
        elif get('videoId'):
            utils.log("Loading video: " + get('videoId'))
            songs = [self.api.getTrack(get('videoId'))]
        else:
            songs = self.api.getFilterSongs(get('filter_type'), get('filter_criteria'), get('artist_name'))

        return songs

