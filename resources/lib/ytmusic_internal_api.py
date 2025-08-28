"""
YouTube Music Internal API Implementation
Similar to th-ch/youtube-music's approach using internal YouTube APIs
to overcome the 100-song playlist limitation.

This module provides an alternative to ytmusicapi for playlist loading
by using the same internal APIs that th-ch/youtube-music uses successfully.
"""

import requests
import time
from typing import Dict, Optional, Any
import xbmc


class YouTubeMusicInternalAPI:
    """
    Internal YouTube Music API client using the same approach as th-ch/youtube-music
    to overcome playlist limitations by using internal APIs instead of the official
    YouTube Music API.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://music.youtube.com"
        self.api_url = "https://music.youtube.com/youtubei/v1"
        
        # Headers based on th-ch/youtube-music implementation
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://music.youtube.com',
            'Referer': 'https://music.youtube.com/',
        }
        
        self.context = {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": "1.0",
                "hl": "en",
                "gl": "US"
            }
        }
    
    def get_full_playlist(self, playlist_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a complete playlist using internal YouTube APIs with continuation support.
        This method overcomes the 100-song limitation by using the same approach
        as th-ch/youtube-music.
        
        Args:
            playlist_id: The playlist ID to load
            limit: Maximum number of tracks to load (None for all)
            
        Returns:
            Dictionary containing playlist information and all tracks
        """
        try:
            xbmc.log(f"[YTMusic Internal] Starting full playlist load for: {playlist_id}", xbmc.LOGDEBUG)
            
            # Initial request
            initial_data = self._get_playlist_initial(playlist_id)
            if not initial_data:
                return {"tracks": [], "error": "Failed to load initial playlist data"}
            
            tracks = initial_data.get("tracks", [])
            total_tracks = len(tracks)
            
            # Check for continuation token
            continuation_token = initial_data.get("continuation")
            
            attempt = 1
            while continuation_token and (not limit or total_tracks < limit):
                xbmc.log(f"[YTMusic Internal] Continuation attempt {attempt}, current tracks: {total_tracks}", xbmc.LOGDEBUG)
                
                # Get continuation data
                continuation_data = self._get_playlist_continuation(continuation_token)
                if not continuation_data:
                    xbmc.log(f"[YTMusic Internal] Failed to get continuation data, stopping", xbmc.LOGWARNING)
                    break
                
                new_tracks = continuation_data.get("tracks", [])
                if not new_tracks:
                    xbmc.log(f"[YTMusic Internal] No new tracks in continuation, stopping", xbmc.LOGDEBUG)
                    break
                
                tracks.extend(new_tracks)
                total_tracks = len(tracks)
                
                # Update continuation token
                continuation_token = continuation_data.get("continuation")
                
                # Rate limiting to avoid being blocked
                time.sleep(0.5)
                attempt += 1
                
                # Safety limit to prevent infinite loops
                if attempt > 50:
                    xbmc.log(f"[YTMusic Internal] Reached maximum continuation attempts", xbmc.LOGWARNING)
                    break
            
            xbmc.log(f"[YTMusic Internal] Successfully loaded {total_tracks} tracks from playlist {playlist_id}", xbmc.LOGDEBUG)
            
            # Apply limit if specified
            if limit and len(tracks) > limit:
                tracks = tracks[:limit]
            
            result = initial_data.copy()
            result["tracks"] = tracks
            result["trackCount"] = len(tracks)
            
            return result
            
        except Exception as e:
            xbmc.log(f"[YTMusic Internal] Error loading playlist {playlist_id}: {str(e)}", xbmc.LOGERROR)
            return {"tracks": [], "error": str(e)}
    
    def _get_playlist_initial(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Get initial playlist data"""
        try:
            # Browse endpoint for playlist
            url = f"{self.api_url}/browse"
            
            payload = {
                "context": self.context,
                "browseId": f"VL{playlist_id}"
            }
            
            response = self.session.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code != 200:
                xbmc.log(f"[YTMusic Internal] Initial request failed: {response.status_code}", xbmc.LOGERROR)
                return None
            
            data = response.json()
            return self._parse_playlist_response(data)
            
        except Exception as e:
            xbmc.log(f"[YTMusic Internal] Error in initial request: {str(e)}", xbmc.LOGERROR)
            return None
    
    def _get_playlist_continuation(self, continuation_token: str) -> Optional[Dict[str, Any]]:
        """Get continuation data for playlist"""
        try:
            url = f"{self.api_url}/browse"
            
            payload = {
                "context": self.context,
                "continuation": continuation_token
            }
            
            response = self.session.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code != 200:
                xbmc.log(f"[YTMusic Internal] Continuation request failed: {response.status_code}", xbmc.LOGERROR)
                return None
            
            data = response.json()
            return self._parse_continuation_response(data)
            
        except Exception as e:
            xbmc.log(f"[YTMusic Internal] Error in continuation request: {str(e)}", xbmc.LOGERROR)
            return None
    
    def _parse_playlist_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse initial playlist response to extract tracks and continuation"""
        try:
            # Navigate to playlist content
            contents = data.get("contents", {})
            single_column = contents.get("singleColumnBrowseResultsRenderer", {})
            tabs = single_column.get("tabs", [])
            
            if not tabs:
                return {"tracks": [], "continuation": None}
            
            tab_content = tabs[0].get("tabRenderer", {}).get("content", {})
            section_list = tab_content.get("sectionListRenderer", {}).get("contents", [])
            
            if not section_list:
                return {"tracks": [], "continuation": None}
            
            # Look for music playlist shelf
            playlist_shelf = None
            for section in section_list:
                music_shelf = section.get("musicPlaylistShelfRenderer")
                if music_shelf:
                    playlist_shelf = music_shelf
                    break
                # Also check for regular music shelf (for some playlist types)
                music_shelf = section.get("musicShelfRenderer") 
                if music_shelf:
                    playlist_shelf = music_shelf
                    break
            
            if not playlist_shelf:
                return {"tracks": [], "continuation": None}
            
            # Extract tracks
            tracks = []
            contents = playlist_shelf.get("contents", [])
            for item in contents:
                track = self._parse_track_item(item)
                if track:
                    tracks.append(track)
            
            # Extract continuation token
            continuation = None
            continuations = playlist_shelf.get("continuations", [])
            if continuations:
                next_continuation = continuations[0].get("nextContinuationData")
                if next_continuation:
                    continuation = next_continuation.get("continuation")
            
            # Get playlist metadata
            header = data.get("header", {})
            playlist_header = header.get("musicDetailHeaderRenderer", {})
            
            result = {
                "tracks": tracks,
                "continuation": continuation,
                "title": self._extract_text(playlist_header.get("title")),
                "description": self._extract_text(playlist_header.get("description")),
                "trackCount": len(tracks)
            }
            
            return result
            
        except Exception as e:
            xbmc.log(f"[YTMusic Internal] Error parsing playlist response: {str(e)}", xbmc.LOGERROR)
            return {"tracks": [], "continuation": None}
    
    def _parse_continuation_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse continuation response to extract additional tracks"""
        try:
            # Navigate to continuation content
            continuation_contents = data.get("continuationContents", {})
            music_shelf = continuation_contents.get("musicPlaylistShelfContinuation", {})
            
            if not music_shelf:
                music_shelf = continuation_contents.get("musicShelfContinuation", {})
            
            if not music_shelf:
                return {"tracks": [], "continuation": None}
            
            # Extract tracks
            tracks = []
            contents = music_shelf.get("contents", [])
            for item in contents:
                track = self._parse_track_item(item)
                if track:
                    tracks.append(track)
            
            # Extract next continuation token
            continuation = None
            continuations = music_shelf.get("continuations", [])
            if continuations:
                next_continuation = continuations[0].get("nextContinuationData")
                if next_continuation:
                    continuation = next_continuation.get("continuation")
            
            return {
                "tracks": tracks,
                "continuation": continuation
            }
            
        except Exception as e:
            xbmc.log(f"[YTMusic Internal] Error parsing continuation response: {str(e)}", xbmc.LOGERROR)
            return {"tracks": [], "continuation": None}
    
    def _parse_track_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual track item from playlist"""
        try:
            # Handle different renderer types
            responsive_item = item.get("musicResponsiveListItemRenderer")
            if not responsive_item:
                return None
            
            # Extract video ID
            video_id = None
            overlay = responsive_item.get("overlay", {})
            play_button = overlay.get("musicItemThumbnailOverlayRenderer", {}).get("content", {})
            play_navigation = play_button.get("musicPlayButtonRenderer", {}).get("playNavigationEndpoint", {})
            watch_endpoint = play_navigation.get("watchEndpoint", {})
            video_id = watch_endpoint.get("videoId")
            
            if not video_id:
                return None
            
            # Extract text columns (title, artist, album, duration)
            flex_columns = responsive_item.get("flexColumns", [])
            
            title = None
            artists = []
            album = None
            duration = None
            
            if len(flex_columns) >= 1:
                # Title is usually in the first column
                title_column = flex_columns[0].get("musicResponsiveListItemFlexColumnRenderer", {})
                title_text = title_column.get("text", {})
                title = self._extract_text(title_text)
            
            if len(flex_columns) >= 2:
                # Artist and album info in second column
                info_column = flex_columns[1].get("musicResponsiveListItemFlexColumnRenderer", {})
                info_text = info_column.get("text", {})
                runs = info_text.get("runs", [])
                
                # Parse runs to extract artist and album
                for i, run in enumerate(runs):
                    text = run.get("text", "")
                    if text and text != " • ":
                        if not artists:
                            artists.append({"name": text})
                        elif not album and i > 0:
                            album = {"name": text}
            
            if len(flex_columns) >= 3:
                # Duration in third column
                duration_column = flex_columns[2].get("musicResponsiveListItemFlexColumnRenderer", {})
                duration_text = duration_column.get("text", {})
                duration = self._extract_text(duration_text)
            
            return {
                "videoId": video_id,
                "title": title or "Unknown Title",
                "artists": artists or [{"name": "Unknown Artist"}],
                "album": album,
                "duration": duration,
                "isAvailable": True
            }
            
        except Exception as e:
            xbmc.log(f"[YTMusic Internal] Error parsing track item: {str(e)}", xbmc.LOGERROR)
            return None
    
    def _extract_text(self, text_obj: Any) -> Optional[str]:
        """Extract text from YouTube Music text objects"""
        if isinstance(text_obj, str):
            return text_obj
        
        if isinstance(text_obj, dict):
            # Simple text
            simple_text = text_obj.get("simpleText")
            if simple_text:
                return simple_text
            
            # Runs text
            runs = text_obj.get("runs", [])
            if runs and len(runs) > 0:
                return runs[0].get("text", "")
        
        return None
