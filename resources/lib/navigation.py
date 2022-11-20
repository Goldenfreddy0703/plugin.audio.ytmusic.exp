import urllib.parse
import api
import utils
import xbmc
import xbmcplugin
from xbmcgui import ListItem

fanart = utils.addon.getAddonInfo('fanart')


class Navigation:
    def __init__(self):
        self.lang = utils.addon.getLocalizedString
        self.api = api.Api()
        self.contextmenu_action = "RunPlugin("+utils.addon_url+"?action=%s&%s)"

        self.main_menu = (
            {'title': "YtMusic "+self.lang(30209), 'params': {'path': "ytmusic_library"}, },
            {'title': "Uploads "+self.lang(30209), 'params': {'path': "uploads_library"}, },
            {'title': self.lang(30202), 'params': {'path': "playlists_menu"}, },
            {'title': self.lang(30208), 'params': {'path': "search"}, }
        )
        self.ytlib_menu = (
            {'title': self.lang(30201), 'params': {'path': "playlist", 'playlist_id': "ytmusic_songs"}},
            {'title': self.lang(30205), 'params': {'path': "filter", 'criteria': "yt_artist"}},
            {'title': self.lang(30206), 'params': {'path': "filter", 'criteria': "yt_album"}},
        )
        self.uplib_menu = (
            {'title': self.lang(30214), 'params': {'path': "playlist", 'playlist_id': "shuffled_albums"}},
            {'title': self.lang(30201), 'params': {'path': "playlist", 'playlist_id': "upload_songs"}},
            {'title': self.lang(30205), 'params': {'path': "filter", 'criteria': "artist"}},
            {'title': self.lang(30206), 'params': {'path': "filter", 'criteria': "album"}},
        )
        self.playlists_menu = (
            {'title': self.lang(30202), 'params': {'path': "playlists", 'type': "user"}, },
            {'title': 'Liked', 'params': {'path': "playlist", 'playlist_id': "thumbsup"}, },
            {'title': 'History', 'params': {'path': "playlist", 'playlist_id': "history"}, },
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

        elif path == "playlists_menu":
            listItems = self.getMenuItems(self.playlists_menu)

        elif path == "playlist":
            listItems = self.listPlaylistSongs(get("playlist_id"))
            if get("playlist_id") in ('upload_songs','ytmusic_songs'):
                sortMethods = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
            content = "songs"

        elif path == "playlists":
            listItems = self.getPlaylists()

        elif path == "filter" and get('criteria') in ("album","yt_album"):
            listItems = self.listAlbums(get('criteria'))
            sortMethods = [xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE, xbmcplugin.SORT_METHOD_VIDEO_YEAR,
                           xbmcplugin.SORT_METHOD_ARTIST, xbmcplugin.SORT_METHOD_ALBUM, xbmcplugin.SORT_METHOD_DATE]
            content = "albums"

        elif path in ["artist", "yt_artist"] and get('name'):
            album_name = get('name')
            paramsAllSongs = {'path': "allcriteriasongs", 'criteria': path, 'name': album_name}
            listItems.insert(0, self.createFolder('* ' + self.lang(30201), paramsAllSongs))
            listItems.extend(self.listAlbums(path, album_name))
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
            songs = self.api.getFilterSongs(path, get('album'), get('artist', ''))
            listItems = self.addSongsFromLibrary(songs, 'library')
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
                listItems = self.getSearch(keyboard.getText())
                history = utils.addon.getSetting('search-history')
                history = keyboard.getText() + ('|' + history if history else '')
                if len(history.split('|')) > 10:
                    history = '|'.join(history.split('|')[0:-1])
                utils.addon.setSetting('search-history', history)
                content = "songs"
            else:
                return

        elif path == "search_query":
            listItems = self.getSearch(get("query"))
            content = "songs"

        elif path == "search_result":
            utils.log("SEARCH_RESULT: " + get('query'))
            listItems = self.getSearch(params)
            content = "songs"

        elif path == "store_album":
            utils.log("ALBUM: " + get('album_id'))
            listItems = self.addSongsFromLibrary(self.api.getAlbum(get('album_id')), 'library')
            content = "songs"

        elif path == "artist_topsongs":
            listItems = self.addSongsFromLibrary(self.api.getArtistInfo(get('artistid'))['tracks'], 'library')
            content = "songs"

        elif path == "related_artists":
            listItems = []
            items = self.api.getArtistInfo(get('artistid'), False, 0, relartists=10)['relartists']
            for item in items:
                params = {'path': 'artist_topsongs', 'artistid': item['artistId']}
                listItems.append(self.createFolder(item['name'], params, arturl=item['artistArtRef']))

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
                cm = self.getPlayAllContextMenu(menu_item['title'], params['playlist_id'])
            elif 'type' in params:
                cm.append(self.create_menu(30304, "update_playlists", {'playlist_type': params['type']}))
                #cm.append(self.create_menu(30306, "add_favourite", {'path': 'playlists', 'playlist_type': params['type'], 'title': menu_item['title']}))
                #cm.append(self.create_menu(30316, "create_playlist"))
            elif params['path'] in ('uploads_library', 'ytmusic_library'):
                cm.append(self.create_menu(30305, "update_library"))
                #cm.append(self.create_menu(30306, "add_favourite", {'path': 'library', 'title': menu_item['title']}))
            #elif 'criteria' in params:
            #    cm.append(self.create_menu(30306, "add_favourite", {'path': 'filter', 'criteria': params['criteria'], 'title': menu_item['title']}))
            menuItems.append(self.createFolder(menu_item['title'], params, cm))
        return menuItems

    def listPlaylistSongs(self, playlist_id):
        utils.log("Loading playlist: " + playlist_id)
        songs = self.api.getPlaylistSongs(playlist_id)
        # utils.log(repr(songs))
        if playlist_id in ('thumbsup', 'history', 'upload_songs', 'shuffled_albums', 'ytmusic_songs'):
            return self.addSongsFromLibrary(songs, 'library')
        return self.addSongsFromLibrary(songs, 'playlist' + playlist_id)

    def addSongsFromLibrary(self, library, song_type):
        return [[utils.getUrl(song), self.createItem(song, song_type)] for song in library]

    def listAllCriteriaSongs(self, filter_type, filter_criteria):
        songs = self.api.getFilterSongs(filter_type, filter_criteria, '')
        listItems = []

        # add album name when showing all artist songs
        for song in songs:
            songItem = self.createItem(song, 'library')
            songItem.setLabel("".join(['[', song['album'], '] ', song['title']]))
            songItem.setLabel2(song['album'])
            listItems.append([utils.getUrl(song), songItem])

        return listItems

    def createItem(self, song, song_type):
        infoLabels = {
            'album': song['album']['name'] if not isinstance(song['album'],str) else song['album'],
            'artist': [song['artist']],
            'title': song['title'],
            'mediatype': 'video'
        }
        li = utils.createItem(song['display_name'], song['albumart'])
        li.setInfo(type='Video', infoLabels=infoLabels)
        li.addContextMenuItems(self.getSongContextMenu(song['videoId'], song['display_name'], song_type))
        return li

    def getPlaylists(self):
        listItems = []
        append = listItems.append
        addFolder = self.createFolder

        for pl_id, pl_name, pl_arturl in self.api.get_playlists():
            cm = self.getPlayAllContextMenu(pl_name, pl_id)
            append(addFolder(pl_name, {'path': "playlist", 'playlist_id': pl_id}, cm, pl_arturl))

        return listItems

    def listAlbums(self, criteria, name=''):
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


    def createAlbumFolder(self, items):
        listItems = []
        for item in items:
            # utils.log("SEA_ALB_ITEM "+repr(item))
            params = {'path': 'store_album', 'album_id': item['browseId']}
            cm = [self.create_menu(30301, "play_all", params),
                  #   self.create_menu(30309, "add_album_library", params),
                  self.create_menu(30315, "add_to_queue", params)]
            folder = self.createFolder(name=f"[{item['artist']}] {item['title']}", 
                params=params, 
                contextMenu=cm, 
                arturl=item['thumbnails'][-1]['url'], 
                name2=item.get('description'), 
                fanarturl=item['thumbnails'][-1]['url'])
                    
            folder[1].setInfo(type='Music', infoLabels={
                              'artist': item['artist'], 'album': item['title'], 'mediatype': 'album'})
            listItems.append(folder)
        return listItems

    def createFolder(self, name, params, contextMenu=[], arturl='', name2='*', fanarturl=fanart):
        li = ListItem(label=name, label2=name2, offscreen=True)
        li.setArt({'thumb': arturl, 'fanart': fanarturl})
        li.addContextMenuItems(contextMenu)
        return "?".join([utils.addon_url, urllib.parse.urlencode(params, doseq=True)]), li, True

    def getSongContextMenu(self, videoId, display_name, song_type):
        params = {'videoId': videoId, 'display_name': display_name}
        cm = []
        #if videoId.startswith('T'):
        #    cm.append(self.create_menu(30309, "add_library", params))
        #    cm.append(self.create_menu(30319, "artist_topsongs", params))
        if song_type == 'library':
            cm.append(self.create_menu(30307, "add_playlist", params))
        elif song_type.startswith('playlist'):
            playlist = {'videoId': videoId,
                        'display_name': display_name, 'playlist_id': song_type[8:]}
            cm.append(self.create_menu(30322, "play_all", playlist))
            cm.append(self.create_menu(30308, "del_from_playlist", playlist))
        #cm.append(self.create_menu(30409, "set_thumbs", params))
        #cm.append(self.create_menu(30313, "play_yt", params))
        #cm.append(self.create_menu(30311, "search_yt", params))
        return cm

    def getPlayAllContextMenu(self, name, playlist):
        params = {'playlist_id': playlist, 'title': name}
        shuffle = params.copy()
        shuffle.update({'shuffle': 'true'})
        cm = [
            self.create_menu(30301, "play_all", params),
            self.create_menu(30302, "play_all", shuffle),
            #self.create_menu(30312, "play_all_yt",params),
            #self.create_menu(30321, "play_all_yt", shuffle),
            #self.create_menu(30306, "add_favourite", {'playlist_id': playlist, 'title': name, 'path': 'playlist'}),
            self.create_menu(30315, "add_to_queue", params),
            self.create_menu(30317, "delete_playlist", params)
            ]
        return cm

    def getFilterContextMenu(self, filter_type, filter_criteria, artist=''):
        params = {'filter_type': filter_type, 'filter_criteria': filter_criteria, 'artist': artist}
        shuffle = params.copy()
        shuffle.update({'shuffle': 'true'})
        return [
            self.create_menu(30301, "play_all", params),
            self.create_menu(30302, "play_all", shuffle),
            #self.create_menu(30312, "play_all_yt", params),
            #self.create_menu(30321, "play_all_yt", shuffle),
            #self.create_menu(30306, "add_favourite", {'path': filter_type, 'name': filter_criteria, 'title': filter_criteria}),
            self.create_menu(30315, "add_to_queue", params),
            self.create_menu(30208, "search", params),
            ]

    def create_menu(self, text_code, action, params={'1':1}):
        return self.lang(text_code), self.contextmenu_action % (action, urllib.parse.urlencode(params, doseq=True))

    def getSearch(self, query):
        listItems = []

        def listAlbumsResults():
            for album in result['albums']:
                if 'browseId' in album:
                    listItems.extend(self.createAlbumFolder([album]))
                else:
                    params = {'path': 'album', 'album': album['title'], 'artist': album['artist']}
                    cm = self.getFilterContextMenu('album', album['title'])
                    folder_name = "[%s] %s" % (album['artist'], album['title'])
                    listItems.append(self.createFolder(folder_name, params, cm, album['albumart']))

        def listArtistsResults():
            cm = []
            for artist in result['artists']:
                params = {'path': 'artist', 'name': artist['artist']}
                if 'browseId' in artist:
                    params = {'path': 'search_result', 'artistid': artist['browseId'], 'query': artist['artist']}
                    cm = [self.create_menu(30301, "play_all", {'artist_id': artist['browseId']})]
                    art = artist['thumbnails'][-1]['url']
                else:
                    art = artist['artistArtRef']
                listItems.append(self.createFolder(artist['artist'], params, cm, arturl=art, fanarturl=art))

        if isinstance(query, str):
            result = self.api.getSearch(query)
            if result['artists']:
                listItems.append(self.createFolder('[COLOR orange]*** ' + self.lang(30205) + ' ***[/COLOR] +>',
                                                   {'path': 'search_result', 'type': 'artists', 'query': query}))
                listArtistsResults()
            if result['albums']:
                listItems.append(self.createFolder('[COLOR orange]*** ' + self.lang(30206) + ' ***[/COLOR] +>',
                                                   {'path': 'search_result', 'type': 'albums', 'query': query}))
                listAlbumsResults()
            if result['tracks']:
                listItems.append(self.createFolder('[COLOR orange]*** ' + self.lang(30213) + ' ***[/COLOR] +>',
                                                   {'path': 'search_result', 'type': 'songs', 'query': query}))
                listItems.extend(self.addSongsFromLibrary(result['tracks'], 'library'))
            if result['playlists']:
                listItems.append(
                    self.createFolder('[COLOR orange]*** ' + self.lang(30202) + ' ***[/COLOR]', {'path': 'none'}))
                for playlist in result['playlists']:
                    cm = self.getPlayAllContextMenu(playlist['title'], playlist['browseId'])
                    listItems.append(
                        self.createFolder(playlist['title'], {'path': "playlist", 'playlist_id': playlist['browseId']}, cm, playlist['thumbnails'][-1]['url']))
            if result['videos']:
                listItems.append(self.createFolder('[COLOR orange]*** Youtube ***[/COLOR]', {'path': 'none'}))
                listItems.extend(self.addSongsFromLibrary(result['videos'], 'library'))

        elif 'artistid' in query:
            result = self.api.getArtistInfo(query['artistid'])
            if result['albums']:
                listItems.append(
                    self.createFolder('[COLOR orange]*** ' + self.lang(30206) + ' ***[/COLOR]', {'path': 'none'}))
                listAlbumsResults()
            listItems.append(
                self.createFolder('[COLOR orange]*** ' + self.lang(30213) + ' ***[/COLOR]', {'path': 'none'}))
            listItems.extend(self.addSongsFromLibrary(result['tracks'], 'library'))

        elif 'type' in query:
            result = self.api.getSearch(query['query'], max_results=50, filter=query['type'])
            if query['type'] == 'artists':
                listArtistsResults()
            elif query['type'] == 'albums':
                listAlbumsResults()
            elif query['type'] == 'songs':
                listItems.extend(self.addSongsFromLibrary(result['tracks'], 'library'))

        else:
            listItems.extend(self.getSearch(query['query']))

        return listItems
