import os, time, json
import utils
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import requests

from pytubefix import YouTube
from pytubefix.exceptions import VideoUnavailable

from ytmusicapi import setup
from ytmusicapi import YTMusic
from ytmusicapi2 import MyYtMus

OAuthInfo = {
    'client_id': '861556708454-d6dlm3lh05idd8npek18k6be8ba3oc68.apps.googleusercontent.com',
    'client_secret': 'SboVhoG9s0rNafixCSGGKXAT'}


class Login:

    class MusicPremiumOnly(VideoUnavailable):
        """Video is music-premium-only.

        YouTube has special videos that are only viewable to users who have
        subscribed to YouTube Music Premium.
        """

        def __init__(self, video_id: str):
            """
            :param str video_id:
                A YouTube video identifier.
            """
            self.video_id = video_id
            super().__init__(self.video_id)

        @property
        def error_string(self):
            return f'{self.video_id} is a music-premium-only video'

    def __init__(self):

        self.path = os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('profile')), 'ytmusic_oauth.json')
        if not self.loginOAuth():
            self.path = os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('profile')), 'headers_auth.json')
            if not os.path.isfile(self.path):
                select = xbmcgui.Dialog().select("Raw headers or JSON file", ["Raw Headers", "JSON"])
                if select == 0:
                    raw_item = xbmcgui.Dialog().browse(1, 'Please select the file containing the raw headers', '')
                    with open(raw_item, 'r', encoding='utf-8') as raw_item_fp:
                        setup(filepath=self.path, headers_raw=raw_item_fp.read())
                elif select == 1:
                    item = xbmcgui.Dialog().browse(1, 'Please select the JSON file containing the headers', '')
                    if item:
                        xbmcvfs.copy(item, self.path)

            if not os.path.isfile(self.path):
                xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, "Headers file not found!", utils.addon.getAddonInfo('icon')))
                raise Exception("Headers file not found!")

        try:
            self.ytmusicapi = MyYtMus(self.path)
        except Exception as ex:
            xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, "ERROR! " + repr(ex), utils.addon.getAddonInfo('icon')))
            os.remove(self.path)
            raise ex


    def clear_oauth_cache(self):
        if os.path.isfile(self.path):
            os.remove(self.path)

    def getApi(self):
        return self.ytmusicapi


    def loginOAuth(self):
        if utils.addon.getSetting('useOAuth') != 'true':
            return False

        if not utils.get_mem_cache('oauth'):
            # path = os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('profile')), "ytmusic_oauth.json")
            credentials = None
            if os.path.isfile(self.path):
                with open(self.path, 'rb') as f:
                    credentials = json.loads(f.read())

            if credentials is None:
                # utils.log("1 "+repr(self.gmusicapi._session_class.oauth._asdict()))

                try:
                    json_data = self.request_device_and_user_code(OAuthInfo['client_id'])
                except Exception:
                    raise
            
                interval = int(json_data.get('interval', 5)) * 1000
                if interval > 60000:
                    interval = 5000
                device_code = json_data['device_code']
                user_code = json_data['user_code']
                verification_url = json_data.get('verification_url', 'youtube.com/activate').lstrip('https://www.')

                utils.log(repr(verification_url), xbmc.LOGDEBUG)

                dp = xbmcgui.DialogProgress()
                dp.create("Sign In", "Access " + verification_url + " and enter code " + user_code)

                steps = ((10 * 60 * 1000) // interval)  # 10 Minutes
                count = 0
                for i in range(steps):
                    dp.update(int(count * 100 / steps))
                    count = count + 1

                    try:
                        json_data = self.request_access_token(
                            device_code, OAuthInfo['client_id'], OAuthInfo['client_secret'])
                        json_data['expires_at'] = time.time() + int(json_data.get('expires_in', 3600))
                        credentials = json_data
                    except Exception:
                        raise

                    if 'error' not in json_data:
                        with open(self.path, 'w') as f:
                            f.write(json.dumps(json_data))
                        return True

                    elif json_data['error'] != u'authorization_pending':
                        message = json_data['error']
                        utils.log('Error requesting access token: |%s|' % message)

                    if dp.iscanceled():
                        utils.log("Wait dialog canceled")
                        dp.close()

                    xbmc.sleep(interval)
                dp.close()
                return False

            elif int(credentials.get('expires_at', '0')) - 3600 <= int(time.time()):
                utils.log("Auth expired, refreshing..")
                json_data = self.refresh_token(credentials.get('refresh_token'), OAuthInfo['client_id'], OAuthInfo['client_secret'])
                credentials['expires_at'] = time.time() + int(json_data.get('expires_in', 3600))
                credentials['access_token'] = json_data['access_token']
                with open(self.path, 'w') as f:
                    f.write(json.dumps(credentials))

            utils.set_mem_cache('oauth', json.dumps(credentials))
            return True

        else:
            utils.log("Loading auth from cache")
            credentials = json.loads(utils.get_mem_cache('oauth'))
            return True            


    def getStreamUrl(self, song_id):
        utils.log("getStreamUrl song id: %s " % (song_id), xbmc.LOGDEBUG)
        streamInfo = dict(self.ytmusicapi.get_song(song_id)['streamingData'])
        # utils.log("STREAM_DATA " + repr(streamInfo))
        if not 'formats' in streamInfo and 'adaptiveFormats' in streamInfo and 'url' in streamInfo["adaptiveFormats"][0]:
            return streamInfo["adaptiveFormats"][0]['url']
        # return YouTube('http://youtube.com/watch?v='+song_id).streams.get_audio_only().url
        
        streams = []
        _only_audio = utils.addon.getSettingInt("stream") == 1
        try:
            streams = YouTube('http://youtube.com/watch?v=' + song_id).streams
            utils.log(f"Playing {song_id} without OAuth.")
        except self.MusicPremiumOnly:
            if utils.addon.getSetting('useOAuth') != 'true':
                dialog = xbmcgui.Dialog()
                dialog.ok(utils.addon.getLocalizedString(30414), utils.addon.getLocalizedString(30415))
                return None
            else:
                try:
                    streams = YouTube('http://youtube.com/watch?v=' + song_id, use_oauth=True, allow_oauth_cache=True).streams
                    utils.log(f"Playing {song_id} with OAuth.")
                except Exception:
                    raise
        except VideoUnavailable:
            _only_audio = True

        if len(streams) == 0:
            # No (public) youtube video found TODO Use youtube api in addition (https://github.com/Goldenfreddy0703/plugin.audio.ytmusic.exp/issues/6)
            return None

        for str in streams:
            utils.log(str, xbmc.LOGDEBUG)
        # return only audio stream?    
        if(_only_audio):
            selected = streams.filter(only_audio=True).order_by('bitrate').desc().first()
        else:
            selected = streams.filter(progressive=True).order_by('resolution').desc().first()
        utils.log("SELECTED: " + repr(selected))
        return selected.url



    def request_device_and_user_code(self, client_id=''):
        # https://developers.google.com/youtube/v3/guides/auth/devices
        headers = {'Host': 'accounts.google.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        post_data = {'client_id': client_id,
                     'scope': 'https://www.googleapis.com/auth/youtube'}

        # url
        url = 'https://accounts.google.com/o/oauth2/device/code'

        result = requests.post(url, data=post_data, headers=headers)

        try:
            json_data = result.json()
            if 'error' in json_data:
                json_data.update({'code': str(result.status_code)})
                raise Exception(json_data)
        except ValueError:
            json_data = None

        if result.status_code != requests.codes.ok:
            response_dump = self._get_response_dump(result, json_data)
            raise Exception('Login Failed ' + repr(response_dump))

        if result.headers.get('content-type', '').startswith('application/json'):
            if json_data:
                return json_data
            else:
                return result.json()
        else:
            response_dump = self._get_response_dump(result, json_data)
            raise Exception('Login Failed: Unknown response ' + repr(response_dump))

    def request_access_token(self, code, client_id='', client_secret=''):
        # https://developers.google.com/youtube/v3/guides/auth/devices
        headers = {'Host': 'www.googleapis.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        post_data = {'client_id': client_id,
                     'client_secret': client_secret,
                     'code': code,
                     'grant_type': 'http://oauth.net/grant_type/device/1.0'}

        # url
        url = 'https://www.googleapis.com/oauth2/v4/token'

        result = requests.post(url, data=post_data, headers=headers)

        authorization_pending = False
        try:
            json_data = result.json()
            if 'error' in json_data:
                if json_data['error'] != u'authorization_pending':
                    json_data.update({'code': str(result.status_code)})
                    raise Exception(json_data)
                else:
                    authorization_pending = True
        except ValueError:
            json_data = None

        if (result.status_code != requests.codes.ok) and not authorization_pending:
            response_dump = self._get_response_dump(result, json_data)
            raise Exception('Login Failed: Code %s ' % str(result.status_code))

        if result.headers.get('content-type', '').startswith('application/json'):
            if json_data:
                return json_data
            else:
                return result.json()
        else:
            response_dump = self._get_response_dump(result, json_data)
            raise Exception('Login Failed: Unknown response ' + 
                            repr(response_dump))



    def refresh_token(self, refresh_token, client_id='', client_secret=''):
        # https://developers.google.com/youtube/v3/guides/auth/devices
        headers = {'Host': 'www.googleapis.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                   'Content-Type': 'application/x-www-form-urlencoded'}

        post_data = {'client_id': client_id,
                     'client_secret': client_secret,
                     'refresh_token': refresh_token,
                     'grant_type': 'refresh_token'}

        # url
        url = 'https://www.googleapis.com/oauth2/v4/token'

        result = requests.post(url, data=post_data, headers=headers)

        try:
            json_data = result.json()
            if 'error' in json_data:
                json_data.update({'code': str(result.status_code)})
                if json_data['error'] == 'invalid_grant' and json_data['code'] == '400':
                    raise Exception('invalid grant')
                raise Exception(json_data)
        except ValueError:
            json_data = None

        if result.status_code != requests.codes.ok:
            response_dump = self._get_response_dump(result, json_data)
            raise Exception('Login Failed ' + repr(response_dump))

        # utils.log("HEADERS: "+repr(result.headers))

        if result.headers.get('content-type', '').startswith('application/json'):
            if not json_data:
                json_data = result.json()
            return json_data

        return '', ''

    @staticmethod
    def _get_response_dump(response, json_data=None):
        if json_data:
            return json_data
        else:
            try:
                return response.json()
            except ValueError:
                try:
                    return response.text
                except:
                    return 'None'
