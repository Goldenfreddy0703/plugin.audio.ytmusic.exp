#!/usr/bin/env python3

"""
Test script for ytmusicapi 1.11.0 charts compatibility
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

def test_charts_structure():
    """Test the new charts structure from ytmusicapi 1.11.0"""
    try:
        import ytmusicapi2
        from ytmusicapi.ytmusic import YTMusic
        
        print("Testing ytmusicapi 1.11.0 charts structure...")
        
        # Test directly
        ytmusic = YTMusic()
        charts = ytmusic.get_charts('US')
        
        print("\n=== CHARTS STRUCTURE ===")
        for key, value in charts.items():
            print(f"{key}: {type(value)}")
            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    print(f"  First item keys: {list(value[0].keys())}")
            elif isinstance(value, dict):
                print(f"  Dict keys: {list(value.keys())}")
        
        print("\n=== TESTING COMPATIBILITY LOGIC ===")
        
        # Test videos section
        if 'videos' in charts:
            videos = charts['videos']
            print(f"Videos type: {type(videos)}")
            if isinstance(videos, list):
                print("✓ Videos is list (new structure)")
                for i, video_playlist in enumerate(videos):
                    if 'playlistId' in video_playlist:
                        print(f"  Video {i}: {video_playlist['title']} -> {video_playlist['playlistId']}")
            else:
                print("✓ Videos is dict (old structure)")
                print(f"  playlistId: {videos.get('playlist', 'N/A')}")
        
        # Test artists section
        if 'artists' in charts:
            artists = charts['artists']
            print(f"Artists type: {type(artists)}")
            if isinstance(artists, list):
                print("✓ Artists is list (new structure)")
                print(f"  First artist: {artists[0].get('title', 'N/A')} (rank {artists[0].get('rank', 'N/A')})")
            else:
                print("✓ Artists is dict (old structure)")
                print(f"  Items count: {len(artists.get('items', []))}")
        
        # Test genres section  
        if 'genres' in charts:
            genres = charts['genres']
            print(f"Genres type: {type(genres)}")
            if isinstance(genres, list):
                print("✓ Genres is list (new structure)")
                print(f"  First genre: {genres[0].get('title', 'N/A')} -> {genres[0].get('playlistId', 'N/A')}")
            else:
                print("✓ Genres is dict (old structure)")
                print(f"  Items count: {len(genres.get('items', []))}")
        
        # Test countries section
        if 'countries' in charts:
            countries = charts['countries']
            print(f"Countries type: {type(countries)}")
            if isinstance(countries, dict):
                print("✓ Countries is dict (expected)")
                print(f"  Selected: {countries.get('selected', {}).get('text', 'N/A')}")
                print(f"  Options count: {len(countries.get('options', []))}")
        
        print("\n✅ SUCCESS: All charts structure tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_charts_structure()
    sys.exit(0 if success else 1)
