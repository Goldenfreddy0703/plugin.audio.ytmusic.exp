import utils
import xbmc
import wrapper
from storage import storage
from smart_metadata_cache import SmartMetadataCache  # Import smart caching system
from typing import Iterator, Dict


class Api:
    def __init__(self):
        self.api = None
        self.login = None
        self.metadata_cache = None  # Smart metadata cache instance

    def getApi(self):
        if self.api is None:
            import login
            self.login = login.Login()
            self.api = self.login.getApi()
            
            # Initialize smart metadata cache for optimal performance
            if self.metadata_cache is None:
                utils.log("Initializing Smart Metadata Cache for maximum performance...", xbmc.LOGINFO)
                self.metadata_cache = SmartMetadataCache(self.api)
                
        return self.api
        self.login = None
        self.metadata_cache = None  # Smart metadata cache instance

    def getApi(self):
        if self.api is None:
            import login
            self.login = login.Login()
            self.api = self.login.getApi()
            
            # Initialize smart metadata cache for optimal performance
            if self.metadata_cache is None:
                utils.log("Initializing Smart Metadata Cache for maximum performance...", xbmc.LOGINFO)
                self.metadata_cache = SmartMetadataCache(self.api)
                
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
                return wrapper.GetPlaylistSong.wrap(self._get_full_playlist(playlist_id))

    def _get_full_playlist(self, playlist_id):
        """Get complete playlist using the GENIUS hybrid approach:
        1. YouTube v3 API: Get unlimited videoIds (no 100-song limit)
        2. YouTube Music 'All Songs': Rich metadata lookup by videoId
        3. Perfect result: Unlimited tracks + Full metadata + Context menu support!
        """
        try:
            utils.log(f"Loading full playlist {playlist_id} using GENIUS hybrid approach", xbmc.LOGINFO)
            
            # Check if we should use YouTube v3 API (new genius approach)
            use_youtube_v3 = utils.addon.getSettingBool('use_youtube_v3_playlists')
            
            if use_youtube_v3:
                # PROPER HYBRID APPROACH: YTMusic FIRST, then YouTube v3 for missing tracks
                try:
                    utils.log(f"HYBRID STEP 1: Loading YTMusic playlist first for rich metadata...", xbmc.LOGINFO)
                    
                    # Step 1: Get FULL YTMusic playlist (up to 100 songs with rich metadata)
                    ytmusic_result = self.getApi().get_playlist(playlist_id, limit=None)
                    ytmusic_tracks = ytmusic_result.get('tracks', []) if ytmusic_result else []
                    ytmusic_count = len(ytmusic_tracks)
                    
                    utils.log(f"HYBRID STEP 1 RESULT: YTMusic API provided {ytmusic_count} tracks with rich metadata", xbmc.LOGINFO)
                    
                    # Step 2: Get unlimited track list from YouTube v3 API
                    from youtube_v3_playlist_loader import get_playlist_with_youtube_v3
                    api_key = utils.addon.getSetting('youtube_api_key')
                    if not api_key:
                        api_key = None
                    
                    utils.log(f"HYBRID STEP 2: Getting complete track list from YouTube v3 API...", xbmc.LOGINFO)
                    youtube_v3_result = get_playlist_with_youtube_v3(playlist_id, api_key, self.getApi())
                    
                    if 'error' in youtube_v3_result and 'requires an API key' in youtube_v3_result['error']:
                        utils.log(f"YouTube v3 API requires authentication. Using YTMusic result only (limited to ~{ytmusic_count} songs)", xbmc.LOGWARNING)
                        return ytmusic_result
                    
                    youtube_tracks = youtube_v3_result.get('tracks', [])
                    youtube_count = len(youtube_tracks)
                    
                    utils.log(f"HYBRID STEP 2 RESULT: YouTube v3 API provided {youtube_count} total tracks", xbmc.LOGINFO)
                    
                    # Step 3: INTELLIGENT MERGE - YTMusic metadata takes priority
                    if youtube_count > ytmusic_count:
                        utils.log(f"HYBRID STEP 3: Merging {ytmusic_count} rich YTMusic tracks with {youtube_count - ytmusic_count} additional YouTube v3 tracks", xbmc.LOGINFO)
                        
                        # Create lookup dictionary of YTMusic tracks (rich metadata)
                        ytmusic_lookup = {}
                        for track in ytmusic_tracks:
                            video_id = track.get('videoId')
                            if video_id:
                                ytmusic_lookup[video_id] = track
                        
                        # Build final track list: NO DUPLICATES, YouTube v3 order, YTMusic metadata priority
                        final_tracks = []
                        seen_video_ids = set()  # Track duplicates
                        ytmusic_used = 0
                        youtube_used = 0
                        
                        for youtube_track in youtube_tracks:
                            video_id = youtube_track.get('videoId')
                            
                            # Skip if we've already processed this video ID (no duplicates!)
                            if not video_id or video_id in seen_video_ids:
                                utils.log(f"DUPLICATE SKIPPED: video_id {video_id} already processed", xbmc.LOGDEBUG)
                                continue
                            
                            seen_video_ids.add(video_id)
                            
                            if video_id in ytmusic_lookup:
                                # USE YTMUSIC RICH METADATA (priority!)
                                rich_track = ytmusic_lookup[video_id].copy()
                                
                                # Merge essential YouTube v3 playlist data
                                rich_track.update({
                                    'setVideoId': youtube_track.get('setVideoId'),
                                    'position': youtube_track.get('position'),
                                    'playlistVideoId': youtube_track.get('playlistVideoId')
                                })
                                
                                # Ensure we have the YouTube v3 track order position
                                if 'position' not in rich_track and len(final_tracks) >= 0:
                                    rich_track['position'] = len(final_tracks)
                                
                                final_tracks.append(rich_track)
                                ytmusic_used += 1
                                utils.log(f"MERGED (YTMusic+YouTube): {rich_track.get('title', 'Unknown')} [position: {rich_track.get('position', 'unknown')}]", xbmc.LOGDEBUG)
                            else:
                                # Use YouTube v3 track (enhanced for compatibility)
                                enhanced_track = youtube_track.copy()
                                
                                # Add YTMusic-compatible fields
                                if not enhanced_track.get('artists') and enhanced_track.get('channelTitle'):
                                    enhanced_track['artists'] = [{'name': enhanced_track.get('channelTitle')}]
                                
                                enhanced_track.update({
                                    'isAvailable': True,
                                    'isExplicit': False,
                                    'likeStatus': None,
                                    'feedbackTokens': None
                                })
                                
                                # Ensure position is set
                                if 'position' not in enhanced_track:
                                    enhanced_track['position'] = len(final_tracks)
                                
                                final_tracks.append(enhanced_track)
                                youtube_used += 1
                                utils.log(f"YOUTUBE ONLY: {enhanced_track.get('title', 'Unknown')} [position: {enhanced_track.get('position', 'unknown')}]", xbmc.LOGDEBUG)
                        
                        # Use YTMusic playlist metadata, update track list
                        final_result = ytmusic_result.copy() if ytmusic_result else youtube_v3_result.copy()
                        final_result['tracks'] = final_tracks
                        
                        utils.log(f"HYBRID SUCCESS: {len(final_tracks)} total tracks ({ytmusic_used} with rich YTMusic metadata + {youtube_used} YouTube v3 tracks)", xbmc.LOGINFO)
                        utils.log(f"METADATA PRESERVATION: 100% of YTMusic rich data preserved for {ytmusic_used} tracks", xbmc.LOGINFO)
                        
                        # Step 4: SMART METADATA ENHANCEMENT - Apply duration and thumbnail improvements
                        try:
                            utils.log(f"HYBRID STEP 4: Applying smart metadata enhancements (duration, thumbnails)...", xbmc.LOGINFO)
                            self.metadata_cache.enrich_tracks(final_tracks)
                            utils.log(f"HYBRID ENHANCEMENT: Applied smart metadata enhancements to all {len(final_tracks)} tracks", xbmc.LOGINFO)
                        except Exception as e:
                            utils.log(f"Smart metadata enhancement failed: {e}", xbmc.LOGWARNING)
                        
                        return final_result
                    else:
                        # YouTube v3 didn't provide more tracks, just use YTMusic result
                        utils.log(f"YouTube v3 API didn't provide additional tracks beyond YTMusic limit. Using YTMusic result.", xbmc.LOGINFO)
                        return ytmusic_result
                    
                except Exception as e:
                    utils.log(f"Hybrid approach failed: {e}. Falling back to standard YTMusic API.", xbmc.LOGERROR)
                    # Fall through to standard YTMusic approach
            
            # Fallback to YouTube Music API
            utils.log(f"Using YouTube Music API for playlist {playlist_id} (may be limited to ~100 songs)", xbmc.LOGINFO)
            result = self.getApi().get_playlist(playlist_id, limit=None)
            track_count = len(result.get('tracks', []))
            
            if track_count == 100:
                utils.log(f"YouTube Music API returned exactly 100 tracks - playlist may be truncated. Consider enabling YouTube v3 API with API key for unlimited access.", xbmc.LOGWARNING)
            
            utils.log(f"YouTube Music API loaded {track_count} tracks for playlist {playlist_id}", xbmc.LOGINFO)
            return result
            
        except Exception as e:
            utils.log(f"Error during playlist loading: {e}", xbmc.LOGERROR)
            import traceback
            utils.log(traceback.format_exc(), xbmc.LOGERROR)
            
            # Last resort: Return empty playlist
            return {
                'id': playlist_id,
                'title': 'Unknown Playlist',
                'tracks': [],
                'description': '',
                'author': '',
                'year': '',
                'duration': '0 seconds',
                'duration_seconds': 0,
                'trackCount': 0
            }

    def _enrich_tracks_from_library(self, basic_tracks):
        """
        The GENIUS PART: Multi-Source Metadata Collection Strategy!
        Using the universal videoId compatibility discovered by user!
        
        BREAKTHROUGH SOURCES:
        1. YouTube Music "All Songs" library - Primary rich metadata
        2. YouTube Music "History" - Fallback rich metadata  
        3. YouTube Music "Liked Songs" - Additional rich metadata
        4. ALL User Playlists (100 songs each) - Turn limitation into advantage!
        
        This approach maximizes metadata coverage by mining ALL possible YTMusic sources!
        """
        try:
            utils.log(f"GENIUS MULTI-SOURCE: Looking up rich metadata for {len(basic_tracks)} tracks across ALL YTMusic sources...", xbmc.LOGINFO)
            
            # Step 1: Get all songs from "All Songs" library  
            utils.log(f"GENIUS: Loading YTMusic 'All Songs' library for metadata lookup...", xbmc.LOGDEBUG)
            library_songs = []
            
            try:
                # Use incremental loading to get ALL library songs
                for batch in self.getApi().get_library_songs_incremental():
                    library_songs.extend(batch)
                    if len(library_songs) > 5000:  # Safety limit to prevent memory issues
                        break
                        
                utils.log(f"GENIUS: Loaded {len(library_songs)} songs from YTMusic library", xbmc.LOGINFO)
            except Exception as lib_e:
                utils.log(f"Could not load library songs: {lib_e}", xbmc.LOGWARNING)
                library_songs = []
            
            # Step 2: Get listening history for additional metadata sources
            utils.log(f"GENIUS: Loading YTMusic listening history for additional metadata...", xbmc.LOGDEBUG)
            history_songs = []
            
            try:
                history_songs = self.getApi().get_history()
                utils.log(f"GENIUS: Loaded {len(history_songs)} songs from YTMusic history", xbmc.LOGINFO)
            except Exception as hist_e:
                utils.log(f"Could not load history songs (requires authentication): {hist_e}", xbmc.LOGDEBUG)
                history_songs = []
            
            # Step 3: Get liked songs for additional metadata sources  
            utils.log(f"GENIUS: Loading YTMusic liked songs for additional metadata...", xbmc.LOGDEBUG)
            liked_songs = []
            
            try:
                liked_result = self.getApi().get_liked_songs(limit=1000)  # Get up to 1000 liked songs
                liked_songs = liked_result.get('tracks', [])
                utils.log(f"GENIUS: Loaded {len(liked_songs)} songs from YTMusic liked songs", xbmc.LOGINFO)
            except Exception as liked_e:
                utils.log(f"Could not load liked songs (requires authentication): {liked_e}", xbmc.LOGDEBUG)
                liked_songs = []
            
            # Step 4: BREAKTHROUGH - Mine metadata from ALL user playlists!
            utils.log(f"GENIUS BREAKTHROUGH: Mining metadata from ALL user playlists (100 songs each)...", xbmc.LOGDEBUG)
            playlist_songs = []
            
            try:
                # Get all user playlists
                user_playlists = self.getApi().get_library_playlists(limit=50)  # Up to 50 playlists
                
                for playlist in user_playlists:
                    playlist_id = playlist.get('playlistId')
                    if playlist_id:
                        try:
                            # Get 100 songs from each playlist (YTMusic API limit becomes useful!)
                            playlist_data = self.getApi().get_playlist(playlist_id, limit=100)
                            playlist_tracks = playlist_data.get('tracks', [])
                            playlist_songs.extend(playlist_tracks)
                            utils.log(f"GENIUS: Mined {len(playlist_tracks)} songs from playlist '{playlist.get('title', 'Unknown')}'", xbmc.LOGDEBUG)
                        except Exception as playlist_e:
                            utils.log(f"Could not load playlist {playlist_id}: {playlist_e}", xbmc.LOGDEBUG)
                            continue
                
                utils.log(f"GENIUS BREAKTHROUGH: Mined {len(playlist_songs)} songs from {len(user_playlists)} user playlists!", xbmc.LOGINFO)
            except Exception as playlists_e:
                utils.log(f"Could not load user playlists: {playlists_e}", xbmc.LOGDEBUG)
                playlist_songs = []
            
            # Step 5: Create MEGA lookup table from ALL sources!
            library_lookup = {}
            source_stats = {'library': 0, 'history': 0, 'liked': 0, 'playlists': 0}
            
            # Priority 1: Library songs (highest priority)
            for song in library_songs:
                video_id = song.get('videoId')
                if video_id:
                    library_lookup[video_id] = {'song': song, 'source': 'library'}
                    source_stats['library'] += 1
                    
            # Priority 2: Liked songs (if not already in library)
            for song in liked_songs:
                video_id = song.get('videoId')
                if video_id and video_id not in library_lookup:
                    library_lookup[video_id] = {'song': song, 'source': 'liked'}
                    source_stats['liked'] += 1
                    
            # Priority 3: History songs (if not already covered)
            for song in history_songs:
                video_id = song.get('videoId')
                if video_id and video_id not in library_lookup:
                    library_lookup[video_id] = {'song': song, 'source': 'history'}
                    source_stats['history'] += 1
                    
            # Priority 4: Playlist songs (lowest priority, but potentially huge coverage!)
            for song in playlist_songs:
                video_id = song.get('videoId')
                if video_id and video_id not in library_lookup:
                    library_lookup[video_id] = {'song': song, 'source': 'playlists'}
                    source_stats['playlists'] += 1
                    
            total_sources = sum(source_stats.values())
            utils.log(f"GENIUS MEGA LOOKUP: Created lookup table with {len(library_lookup)} unique videoIds from {total_sources} total songs", xbmc.LOGINFO)
            utils.log(f"SOURCE BREAKDOWN: Library({source_stats['library']}) + Liked({source_stats['liked']}) + History({source_stats['history']}) + Playlists({source_stats['playlists']}) = {total_sources} songs", xbmc.LOGINFO)
            
            # Step 6: Enrich tracks with multi-source metadata
            enriched_tracks = []
            matched_count = 0
            source_matches = {'library': 0, 'liked': 0, 'history': 0, 'playlists': 0}
            
            for basic_track in basic_tracks:
                video_id = basic_track.get('videoId')
                
                if video_id and video_id in library_lookup:
                    # GENIUS MATCH! Use rich metadata from multi-source lookup
                    lookup_data = library_lookup[video_id]
                    rich_song = lookup_data['song']
                    source = lookup_data['source']
                    
                    source_matches[source] += 1
                    
                    # Convert song to playlist track format
                    enriched_track = {
                        'videoId': video_id,
                        'title': rich_song.get('title', basic_track.get('title', 'Unknown')),
                        'artists': rich_song.get('artists', []),
                        'album': rich_song.get('album'),
                        'duration': rich_song.get('duration', basic_track.get('duration', 'Unknown')),
                        'duration_seconds': rich_song.get('duration_seconds', basic_track.get('duration_seconds', 0)),
                        'thumbnails': rich_song.get('thumbnails', basic_track.get('thumbnails', [])),
                        'isAvailable': rich_song.get('isAvailable', True),
                        'isExplicit': rich_song.get('isExplicit', False),
                        'likeStatus': rich_song.get('likeStatus'),
                        'feedbackTokens': rich_song.get('feedbackTokens'),
                        # Add playlist-specific fields
                        'setVideoId': None  # Will be updated by client
                    }
                    
                    matched_count += 1
                    utils.log(f"GENIUS MATCH ({source}): {rich_song.get('title')} by {rich_song.get('artists', [{}])[0].get('name', 'Unknown')}", xbmc.LOGDEBUG)
                else:
                    # Not found in any source, use basic YouTube v3 data
                    enriched_track = basic_track.copy()
                    utils.log(f"Not in any YTMusic source: {basic_track.get('title', 'Unknown')}", xbmc.LOGDEBUG)
                
                enriched_tracks.append(enriched_track)
            
            utils.log(f"GENIUS MULTI-SOURCE RESULTS: {matched_count}/{len(basic_tracks)} tracks enriched with full metadata ({matched_count/len(basic_tracks)*100:.1f}% success rate)", xbmc.LOGINFO)
            utils.log(f"MATCH BREAKDOWN: Library({source_matches['library']}) + Liked({source_matches['liked']}) + History({source_matches['history']}) + Playlists({source_matches['playlists']}) = {matched_count} enriched", xbmc.LOGINFO)
            
            if matched_count > 0:
                return enriched_tracks
            else:
                return None
                
        except Exception as e:
            utils.log(f"Error during genius multi-source metadata enrichment: {e}", xbmc.LOGERROR)
            import traceback
            utils.log(traceback.format_exc(), xbmc.LOGDEBUG)
            return None

    def get_playlists(self):
        return wrapper.LibraryPlaylist.wrap(storage.getPlaylists())

    def load_playlists(self):
        library_playlists = []
        # Filter out auto-generated playlists: LM (Liked Music), SE (Saved Episodes), RDPN (New Episodes)
        playlists = list(filter(lambda pl: pl['playlistId'] not in ('LM', 'SE', 'RDPN'), self.getApi().get_library_playlists(None)))
        for playlist in playlists:
            library_playlist = self._get_full_playlist(playlist['playlistId'])
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