# YouTube v3 API Playlist Loader (Hybrid Approach)

## Overview

This module implements a **hybrid approach** that combines the best of both YouTube Music API and YouTube v3 API:

- **YouTube Music API**: Provides proper playlist metadata (real titles, thumbnails, descriptions, author info)
- **YouTube v3 API**: Provides unlimited track loading without the 100-song restriction

This approach is the same core method used successfully by the `anxdpanic/plugin.video.youtube` addon, enhanced with YouTube Music metadata integration.

## The Problem

YouTube Music API has a fundamental server-side limitation that restricts playlist loading to approximately 100 songs. However, it provides excellent playlist metadata. YouTube v3 API can load unlimited tracks but only provides basic video information without proper playlist context.

## The Hybrid Solution

Our solution combines both APIs optimally:

1. **Step 1**: Get playlist metadata from YouTube Music API (title, thumbnails, description, author)
2. **Step 2**: Get unlimited tracks from YouTube v3 Data API using recursive pagination
3. **Step 3**: Merge the rich metadata with unlimited track data

```python
# Hybrid approach
metadata = ytmusic_api.get_playlist(playlist_id, limit=1)  # Just for metadata
tracks = youtube_v3_api.get_playlist_items(playlist_id, all_pages=True)  # Unlimited tracks
result = combine_metadata_with_unlimited_tracks(metadata, tracks)
```

## Benefits

- **Real playlist names**: No more "Playlist PLxxx..." - get actual playlist titles
- **Proper thumbnails**: Playlist artwork from YouTube Music
- **Complete metadata**: Author, description, privacy settings, etc.
- **Unlimited tracks**: No 100-song restriction via YouTube v3 API  
- **Proven reliability**: Uses the same pagination method as successful YouTube addon
- **Graceful fallback**: Works even if YouTube Music API fails

## Configuration

### Settings

1. **Use YouTube v3 API for Playlists** (default: enabled)
   - Enables the new unlimited playlist loading
   - Falls back to YouTube Music API if disabled or if API fails

2. **YouTube API Key** (optional)
   - YouTube Data API v3 key for authentication
   - Required for most playlists due to YouTube API policies
   - Can be obtained from Google Cloud Console

### Getting a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)
5. Restrict the key to YouTube Data API v3 for security
6. Enter the key in addon settings

## Benefits

- **Unlimited playlist loading**: No more 100-song restrictions
- **Proven reliability**: Uses the same method as successful YouTube addon
- **Graceful fallback**: Automatically falls back to YouTube Music API if needed
- **Better error handling**: Clear messages about API key requirements
- **Performance**: Efficient pagination with rate limiting

## Technical Details

### API Endpoints

- **YouTube v3 API**: `https://www.googleapis.com/youtube/v3/playlistItems`
- **Parameters**: `part=snippet,contentDetails&maxResults=50&pageToken=...`
- **Authentication**: API key required for most playlists

### Data Conversion

The YouTube v3 API response is converted to YouTube Music API compatible format:

```python
{
    "videoId": "...",
    "title": "...",
    "artists": [{"name": "..."}],
    "thumbnails": [...],
    # ... other fields
}
```

### Error Handling

- **403 Forbidden**: API key required or invalid
- **Quota exceeded**: Rate limiting applied
- **Network errors**: Automatic retry with backoff
- **Invalid playlist**: Graceful fallback to YouTube Music API

## Compatibility

- **Maintains API compatibility**: Drop-in replacement for existing code
- **Preserves metadata**: All existing playlist fields supported
- **Caching support**: Works with existing storage/caching system
- **Context menu support**: All YouTube Music actions still work

## Usage

The YouTube v3 API loader is automatically used when:

1. "Use YouTube v3 API for Playlists" setting is enabled (default)
2. A valid API key is configured (recommended)
3. The playlist is accessible via YouTube v3 API

Fallback to YouTube Music API occurs when:

1. YouTube v3 API is disabled in settings
2. API key is missing or invalid
3. YouTube v3 API returns an error
4. Network connectivity issues

## Performance Notes

- **Rate limiting**: 0.5 second delay between pages to avoid quota issues
- **Batch size**: 50 items per request (YouTube v3 API maximum)
- **Safety limits**: Maximum 100 pages to prevent infinite loops
- **Caching**: Results are cached using existing storage system

## Migration

For users upgrading:

1. **No action required**: YouTube v3 API is enabled by default
2. **For full functionality**: Configure YouTube API key in settings
3. **Large playlists**: Will now load completely instead of being truncated
4. **Existing playlists**: Will be refreshed with complete content on next load

## Troubleshooting

### "API key required" message
- Configure YouTube API key in addon settings
- Check that the key has YouTube Data API v3 enabled
- Verify the key isn't restricted to wrong APIs

### Playlist still limited to 100 songs
- Check that "Use YouTube v3 API for Playlists" is enabled
- Verify API key is configured correctly
- Check Kodi log for error messages

### "Quota exceeded" errors
- YouTube API has daily quotas
- Rate limiting will help but may not prevent all quota issues
- Consider requesting quota increase from Google Cloud Console

For more details, check the Kodi log at DEBUG level.
