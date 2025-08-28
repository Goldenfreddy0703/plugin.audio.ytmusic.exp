import urllib.parse
import api
import utils
import wrapper
import xbmc
import xbmcplugin
from xbmcgui import ListItem

fanart = utils.addon.getAddonInfo('fanart')


class Navigation:

    def __init__(self, params, return_params):
        self.lang = utils.addon.getLocalizedString
        self.api = api.Api()
        self.contextmenu_action = "RunPlugin(" + utils.addon_url + "?action=%s&%s)"
        self.params = params
        self.return_params = return_params

        self.main_menu = (
            {"title": self.lang(30228), "params": {"path": "home"}, "icon": "home.png"},
            {"title": "YtMusic " + self.lang(30209), "params": {"path": "ytmusic_library"}, "icon": "library.png"},
            {"title": "YtMusic " + self.lang(30234), "params": {"path": "uploads_library"}, "icon": "upload_music.png"},
            {"title": self.lang(30229), "params": {"path": "moods_genres"}, "icon": "moods_&_genres.png"},
            {"title": self.lang(30208), "params": {"path": "search"}, "icon": "search.png"},
            {"title": self.lang(30230), "params": {"path": "playlist", "playlist_id": "LM"}, "icon": "likes.png"},
            {"title": self.lang(30231), "params": {"path": "playlist", "playlist_id": "history"}, "icon": "history.png"},
            {"title": self.lang(30238), "params": {"path": "charts"}, "icon": "charts.png"}
        )
        self.ytlib_menu = (
            {"title": self.lang(30201), "params": {"path": "playlist", "playlist_id": "ytmusic_songs"}, "icon": "songs.png"},
            {"title": self.lang(30205), "params": {"path": "filter", "criteria": "yt_artist"}, "icon": "artists.png"},
            {"title": self.lang(30206), "params": {"path": "filter", "criteria": "yt_album"}, "icon": "albums_1.png"},
            {"title": self.lang(30202), "params": {"path": "playlists", "type": "user"}, "icon": "queue.png"},
            {"title": self.lang(30226), "params": {"path": "subscriptions"}, "icon": "artist_subscriptions.png"},
            {"title": self.lang(30236), "params": {"path": "podcasts"}, "icon": "podcasts.png"},
            {"title": self.lang(30235), "params": {"path": "playlist", "playlist_id": "SE"}, "icon": "saved-episodes.png"},
            {"title": self.lang(30237), "params": {"path": "channels"}, "icon": "channels.png"}
        )
        if utils.headless_mode:
            self.ytlib_menu += (
                {"title": self.lang(30304), "params": {"action": "update_playlists", "playlist_type": "user", "return_params": "path=ytmusic_library"}},
                {"title": self.lang(30305), "params": {"action": "update_library", "return_params": "path=ytmusic_library"}}
            )
        self.uplib_menu = (
            {"title": self.lang(30214), "params": {"path": "playlist", "playlist_id": "shuffled_albums"}, "icon": "shuffle.png"},
            {"title": self.lang(30201), "params": {"path": "playlist", "playlist_id": "upload_songs"}, "icon": "uploads.png"},
            {"title": self.lang(30205), "params": {"path": "filter", "criteria": "artist"}, "icon": "artists.png"},
            {"title": self.lang(30206), "params": {"path": "filter", "criteria": "album"}, "icon": "albums_1.png"}
        )

    def listMenu(self):
        get = self.params.get
        path = get("path", "root")
        utils.log("PATH: " + path)

        listItems = []
        content = ''
        sortMethods = [xbmcplugin.SORT_METHOD_UNSORTED]

        if path == "root":
            listItems = self.getMenuItems(self.main_menu)

        elif path == "ytmusic_library":
            listItems = self.getMenuItems(self.ytlib_menu)

        elif path == "uploads_library":
            listItems = self.getMenuItems(self.uplib_menu)

        elif path == "playlist":
            listItems = self.listPlaylistSongs(get("playlist_id"))
            if get("playlist_id") in ('upload_songs', 'ytmusic_songs'):
                sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "songs"

        elif path == "playlists":
            listItems = self.listLibraryPlaylists()
            content = "playlists"

        elif path == "filter" and get('criteria') in ("album", "yt_album"):
            listItems = self.listLibraryAlbums(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path == "filter":
            listItems, content = self.getCriteria(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]

        elif path == "allcriteriasongs":
            listItems = self.listAllCriteriaSongs(get('criteria'), get('artist_name'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "songs"

        elif path in ["artist", "yt_artist"] and get('artist_name') and not get('album_name'):
            artist_name = get('artist_name')
            paramsAllSongs = {'path': "allcriteriasongs", 'criteria': path, 'artist_name': artist_name}
            listItems.insert(0, self.createFolder('* ' + self.lang(30201), paramsAllSongs))
            listItems.extend(self.listLibraryAlbums(path, artist_name))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path in ["artist", "album", "yt_artist", "yt_album"]:
            songs = self.api.getFilterSongs(path, get('album_id'), get('artist_name', ''))
            listItems = self.listSongs(songs)
            sortMethods = [xbmcplugin.SORT_METHOD_TRACKNUM, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
                           xbmcplugin.SORT_METHOD_PLAYCOUNT, xbmcplugin.SORT_METHOD_SONG_RATING]
            content = "songs"

        elif path == "search":
            listItems.append(self.createFolder(self.lang(30223), {'path': 'search_new'}, arturl=utils.get_icon_path("new_search.png")))
            history = utils.addon.getSetting('search-history').split('|')
            for item in history:
                if item:
                    listItems.append(self.createFolder(item, {'path': 'search_query', 'query': item}))

        elif path == "search_new":
            keyboard = xbmc.Keyboard('', self.lang(30208))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                listItems, content = self.getSearch(keyboard.getText())
                history = utils.addon.getSetting('search-history')
                history = keyboard.getText() + ('|' + history if history else '')
                if len(history.split('|')) > 10:
                    history = '|'.join(history.split('|')[0:-1])
                utils.addon.setSetting('search-history', history)
            else:
                return

        elif path == "search_query":
            listItems, content = self.getSearch(get("query"))

        elif path == "search_result":
            utils.log("SEARCH_RESULT: " + get('query'))
            listItems, content = self.getSearch(self.params)

        elif path == "store_album":
            utils.log("ALBUM: " + get('album_id'))
            listItems = self.listSongs(self.api.getAlbum(get('album_id')))
            content = "songs"

        elif path == "artist_topsongs":
            listItems = self.listSongs(self.api.getArtistInfo(get('artistid'))['songs'])
            content = "songs"

        elif path == "related_artists":
            listItems = self.createArtistFolders(self.api.getArtistInfo(get('artistid'))['related'])
            sortMethods = [xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE]
            content = "artists"

        elif path == "subscriptions":
            listItems = self.getSubscriptions()
            sortMethods = [xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE]
            content = "artists"

        elif path == "moods_genres":
            listItems = self.getMoodsGenres()

        elif path == "mood_playlists":
            listItems = self.getMoodPlaylists(get('params'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "playlists"

        elif path == "home":
            listItems = self.getHome(get('params'))
            content = "songs"
        
        elif path == "charts":
            listItems = self.getCharts(get('country'))
            content = "songs"

        elif path == "podcast":
            listItems = self.listPodcastEpisodes(get('podcast_id'))
            content = "episodes"

        elif path == "podcasts":
            listItems = self.getPodcasts()
            content = "tvshows"

        elif path == "channels":
            listItems = self.getChannels()
            content = "artists"

        elif path == "songMenu":
            listItems = self.getSongMenu(self.api.getSong(get('videoId')))
            content = "songs"

        else:
            utils.log("Invalid path: " + get("path"))
            return

        utils.setDirectory(listItems, content, sortMethods)

    def getMenuItems(self, items):
        menuItems = []
        for menu_item in items:
            params = menu_item['params']
            cm = []
            if not utils.headless_mode:
                if 'playlist_id' in params:
                    cm = self.getPlaylistContextMenu(wrapper.Playlist({'title': menu_item['title'], 'playlistId': params['playlist_id']}))
                elif 'type' in params:
                    cm.append(self.create_menu(30304, "update_playlists", {'playlist_type': params['type']}))
                    # cm.append(self.create_menu(30306, "add_favourite", {'path': 'playlists', 'playlist_type': params['type'], 'title': menu_item['title']}))
                    # cm.append(self.create_menu(30316, "create_playlist"))
                elif params['path'] in ('uploads_library', 'ytmusic_library'):
                    cm.append(self.create_menu(30305, "update_library"))
                    # cm.append(self.create_menu(30306, "add_favourite", {'path': 'library', 'title': menu_item['title']}))
                # elif 'criteria' in params:
                #    cm.append(self.create_menu(30306, "add_favourite", {'path': 'filter', 'criteria': params['criteria'], 'title': menu_item['title']}))
            art_url = utils.get_icon_path(menu_item['icon']) if 'icon' in menu_item and utils.icon_path else ''
            menuItems.append(self.createFolder(menu_item['title'], params, cm, art_url))
        return menuItems

    def listPlaylistSongs(self, playlist_id):
        utils.log("Loading playlist: " + playlist_id)
        return self.listSongs(self.api.getPlaylistSongs(playlist_id))

    def listSongs(self, songs):
        if utils.addon.getSetting('headless_mode.songs') == 'true':
            listItems = []
            for song in songs:
                li = utils.createItem(song)
                li.setProperties({'IsPlayable': 'false'})
                li.setProperties({'IsFolder': 'false'})  # Does this really help ?
                params = {'path': 'songMenu', 'videoId': song.video_id, 'return_params': urllib.parse.urlencode(self.params, doseq=True)}
                folder = "?".join([utils.addon_url, urllib.parse.urlencode(params, doseq=True)]), li, True
                folder[1].setInfo(type='Music', infoLabels={'mediatype': 'music'})
                listItems.append(folder)
            return listItems
        else:
            return [[utils.getUrl(song), self.createItem(song)] for song in songs]

    def listAllCriteriaSongs(self, filter_type, artist_name):
        return self.listSongs(self.api.getFilterSongs(filter_type, None, artist_name))

    def createItem(self, song):
        li = utils.createItem(song)
        li.addContextMenuItems(self.getSongContextMenu(song))
        return li

    def createFolder(self, name, params, contextMenu=[], arturl='', name2='*', fanarturl=fanart):
        li = ListItem(label=name, label2=name2, offscreen=True)
        li.setArt({'thumb': arturl, 'fanart': fanarturl})
        li.addContextMenuItems(contextMenu)
        return "?".join([utils.addon_url, urllib.parse.urlencode(params, doseq=True)]), li, True

    def listLibraryPlaylists(self):
        return self.createPlaylistFolders(self.api.get_playlists())

    def listLibraryAlbums(self, criteria, artist_name=''):
        utils.log("LIST ALBUMS: " + repr(criteria) + " " + repr(artist_name))
        items, content = self.api.getCriteria(criteria, artist_name)
        return self.createAlbumFolders(items, artist_name=artist_name)

    def getCriteria(self, criteria):
        utils.log("CRITERIA: " + repr(criteria))

        items, content = self.api.getCriteria(criteria)
        if content == 'artists':
            return self.createArtistFolders(items, criteria), content
        elif content == 'albums':
            return self.createAlbumFolders(items, criteria), content
        else:
            return self.listSongs(items), content

    def createPlaylistFolders(self, playlists):
        listItems = []
        for playlist in playlists:
            cm = self.getPlaylistContextMenu(playlist)
            folder = self.createFolder(playlist.playlist_name, {'path': "playlist", 'playlist_id': playlist.playlist_id}, cm, playlist.thumbnail)
            folder[1].setInfo(type='Music', infoLabels={'comment': playlist.description, 'mediatype': 'music'})
            listItems.append(folder)
        return listItems

    def createAlbumFolders(self, albumlist, path='album', artist_name=None):
        listItems = []
        for album in albumlist:
            if album.is_library_item:
                params = {'path': path, 'album_id': album.album_id}
                if artist_name:
                    params['artist_name'] = artist_name
                cm = self.getFilterContextMenu(path, album.album_id, album.album_title)
                cm.append(self.create_menu(30330, "remove_album_library", params))
                folder_name = "[%s] %s" % (album.artist_name, album.album_title)
                listItems.append(self.createFolder(folder_name, params, cm, album.thumbnail))
            else:
                # utils.log("SEA_ALB_ITEM "+repr(item))
                params = {'path': 'store_album', 'album_id': album.album_id}
                cm = [self.create_menu(30301, "play_all", params),
                      self.create_menu(30315, "add_to_queue", params),
                      self.create_menu(30309, "add_album_library", params),
                      self.create_menu(30330, "remove_album_library", params)]

                folder = self.createFolder(name=f"[{album.artist_name}] {album.album_title}",
                    params=params,
                    contextMenu=cm,
                    arturl=album.thumbnail,
                    name2=album.description,
                    fanarturl=album.thumbnail
                )
                folder[1].setInfo(type='Music', infoLabels={'artist': album.artist_name, 'album': album.album_title, 'mediatype': 'album'})
                listItems.append(folder)
        return listItems

    def createArtistFolders(self, artists, path='artist'):
        listItems = []
        for artist in artists:
            if artist.is_library_item:
                params = {'path': path, 'artist_name': artist.artist_name}
                cm = self.getFilterContextMenu(path, artist_name=artist.artist_name)
            else:
                params = {'path': 'search_result', 'artistid': artist.artist_id, 'query': artist.artist_name}
                cm = self.getArtistContextMenu(artist)
            folder = self.createFolder(artist.artist_name, params, cm, arturl=artist.thumbnail, fanarturl=artist.thumbnail)
            folder[1].setInfo(type='Music', infoLabels={'artist': artist.artist_name, 'mediatype': 'artist'})
            listItems.append(folder)
        return listItems

    def getSongContextMenu(self, song):
        params = {'videoId': song.video_id, 'display_name': song.display_name}
        cm = []
        
        # Primary actions (like YouTube Music)
        cm.append(self.create_menu(30325, "play_song", params))  # Play
        cm.append(self.create_menu(30326, "play_next", params))  # Play next
        cm.append(self.create_menu(30315, "add_to_queue", params))  # Add to queue
        
        # Separator
        cm.append(('─────────────────', 'noop'))
        
        # Library actions
        if not song.is_library_item and song.add_token:
            cm.append(self.create_menu(30309, "add_library", {'token': song.add_token}))  # Add to Your Library
        if song.is_library_item and song.remove_token:
            cm.append(self.create_menu(30330, "remove_library", {'video_id': song.video_id, 'token': song.remove_token}))  # Remove from Library
        
        # Playlist actions
        cm.append(self.create_menu(30307, "add_to_playlist", params))  # Add to playlist
        if song.is_playlist_song and song.is_library_item:
            playlist_params = {'videoId': song.video_id, 'display_name': song.display_name, 'playlist_id': song.playlist_id}
            cm.append(self.create_menu(30308, "del_from_playlist", playlist_params))  # Remove from this playlist
        
        # Like/Unlike
        cm.append(self.create_menu(30409, "set_thumbs", params))  # Like/Unlike
        
        # Separator  
        cm.append(('─────────────────', 'noop'))
        
        # Navigation actions
        if song.album_id:
            cm.append(self.create_menu(30327, "goto_album", {'album_id': song.album_id}))  # Go to album
            cm.append(self.create_menu(30331, "add_album_library", {'album_id': song.album_id}))  # Add album to library
        
        if song.artist_id:
            cm.append(self.create_menu(30319, "artist_topsongs", {'artistid': song.artist_id}))  # Go to artist
            cm.append(self.create_menu(30328, "goto_artist", {'artistid': song.artist_id, 'query': song.artist_name}))  # Artist page
            cm.append(self.create_menu(30432, "start_radio", {'type': 'artist', 'id': song.artist_id}))  # Start artist radio
        
        # Additional YouTube Music features
        cm.append(self.create_menu(30433, "start_radio", {'type': 'song', 'videoId': song.video_id}))  # Start song radio
        cm.append(self.create_menu(30434, "view_lyrics", params))  # View lyrics
        
        # Playlist context for playlist songs
        if song.is_playlist_song:
            playlist_params = {'videoId': song.video_id, 'display_name': song.display_name, 'playlist_id': song.playlist_id}
            cm.append(self.create_menu(30322, "play_all", playlist_params))  # Play from here
        
        return cm

    def getPlaylistContextMenu(self, playlist):
        params = {'playlist_id': playlist.playlist_id, 'title': playlist.playlist_name}
        shuffle = params.copy()
        shuffle.update({'shuffle': 'true'})
        cm = []
        
        # Primary actions
        cm.append(self.create_menu(30301, "play_all", params))  # Play
        cm.append(self.create_menu(30302, "play_all", shuffle))  # Shuffle play
        cm.append(self.create_menu(30315, "add_to_queue", params))  # Add to queue
        
        # Separator
        cm.append(('─────────────────', 'noop'))
        
        # Library actions
        if playlist.is_owned:
            cm.append(self.create_menu(30317, "delete_playlist", params))  # Delete playlist
            cm.append(self.create_menu(30436, "edit_playlist", params))  # Edit details
        elif playlist.is_library_item:  # community playlist
            cm.append(self.create_menu(30330, "remove_playlist", params))  # Remove from library
        else:
            cm.append(self.create_menu(30309, "add_playlist", params))  # Add to library
        
        # Additional actions
        cm.append(self.create_menu(30437, "share_playlist", params))  # Share playlist
        cm.append(self.create_menu(30432, "start_radio", {'type': 'playlist', 'id': playlist.playlist_id}))  # Start radio
        
        return cm

    def getFilterContextMenu(self, filter_type, album_id='', album_title='', artist_name=''):
        params = {'filter_type': filter_type, 'filter_criteria': album_id, 'artist_name': artist_name}
        shuffle = params.copy()
        shuffle.update({'shuffle': 'true'})
        return [
            self.create_menu(30301, "play_all", params),  # Play all
            self.create_menu(30302, "play_all", shuffle),  # Shuffle play
            self.create_menu(30315, "add_to_queue", params),  # Add to queue
        ]

    def getArtistContextMenu(self, artist):
        params = {'artist_id': artist.artist_id}
        cm = []
        
        # Primary actions
        cm.append(self.create_menu(30301, "play_all", params))  # Play all songs
        cm.append(self.create_menu(30432, "start_radio", {'type': 'artist', 'id': artist.artist_id}))  # Start artist radio
        
        # Separator
        cm.append(('─────────────────', 'noop'))
        
        # Subscription actions
        cm.append(self.create_menu(30323, "subscribe_artist", params))  # Subscribe
        cm.append(self.create_menu(30324, "unsubscribe_artist", params))  # Unsubscribe
        
        # Navigation
        cm.append(self.create_menu(30439, "view_artist_albums", params))  # View albums
        cm.append(self.create_menu(30440, "view_artist_singles", params))  # View singles
        cm.append(self.create_menu(30441, "view_related_artists", params))  # View related artists
        
        return cm

    def create_menu(self, text_code, action, params={'1':1}):
        return self.lang(text_code), self.contextmenu_action % (action, urllib.parse.urlencode(params, doseq=True))

    def getSearch(self, query):
        listItems = []
        content = "songs"

        if isinstance(query, str):
            result = self.api.getSearch(query)
            if result['artists']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30205), True),
                    {'path': 'search_result', 'type': 'artists', 'query': query}, arturl=utils.get_icon_path("artists.png")))
                listItems.extend(self.createArtistFolders(result['artists']))
            if result['albums']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30206), True),
                    {'path': 'search_result', 'type': 'albums', 'query': query}, arturl=utils.get_icon_path("albums.png")))
                listItems.extend(self.createAlbumFolders(result['albums']))
            if result['tracks']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30213), True),
                    {'path': 'search_result', 'type': 'songs', 'query': query}, arturl=utils.get_icon_path("songs_1.png")))
                listItems.extend(self.listSongs(result['tracks']))
            if result['playlists']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30202)),
                    {'path': 'none'}, arturl=utils.get_icon_path("queue.png")))
                listItems.extend(self.createPlaylistFolders(result['playlists']))
            if result['videos']:
                listItems.append(self.createFolder(utils.getTitle('Youtube'),
                    {'path': 'none'}, arturl=utils.get_icon_path("ytmusic_icon.png")))
                listItems.extend(self.listSongs(result['videos']))
            if result['podcasts']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30236)),
                    {'path': 'none'}, arturl=utils.get_icon_path("podcasts.png")))
                listItems.extend(self.createPodcastFolders(result['podcasts']))
            if result['episodes']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30239)),
                    {'path': 'none'}, arturl=utils.get_icon_path("songs_1.png")))
                listItems.extend(self.listSongs(result['episodes']))

        elif 'album_params' in query:
            result = self.api.getArtistAlbums(query['query'], query['browseId'], query['album_params'])
            listItems.extend(self.createAlbumFolders(result['albums']))
            content = "albums"
 
        elif 'episode_params' in query:
            result = self.api.getChannelEpisodes(query['query'], query['browseId'], query['episode_params'])
            listItems.extend(self.listSongs(result))
            content = "episodes"
 
        elif 'artistid' in query:
            listItems.extend(self.renderMixedResult(self.api.getArtistInfo(query['artistid']), query))

        elif 'channelid' in query:
            listItems.extend(self.renderMixedResult(self.api.getChannelInfo(query['channelid']), query))

        elif 'type' in query:
            result = self.api.getSearch(query['query'], max_results=50, filter=query['type'])
            if query['type'] == 'artists':
                listItems.extend(self.createArtistFolders(result['artists']))
                content = "artists"
            elif query['type'] == 'albums':
                listItems.extend(self.createAlbumFolders(result['albums']))
                content = "albums"
            elif query['type'] == 'songs':
                listItems.extend(self.listSongs(result['tracks']))

        else:
            items, content = (self.getSearch(query['query']))
            listItems.extend(items)

        return listItems, content

    def renderMixedResult(self, result, query):
        listItems = []
        if result['albums']:
            if result['browseId']['albums']:
                listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30206), True),
                        {'path': 'search_result', 'query': query['query'], 'browseId': result['browseId']['albums'], 'album_params': result['params']['albums']},
                        arturl=utils.get_icon_path("albums_1.png")))
            else:
                listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30206)), {'path': 'none'}, arturl=utils.get_icon_path("albums_1.png")))
            listItems.extend(self.createAlbumFolders(result['albums']))
        if result['singles']:
            if result['browseId']['singles']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30227), True),
                    {'path': 'search_result', 'query': query['query'], 'browseId': result['browseId']['singles'], 'album_params': result['params']['singles']},
                    arturl=utils.get_icon_path("albums.png")))
            else:
                listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30227)), {'path': 'none'}, arturl=utils.get_icon_path("albums.png")))
            listItems.extend(self.createAlbumFolders(result['singles']))
        if result['songs']:
            if result['browseId']['songs']:
                listItems.extend(self.createPlaylistFolders([wrapper.Playlist({
                    'playlistId': result['browseId']['songs'],
                    'title': utils.getTitle(self.lang(30213), True),
                    'thumbnails': [{'url': utils.get_icon_path("songs_1.png")}]
                })]))
            else:
                listItems.append(
                self.createFolder(utils.getTitle(self.lang(30213)), {'path': 'none'}, arturl=utils.get_icon_path("songs_1.png")))
            listItems.extend(self.listSongs(result['songs']))
        if result['videos']:
            listItems.append(self.createFolder(utils.getTitle('Youtube'), {'path': 'none'}, arturl=utils.get_icon_path("ytmusic_icon.png")))
            listItems.extend(self.listSongs(result['videos']))
        if result['podcasts']:
            if result['browseId']['podcasts']:
                listItems.extend(self.createPlaylistFolders([wrapper.Playlist({
                    'playlistId': result['browseId']['podcasts'],
                    'title': utils.getTitle(self.lang(30236), True),
                    'thumbnails': [{'url': utils.get_icon_path("podcasts.png")}]
                })]))
            else:
                listItems.append(
                self.createFolder(utils.getTitle(self.lang(30236)), {'path': 'none'}, arturl=utils.get_icon_path("podcasts.png")))
            listItems.extend(self.createPodcastFolders(result['podcasts']))
        if result['episodes']:
            if result['browseId']['episodes']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30239), True),
                    {'path': 'search_result', 'query': query['query'], 'browseId': result['browseId']['episodes'], 'episode_params': result['params']['episodes']},
                    arturl=utils.get_icon_path("songs_1.png")))
            else:
                listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30239)), {'path': 'none'}, arturl=utils.get_icon_path("songs_1.png")))
            listItems.extend(self.listSongs(result['episodes']))
        if result['related']:
            listItems.append(
                self.createFolder(utils.getTitle(self.lang(30320)), {'path': 'none'}, arturl=utils.get_icon_path("artists.png")))
            listItems.extend(self.createArtistFolders(result['related']))
        return listItems

    def getSubscriptions(self):
        return self.createArtistFolders(wrapper.Artist.wrap(self.api.getApi().get_library_subscriptions(limit=None)))
    
    def getMoodsGenres(self):
        listItems = []
        result = self.api.getApi().get_mood_categories()
        for section, categories in result.items():
            listItems.append(self.createFolder(utils.getTitle(section), {'path': 'none'}, arturl=utils.get_icon_path('explore.png')))
            for category in categories:
                params = {'path': 'mood_playlists', 'params': category['params']}
                listItems.append(self.createFolder(category['title'], params))
        return listItems
        
    def getMoodPlaylists(self, params):
        return self.createPlaylistFolders(wrapper.Playlist.wrap(self.api.getApi().get_mood_playlists(params)))
    
    def getHome(self, continuation_params=None):
        listItems = []
        result, additional_params = self.api.getApi().get_home_paged(continuation_params)
        for section in filter(lambda s: s['contents'] and not s['contents'][0] is None, result):
            home_icons = {
                'Quick picks': 'trending.png',
                'Forgotten favorites': 'likes.png',
                'Long listening': 'explore.png',
                'Listen again': 'repeat.png',
                'Mixed for you': 'shuffle.png',
                'Jazz Artists': 'artists.png',
                'Jazz playlists': 'queue.png',
                'Jazz Favorites': 'likes.png',
                'Jazz Styles': 'explore.png',
                'Jazz Moods': 'moods_&_genres.png',
                'Soothing tunes': 'moods_&_genres.png',
                'Feeling good': 'moods_&_genres.png',
                'Live performances': 'explore.png',
                'Charts': 'charts.png',
                'Covers and remixes': 'explore.png',
                'Pop Moods': 'moods_&_genres.png',
                'Pop playlists': 'queue.png',
                'From the community': 'queue.png',
                'From your library': 'albums_1.png',
                'Recommended music videos': 'ytmusic_icon.png',
                'Recommended albums': 'albums.png',
                'Recommended radios': 'start_radio.png',
                'Recommended artists': 'artists.png',
                'Recommended playlists': 'queue.png',
                'New releases': 'new_releases.png'
            }
            icon = home_icons[section['title']] if section['title'] in home_icons else 'explore.png'
            listItems.append(self.createFolder(utils.getTitle(section['title']), {'path': 'none'}, arturl=utils.get_icon_path(icon)))
            for item in section['contents']:
                if 'subscribers' in item:
                    listItems.extend(self.createArtistFolders([wrapper.HomeArtist(item)]))
                elif 'views' in item:
                    listItems.extend(self.listSongs([wrapper.Video(item)]))
                elif 'videoId' in item:
                    listItems.extend(self.listSongs([wrapper.Song(item)]))
                elif 'channel' in item:
                    listItems.extend(self.createPodcastFolders([wrapper.Podcast(item)]))
                elif 'browseId' in item:
                    listItems.extend(self.createAlbumFolders([wrapper.HomeAlbum(item)]))
                elif 'playlistId' in item:
                    listItems.extend(self.createPlaylistFolders([wrapper.Playlist(item)]))
        if additional_params:
            listItems.append(self.createFolder(">> %s >>" % str.upper(self.lang(30233)), {'path': 'home', 'params': additional_params}, arturl=utils.get_icon_path('play_next.png')))
        return listItems

    def getCharts(self, country=None):
        if country == None:
            country = utils.addon.getSetting('charts_country')
        elif country != utils.addon.getSetting('charts_country'):
            utils.addon.setSetting('charts_country', country)

        listItems = []
        result = self.api.getApi().get_charts(country)
        if 'genres' in result:
            listItems.append(self.createFolder(utils.getTitle(self.lang(30207)), {'path': 'none'}, arturl=utils.get_icon_path('moods_&_genres.png')))
            # Handle both old and new ytmusicapi structures
            if isinstance(result['genres'], list):
                # New structure: direct list of playlists (ytmusicapi 1.11.0)
                listItems.extend(self.createPlaylistFolders(wrapper.Playlist.wrap(result['genres'])))
            else:
                # Old structure: dict with 'items' key
                listItems.extend(self.createPlaylistFolders(wrapper.Playlist.wrap(result['genres']['items'])))
        if 'trending' in result:
            listItems.extend(self.createPlaylistFolders([wrapper.Playlist({'playlistId': result['trending']['playlist'],
                'title': utils.getTitle('Trending', True), 'thumbnails': [{'url': utils.get_icon_path("trending.png")}]})]))
            listItems.extend(self.listSongs(wrapper.Song.wrap(result['trending']['items'])))
        if 'songs' in result:
            listItems.extend(self.createPlaylistFolders([wrapper.Playlist({'playlistId': result['songs']['playlist'],
                'title': utils.getTitle(self.lang(30213), True), 'thumbnails': [{'url': utils.get_icon_path("songs_1.png")}]})]))
            listItems.extend(self.listSongs(wrapper.Video.wrap(result['songs']['items'])))
        if 'videos' in result:
            # Handle both old and new ytmusicapi structures
            if isinstance(result['videos'], list):
                # New structure: list of playlists (ytmusicapi 1.11.0)
                for video_playlist in result['videos']:
                    if 'playlistId' in video_playlist:
                        listItems.extend(self.createPlaylistFolders([wrapper.Playlist({
                            'playlistId': video_playlist['playlistId'],
                            'title': video_playlist.get('title', utils.getTitle('Videos', True)),
                            'thumbnails': video_playlist.get('thumbnails', [])
                        })]))
            else:
                # Old structure: dict with 'playlist' and 'items' keys
                listItems.extend(self.createPlaylistFolders([wrapper.Playlist({'playlistId': result['videos']['playlist'],
                    'title': utils.getTitle('Videos', True)})]))
                listItems.extend(self.listSongs(wrapper.Video.wrap(result['videos']['items'])))
        if 'artists' in result:
            listItems.append(self.createFolder(utils.getTitle(self.lang(30205)), {'path': 'none'}, arturl=utils.get_icon_path("artists.png")))
            # Handle both old and new ytmusicapi structures
            if isinstance(result['artists'], list):
                # New structure: direct list of artists (ytmusicapi 1.11.0)
                listItems.extend(self.createArtistFolders(wrapper.HomeArtist.wrap(result['artists'])))
            else:
                # Old structure: dict with 'items' key
                listItems.extend(self.createArtistFolders(wrapper.HomeArtist.wrap(result['artists']['items'])))
        if 'countries' in result:
            listItems.append(self.createFolder(utils.getTitle("%s: %s" % (self.lang(30232), result['countries']['selected']['text'])), {'path': 'none'}))
            for country in result['countries']['options']:
                params = {'path': 'charts', 'country': country}
                listItems.append(self.createFolder(country, params))          
        return listItems

    def getPodcasts(self):
        return self.createPodcastFolders(self.api.getPodcasts())

    def createPodcastFolders(self, podcasts):
        listItems = []
        for podcast in podcasts:
            cm = []  # self.getPlaylistContextMenu(podcast)
            folder = self.createFolder(podcast.podcast_name, {'path': "podcast", 'podcast_id': podcast.podcast_id}, cm, podcast.thumbnail)
            folder[1].setInfo(type='Music', infoLabels={
                                  'comment': podcast.description, 'mediatype': 'music'})
            listItems.append(folder)
        return listItems

    def listPodcastEpisodes(self, podcast_id):
        utils.log("Loading podcast: " + podcast_id)
        return self.listSongs(self.api.getPodcastEpisodes(podcast_id))

    def getChannels(self):
        return self.createChannelFolders(wrapper.Channel.wrap(self.api.getApi().get_library_channels()))

    def createChannelFolders(self, channels, path='channels'):
        listItems = []
        cm = []
        for channel in channels:
            params = {'path': 'search_result', 'query': channel.artist_name}
            if channel.type == 'artist':
                cm = self.getArtistContextMenu(channel)
                params['artistid'] = channel.artist_id
            elif channel.type == 'channel':
                params['channelid'] = channel.artist_id
            folder = self.createFolder(channel.artist_name, params, cm, arturl=channel.thumbnail, fanarturl=channel.thumbnail)
            folder[1].setInfo(type='Music', infoLabels={'artist': channel.artist_name, 'mediatype': 'artist'})
            listItems.append(folder)
        return listItems

    def getSongMenu(self, song:wrapper.Song):
        return_params = urllib.parse.urlencode({'return_params': urllib.parse.urlencode(self.return_params, doseq=True)}, doseq=True)
        cmItems = self.getSongContextMenu(song)
        utils.log(message="cmItems: ", log_level=xbmc.LOGDEBUG, log_object=cmItems)
        listItems = [[utils.getUrl(song), self.createItem(song)]]
        for cmItem in cmItems[3:]:
            li = ListItem(label=cmItem[0], label2=cmItem[0], offscreen=True)
            listItems.append(('&'.join([cmItem[1][10:len(cmItem[1])- 1], return_params]), li, True))
        return listItems
