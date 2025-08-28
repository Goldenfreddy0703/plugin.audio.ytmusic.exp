import os
import sqlite3
import utils
import xbmc
import xbmcvfs


class Storage:
    def __init__(self):
        self.path = os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('profile')), 'gpmusic.db')
        #self._connect()
        self.init_database()

    def clearCache(self):
        if os.path.isfile(self.path):
            if self.conn: self.conn.close()
            try:
                os.remove(self.path)
            except Exception as ex:
                utils.log("Error trying to delete database " + repr(ex))
                self._connect()
        utils.addon.setSettingInt("fetched_time", 0)

    def getPlaylistSongs(self, playlist_id):
        if playlist_id == 'all_songs':
            query = "SELECT * FROM songs ORDER BY display_name"
        elif playlist_id == 'upload_songs':
            query = "SELECT * FROM songs WHERE type=2 ORDER BY display_name"
        elif playlist_id == 'ytmusic_songs':
            query = "SELECT * FROM songs WHERE type=0 ORDER BY display_name"
        elif playlist_id == 'shuffled_albums':
            self.curs.execute(
                'CREATE TABLE shuffled_albums AS SELECT album, artist FROM songs GROUP BY album, artist ORDER BY RANDOM()')
            res = self.curs.execute('''
                SELECT songs.* FROM shuffled_albums LEFT JOIN songs ON songs.album = shuffled_albums.album AND songs.artist = shuffled_albums.artist
                ORDER BY shuffled_albums.rowid
            ''').fetchall()

            self.curs.execute('DROP TABLE shuffled_albums')
            return res
        else:
            query = "SELECT * FROM songs " \
                    "INNER JOIN playlists_songs ON songs.videoId = playlists_songs.videoId " \
                    "WHERE playlists_songs.playlist_id = :id"
        return self.curs.execute(query, {'id': playlist_id}).fetchall()

    def getFilterSongs(self, filter_type, album_id, artist_name):
        query = ""
        utils.log("### storage getfiltersongs: " + repr(filter_type) + " " + repr(album_id) + " " + repr(artist_name))

        if artist_name and album_id:
            query = "select * from songs where album_id = :album_id and artist = :artist_name " \
                    "order by display_name asc"
        elif filter_type == 'album':
            query = "select * from songs where album_id = :album_id " \
                    "order by display_name asc"
        elif filter_type in ('artist', 'yt_artist'):
            query = "select * from songs where artist = :artist_name " \
                    "order by album asc, display_name asc"

        return self.curs.execute(query, {'album_id': album_id, 'artist_name': artist_name}).fetchall()

    def getCriteria(self, criteria, artist_name):
        utils.log("### storage get criteria: " + repr(criteria) + " " + repr(artist_name))

        if criteria in ('yt_artist','yt_album'):
            song_type = 0
        else:
            song_type = 2

        if criteria in ('album','yt_album'):
            query = "select max(artist) as artist, max(album) as album, album_id, max(albumart) as albumart " \
                    "from songs where album <> '-???-' and length(album)>1 and type=:type group by album_id"
            content = "albums"
        elif criteria in ('artist','yt_artist') and not artist_name:
            query = "select artist as artist, albumart as artistartref from songs "\
                    "where length(artist)>1 and type=:type group by lower(artist)"
            content = "artists"
        elif criteria in ('artist','yt_artist') and artist_name:
            query = "select artist, album, album_id, albumart " \
                    "from songs where artist=:name and type=:type group by album_id"
            content = "albums"
        '''
        elif artist_name:
            query = "select artist, album, max(albumart) as arturl " \
                    "from songs where %s=:name and type=:type group by lower(artist), lower(album)" % criteria
            content = "albums"
        else:
            query = "select %s as criteria, max(albumart) as arturl from songs group by lower(%s)" % (
                criteria, criteria)
            content = "%ss" % criteria
        '''
        return self.curs.execute(query, {'name': artist_name, 'type': song_type}).fetchall(), content

    def getPlaylists(self):
        return self.curs.execute("SELECT * FROM playlists ORDER BY name").fetchall()

    def getSong(self, videoId):
        return self.curs.execute("SELECT * FROM songs WHERE videoId = ? ", (videoId,)).fetchone()

    def getVideo(self, title):
        videoid = self.curs.execute("SELECT videoid FROM songs WHERE display_name like ? ", ('%' + title + '%',)).fetchone()
        return videoid['videoid'] if videoid else ''

    def getArtist(self, artist_id):
        artist = self.curs.execute("SELECT artistart FROM artists WHERE artist_id = ? ", (artist_id,)).fetchone()
        return artist['artistart'] if artist else ''

    def setArtist(self, artist_id, artistart):
        self.curs.execute("INSERT OR REPLACE INTO artists VALUES (:artist_id, :artistart)", (artist_id, artistart))
        self.conn.commit()

    def getSearch(self, query, max_results=10):
        query = '%' + query.replace('%', '') + '%'
        result = {
            'artists': self.curs.execute(
                "SELECT artist, max(album_id) as album_id, max(albumart) as artistArtRef FROM songs WHERE artist like ? " +
                "GROUP BY artist LIMIT %s" % max_results, (query,)).fetchall(),
            'tracks': self.curs.execute(
                "SELECT * FROM songs WHERE display_name like ? ORDER BY display_name LIMIT %s" % max_results, (query,)).fetchall(),
            'albums': self.curs.execute(
                "SELECT album as album, max(album_id) as album_id, artist, max(albumart) as albumart FROM songs " +
                "WHERE album like ? or artist like ? GROUP BY album, artist LIMIT %s" % max_results, (query, query)).fetchall()}
        return result

    def storePlaylists(self, playlists):
        self.curs.execute("DELETE FROM playlists")
        insert = "INSERT OR REPLACE INTO playlists (name, playlist_id, arturl, count, owned) VALUES (?, ?, ?, ?, ?)"
        for playlist in playlists:
            utils.log("PLAYLIST: "+repr(playlist))
            # Use centralized thumbnail enhancement
            playlist_thumbnail = utils.get_best_thumbnail(playlist.get("thumbnails", []))
            
            self.curs.execute(
                    insert, (playlist['title'], playlist['id'], playlist_thumbnail, playlist.get('count',0), playlist['owned']))

        self.conn.commit()


    def storePlaylistSongs(self, playlist):
        playlistId = playlist['id']
        self.curs.execute("PRAGMA foreign_keys = OFF")
        self.curs.execute("DELETE FROM playlists_songs where playlist_id=?", (playlistId,))
        insert = "INSERT OR REPLACE INTO playlists_songs (playlist_id, videoId, setVideoId ) VALUES (?, ?, ?)"

        utils.log("PLAYLIST ID: "+playlistId+"\n"+repr(playlist))
        if 'tracks' in playlist:
            utils.log("STORING PLAYLIST SONGS - Playlist: " + playlist.get('title', 'Unknown') + " - Track count: " + str(len(playlist['tracks'])))
            for track in playlist['tracks']:
                if track['videoId'] is None: continue
                if track['isAvailable']==False: continue
                self.curs.execute(insert, (playlistId, track['videoId'], track['setVideoId'] if 'setVideoId' in track else None))

            self.storeInAllSongs(playlist['tracks'], 1)
        self.conn.commit()


    def storeInAllSongs(self, api_songs, track_type=0):
        self.curs.execute("PRAGMA foreign_keys = OFF")
        
        # Pre-collect all video IDs that might need YouTube API fallback
        video_ids_for_batch = []
        for api_song in api_songs:
            video_id = api_song.get("videoId")
            if video_id:
                thumbnails = api_song.get("thumbnails", [])
                # Check if this might need YouTube API fallback
                if thumbnails:
                    from utils import is_generic_thumbnail
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
            utils.log(f"Pre-fetching thumbnails for {len(video_ids_for_batch)} videos in batch requests")
            from utils import get_youtube_thumbnails_batch
            get_youtube_thumbnails_batch(video_ids_for_batch)

        def songs():
            for api_song in api_songs:
                utils.log(message="Storing song %s", log_object=repr(api_song), log_level=xbmc.LOGDEBUG)
                get = api_song.get
                if get("videoId") is None: continue
                video_id = get("videoId")
                yield {
                    'videoId': video_id,
                    'album': get("album").get("name") if (get("album") is not None) else "-???-",
                    'album_id': get("album").get("id") if (get("album") is not None) else "",
                    'title': get("title"),
                    'artist': get("artist", get("artists"))[0].get("name") if (get("artist", get("artists")) is not None) else "-???-",
                    'duration': self._get_duration(api_song),
                    'display_name': self._get_display_name(api_song),
                    'albumart': utils.get_best_thumbnail(get("thumbnails"), video_id),
                    'type': track_type,
                    'removeToken': get("feedbackTokens").get("remove") if get("feedbackTokens") is not None else ""
                }

        self.curs.executemany("INSERT OR REPLACE INTO songs VALUES (" +
                              ":videoId, :album, :album_id, :title, :artist, :duration, :display_name, :albumart, :type, :removeToken)", songs())

        self.conn.commit()
        utils.log("Songs Stored: "+repr(len(api_songs)))

        self.curs.executemany("INSERT OR REPLACE INTO songs VALUES (" +
                              ":videoId, :album, :album_id, :title, :artist, :duration, :display_name, :albumart, :type, :removeToken)", songs())

        self.conn.commit()
        utils.log("Songs Stored: "+repr(len(api_songs)))

    def addToPlaylist(self, playlist_id, videoId, setVideoId):
        self.curs.execute("INSERT OR REPLACE INTO playlists_songs(playlist_id, videoId, setVideoId) VALUES (?,?,?)",
                          (playlist_id, videoId, setVideoId))
        self.conn.commit()

    def delFromPlaylist(self, playlist_id, videoId):
        entry = self.curs.execute("SELECT videoID, setVideoId FROM playlists_songs WHERE playlist_id=? and videoId=?",
                                     (playlist_id, videoId)).fetchone()
        self.curs.execute("DELETE from playlists_songs WHERE setVideoId=?", (entry['setVideoId'],))
        self.conn.commit()
        return entry

    def deletePlaylist(self, playlist_id):
        self.curs.execute("DELETE FROM playlists_songs WHERE playlist_id = ?", (playlist_id,))
        self.curs.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
        self.conn.commit()

    def delSongFromLibrary(self, video_id):
        self.curs.execute("DELETE from songs WHERE videoId=?", (video_id,))
        self.conn.commit()

    def delAlbumFromLibrary(self, album_id):
        self.curs.execute("DELETE from songs WHERE album_Id=?", (album_id,))
        self.conn.commit()

    def createPlaylist(self, name, playlist_id):
        self.curs.execute("INSERT OR REPLACE INTO playlists(playlist_id, name ) VALUES (?,?)",
                          (playlist_id, name))
        self.conn.commit()

    def setThumbs(self, videoId, thumbs):
        self.curs.execute(
            "UPDATE songs SET rating = ? WHERE videoId = ?", (thumbs, videoId))
        self.conn.commit()

    def _connect(self):
        self.conn = sqlite3.connect(self.path)
        self.conn.text_factory = str
        self.conn.row_factory = sqlite3.Row
        self.curs = self.conn.cursor()

    def init_database(self):
        self._connect()

        self.curs.executescript('''
            CREATE TABLE IF NOT EXISTS songs (
                videoId VARCHAR NOT NULL PRIMARY KEY,      --# 0
                album VARCHAR,                             --# 7
                album_id VARCHAR,
                title VARCHAR,                             --# 8
                artist VARCHAR,                            --# 15
                duration INTEGER NOT NULL DEFAULT 0,       --# 16
                display_name VARCHAR,                      --# 18
                albumart VARCHAR,
                type INTEGER NOT NULL DEFAULT 0,
                removeToken VARCHAR
            );
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id VARCHAR NOT NULL PRIMARY KEY,
                name VARCHAR,
                arturl VARCHAR,
                count INTEGER NOT NULL DEFAULT 0,
                owned BOOLEAN NOT NULL CHECK (owned IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS playlists_songs (
                playlist_id VARCHAR,
                videoId VARCHAR NOT NULL,
                setVideoId VARCHAR,
                FOREIGN KEY(playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS artists (
                artist_id VARCHAR NOT NULL PRIMARY KEY,
                artistart VARCHAR
            );
        ''')

        self.conn.commit()

    def init_indexes(self):
        self.curs.executescript('''
            CREATE INDEX IF NOT EXISTS playlistindex ON playlists_songs(playlist_id);
            CREATE INDEX IF NOT EXISTS songindex ON playlists_songs(videoId);
            CREATE INDEX IF NOT EXISTS songinfoindex ON songs(album,artist,type);
        ''')
        self.conn.commit()

    def _get_display_name(self, api_song):
        displayName = "-???-"
        song_name = api_song.get("title")
        song_artist = api_song.get("artist", api_song.get("artists"))
        if isinstance(song_artist, list):
            song_artist = song_artist[0].get("name")

        if song_artist:
            displayName = song_artist.strip()
            if song_name:
                displayName += " - " + song_name.strip()
        elif song_name:
            displayName = song_name.strip()

        return displayName

    def _get_duration(self, track):
        duration = 0
        try:
            if 'duration' in track and track['duration'] is not None:
                duration_str = str(track['duration']).strip()
                
                # Handle empty or invalid duration strings
                if not duration_str or duration_str.lower() in ['unknown', 'none', '']:
                    return 0
                
                # Split by colon for MM:SS or HH:MM:SS format
                dur = duration_str.split(':')
                
                # Ensure we have at least 2 parts (minutes:seconds)
                if len(dur) >= 2:
                    # Convert to integers safely
                    try:
                        seconds = int(dur[-1])  # Last part is always seconds
                        minutes = int(dur[-2])  # Second to last is minutes
                        duration = minutes * 60 + seconds
                        
                        # Add hours if present (HH:MM:SS format)
                        if len(dur) >= 3:
                            hours = int(dur[-3])
                            duration += hours * 3600
                            
                    except (ValueError, IndexError) as e:
                        utils.log(f"Duration parsing error for '{duration_str}': {e}", xbmc.LOGDEBUG)
                        duration = 0
                elif len(dur) == 1:
                    # Handle single number (assume seconds)
                    try:
                        duration = int(dur[0])
                    except ValueError:
                        duration = 0
                else:
                    utils.log(f"Invalid duration format: '{duration_str}'", xbmc.LOGDEBUG)
                    duration = 0
                    
            elif 'lengthMs' in track:
                duration = int(track.pop('lengthMs', 0)) / 1000
            elif 'duration_seconds' in track:
                duration = int(track.get('duration_seconds', 0))
                
        except Exception as e:
            utils.log(f"Unexpected error parsing duration for track: {e}", xbmc.LOGWARNING)
            duration = 0
            
        return duration
        

storage = Storage()
