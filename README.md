[![Kodi version](https://img.shields.io/badge/kodi%20versions19-blue)](https://kodi.tv/)
[![License: GPL3](https://img.shields.io/badge/License-GPL3-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

# YT Music (plugin.audio.ytmusic.exp)

This addon is a rewrite of the Experimental Google Music addon to Youtube Music made by Foreverguest. 

All credit goes to Foreverguest.


## Requires:

Kodi 19 Matrix

## Important:

On first run it will ask for the headers file with cookie data from your web session.

JSON File template:
```sh
{
    "Cookie": "xxxx",
    "X-Goog-Visitor-Id": "yyyy",
    "origin": "https://music.youtube.com"
}
```
## Obtaining Cookie Data:

Please follow this guide [https://ytmusicapi.readthedocs.io/en/lat...on-headers](https://ytmusicapi.readthedocs.io/en/latest/setup.html#copy-authentication-headers)

After you have the cookie and visitor-id strings, just create a text file like the template above and fill the strings.

## Donations:

[Donations for this addon gratefully accepted](https://pages.github.com/).

Note: All Donations will be going to Foreverguest.

## New version:


[plugin.audio.ytmusic.exp-1.0~beta4](https://app.box.com/s/381gbuuzcu1diletnpjmfnqxnwm6mcw0)
- update library dependencies, should fix playback

## Older:

[plugin.audio.ytmusic.exp-1.0~beta3](https://app.box.com/s/bc9xbr4nvjqyfrul0wligozzj6de0ke9)

[plugin.audio.ytmusic.exp-1.0~beta2](https://app.box.com/s/4a0jly0ezg9pe21hyi3sbmbbpnxtabha)

[plugin.audio.ytmusic.exp-1.0~beta1](https://app.box.com/s/d9tcjkan4ih3oa5d8ain13ybuydjnp5a)

## TODO:

- implement logon like Youtube Addon
- support adaptive streaming
- add playlist operations 

## License

Licensed under The GPL License.
