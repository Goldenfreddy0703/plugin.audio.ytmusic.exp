import utils
import xbmc
import wrapper
from storage import storage
from typing import Iterator, Dict


class Api:
    def __init__(self):
        self.api = None
        self.login = None

    def getApi(self):
        if self.api is None:
            import login
            self.login = login.Login()
            self.api = self.login.getApi()
        return self.api

    def getLogin(self):
        if self.login is None:
            self.getApi()
        return self.login

    def clearCache(self):
        storage.clearCache()
        storage.init_database()
        #storage.init_indexes()

    def clear_auth_cache(self):
        self.getLogin().clear_oauth_cache()

    def getPlaylistSongs(self, playlist_id) -> Iterator[wrapper.Song]:
        if playlist_id == 'thumbsup':
            return wrapper.Song.wrap(self.getApi().get_liked_songs())
        elif playlist_id == 'history':
            return wrapper.Song.wrap(self.getApi().get_history())
        else:
            storage_songs = storage.getPlaylistSongs(playlist_id)
            if playlist_id in ('upload_songs','ytmusic_songs','shuffled_albums'):
                if storage_songs:
                    return wrapper.LibrarySong.wrap(storage_songs)
                else:
                    return []
            elif storage_songs:
                return wrapper.LibraryPlaylistSong.wrap(storage_songs, playlist_id)
            else:
                return wrapper.GetPlaylistSong.wrap(self.getApi().get_playlist(playlist_id))

    def get_playlists(self):
        return wrapper.LibraryPlaylist.wrap(storage.getPlaylists())

    def load_playlists(self):
        library_playlists = []
        # Filter out auto-generated playlists: LM (Liked Music), SE (Saved Episodes), RDPN (New Episodes)
        playlists = list(filter(lambda pl: pl['playlistId'] not in ('LM', 'SE', 'RDPN'), self.getApi().get_library_playlists(100)))
        for playlist in playlists:
            library_playlist = self.getApi().get_playlist(playlistId=playlist['playlistId'], limit=1000)
            storage.storePlaylistSongs(library_playlist)
            library_playlist.pop('tracks')
            library_playlists.append(library_playlist)
        storage.storePlaylists(library_playlists)

    def getSong(self, video_id) -> wrapper.Song:
        storage_song = storage.getSong(video_id)
        if storage_song:
            return wrapper.LibrarySong(storage_song)
        else:
            return self.getTrack(video_id)

    def getSongStreamUrl(self, videoId):
        stream_url = self.getLogin().getStreamUrl(videoId)
        return stream_url

    def createPlaylist(self, name):
        playlist_id = self.getApi().create_playlist(name)
        storage.createPlaylist(name, playlist_id)

    def deletePlaylist(self, playlist_id):
        self.getApi().delete_playlist(playlist_id)
        storage.deletePlaylist(playlist_id)

    def set_rating(self, videoId, rating):
        self.getApi().rate_song(videoId, rating)
        # storage.setThumbs(videoId, thumbs)

    def getFilterSongs(self, filter_type, album_id, artist_name) -> Iterator[wrapper.Song]:
        return wrapper.LibrarySong.wrap(storage.getFilterSongs(filter_type, album_id, artist_name))

    def getCriteria(self, criteria, artist_name='') -> Iterator[wrapper.YTMusicItemWrapper]:
        #return storage.getCriteria(criteria, artist_name)
        items, content = storage.getCriteria(criteria, artist_name)
        if content == 'songs':
            return wrapper.LibrarySong.wrap(items), content
        elif content == 'albums':
            return wrapper.LibraryAlbum.wrap(items), content
        elif content == 'artists':
            return wrapper.LibraryArtist.wrap(items), content

    def getSearch(self, query, max_results:int=20, filter:str=None) -> Dict:
        import urllib.parse
        query = urllib.parse.unquote(query)
        utils.log("API get search: " + query)
        result = storage.getSearch(query, max_results)
        tracks = []
        albums = []
        artists = []
        videos = []
        playlists = []
        podcasts = []
        episodes = []
        tracks.extend(wrapper.LibrarySong.wrap(result['tracks']))
        albums.extend(wrapper.LibraryAlbum.wrap(result['albums']))
        artists.extend(wrapper.LibraryArtist.wrap(result['artists']))
        try:
            store_result = self.getApi().search(query, limit=max_results, filter=filter)
            utils.log(message="API get search aa: ", log_object=store_result, log_level=xbmc.LOGDEBUG)
            for sr in store_result:
                if sr['resultType']=='song':
                    tracks.append(wrapper.Song(sr))
                elif sr['resultType']=='album':
                    albums.append(wrapper.Album(sr))
                elif sr['resultType']=='artist':
                    artists.append(wrapper.Artist(sr))
                elif sr['resultType']=='playlist':
                    playlists.append(wrapper.Playlist(sr))
                elif sr['category']=='Videos' and sr['resultType']=='video':
                    videos.append(wrapper.Video(sr))
                elif sr['resultType']=='podcast':
                    podcasts.append(wrapper.Podcast(sr))
                elif sr['category']=='Episodes' and sr['resultType']=='video':
                    episodes.append(wrapper.Episode(sr))
                else:
                    utils.log("INVALID TYPE "+sr['resultType']+" "+repr(sr), xbmc.LOGWARNING)
            utils.log("API search results: tracks " + repr(len(tracks)) + " albums " + repr(len(albums))
                      + " artists " + repr(len(artists))  + " playlists " + repr(len(playlists)) + " videos " + repr(len(videos))
                      + " podcasts " + repr(len(podcasts)) + " episodes " + repr(len(episodes))
                      )

        except Exception as e:
            import sys
            utils.log("*** NO ALL ACCESS RESULT IN SEARCH *** " + repr(sys.exc_info()[0]), xbmc.LOGERROR)
            raise e
        return {'tracks': tracks, 'albums': albums, 'artists': artists, 'playlists': playlists, 
                'videos': videos, 'podcasts': podcasts, 'episodes': episodes}

    def getAlbum(self, album_id) -> wrapper.Song:
        return wrapper.GetAlbumSong.wrap(self.getApi().get_album(album_id))

    def getArtistInfo(self, artist_id) -> Dict:
        return self.wrapMixedInfo(self.getApi().get_artist(artist_id), name_key = 'name')

    def getChannelInfo(self, channel_id) -> Dict:
        return self.wrapMixedInfo(self.getApi().get_channel(channel_id), name_key = 'title')

    def wrapMixedInfo(self, info, name_key) -> Dict:
        result = {'songs': wrapper.Song.wrap(info['songs']['results']) if 'songs' in info and 'results' in info['songs'] else None,
                  'videos': wrapper.Video.wrap(info['videos']['results']) if 'videos' in info and 'results' in info['videos'] else None,
                  'albums': wrapper.GetArtistAlbum.wrap(info['albums']['results'], info[name_key]) if 'albums' in info and 'results' in info['albums'] else None,
                  'singles': wrapper.GetArtistAlbum.wrap(info['singles']['results'], info[name_key]) if 'singles' in info and 'results' in info['singles'] else None,
                  'related': wrapper.HomeArtist.wrap(info['related']['results']) if 'related' in info and 'results' in info['related'] else None,
                  'episodes': wrapper.GetArtistEpisode.wrap(info['episodes']['results'], info[name_key]) if 'episodes' in info and 'results' in info['episodes'] else None,
                  'podcasts': wrapper.Podcast.wrap(info['podcasts']['results']) if 'podcasts' in info and 'results' in info['podcasts'] else None,
                  'params': {
                      'albums' : info['albums']['params'] if 'albums' in info and 'params' in info['albums'] else None,
                      'singles' : info['singles']['params'] if 'singles' in info and 'params' in info['singles'] else None,
                      'episodes' : info['episodes']['params'] if 'episodes' in info and 'params' in info['episodes'] else None
                      },
                  'browseId': {
                      'albums' : info['albums']['browseId'] if 'albums' in info and 'browseId' in info['albums'] else None,
                      'singles' : info['singles']['browseId'] if 'singles' in info and 'browseId' in info['singles'] else None,
                      'songs' : info['songs']['browseId'] if 'albums' in info and 'browseId' in info['songs'] else None,
                      'episodes' : info['episodes']['browseId'] if 'episodes' in info and 'browseId' in info['episodes'] else None,
                      'podcasts' : info['podcasts']['browseId'] if 'podcasts' in info and 'browseId' in info['podcasts'] else None
                      }
                  }    
        return result

    def getArtistAlbums(self, artist_name, browse_id, params) -> Dict:
        info = self.getApi().get_artist_albums(browse_id, params )
        result = {'albums': wrapper.GetArtistAlbum.wrap(info, artist_name)}
        return result

    def getChannelEpisodes(self, channel_name, browse_id, params) -> Dict:
        info = self.getApi().get_channel_episodes(browse_id, params )
        return wrapper.GetArtistEpisode.wrap(info, channel_name)

    def getTrack(self, videoId) -> wrapper.Song:
        # return self._convertStoreTrack(self.getApi().get_track_info(trackid))
        # return self._load_tracks([self.getApi().get_song(videoId)])[0]
        return wrapper.SongFromVideoId(self.getApi().get_song(videoId)['videoDetails'])

    def addToPlaylist(self, playlist_id, videoId):
        self.getApi().add_playlist_items(playlist_id, videoIds = [videoId])
        self.load_playlists()

    def delFromPlaylist(self, playlist_id, videoId):
       entry = storage.delFromPlaylist(playlist_id, videoId)
       if entry != None:
            self.getApi().remove_playlist_items(playlist_id, [dict(entry)])

    def delAlbumFromLibrary(self, album_id):
        for track in self.getAlbum(album_id):
            if track.remove_token:
                self.getApi().edit_song_library_status(track.remove_token)
            else:
                return False
        storage.delAlbumFromLibrary(album_id)
        return True

    def delSongFromLibrary(self, video_id, token):
        self.getApi().edit_song_library_status(token)
        storage.delSongFromLibrary(video_id)

    def removePlaylist(self, playlist_id):
        self.getApi().rate_playlist(playlist_id,"INDIFFERENT")
        storage.deletePlaylist(playlist_id)

    def getPodcastEpisodes(self, podcast_id) -> Iterator[wrapper.Episode]:
        # Handle "New Episodes" playlist which has incorrect podcast_id "PN" due to wrapper extraction issue
        if podcast_id == "PN":
            # Use get_episodes_playlist for the "New Episodes" auto-generated playlist
            return wrapper.GetPodcastEpisode.wrap(self.getApi().get_episodes_playlist("RDPN"))
        return wrapper.GetPodcastEpisode.wrap(self.getApi().get_podcast(podcast_id))

    def getPodcasts(self) -> Iterator[wrapper.Podcast]:
        return wrapper.Podcast.wrap(filter(lambda pc: pc['podcastId'] != 'SE', self.getApi().get_library_podcasts()))