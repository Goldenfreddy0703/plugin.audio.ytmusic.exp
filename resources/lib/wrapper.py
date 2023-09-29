'''
Created on 10.09.2023

@author: bernt
'''
from abc import ABCMeta, abstractmethod


class YTMusicItemWrapper(metaclass=ABCMeta): 
    '''
    Base Class for YTMusic item wrappers
    '''

    @classmethod
    def wrap(cls, items):
        '''
        Generator method yielding each list item wrapped 
        '''       
        for item in items:
            yield cls(item)
    
    def __init__(self, item):
        '''
        Initialize class with list item to wrap 
        '''       
        self._item = item
        
    @property
    def is_library_item(self):
        return False

    @property
    def thumbnail(self):
        if 'thumbnails' in self._item:
            return self._item['thumbnails'][-1]['url']

    @property
    def artist_name(self):
        if 'artists' in self._item:
            if isinstance(self._item['artists'], list) and len(self._item['artists']) > 0:
                name = self._item['artists'][0]['name']
                return name if name != 'Song' else self._item['artists'][1]['name']
            else:
                return ''
        else:
            return self._item['artist']

    @property
    def artist_id(self):
        if 'artists' in self._item:
            if not self._item['artists'] is None:
                name = self._item['artists'][0]['name']
                return self._item['artists'][0]['id'] if name != 'Song' else self._item['artists'][1]['id']


    @property
    def duration(self):
        if 'duration_seconds' in self._item:
            return int(self._item['duration_seconds'])
        elif 'lengthSeconds' in self._item:
            return int(self._item['lengthSeconds'])
        elif 'duration' in self._item:
            dur = self._item['duration'].split(':')
            duration = int(dur[-2]) * 60 + int(dur[-1])
            if len(dur) > 2:
                duration = duration + int(dur[-3]) * 60 * 60
            return duration


class Song(YTMusicItemWrapper):
    '''
    Wrapper Class for a YTMusic song
    '''
    
    @property
    def is_playlist_song(self):
        return False

    @property
    def is_video(self):
        return False

    @property
    def video_id(self):
        return self._item['videoId']

    @property
    def title(self):
        return self._item['title']
    
    @property
    def display_name(self):
        return self.artist_name + " - " + self.title
    
    @property
    def album_title(self):
        return self._item['album']['name'] if 'album' in self._item and isinstance(self._item['album'], list) else ''

    @property
    def album_id(self):
        return self._item['album']['id'] if 'album' in self._item and isinstance(self._item['album'], list) else None


class SongFromVideoId(Song):
    '''
    Wrapper Class for a song obtained from YTMusic.get_song() function
    '''
        
    @property
    def artist_name(self):
        return self._item['author']
        

class GetAlbumSong(Song):
    '''
    Wrapper Class for a song obtained from YTMusic.get_album() function
    '''
    
    @classmethod
    def wrap(cls, get_album_result):
        '''
        Generator method yielding each list item wrapped with thumbnail from album
        '''
        thumbnail = get_album_result['thumbnails'][-1]['url']
        #album_title = get_album_result['title']  
        
        for item in get_album_result['tracks']:
            yield cls(item, thumbnail) #, album_title)
    
    def __init__(self, item, thumbnail): #, album_title):
        '''
        Initialize class with list item to wrap 
        '''       
        self._item = item
        #self._album_title = album_title
        self._thumbnail = thumbnail
        
    @property
    def album_title(self):
        #return self._album_title
        return self._item['album']      

    @property
    def thumbnail(self):
        return self._thumbnail      


class PlaylistSong(Song):
    '''
    Wrapper Class for a song which is part of a playlist
    '''
    
    @classmethod
    def wrap(cls, items, playlist_id):
        '''
        Generator method yielding each list item wrapped with artist name from call argument
        '''
        
        for item in items:
            yield cls(item, playlist_id)
    
    def __init__(self, item, playlist_id):
        '''
        Initialize class with list item to wrap 
        '''       
        self._item = item
        self._playlist_id = playlist_id
        
    @property
    def is_playlist_song(self):
        return True

    @property
    def playlist_id(self):
        return self._playlist_id   
 
    
class LibrarySong(Song):
    '''
    Wrapper Class for a song read from stored YTMusic library
    '''
    
    @property
    def is_library_item(self):
        return True

    @property
    def duration(self):
        return self._item['duration']
    
    @property
    def album_title(self):
        return self._item['album']

    @property
    def album_id(self):
        return None

    @property
    def artist_name(self):
        return self._item['artist']
    
    @property
    def thumbnail(self):
        return self._item['albumart']


class LibraryPlaylistSong(PlaylistSong, LibrarySong):
    '''
    Wrapper Class for songs which is part of a playlist read from stored YTMusic library
    '''
    pass


class SongFromParams(Song):
    '''
    Wrapper Class for a song read from play_song params
    '''
    
    @property
    def is_video(self):
        if 'isVideo' in self._item:
            return str.strip(self._item['isVideo']) == 'True'

    @property
    def duration(self):
        if 'duration' in self._item and self._item['duration'] != 'None':
            return int(self._item['duration'])
    
    @property
    def album_title(self):
        if 'album' in self._item:
            return self._item['album']

    @property
    def album_id(self):
        return None

    @property
    def artist_name(self):
        return self._item['artist']
    
    @property
    def thumbnail(self):
        return self._item['albumart']


class GetPlaylistSong(PlaylistSong):
    '''
    Wrapper Class for a song obtained from YTMusic.get_playlist() function
    '''
    
    @classmethod
    def wrap(cls, get_playlist_result):
        '''
        Generator method yielding each list item wrapped with artist name from call argument
        '''
        
        playlist_id = get_playlist_result['id']
        if 'tracks' in get_playlist_result:
            for item in get_playlist_result['tracks']:
                yield cls(item, playlist_id)

     
class Video(Song):
    '''
    Wrapper Class for a video
    '''

    @property
    def is_video(self):
        return True
    

class Playlist(YTMusicItemWrapper):
    '''
    Wrapper Class for a playlist
    '''

    @property
    def playlist_id(self):
        return self._item['playlistId']

    @property
    def playlist_name(self):
        return self._item['title']
    
    @property
    def count(self):
        if 'count' in self._item:
            return self._item['count']

    @property
    def description(self):
        if 'description' in self._item:
            return self._item['description']

    
class SearchPlaylist(Playlist): 
    '''
    Wrapper Class for a playlist obtained from YTMusic.get_home() function
    '''

    @property
    def playlist_id(self):
        return self._item['browseId']


class LibraryPlaylist(Playlist): 
    '''
    Wrapper Class for a playlist read from stored YTMusic library
    '''

    @property
    def is_library_item(self):
        return True

    @property
    def playlist_id(self):
        return self._item['playlist_id']

    @property
    def playlist_name(self):
        return self._item['name']
    
    @property
    def thumbnail(self):
        return self._item['arturl']
    

class Album(YTMusicItemWrapper):
    '''
    Wrapper Class for an album
    '''
    
    @property
    def album_title(self):
        return self._item['title'] if 'title' in self._item else ''

    @property
    def album_id(self):
        if 'browseId' in self._item:
            return self._item['browseId']

    @property
    def description(self):
        return self._item['description'] if 'description' in self._item else ''
            

class LibraryAlbum(Album):
    '''
    Wrapper Class for an album read from stored YTMusic library
    '''
    
    @property
    def is_library_item(self):
        return True

    @property
    def thumbnail(self):
        return self._item['albumart']

   
class HomeAlbum(Album):
    '''
    Wrapper Class for an album obtained from YTMusic.get_home() function
    '''
    
    @property
    def artist_name(self):
        return self._item['year'] if 'year' in self._item else super().artist_name


class GetArtistAlbum(Album):
    '''
    Wrapper Class for an album obtained from YTMusic.get_artist() function
    '''
    
    @classmethod
    def wrap(cls, items, artist_name):
        '''
        Generator method yielding each list item wrapped with artist name from call argument
        '''
        
        for item in items:
            yield cls(item, artist_name)
    
    def __init__(self, item, artist_name):
        '''
        Initialize class with list item to wrap 
        '''       
        self._item = item
        self._artist_name = artist_name
        
    @property
    def artist_name(self):
        return self._artist_name   
    
    
class Artist(YTMusicItemWrapper):
    '''
    Wrapper Class for an artist
    '''

    @property
    def artist_id(self):
        if 'browseId' in self._item:
            return self._item['browseId']
        else:
            return super().artist_id
         
    @property
    def shuffle_id(self):
        if 'shuffleId' in self._item:
            return self._item['shuffleId']

    @property
    def radio_id(self):
        if 'radioId' in self._item:
            return self._item['radioId']


class LibraryArtist(Artist):
    '''
    Wrapper Class for an artist read from stored YTMusic library
    '''

    @property
    def is_library_item(self):
        return True

    @property
    def artist_name(self):
        return self._item['artist']

    @property
    def thumbnail(self):
        return self._item['artistArtRef']


class HomeArtist(Artist):
    '''
    Wrapper Class for an artist obtained from YTMusic.get_artist() function
    '''

    @property
    def artist_name(self):
        if 'title' in self._item:
            return self._item['title']
        else:
            return super().artist_name
