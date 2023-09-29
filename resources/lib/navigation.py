import urllib.parse
import api
import utils
import wrapper
import xbmc
import xbmcplugin
from xbmcgui import ListItem

fanart = utils.addon.getAddonInfo('fanart')


class Navigation:
    def __init__(self):
        self.lang = utils.addon.getLocalizedString
        self.api = api.Api()
        self.contextmenu_action = "RunPlugin(" + utils.addon_url + "?action=%s&%s)"

        self.main_menu = (
            {'title': self.lang(30228), 'params': {'path': "home"}, },
            {'title': "YtMusic " + self.lang(30209), 'params': {'path': "ytmusic_library"}, },
            {'title': "Uploads " + self.lang(30209), 'params': {'path': "uploads_library"}, },
            {'title': self.lang(30229), 'params': {'path': "moods_genres"}, },
            {'title': self.lang(30208), 'params': {'path': "search"}, },
            {'title': self.lang(30230), 'params': {'path': "playlist", 'playlist_id': "LM"}, },
            {'title': self.lang(30231), 'params': {'path': "playlist", 'playlist_id': "history"}, },
            {'title': "Charts", 'params': {'path': "charts"}, }
        )
        self.ytlib_menu = (
            {'title': self.lang(30201), 'params': {'path': "playlist", 'playlist_id': "ytmusic_songs"}},
            {'title': self.lang(30205), 'params': {'path': "filter", 'criteria': "yt_artist"}},
            {'title': self.lang(30206), 'params': {'path': "filter", 'criteria': "yt_album"}},
            {'title': self.lang(30202), 'params': {'path': "playlists", 'type': "user"}, },
            {'title': self.lang(30226), 'params': {'path': "subscriptions"}, }
        )
        self.uplib_menu = (
            {'title': self.lang(30214), 'params': {'path': "playlist", 'playlist_id': "shuffled_albums"}},
            {'title': self.lang(30201), 'params': {'path': "playlist", 'playlist_id': "upload_songs"}},
            {'title': self.lang(30205), 'params': {'path': "filter", 'criteria': "artist"}},
            {'title': self.lang(30206), 'params': {'path': "filter", 'criteria': "album"}}
        )

    def listMenu(self, params):
        get = params.get
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

        elif path == "filter" and get('criteria') in ("album", "yt_album"):
            listItems = self.listLibraryAlbums(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path in ["artist", "yt_artist"] and get('name'):
            album_name = get('name')
            paramsAllSongs = {'path': "allcriteriasongs", 'criteria': path, 'name': album_name}
            listItems.insert(0, self.createFolder('* ' + self.lang(30201), paramsAllSongs))
            listItems.extend(self.listLibraryAlbums(path, album_name))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path == "filter":
            listItems = self.getCriteria(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]

        elif path == "allcriteriasongs":
            listItems = self.listAllCriteriaSongs(get('criteria'), get('name'))
            sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "songs"

        elif path in ["artist", "album", "yt_artist", "yt_album"]:
            songs = wrapper.LibrarySong.wrap(self.api.getFilterSongs(path, get('album'), get('artist', '')))
            listItems = self.listSongs(songs)
            sortMethods = [xbmcplugin.SORT_METHOD_TRACKNUM, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
                           xbmcplugin.SORT_METHOD_PLAYCOUNT, xbmcplugin.SORT_METHOD_SONG_RATING]
            content = "songs"

        elif path == "search":
            listItems.append(self.createFolder(self.lang(30223), {'path': 'search_new'}))
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
            listItems, content = self.getSearch(params)

        elif path == "store_album":
            utils.log("ALBUM: " + get('album_id'))
            listItems = self.listSongs(self.api.getAlbum(get('album_id')))
            content = "songs"

        elif path == "artist_topsongs":
            listItems = self.listSongs(wrapper.Song.wrap(self.api.getArtistInfo(get('artistid'))['tracks']))
            content = "songs"

        elif path == "related_artists":
            listItems = []
            items = self.api.getArtistInfo(get('artistid'), False, 0, relartists=10)['relartists']
            for item in items:
                params = {'path': 'artist_topsongs', 'artistid': item['artistId']}
                listItems.append(self.createFolder(item['name'], params, arturl=item['artistArtRef']))
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

        elif path == "home":
            listItems = self.getHome()
            content = "songs"
        
        elif path == "charts":
            listItems = self.getCharts(get('country'))
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
            menuItems.append(self.createFolder(menu_item['title'], params, cm))
        return menuItems

    def listPlaylistSongs(self, playlist_id):
        utils.log("Loading playlist: " + playlist_id)
        return self.listSongs(self.api.getPlaylistSongs(playlist_id))

    def listSongs(self, songs):
        return [[utils.getUrl(song), self.createItem(song)] for song in songs]

    def listAllCriteriaSongs(self, filter_type, filter_criteria):
        songs = self.api.getFilterSongs(filter_type, filter_criteria, '')
        listItems = []

        # add album name when showing all artist songs
        for song in songs:
            songItem = self.createItem(song)
            songItem.setLabel("".join(['[', song.album_title, '] ', song.title]))
            songItem.setLabel2(song.album_title)
            listItems.append([utils.getUrl(song), songItem])

        return listItems

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
        return self.createPlaylistFolders(wrapper.LibraryPlaylist.wrap(self.api.get_playlists()))

    def listLibraryAlbums(self, criteria, name=''):
        utils.log("LIST ALBUMS: " + repr(criteria) + " " + repr(name))
        listItems = []
        getCm = self.getFilterContextMenu
        items = self.api.getCriteria(criteria, name)

        for item in items:
            # utils.log(repr(item))
            album = item['album']
            artist = item['artist']
            params = {'path': criteria, 'album': album, 'artist': artist}
            folder = self.createFolder(album, params, getCm(criteria, album, artist), item['arturl'], artist)
            folder[1].setInfo(type='Music', infoLabels={'artist': artist, 'album': album, 'mediatype': 'album'})
            listItems.append(folder)

        return listItems

    def getCriteria(self, criteria):
        utils.log("CRITERIA: " + repr(criteria))
        folder = self.createFolder
        getCm = self.getFilterContextMenu
        items = self.api.getCriteria(criteria)

        if criteria in ('artist', 'yt_artist'):
            return [folder(item['criteria'], {'path': criteria, 'name': item['criteria']},
                           getCm(criteria, item['criteria']), item['arturl'], fanarturl=item['arturl']) for item in items]
        else:
            return [folder(item['criteria'], {'path': criteria, 'album': item['criteria']},
                           getCm(criteria, item['criteria'])) for item in items]

    def createPlaylistFolders(self, playlists):
        listItems = []
        for playlist in playlists:
            cm = self.getPlaylistContextMenu(playlist)
            folder = self.createFolder(playlist.playlist_name, {'path': "playlist", 'playlist_id': playlist.playlist_id}, cm, playlist.thumbnail)
            folder[1].setInfo(type='Music', infoLabels={
                                  'comment': playlist.description, 'mediatype': 'music'})
            listItems.append(folder)
        return listItems

    def createAlbumFolders(self, albumlist):
        listItems = []
        for album in albumlist:
            if album.is_library_item:
                params = {'path': 'album', 'album': album.album_title, 'artist': album.artist_name}
                cm = self.getFilterContextMenu('album', album.album_title)
                folder_name = "[%s] %s" % (album.artist_name, album.album_title)
                listItems.append(self.createFolder(folder_name, params, cm, album.thumbnail))
            else:
                # utils.log("SEA_ALB_ITEM "+repr(item))
                params = {'path': 'store_album', 'album_id': album.album_id}
                cm = [self.create_menu(30301, "play_all", params),
                      #   self.create_menu(30309, "add_album_library", params),
                      self.create_menu(30315, "add_to_queue", params)]

                folder = self.createFolder(name=f"[{album.artist_name}] {album.album_title}",
                    params=params,
                    contextMenu=cm,
                    arturl=album.thumbnail,
                    name2=album.description,
                    fanarturl=album.thumbnail
                )
                folder[1].setInfo(type='Music', infoLabels={
                                  'artist': album.artist_name, 'album': album.album_title, 'mediatype': 'album'})
                listItems.append(folder)
        return listItems

    def createArtistFolders(self, artists):
        listItems = []
        for artist in artists:
            if artist.is_library_item:
                params = {'path': 'artist', 'name': artist.artist_name}
                cm = []
            else:
                params = {'path': 'search_result', 'artistid': artist.artist_id, 'query': artist.artist_name}
                cm = self.getArtistContextMenu(artist)
            folder = self.createFolder(artist.artist_name, params, cm, arturl=artist.thumbnail, fanarturl=artist.thumbnail)
            folder[1].setInfo(type='Music', infoLabels={
                              'artist': artist.artist_name, 'mediatype': 'artist'})
            listItems.append(folder)
        return listItems

    def getSongContextMenu(self, song):
        params = {'videoId': song.video_id, 'display_name': song.display_name}
        cm = []
        #if not song.is_library_item:
        #    cm.append(self.create_menu(30309, "add_library", params))
        cm.append(self.create_menu(30325, "play_all", params))
        cm.append(self.create_menu(30326, "play_next", params))
        cm.append(self.create_menu(30315, "add_to_queue", params))
        cm.append(self.create_menu(30307, "add_playlist", params))
        if song.album_id:
            cm.append(self.create_menu(30327, "goto_album", {'album_id': song.album_id}))
        if song.artist_id:
            cm.append(self.create_menu(30319, "artist_topsongs", {'artistid': song.artist_id}))
            cm.append(self.create_menu(30328, "goto_artist", {'artistid': song.artist_id, 'query': song.artist_name}))
        if song.is_playlist_song:
            playlist_params = {'videoId': song.video_id,
                        'display_name': song.display_name, 'playlist_id': song.playlist_id}
            cm.append(self.create_menu(30322, "play_all", playlist_params))
            if song.is_library_item:
                cm.append(self.create_menu(30308, "del_from_playlist", playlist_params))
        # cm.append(self.create_menu(30409, "set_thumbs", params))
        # cm.append(self.create_menu(30313, "play_yt", params))
        # cm.append(self.create_menu(30311, "search_yt", params))
        return cm

    def getPlaylistContextMenu(self, playlist):
        params = {'playlist_id': playlist.playlist_id, 'title': playlist.playlist_name}
        shuffle = params.copy()
        shuffle.update({'shuffle': 'true'})
        cm = [
            self.create_menu(30301, "play_all", params),
            self.create_menu(30302, "play_all", shuffle),
            # self.create_menu(30312, "play_all_yt",params),
            # self.create_menu(30321, "play_all_yt", shuffle),
            # self.create_menu(30306, "add_favourite", {'playlist_id': playlist, 'title': name, 'path': 'playlist'}),
            self.create_menu(30315, "add_to_queue", params)
        ]
        if playlist.is_library_item:
            cm.append(self.create_menu(30317, "delete_playlist", params))
        return cm

    def getFilterContextMenu(self, filter_type, filter_criteria, artist=''):
        params = {'filter_type': filter_type, 'filter_criteria': filter_criteria, 'artist': artist}
        shuffle = params.copy()
        shuffle.update({'shuffle': 'true'})
        return [
            self.create_menu(30301, "play_all", params),
            self.create_menu(30302, "play_all", shuffle),
            # self.create_menu(30312, "play_all_yt", params),
            # self.create_menu(30321, "play_all_yt", shuffle),
            # self.create_menu(30306, "add_favourite", {'path': filter_type, 'name': filter_criteria, 'title': filter_criteria}),
            self.create_menu(30315, "add_to_queue", params),
            self.create_menu(30208, "search", params),
        ]

    def getArtistContextMenu(self, artist):
        params = {'artist_id': artist.artist_id}
        return [
            self.create_menu(30301, "play_all", params),
            self.create_menu(30323, "subscribe_artist", params),
            self.create_menu(30324, "unsubscribe_artist", params)
        ]

    def create_menu(self, text_code, action, params={'1':1}):
        return self.lang(text_code), self.contextmenu_action % (action, urllib.parse.urlencode(params, doseq=True))

    def getSearch(self, query):
        listItems = []
        content = "songs"

        if isinstance(query, str):
            result = self.api.getSearch(query)
            if result['artists']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30205), True),
                                                   {'path': 'search_result', 'type': 'artists', 'query': query}))
                listItems.extend(self.createArtistFolders(result['artists']))
            if result['albums']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30206), True),
                                                   {'path': 'search_result', 'type': 'albums', 'query': query}))
                listItems.extend(self.createAlbumFolders(result['albums']))
            if result['tracks']:
                listItems.append(self.createFolder(utils.getTitle(self.lang(30213), True),
                                                   {'path': 'search_result', 'type': 'songs', 'query': query}))
                listItems.extend(self.listSongs(result['tracks']))
            if result['playlists']:
                listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30202)), {'path': 'none'}))
                listItems.extend(self.createPlaylistFolders(result['playlists']))
            if result['videos']:
                listItems.append(self.createFolder(utils.getTitle('Youtube'), {'path': 'none'}))
                listItems.extend(self.listSongs(result['videos']))

        elif 'album_params' in query:
            result = self.api.getArtistAlbums(query['query'], query['browseId'], query['album_params'])
            listItems.extend(self.createAlbumFolders(result['albums']))
 
        elif 'artistid' in query:
            result = self.api.getArtistInfo(query['artistid'])
            if result['albums']:
                if result['browseId']['albums']:
                    listItems.append(
                        self.createFolder(utils.getTitle(self.lang(30206), True),
                                          {'path': 'search_result', 'query': query['query'], 'browseId': result['browseId']['albums'], 'album_params': result['params']['albums']}))
                else:
                    listItems.append(
                        self.createFolder(utils.getTitle(self.lang(30206)), {'path': 'none'}))
                listItems.extend(self.createAlbumFolders(result['albums']))
            if result['singles']:
                if result['browseId']['singles']:
                    listItems.append(
                        self.createFolder(utils.getTitle(self.lang(30227), True),
                                          {'path': 'search_result', 'query': query['query'], 'browseId': result['browseId']['singles'], 'album_params': result['params']['singles']}))
                else:
                    listItems.append(
                        self.createFolder(utils.getTitle(self.lang(30227)), {'path': 'none'}))
                listItems.extend(self.createAlbumFolders(result['singles']))
            if result['songs']:
                if result['browseId']['songs']:
                    listItems.extend(self.createPlaylistFolders([wrapper.Playlist({'playlistId': result['browseId']['songs'],
                                                                                   'title': utils.getTitle(self.lang(30213), True)})]))
                else:
                    listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30213)), {'path': 'none'}))
                listItems.extend(self.listSongs(result['songs']))
            if result['videos']:
                listItems.append(self.createFolder(utils.getTitle('Youtube'), {'path': 'none'}))
                listItems.extend(self.listSongs(result['videos']))
            if result['artists']:
                listItems.append(
                    self.createFolder(utils.getTitle(self.lang(30320)), {'path': 'none'}))
                listItems.extend(self.createArtistFolders(result['artists']))

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

    def getSubscriptions(self):
        return self.createArtistFolders(wrapper.Artist.wrap(self.api.getApi().get_library_subscriptions()))
    
    def getMoodsGenres(self):
        listItems = []
        result = self.api.getApi().get_mood_categories()
        for section, categories in result.items():
            listItems.append(self.createFolder(utils.getTitle(section), {'path': 'none'}))
            for category in categories:
                params = {'path': 'mood_playlists', 'params': category['params']}
                listItems.append(self.createFolder(category['title'], params))
        return listItems
        
    def getMoodPlaylists(self, params):
        return self.createPlaylistFolders(wrapper.Playlist.wrap(self.api.getApi().get_mood_playlists(params)))
    
    def getHome(self):
        listItems = []
        result = self.api.getApi().get_home(10)
        for section in result:
            listItems.append(self.createFolder(utils.getTitle(section['title']), {'path': 'none'}))
            for item in section['contents']:
                if 'subscribers' in item:
                    listItems.extend(self.createArtistFolders([wrapper.HomeArtist(item)]))
                elif 'views' in item:
                    listItems.extend(self.listSongs([wrapper.Video(item)]))
                elif 'videoId' in item:
                    listItems.extend(self.listSongs([wrapper.Song(item)]))
                elif 'browseId' in item:
                    listItems.extend(self.createAlbumFolders([wrapper.HomeAlbum(item)]))
                elif 'playlistId' in item:
                    listItems.extend(self.createPlaylistFolders([wrapper.Playlist(item)]))
        return listItems

    def getCharts(self, country = None):
        if country == None:
            country = utils.addon.getSetting('charts_country')
        elif country != utils.addon.getSetting('charts_country'):
            utils.addon.setSetting('charts_country', country)

        listItems = []
        result = self.api.getApi().get_charts(country)
        if 'genres' in result:
            listItems.append(self.createFolder(utils.getTitle(self.lang(30207)), {'path': 'none'}))
            listItems.extend(self.createPlaylistFolders(wrapper.Playlist.wrap(result['genres'])))
        if 'trending' in result:
            listItems.extend(self.createPlaylistFolders([wrapper.Playlist({'playlistId': result['trending']['playlist'],
                'title': utils.getTitle('Trending', True)})]))
            listItems.extend(self.listSongs(wrapper.Song.wrap(result['trending']['items'])))
        if 'videos' in result:
            listItems.extend(self.createPlaylistFolders([wrapper.Playlist({'playlistId': result['videos']['playlist'],
                'title': utils.getTitle('Videos', True)})]))
            listItems.extend(self.listSongs(wrapper.Video.wrap(result['videos']['items'])))
        if 'artists' in result:
            listItems.append(self.createFolder(utils.getTitle(self.lang(30205)), {'path': 'none'}))
            listItems.extend(self.createArtistFolders(wrapper.HomeArtist.wrap(result['artists']['items'])))
        if 'countries' in result:
            listItems.append(self.createFolder(utils.getTitle("%s: %s" % (self.lang(30232), result['countries']['selected']['text'])), {'path': 'none'}))
            for country in result['countries']['options']:
                params = {'path': 'charts', 'country': country}
                listItems.append(self.createFolder(country, params))          
        return listItems
