"""
Smart Metadata Caching System
Pre-loads and caches ALL YTMusic sources for maximum performance and coverage
"""

import time
import json
from typing import Dict, List, Optional
import xbmc


class SmartMetadataCache:
    """
    Smart caching system that pre-loads ALL YTMusic sources for optimal performance.
    Implements the user's brilliant optimization strategy!
    """
    
    def __init__(self, ytmusic_api):
        self.ytmusic_api = ytmusic_api
        self.cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.is_loading = False
        
    def get_cached_metadata(self, video_id: str) -> Optional[Dict]:
        """Get cached metadata for a videoId with source information"""
        if not self._is_cache_valid():
            self._refresh_cache_async()
            
        return self.cache.get(video_id)
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics for logging/debugging"""
        return {
            'total_entries': len(self.cache),
            'sources': self._get_source_breakdown(),
            'cache_age_minutes': (time.time() - self.cache_timestamp) / 60,
            'is_valid': self._is_cache_valid()
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.cache:
            return False
        age = time.time() - self.cache_timestamp
        return age < self.cache_ttl
    
    def _refresh_cache_async(self):
        """Refresh cache asynchronously to avoid blocking"""
        if self.is_loading:
            return  # Already loading
            
        # For now, do synchronous loading (can be made async later)
        self._load_all_metadata_sources()
    
    def _load_all_metadata_sources(self):
        """
        The GENIUS part: Pre-load ALL YTMusic sources for maximum coverage!
        This implements the user's brilliant optimization strategy.
        """
        try:
            self.is_loading = True
            start_time = time.time()
            
            xbmc.log("[SmartCache] Starting GENIUS multi-source metadata loading...", xbmc.LOGINFO)
            
            # Initialize cache and source tracking
            new_cache = {}
            source_stats = {'library': 0, 'liked': 0, 'history': 0, 'playlists': 0}
            
            # Source 1: Library Songs (Primary priority)
            xbmc.log("[SmartCache] Loading YTMusic 'All Songs' library...", xbmc.LOGDEBUG)
            try:
                library_songs = []
                for batch in self.ytmusic_api.get_library_songs_incremental():
                    library_songs.extend(batch)
                    if len(library_songs) > 5000:  # Safety limit
                        break
                        
                for song in library_songs:
                    video_id = song.get('videoId')
                    if video_id:
                        new_cache[video_id] = {'song': song, 'source': 'library'}
                        source_stats['library'] += 1
                        
                xbmc.log(f"[SmartCache] Loaded {len(library_songs)} songs from library", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"[SmartCache] Could not load library songs: {e}", xbmc.LOGWARNING)
            
            # Source 2: Liked Songs (Secondary priority)
            xbmc.log("[SmartCache] Loading YTMusic liked songs...", xbmc.LOGDEBUG)
            try:
                liked_result = self.ytmusic_api.get_liked_songs(limit=1000)
                liked_songs = liked_result.get('tracks', [])
                
                for song in liked_songs:
                    video_id = song.get('videoId')
                    if video_id and video_id not in new_cache:
                        new_cache[video_id] = {'song': song, 'source': 'liked'}
                        source_stats['liked'] += 1
                        
                xbmc.log(f"[SmartCache] Loaded {len(liked_songs)} liked songs", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"[SmartCache] Could not load liked songs: {e}", xbmc.LOGDEBUG)
            
            # Source 3: History (Tertiary priority)
            xbmc.log("[SmartCache] Loading YTMusic history...", xbmc.LOGDEBUG)
            try:
                history_songs = self.ytmusic_api.get_history()
                
                for song in history_songs:
                    video_id = song.get('videoId')
                    if video_id and video_id not in new_cache:
                        new_cache[video_id] = {'song': song, 'source': 'history'}
                        source_stats['history'] += 1
                        
                xbmc.log(f"[SmartCache] Loaded {len(history_songs)} history songs", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"[SmartCache] Could not load history: {e}", xbmc.LOGDEBUG)
            
            # Source 4: ALL User Playlists (BREAKTHROUGH source!)
            xbmc.log("[SmartCache] Loading ALL user playlists for metadata mining...", xbmc.LOGDEBUG)
            try:
                user_playlists = self.ytmusic_api.get_library_playlists(limit=50)
                
                for playlist in user_playlists:
                    playlist_id = playlist.get('playlistId')
                    if playlist_id:
                        try:
                            # Get up to 100 songs from each playlist
                            playlist_data = self.ytmusic_api.get_playlist(playlist_id, limit=100)
                            playlist_tracks = playlist_data.get('tracks', [])
                            
                            for song in playlist_tracks:
                                video_id = song.get('videoId')
                                if video_id and video_id not in new_cache:
                                    new_cache[video_id] = {'song': song, 'source': 'playlists'}
                                    source_stats['playlists'] += 1
                                    
                            xbmc.log(f"[SmartCache] Mined {len(playlist_tracks)} songs from playlist '{playlist.get('title', 'Unknown')}'", xbmc.LOGDEBUG)
                        except Exception as playlist_e:
                            xbmc.log(f"[SmartCache] Could not load playlist {playlist_id}: {playlist_e}", xbmc.LOGDEBUG)
                            continue
                
                xbmc.log(f"[SmartCache] Mined metadata from {len(user_playlists)} user playlists", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"[SmartCache] Could not load user playlists: {e}", xbmc.LOGDEBUG)
            
            # Update cache atomically
            self.cache = new_cache
            self.cache_timestamp = time.time()
            
            load_time = time.time() - start_time
            total_sources = sum(source_stats.values())
            
            xbmc.log(f"[SmartCache] GENIUS CACHE LOADED! {len(self.cache)} unique videoIds from {total_sources} total songs in {load_time:.2f}s", xbmc.LOGINFO)
            xbmc.log(f"[SmartCache] SOURCE BREAKDOWN: Library({source_stats['library']}) + Liked({source_stats['liked']}) + History({source_stats['history']}) + Playlists({source_stats['playlists']}) = {total_sources}", xbmc.LOGINFO)
            
        except Exception as e:
            xbmc.log(f"[SmartCache] Error during cache loading: {e}", xbmc.LOGERROR)
            import traceback
            xbmc.log(traceback.format_exc(), xbmc.LOGDEBUG)
        finally:
            self.is_loading = False
    
    def _get_source_breakdown(self) -> Dict:
        """Get breakdown of cache entries by source"""
        breakdown = {'library': 0, 'liked': 0, 'history': 0, 'playlists': 0}
        for entry in self.cache.values():
            source = entry.get('source', 'unknown')
            if source in breakdown:
                breakdown[source] += 1
        return breakdown
    
    def force_refresh(self):
        """Force cache refresh (for testing or manual refresh)"""
        self.cache_timestamp = 0  # Invalidate cache
        self._load_all_metadata_sources()
    
    def enrich_tracks(self, basic_tracks: List[Dict]) -> List[Dict]:
        """
        INTELLIGENT HYBRID ENRICHMENT:
        1. Use YTMusic cache metadata when available (rich data)
        2. Fill gaps with YouTube v3 metadata (title, duration, thumbnails)
        3. Best of both worlds - unlimited tracks + rich metadata!
        """
        if not self._is_cache_valid():
            self._refresh_cache_async()
        
        enriched_tracks = []
        matched_count = 0
        source_matches = {'library': 0, 'liked': 0, 'history': 0, 'playlists': 0}
        
        for basic_track in basic_tracks:
            video_id = basic_track.get('videoId')
            
            if video_id and video_id in self.cache:
                # PERFECT MATCH! Use cached rich metadata as base
                lookup_data = self.cache[video_id]
                rich_song = lookup_data['song']
                source = lookup_data['source']
                
                source_matches[source] += 1
                matched_count += 1
                
                # INTELLIGENT MERGE: Start with YTMusic rich data, fill gaps with YouTube v3
                enriched_track = {
                    'videoId': video_id,
                    # Rich metadata from YTMusic (prioritized)
                    'title': rich_song.get('title', basic_track.get('title', 'Unknown')),
                    'artists': rich_song.get('artists', []),
                    'album': rich_song.get('album'),
                    'duration': rich_song.get('duration', basic_track.get('duration', 'Unknown')),
                    'duration_seconds': rich_song.get('duration_seconds', basic_track.get('duration_seconds', 0)),
                    'isAvailable': rich_song.get('isAvailable', True),
                    'isExplicit': rich_song.get('isExplicit', False),
                    'likeStatus': rich_song.get('likeStatus'),
                    'feedbackTokens': rich_song.get('feedbackTokens'),
                    
                    # Intelligent thumbnail merging (best quality from either source)
                    'thumbnails': self._merge_thumbnails(rich_song.get('thumbnails', []), basic_track.get('thumbnails', [])),
                    
                    # YouTube v3 specific data
                    'setVideoId': basic_track.get('setVideoId', None),
                    'playlistVideoId': basic_track.get('playlistVideoId'),
                    'position': basic_track.get('position'),
                    
                    # Fallbacks for missing data
                    'publishedAt': basic_track.get('publishedAt'),
                    'channelTitle': basic_track.get('channelTitle', self._extract_artist_name(rich_song.get('artists', []))),
                }
                
                xbmc.log(f"[SmartCache] HYBRID MATCH ({source}): {rich_song.get('title')} - Rich YTMusic + YouTube v3 data", xbmc.LOGDEBUG)
            else:
                # NOT IN CACHE: Use YouTube v3 data but enhance what we can
                enriched_track = basic_track.copy()
                
                # Try to extract artist from channelTitle if no artists array
                if not enriched_track.get('artists') and enriched_track.get('channelTitle'):
                    enriched_track['artists'] = [{'name': enriched_track.get('channelTitle')}]
                
                # Ensure we have required fields
                enriched_track.update({
                    'isAvailable': True,  # Assume available if in YouTube v3
                    'isExplicit': False,
                    'likeStatus': None,
                    'feedbackTokens': None,
                })
                
                xbmc.log(f"[SmartCache] YOUTUBE v3 ONLY: {basic_track.get('title', 'Unknown')} - Using raw YouTube data", xbmc.LOGDEBUG)
            
            enriched_tracks.append(enriched_track)
        
        success_rate = (matched_count / len(basic_tracks)) * 100 if basic_tracks else 0
        xbmc.log(f"[SmartCache] HYBRID ENRICHMENT: {matched_count}/{len(basic_tracks)} with rich YTMusic data ({success_rate:.1f}% cache hit rate)", xbmc.LOGINFO)
        xbmc.log(f"[SmartCache] REMAINING {len(basic_tracks) - matched_count} tracks using YouTube v3 metadata", xbmc.LOGINFO)
        xbmc.log(f"[SmartCache] CACHE BREAKDOWN: Library({source_matches['library']}) + Liked({source_matches['liked']}) + History({source_matches['history']}) + Playlists({source_matches['playlists']}) = {matched_count} enriched", xbmc.LOGINFO)
        
        return enriched_tracks
    
    def _merge_thumbnails(self, ytmusic_thumbs: List[Dict], youtube_thumbs: List[Dict]) -> List[Dict]:
        """Intelligently merge thumbnails from both sources, preferring higher quality"""
        if not ytmusic_thumbs and not youtube_thumbs:
            return []
        
        # Use YTMusic thumbnails if available (usually better quality)
        if ytmusic_thumbs:
            return ytmusic_thumbs
        
        # Fallback to YouTube v3 thumbnails
        return youtube_thumbs
    
    def _extract_artist_name(self, artists: List[Dict]) -> str:
        """Extract first artist name from artists array"""
        if artists and len(artists) > 0:
            return artists[0].get('name', 'Unknown Artist')
        return 'Unknown Artist'
