# Changelog

## plugin.audio.ytmusic.exp-1.0~~beta28.1
- Update to Pytubefix 5.6.3
- Add rudimentary headless mode (to be extended)
- Add experimental settings to force viewtypes on menus

## plugin.audio.ytmusic.exp-1.0~~beta27
- Update to Pytubefix 5.1.1

## plugin.audio.ytmusic.exp-1.0~~beta26

- Add menu icons
- Update to YTMusicAPI 1.6.0 plus various commits
- Change from Pytube to Pytubefix 4.0.0
- Add support for Library Podcasts and Channels

## plugin.audio.ytmusic.exp-1.0~~beta25

- Quick fix preventing the 'Home' list from failing if it contains sections YTMusicAPI cannot yet parse correctly (such as 'Keep Listening' and 'Your Shows') by filtering out sections with empty or invalid content

## plugin.audio.ytmusic.exp-1.0~~beta24

- Update ytmusicapi to version `1.5.4`
- Fix a bug in displaying of album information
- Enable adding and removing of playlists from library
- Add an experimental feature to display playlists and episodes in search results

## plugin.audio.ytmusic.exp-1.0~~beta23

- Fix an error caused by playlists in search results lacking a browseId

## plugin.audio.ytmusic.exp-1.0~~beta22

- Fix a bug when loading a song with no artist id (e.g. from search)
- Fix a bug when playing playlists containing ytmusic songs and songs from other sources

## plugin.audio.ytmusic.exp-1.0~~beta21

- Fix a bug causing loading of playlists to fail for playlists without setVideoId (e.g. recap)
- Fix loading of uploaded songs into library
- Differentiate between log levels
- Switch to new settings format

## plugin.audio.ytmusic.exp-1.0~~beta20

- Fix an issue introduced in in 1.0~~beta19 that caused the 'search' context menu option to fail
- Re-enable context menu option to mark songs as thumbs up / down (liked / disliked)
- Update ytmusicapi to version `1.3.2`
- Add experimental feature to add songs to the YT library or remove them (depending on availability of feedback tokens)
- Add setting to control automatic reloading of the YT library after adding a song

## plugin.audio.ytmusic.exp-1.0~~beta19

- Fix a dump introduced in 1.0~~beta18 when trying to play a song from library albums and artists
- More consistent rendering of information and context menus for library and non-library items
- Remove fixed length of 'Home' menu output and added a next 'page button' instead

## plugin.audio.ytmusic.exp-1.0~~beta18

- Apply an improved fix to PyTube parser.py from https://github.com/sluggish-yard/pytube-saguaro/pull/5/commits/e91d5281c06cb7236c66053c3ce5561e647598a6
- Update ytmusicapi to version `1.2.1`
- Enable OAuth login into ytmusicapi
- Add 'Home' menu item to YtMusic Library menu
- Add experimental 'Charts' menu item to YtMusic Library menu (songs don't work yet)
- Show more detailed song information
- Add albumart to songs in playlist when adding entire albums / singles
- Add context menu items 'Play' / 'Play next' / 'Add to queue' to songs
- Add option to turn off colored titles (for headless operation of Kodi)
- Add wrapper class around YtMusic Library results exposing a uniform interface for results obtained from internal storage and from different API calls

## plugin.audio.ytmusic.exp-1.0~~beta17

- Apply another fix to PyTube cipher.py from PyTube Discussions
- Add 'Artist subscriptions' menu item to YtMusic Library menu
- Extend navigability of artist search results
- Add subscribe / unsubscribe context menu to artst menu items
- Show albumart for album songs in search results

## plugin.audio.ytmusic.exp-1.0~beta16

- Apply fix to PyTube cipher.py from PyTube Pull Request #1680.

## plugin.audio.ytmusic.exp-1.0~beta15

- Update to pytube version `15.0.0`
- Fix a dump in extract.py which apparently only occurs in a kodi environment.

## plugin.audio.ytmusic.exp-1.0~beta14

- Fix syntax error in api.py introduced in 1.0~beta13.
- Enable pytube JS parser to recognize regular expressions.

## plugin.audio.ytmusic.exp-1.0~beta13

- Update ytmusicapi to version `0.25.0` to restore library and playlist functionality.
- Refresh playlist after deleting a song from the playlist.
- Fix error when attempting to display an empty playlist.

## plugin.audio.ytmusic.exp-1.0~beta12

- Fix errors caused by the introduction of album IDs in song data.
- Fix an error causing the artist in playlist songs to be displayed as '-???-'.

## plugin.audio.ytmusic.exp-1.0~beta11

- Add cover to albums and allow song playback from album.
- Increase songs per playlist from default 100 to 1000.

## plugin.audio.ytmusic.exp-1.0~beta10

- Fix the handling of artist albums.

## plugin.audio.ytmusic.exp-1.0~beta9

- Workaround for 'ValueError' problem inside PyTube code.

## plugin.audio.ytmusic.exp-1.0~beta8

- Add support for OAuth (for YouTube).

## plugin.audio.ytmusic.exp-1.0~beta7

- Add possibility to provide 'raw' headers.
- Catch the JsonDecodeError for good.

## plugin.audio.ytmusic.exp-1.0~beta6

- Fix catch of exception for JsonDecodeError
- Catch VideoUnavailable exception

## plugin.audio.ytmusic.exp-1.0~beta5

- Update pytube to version `v23.0.0`
- Update ytmusicapi to version `0.21.0`
