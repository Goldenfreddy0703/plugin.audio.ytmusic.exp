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
        Fast track enrichment using pre-loaded cache.
        This is much faster than loading sources on-demand!
        """
        if not self._is_cache_valid():
            self._refresh_cache_async()
        
        enriched_tracks = []
        matched_count = 0
        source_matches = {'library': 0, 'liked': 0, 'history': 0, 'playlists': 0}
        
        for basic_track in basic_tracks:
            video_id = basic_track.get('videoId')
            
            if video_id and video_id in self.cache:
                # GENIUS MATCH! Use cached rich metadata
                lookup_data = self.cache[video_id]
                rich_song = lookup_data['song']
                source = lookup_data['source']
                
                source_matches[source] += 1
                matched_count += 1
                
                # Convert to playlist track format
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
                    'setVideoId': None  # Will be updated by client
                }
                
                xbmc.log(f"[SmartCache] FAST MATCH ({source}): {rich_song.get('title')} by {rich_song.get('artists', [{}])[0].get('name', 'Unknown')}", xbmc.LOGDEBUG)
            else:
                # Not in cache, use basic YouTube v3 data
                enriched_track = basic_track.copy()
                xbmc.log(f"[SmartCache] Not in cache: {basic_track.get('title', 'Unknown')}", xbmc.LOGDEBUG)
            
            enriched_tracks.append(enriched_track)
        
        success_rate = (matched_count / len(basic_tracks)) * 100 if basic_tracks else 0
        xbmc.log(f"[SmartCache] FAST ENRICHMENT: {matched_count}/{len(basic_tracks)} tracks enriched ({success_rate:.1f}% success rate)", xbmc.LOGINFO)
        xbmc.log(f"[SmartCache] MATCH BREAKDOWN: Library({source_matches['library']}) + Liked({source_matches['liked']}) + History({source_matches['history']}) + Playlists({source_matches['playlists']}) = {matched_count} enriched", xbmc.LOGINFO)
        
        return enriched_tracks
