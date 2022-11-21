import os
import sqlite3
import utils
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

    def getFilterSongs(self, filter_type, filter_criteria, albumArtist):
        query = ""
        utils.log("### storage getfiltersongs: " + repr(filter_type) + " " + repr(filter_criteria) + " " + repr(albumArtist))

        if albumArtist:
            query = "select * from songs where album = :filter and artist = :albumArtist " \
                    "order by display_name asc"
        elif filter_type == 'album':
            query = "select * from songs where album = :filter " \
                    "order by display_name asc"
        elif filter_type == 'artist':
            query = "select * from songs where artist = :filter " \
                    "order by album asc, display_name asc"

        return self.curs.execute(query, {'filter': filter_criteria, 'albumArtist': albumArtist}).fetchall()

    def getCriteria(self, criteria, name):
        utils.log("### storage get criteria: " + repr(criteria) + " " + repr(name))

        if criteria in ('yt_artist','yt_album'):
            song_type = 0
        else:
            song_type = 2

        if criteria in ('album','yt_album'):
            query = "select artist, album, max(albumart) as arturl " \
                    "from songs where album <> '-???-' and length(album)>1 and type=:type group by lower(artist), lower(album)"
        elif criteria in ('artist','yt_artist') and not name:
            query = "select artist as criteria, albumart as arturl from songs "\
                    "where length(artist)>1 and type=:type group by lower(artist)"
        elif criteria in ('artist','yt_artist') and name:
            query = "select artist, album, albumart as arturl " \
                    "from songs where artist=:name and type=:type group by lower(artist), lower(album)"
        elif name:
            query = "select artist, album, max(albumart) as arturl " \
                    "from songs where %s=:name and type=:type group by lower(artist), lower(album)" % criteria
        else:
            query = "select %s as criteria, max(albumart) as arturl from songs group by lower(%s)" % (
                criteria, criteria)

        return self.curs.execute(query, {'name': name, 'type': song_type}).fetchall()

    def getPlaylists(self):
        return self.curs.execute("SELECT playlist_id, name, arturl FROM playlists ORDER BY name").fetchall()

    def getSong(self, videoId):
        return self.curs.execute("SELECT title,artist,album,albumart " +
                                 "FROM songs WHERE videoId = ? ", (videoId,)).fetchone()

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
                "SELECT artist, max(albumart) as artistArtRef FROM songs WHERE artist like ? " +
                "GROUP BY artist LIMIT %s" % max_results, (query,)).fetchall(),
            'tracks': self.curs.execute(
                "SELECT * FROM songs WHERE display_name like ? ORDER BY display_name LIMIT %s" % max_results, (query,)).fetchall(),
            'albums': self.curs.execute(
                "SELECT album as title, artist, max(albumart) as albumart FROM songs " +
                "WHERE album like ? or artist like ? GROUP BY album, artist LIMIT %s" % max_results, (query, query)).fetchall()}
        return result

    def storePlaylists(self, playlists):
        self.curs.execute("DELETE FROM playlists")
        insert = "INSERT OR REPLACE INTO playlists (name, playlist_id, arturl, count) VALUES (?, ?, ?, ?)"
        for playlist in playlists:
            utils.log("PLAYLIST: "+repr(playlist))
            self.curs.execute(
                    insert, (playlist['title'], playlist['playlistId'], playlist["thumbnails"][-1].get("url") , playlist.get('count',0)))

        self.conn.commit()


    def storePlaylistSongs(self, playlist):
        playlistId = playlist['id']
        self.curs.execute("PRAGMA foreign_keys = OFF")
        self.curs.execute("DELETE FROM playlists_songs where playlist_id=?", (playlistId,))
        insert = "INSERT OR REPLACE INTO playlists_songs (playlist_id, videoId ) VALUES (?, ?)"

        utils.log("PLAYLIST ID: "+playlistId+"\n"+repr(playlist))
        for track in playlist['tracks']:
            if track['videoId'] is None: continue
            if track['isAvailable']==False: continue
            self.curs.execute(insert, (playlistId, track['videoId']))

        self.storeInAllSongs(playlist['tracks'], 1)
        self.conn.commit()


    def storeInAllSongs(self, api_songs, track_type=0):
        self.curs.execute("PRAGMA foreign_keys = OFF")

        def songs():
            for api_song in api_songs:
                # utils.log(repr(api_song))
                get = api_song.get
                if get("videoId") is None: continue
                yield {
                    'videoId': get("videoId"),
                    'album': get("album").get("name") if (get("album") is not None) else "-???-",
                    'title': get("title"),
                    'artist': get("artist", get("artists"))[0].get("name") if (get("artist", get("artists")) is not None) else "-???-",
                    'duration': self._get_duration(api_song),
                    'display_name': self._get_display_name(api_song),
                    'albumart': get("thumbnails")[-1].get("url"),
                    'type': track_type
                }

        self.curs.executemany("INSERT OR REPLACE INTO songs VALUES (" +
                              ":videoId,  :album, :title, :artist,  :duration, :display_name, :albumart, :type)", songs())

        self.conn.commit()
        # utils.log("Songs Stored: "+repr(len(api_songs)))

    def addToPlaylist(self, playlist_id, videoId, entry_id):
        self.curs.execute("INSERT OR REPLACE INTO playlists_songs(playlist_id, videoId, entry_id) VALUES (?,?,?)",
                          (playlist_id, videoId, entry_id))
        self.conn.commit()

    def delFromPlaylist(self, playlist_id, videoId):
        entry_id = self.curs.execute("SELECT entry_id FROM playlists_songs WHERE playlist_id=? and videoId=?",
                                     (playlist_id, videoId)).fetchone()
        self.curs.execute("DELETE from playlists_songs WHERE entry_id=?", (entry_id[0],))
        self.conn.commit()
        return entry_id[0]

    def deletePlaylist(self, playlist_id):
        self.curs.execute("DELETE FROM playlists_songs WHERE playlist_id = ?", (playlist_id,))
        self.curs.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
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
                title VARCHAR,                             --# 8
                artist VARCHAR,                            --# 15
                duration INTEGER NOT NULL DEFAULT 0,       --# 16
                display_name VARCHAR,                      --# 18
                albumart VARCHAR,
                type INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id VARCHAR NOT NULL PRIMARY KEY,
                name VARCHAR,
                arturl VARCHAR,
                count INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS playlists_songs (
                playlist_id VARCHAR,
                videoId VARCHAR NOT NULL,
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
        song_artist = api_song.get("artist", api_song.get("artists"))[0].get("name")
        
        if song_artist:
            displayName = song_artist.strip()
            if song_name:
                displayName += " - " + song_name.strip()
        elif song_name:
            displayName = song_name.strip()

        return displayName

    def _get_duration(self, track):
        duration = 0
        if 'duration' in track and track['duration'] is not None:
            dur = track['duration'].split(':')
            duration = int(dur[-2]) * 60 + int(dur[-1])
            if len(dur) > 2:
                duration = int(duration) + int(dur[-3]) * 60 * 60
        elif 'lengthMs' in track:
            duration = int(track.pop('lengthMs',0)) / 1000
        return duration
        

storage = Storage()
