"""
YouTube v3 API Playlist Loader
Replaces YouTube Music API playlist functionality with proven YouTube v3 API approach
This overcomes the 100-song limitation by using the same method as the YouTube addon.
"""

import requests
import time
from typing import Dict, List, Optional, Any
import xbmc


class YouTubeV3PlaylistLoader:
    """
    YouTube v3 API client for loading complete playlists without the 100-song limit.
    Uses the same approach as the anxdpanic/plugin.video.youtube addon.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session = requests.Session()
        
    def get_playlist_items(self, playlist_id: str, all_pages: bool = True, ytmusic_api=None) -> Dict[str, Any]:
        """
        Get playlist items using YouTube v3 API with all_pages functionality.
        This is the same approach used by the YouTube addon that successfully
        overcomes pagination limits.
        
        Args:
            playlist_id: The playlist ID to load
            all_pages: Whether to load all pages (True) or just first page (False)
            ytmusic_api: Optional YouTube Music API instance to get playlist metadata
            
        Returns:
            Dictionary containing all playlist items with proper metadata
        """
        try:
            xbmc.log(f"[YTMusic YouTube v3] Loading playlist {playlist_id} with all_pages={all_pages}", xbmc.LOGDEBUG)
            
            # First, try to get playlist metadata from YouTube Music API
            playlist_metadata = None
            if ytmusic_api:
                try:
                    # Get just the metadata (without tracks) from YouTube Music API
                    metadata_result = ytmusic_api.get_playlist(playlist_id, limit=1)  # Just get 1 track for metadata
                    if metadata_result:
                        playlist_metadata = {
                            'title': metadata_result.get('title', f'Playlist {playlist_id}'),
                            'description': metadata_result.get('description', ''),
                            'thumbnails': metadata_result.get('thumbnails', []),
                            'author': metadata_result.get('author', ''),
                            'privacy': metadata_result.get('privacy', 'PUBLIC'),
                            'owned': metadata_result.get('owned', False),
                            'year': metadata_result.get('year', ''),
                            'duration': metadata_result.get('duration', 'Unknown'),
                            'duration_seconds': metadata_result.get('duration_seconds', 0)
                        }
                        xbmc.log(f"[YTMusic YouTube v3] Got playlist metadata from YouTube Music API: {playlist_metadata['title']}", xbmc.LOGINFO)
                except Exception as meta_e:
                    xbmc.log(f"[YTMusic YouTube v3] Could not get metadata from YouTube Music API: {meta_e}", xbmc.LOGDEBUG)
            
            # Now get unlimited tracks from YouTube v3 API
            items = []
            page_token = ''
            page_count = 0
            
            while True:
                # Get items for this page
                page_items, next_page_token, error = self._get_items(playlist_id, page_token)
                
                if error:
                    xbmc.log(f"[YTMusic YouTube v3] Error on page {page_count + 1}: {error}", xbmc.LOGERROR)
                    break
                
                if page_items:
                    items.extend(page_items)
                    page_count += 1
                    xbmc.log(f"[YTMusic YouTube v3] Page {page_count}: Added {len(page_items)} items, total: {len(items)}", xbmc.LOGDEBUG)
                
                # Check if we should continue
                if not next_page_token or not all_pages:
                    break
                    
                page_token = next_page_token
                
                # Rate limiting to avoid hitting API limits
                if page_count > 1:
                    time.sleep(0.5)
                
                # Safety limit to prevent infinite loops
                if page_count > 100:
                    xbmc.log(f"[YTMusic YouTube v3] Reached maximum page limit ({page_count})", xbmc.LOGWARNING)
                    break
            
            xbmc.log(f"[YTMusic YouTube v3] Successfully loaded {len(items)} items from {page_count} pages", xbmc.LOGINFO)
            
            # Convert to YouTube Music API compatible format with proper metadata
            result = self._convert_to_ytmusic_format(items, playlist_id, playlist_metadata)
            
            # ENHANCEMENT: Get duration data for all tracks in batch
            if result.get('tracks'):
                self._add_duration_data(result['tracks'])
            
            return result
            
        except Exception as e:
            xbmc.log(f"[YTMusic YouTube v3] Error loading playlist {playlist_id}: {str(e)}", xbmc.LOGERROR)
            import traceback
            xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
            return {"tracks": [], "error": str(e)}
    
    def _get_items(self, playlist_id: str, page_token: str = '') -> tuple:
        """
        Get a single page of playlist items from YouTube v3 API.
        
        Returns:
            Tuple of (items, next_page_token, error)
        """
        try:
            url = f"{self.base_url}/playlistItems"
            
            params = {
                'part': 'snippet,contentDetails',
                'playlistId': playlist_id,
                'maxResults': 50,  # YouTube v3 API maximum
            }
            
            if self.api_key:
                params['key'] = self.api_key
            
            if page_token:
                params['pageToken'] = page_token
            
            response = self.session.get(url, params=params, timeout=30)
            
            # Handle 403 errors - YouTube v3 API requires authentication for most playlists
            if response.status_code == 403:
                if self.api_key:
                    error_msg = "API key invalid or insufficient permissions"
                else:
                    error_msg = "YouTube v3 API requires an API key for playlist access. Please configure one in settings."
                return [], None, error_msg
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return [], None, error_msg
            
            data = response.json()
            
            items = data.get('items', [])
            next_page_token = data.get('nextPageToken')
            
            return items, next_page_token, None
            
        except Exception as e:
            return [], None, str(e)
    
    def _add_duration_data(self, tracks: List[Dict[str, Any]]) -> None:
        """
        Add duration data to tracks by making batch requests to YouTube v3 API.
        This gets accurate duration information that may be missing from YouTube Music API.
        """
        try:
            if not self.api_key:
                xbmc.log("[YTMusic YouTube v3] No API key configured, skipping duration enhancement", xbmc.LOGINFO)
                return
            
            # Extract video IDs that need duration data
            video_ids = []
            for track in tracks:
                video_id = track.get('videoId')
                track_title = track.get('title', 'Unknown')
                existing_duration = track.get('duration_seconds', 0)
                
                xbmc.log(f"[YTMusic YouTube v3] Track '{track_title}': videoId={video_id}, existing_duration={existing_duration}", xbmc.LOGDEBUG)
                
                if video_id and not track.get('duration_seconds'):
                    video_ids.append(video_id)
            
            if not video_ids:
                xbmc.log("[YTMusic YouTube v3] No videos need duration enhancement", xbmc.LOGDEBUG)
                return
            
            xbmc.log(f"[YTMusic YouTube v3] Enhancing duration for {len(video_ids)} videos", xbmc.LOGINFO)
            
            # Make batch requests to YouTube v3 API (up to 50 video IDs per request)
            batch_size = 50
            video_durations = {}
            
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                url = f"{self.base_url}/videos"
                params = {
                    'part': 'contentDetails',
                    'id': ','.join(batch_ids),
                    'key': self.api_key
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get('items', []):
                        video_id = item.get('id')
                        duration_iso = item.get('contentDetails', {}).get('duration')
                        
                        if video_id and duration_iso:
                            # Convert ISO 8601 duration to seconds and human-readable format
                            duration_seconds = self._parse_iso8601_duration(duration_iso)
                            duration_formatted = self._format_duration(duration_seconds)
                            
                            video_durations[video_id] = {
                                'duration': duration_formatted,
                                'duration_seconds': duration_seconds
                            }
                            xbmc.log(f"[YTMusic YouTube v3] Got duration for {video_id}: {duration_formatted} ({duration_seconds}s)", xbmc.LOGDEBUG)
                    
                    # Apply duration data to tracks
                    for track in tracks:
                        video_id = track.get('videoId')
                        if video_id in video_durations:
                            duration_data = video_durations[video_id]
                            track.update(duration_data)
                            xbmc.log(f"[YTMusic YouTube v3] Added duration to {track.get('title', 'Unknown')}: {duration_data['duration']}", xbmc.LOGDEBUG)
                        else:
                            # Set default values for tracks without duration
                            track.update({
                                'duration': 'Unknown',
                                'duration_seconds': 0
                            })
                            xbmc.log(f"[YTMusic YouTube v3] No duration found for {track.get('title', 'Unknown')} (videoId: {video_id})", xbmc.LOGDEBUG)
                else:
                    xbmc.log(f"[YTMusic YouTube v3] Duration API request failed: HTTP {response.status_code}", xbmc.LOGWARNING)
                    
        except Exception as e:
            xbmc.log(f"[YTMusic YouTube v3] Error adding duration data: {str(e)}", xbmc.LOGWARNING)
    
    def _parse_iso8601_duration(self, duration_iso: str) -> int:
        """
        Parse ISO 8601 duration format (PT4M13S) to seconds
        Based on YouTube addon implementation
        """
        import re
        
        # Remove PT prefix
        duration_str = duration_iso.replace('PT', '')
        
        # Extract hours, minutes, seconds using regex
        hours = 0
        minutes = 0
        seconds = 0
        
        # Match patterns like 1H, 30M, 45S
        h_match = re.search(r'(\d+)H', duration_str)
        m_match = re.search(r'(\d+)M', duration_str)
        s_match = re.search(r'(\d+)S', duration_str)
        
        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))
        if s_match:
            seconds = int(s_match.group(1))
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _format_duration(self, total_seconds: int) -> str:
        """
        Format duration in seconds to MM:SS or HH:MM:SS format
        Based on YouTube addon implementation
        """
        if total_seconds <= 0:
            return 'Unknown'
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _convert_to_ytmusic_format(self, items: List[Dict], playlist_id: str, playlist_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Convert YouTube v3 API response to YouTube Music API compatible format.
        """
        tracks = []
        
        for item in items:
            try:
                snippet = item.get('snippet', {})
                content_details = item.get('contentDetails', {})
                
                video_id = snippet.get('resourceId', {}).get('videoId')
                if not video_id:
                    continue
                
                # Parse title and artist from YouTube video title
                title = snippet.get('title', 'Unknown Title')
                channel_title = snippet.get('videoOwnerChannelTitle') or snippet.get('channelTitle', 'Unknown Artist')
                
                # Try to parse artist from title (common formats: "Artist - Title" or "Title by Artist")
                artists = [{"name": channel_title}]
                if ' - ' in title:
                    parts = title.split(' - ', 1)
                    if len(parts) == 2:
                        artists = [{"name": parts[0].strip()}]
                        title = parts[1].strip()
                elif ' by ' in title.lower():
                    parts = title.lower().split(' by ', 1)
                    if len(parts) == 2:
                        title = title[:len(parts[0])].strip()
                        artists = [{"name": parts[1].strip()}]
                
                # Get thumbnails with better error handling
                thumbnails = []
                thumbnail_data = snippet.get('thumbnails', {})
                for quality in ['maxres', 'standard', 'high', 'medium', 'default']:
                    if quality in thumbnail_data:
                        thumb = thumbnail_data[quality]
                        if thumb and thumb.get('url'):  # Ensure thumbnail has URL
                            thumbnails.append({
                                'url': thumb.get('url'),
                                'width': thumb.get('width', 0),
                                'height': thumb.get('height', 0)
                            })
                
                # Ensure we always have at least an empty thumbnail list
                if not thumbnails:
                    thumbnails = []
                
                track = {
                    "videoId": video_id,
                    "title": title,
                    "artists": artists,
                    "album": None,  # YouTube v3 API doesn't provide album info
                    "duration": "Unknown",  # Will be filled by _add_duration_data()
                    "duration_seconds": 0,  # Will be filled by _add_duration_data()
                    "thumbnails": thumbnails,
                    "isAvailable": True,
                    "isExplicit": False,
                    # YouTube Music specific fields with reasonable defaults
                    "likeStatus": "INDIFFERENT",
                    "feedbackTokens": None,
                    "videoType": "MUSIC_VIDEO_TYPE_OMV"
                }
                
                tracks.append(track)
                
            except Exception as e:
                xbmc.log(f"[YTMusic YouTube v3] Error parsing item: {str(e)}", xbmc.LOGDEBUG)
                continue
        
        # Create playlist metadata - use YouTube Music API data if available, otherwise defaults
        if playlist_metadata:
            result = {
                "id": playlist_id,
                "title": playlist_metadata.get('title', f'Playlist {playlist_id}'),
                "description": playlist_metadata.get('description', ''),
                "privacy": playlist_metadata.get('privacy', 'PUBLIC'),
                "owned": playlist_metadata.get('owned', False),
                "author": playlist_metadata.get('author', ''),
                "year": playlist_metadata.get('year', ''),
                "duration": playlist_metadata.get('duration', 'Unknown'),
                "duration_seconds": playlist_metadata.get('duration_seconds', 0),
                "trackCount": len(tracks),
                "tracks": tracks,
                "suggestions": [],
                "related": [],
                "thumbnails": playlist_metadata.get('thumbnails', [])  # Use YouTube Music API thumbnails
            }
        else:
            # Fallback to basic metadata
            result = {
                "id": playlist_id,
                "title": f"Playlist {playlist_id}",
                "description": "",
                "privacy": "PUBLIC",
                "owned": False,
                "author": "",
                "year": "",
                "duration": "Unknown",
                "duration_seconds": 0,
                "trackCount": len(tracks),
                "tracks": tracks,
                "suggestions": [],
                "related": [],
                "thumbnails": []  # Empty thumbnails list to prevent KeyError
            }
        
        return result


def get_playlist_with_youtube_v3(playlist_id: str, api_key: Optional[str] = None, ytmusic_api=None) -> Dict[str, Any]:
    """
    Convenience function to get a complete playlist using YouTube v3 API.
    This function replicates the YouTube addon's successful approach.
    
    Args:
        playlist_id: The playlist ID to load
        api_key: YouTube Data API v3 key
        ytmusic_api: YouTube Music API instance for getting playlist metadata
    """
    loader = YouTubeV3PlaylistLoader(api_key)
    return loader.get_playlist_items(playlist_id, all_pages=True, ytmusic_api=ytmusic_api)
