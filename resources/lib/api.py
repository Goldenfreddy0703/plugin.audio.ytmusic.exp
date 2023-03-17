import utils
from storage import storage


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

    def getPlaylistSongs(self, playlist_id):
        if playlist_id == 'thumbsup':
            songs = self._load_tracks(self.getApi().get_liked_songs())
        elif playlist_id == 'history':
            songs = self._load_tracks(self.getApi().get_history())
        else:
            songs = storage.getPlaylistSongs(playlist_id)
            if not songs and playlist_id not in ('upload_songs','ytmusic_songs','shuffled_albums'):
                songs = self._load_tracks(
                    self.getApi().get_playlist(playlist_id))
        return songs

    def get_playlists(self):
        return storage.getPlaylists()

    def load_playlists(self):
        playlists = self.getApi().get_library_playlists(100)
        storage.storePlaylists(playlists)
        for playlist in playlists:
            storage.storePlaylistSongs(self.getApi().get_playlist(playlistId=playlist['playlistId'], limit=1000))

    def getSong(self, videoId):
        return storage.getSong(videoId)

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

    def getFilterSongs(self, filter_type, filter_criteria, albums):
        return storage.getFilterSongs(filter_type, filter_criteria, albums)

    def getCriteria(self, criteria, artist=''):
        return storage.getCriteria(criteria, artist)

    def getSearch(self, query, max_results:int=20, filter:str=None):
        import urllib.parse
        query = urllib.parse.unquote(query)
        utils.log("API get search: " + query)
        result = storage.getSearch(query, max_results)
        # result = {'tracks':[],'albums':[],'artists':[]}
        tracks = result['tracks']
        albums = result['albums']
        artists = result['artists']
        videos = []
        playlists = []
        stations = []
        result['videos'] = videos
        result['playlists'] = playlists
        result['stations'] = stations
        try:
            store_result = self.getApi().search(query, limit=max_results, filter=filter)
            # utils.log("API get search aa: "+repr(store_result))
            for sr in store_result:
                if sr['resultType']=='song':
                    tracks.extend(self._load_tracks([sr]))
                elif sr['resultType']=='album':
                    albums.extend(self._load_albums([sr]))
                elif sr['resultType']=='artist':
                    #utils.log("TYPE "+sr['resultType']+" "+repr(sr))
                    artists.append(sr)
                elif sr['resultType']=='playlist':
                    # utils.log("TYPE "+sr['resultType']+" "+repr(sr))
                    playlists.append(sr)
                elif sr['resultType']=='video':
                    videos.extend(self._load_tracks([sr]))
                else:
                    utils.log("TYPE "+sr['resultType']+" "+repr(sr))
            utils.log("API search results: tracks " + repr(len(tracks)) + " albums " + repr(len(albums))
                      + " artists " + repr(len(artists)) + " stations " + repr(len(stations)) + " videos " + repr(len(videos)))
        except Exception as e:
            import sys
            utils.log("*** NO ALL ACCESS RESULT IN SEARCH *** " + repr(sys.exc_info()[0]))
            raise e
        return result

    def getAlbum(self, albumid):
        return self._load_tracks(self.getApi().get_album(albumid))

    def getArtistInfo(self, artistid):
        info = self.getApi().get_artist(artistid)

        result = {'tracks': self._load_tracks(info['songs']['results']) if 'songs' in info else None,
                  'albums': self._load_albums(info['albums']['results'], name=info['name']) if 'albums' in info else None}
        return result

    def getTrack(self, videoId):
        # return self._convertStoreTrack(self.getApi().get_track_info(trackid))
        return self._load_tracks([self.getApi().get_song(videoId)])[0]

    def addToPlaylist(self, playlist_id, videoId):
        self.getApi().add_playlist_items(playlist_id, videoIds = [videoId])
        self.load_playlists())

    def delFromPlaylist(self, playlist_id, videoId):
       entry = storage.delFromPlaylist(playlist_id, videoId)
       if entry != None:
            self.getApi().remove_playlist_items(playlist_id, [dict(entry)])

    def _loadArtistArt(self, artistid):
        if artistid not in self.artistInfo:
            artistart = storage.getArtist(artistid)
            if artistart:
                self.artistInfo[artistid] = {'artistArtRefs': [{'url': artistart}]}
            else:
                self.miss += 1
                try:
                    self.artistInfo[artistid] = self.getApi().get_artist(artistid)
                except:
                    self.artistInfo[artistid] = {}
                if 'artistArtRefs' in self.artistInfo[artistid]:
                    storage.setArtist(artistid, self.artistInfo[artistid]['artistArtRefs'][0]['url'])
                else:
                    utils.log("NO ART FOR ARTIST: " + repr(artistid))
                    self.artistInfo[artistid] = {'artistArtRefs': [{'url': ''}]}
        return self.artistInfo[artistid]['artistArtRefs']

    def _load_albums(self, albums, name = None):
        # utils.log("LOADSTOREALBUMS "+repr(albums))

        for item in albums:
            item['albumart'] = item['thumbnails'][-1]['url']

            if name is not None:
                item['artist'] = name
            else: 
                item['artist'] = item['artists'][0]['name'] if not isinstance(
                    item['artists'], str) else item['artists']

        return albums

    def _load_tracks(self, result):
        # utils.log("LOADSTORETRACKS "+repr(result))
        tracks = result['tracks'] if 'tracks' in result else result if isinstance(result, list) else []

        for item in tracks:
            item['artist'] = item['artists'][0]['name'] if not isinstance(item['artists'],str) else item['artists']
            item['albumart'] = '' if item['thumbnails'] is None else item['thumbnails'][-1]['url']
            item['album'] = 'none' if 'album' not in item or item['album'] is None else item['album']
            item['display_name'] = item['artist'] + " - " + item['title']
            if 'duration' in item:
                dur = item['duration'].split(':')
                item['duration'] = int(dur[-2]) * 60 + int(dur[-1])
                if len(dur) > 2:
                    item['duration'] = int(item['duration']) + int(dur[-3]) * 60 * 60
            elif 'lengthMs' in item:
                item['duration'] = int(item.pop('lengthMs')) / 1000

        return tracks

 
