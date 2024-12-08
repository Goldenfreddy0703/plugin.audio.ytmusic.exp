[![Kodi version](https://img.shields.io/badge/kodi%20versions19-blue)](https://kodi.tv/)
[![License: GPL3](https://img.shields.io/badge/License-GPL3-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

# YT Music (plugin.audio.ytmusic.exp)

This addon is a rewrite of the Experimental Google Music addon to Youtube Music made by Foreverguest. 

All credit goes to Foreverguest.

# Used libraries and versions

- https://github.com/sigma67/ytmusicapi/tree/1.8.1
- https://github.com/JuanBindez/pytubefix/tree/v7.3.0

## Requires:

Kodi 19 Matrix

# Installation & Updates

_You can install it via repository to provide automatic updates (future updates may require to rebuild database)_

- Download repository: [repository.ytmusic](https://github.com/Goldenfreddy0703/repository.ytmusic/blob/master/repository.ytmusic-1.0.zip?raw=true)
- Or install it via Kodi file-manager
  - add source: <https://goldenfreddy0703.github.io/repository.ytmusic>

_or install it manually (updates should be installed manually)_

- [plugin.audio.ytmusic.exp](https://github.com/Goldenfreddy0703/plugin.audio.ytmusic.exp/archive/refs/heads/main.zip)

## Important:

Due to changes in the Google API, you must now configure a API Client ID and API Client Secret in the Settings under 'API'. You can use the same values you use for the official Kodi youtube addon (and follow the instructions on how to obtain these credentials provided for that addon).

On first run it will ask for OAuth authentication. Follow the instructions displayed in the UI.

## Using Cookie Data instead of OAuth:

If OAuth authentication is disabled in the settings, on first run it will ask for a headers file with cookie data from your web session. The plugin will accept either 'raw header files' or 'JSON files'.

Please follow this guide [https://ytmusicapi.readthedocs.io/en/lat...on-headers](https://ytmusicapi.readthedocs.io/en/0.21.0/setup.html#authenticated-requests)

See the two points below for further guidance:

### Creating a JSON file
JSON File template:
```sh
{
    "Cookie": "xxxx",
    "X-Goog-Visitor-Id": "yyyy",
    "origin": "https://music.youtube.com"
}
```
Create the JSON file manually as described in [Manual file creation](https://ytmusicapi.readthedocs.io/en/0.21.0/setup.html#manual-file-creation).

### Using the raw headers
Copy the request headers to a plain text file as described in [Copy authentication headers](https://ytmusicapi.readthedocs.io/en/0.21.0/setup.html#copy-authentication-headers).

## Donations:

[Donations for this addon gratefully accepted](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=VH2UFT2Y3PZZN&lc=BR&item_name=foreverguest&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHosted).

Note: All Donations will be going to Foreverguest.

## Versions:

From 1.0~beta8 ongoing you can find the releases under [Releases](https://github.com/Goldenfreddy0703/plugin.audio.ytmusic.exp/releases).

## Older:

[plugin.audio.ytmusic.exp-1.0~beta7](https://github.com/Goldenfreddy0703/plugin.audio.ytmusic.exp/archive/d7372dd4b04ba30950389352935e534c3e0bace2.zip)

[plugin.audio.ytmusic.exp-1.0~beta6](https://github.com/Goldenfreddy0703/plugin.audio.ytmusic.exp/archive/99b245a7eb2d2d2844c61e3f6e32d9343d8f2bb2.zip)

[plugin.audio.ytmusic.exp-1.0~beta5](https://github.com/Goldenfreddy0703/plugin.audio.ytmusic.exp/archive/4e360a43a2c04815daef7171e360b056a3204965.zip)
- Update ytmusicapi and pytube thanks to @woernsn. 

[plugin.audio.ytmusic.exp-1.0~beta4](https://app.box.com/s/381gbuuzcu1diletnpjmfnqxnwm6mcw0)

[plugin.audio.ytmusic.exp-1.0~beta3](https://app.box.com/s/bc9xbr4nvjqyfrul0wligozzj6de0ke9)

[plugin.audio.ytmusic.exp-1.0~beta2](https://app.box.com/s/4a0jly0ezg9pe21hyi3sbmbbpnxtabha)

[plugin.audio.ytmusic.exp-1.0~beta1](https://app.box.com/s/d9tcjkan4ih3oa5d8ain13ybuydjnp5a)

## TODO:

- [ ] extend headless mode to song, album and playlist context menus
- [x] implement OAuth login
- [x] support adaptive streaming
- [x] add playlist operations
- [x] add Android/Linux support
- [x] make Youtube Music thumbnails have better resolution
- [x] adding icons in the future

## Help needed with maintaining!!!

I am very clueless on this project currently cause this addon was made by foreverguest who has done a very great job maintaining this addon. Be aware that this is a community driven project, so feel free to submit PR's yourself to improve the code and/or help others with support on the forums etc. If you're willing to really participate in the development, please contact me so I can give you write access to the repo. I will do my best to maintain the project for foreverguest. Thanks for understanding!

All credit goes to foreverguest

## License

Licensed under The GPL License.
