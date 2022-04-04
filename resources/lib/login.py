import os, time, json
import utils
import xbmc
import xbmcgui
import xbmcvfs

import requests

from pytube import YouTube
from pytube.exceptions import VideoUnavailable

from ytmusicapi2 import MyYtMus

OAuthInfo = {
    'client_id': '487798644496-1tub18om78iubejcrrr6aavg9f962suf',
    'client_secret': 'vKmDO3AKnLeTthyrkquW2hC0'}

class Login:
    def __init__(self):

        # self.login()

        self.path = os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('profile')), 'headers_auth.json')
        if not os.path.isfile(self.path):
            item = xbmcgui.Dialog().browse(1, 'Please select the headers file', '')
            if item:
                xbmcvfs.copy(item,self.path)

        if not os.path.isfile(self.path):
            xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, "Headers file not found!", utils.addon.getAddonInfo('icon')))
            raise "Headers file not found!"

        try:
            self.ytmusicapi = MyYtMus(self.path)
        except Exception as ex:
            xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, "ERROR! "+repr(ex), utils.addon.getAddonInfo('icon')))
            os.remove(self.path)
            raise ex


    def clear_oauth_cache(self):
        if os.path.isfile(self.path):
            os.remove(self.path)

    def getApi(self):
        return self.ytmusicapi


    def login(self):
        if not utils.get_mem_cache('oauth'):
            path = os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('profile')), "ytmusic_oauth.json")
            credentials = None
            if os.path.isfile(path):
                with open(path, 'rb') as f:
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

                utils.log(repr(verification_url))

                dp = xbmcgui.DialogProgress()
                dp.create("Sign In", "Access " +verification_url+" and enter code "+user_code)

                steps = ((10 * 60 * 1000) // interval)  # 10 Minutes
                count = 0
                for i in range(steps):
                    dp.update(int(count * 100 / steps))
                    count = count + 1

                    try:
                        json_data = self.request_access_token(
                            device_code, OAuthInfo['client_id'], OAuthInfo['client_secret'])
                        json_data['expires_in'] = time.time() + int(json_data.get('expires_in', 3600))
                        credentials = json_data
                    except Exception:
                        raise

                    if 'error' not in json_data:
                        with open(path, 'w') as f:
                            f.write(json.dumps(json_data))
                        break

                    elif json_data['error'] != u'authorization_pending':
                        message = json_data['error']
                        utils.log('Error requesting access token: |%s|' % message)

                    if dp.iscanceled():
                        utils.log("Wait dialog canceled")
                        dp.close()

                    xbmc.sleep(interval)
                dp.close()

            elif int(credentials.get('expires_in','0')) <= int(time.time()):
                utils.log("Auth expired, refreshing..")
                json_data = self.refresh_token(credentials.get('refresh_token'), OAuthInfo['client_id'], OAuthInfo['client_secret'])
                credentials['expires_in'] = time.time() + int(json_data.get('expires_in', 3600))
                credentials['access_token'] = json_data['access_token']
                with open(path, 'w') as f:
                    f.write(json.dumps(credentials))

            utils.set_mem_cache('oauth', json.dumps(credentials))

        else:
            utils.log("Loading auth from cache")
            credentials = json.loads(utils.get_mem_cache('oauth'))



    def getStreamUrl(self, song_id):
        utils.log("getStreamUrl song id: %s " % (song_id))
        streamInfo = dict(self.ytmusicapi.get_song(song_id)['streamingData'])
        # utils.log("STREAM_DATA " + repr(streamInfo))
        if not 'formats' in streamInfo and 'adaptiveFormats' in streamInfo and 'url' in streamInfo["adaptiveFormats"][0]:
            return streamInfo["adaptiveFormats"][0]['url']
        #return YouTube('http://youtube.com/watch?v='+song_id).streams.get_audio_only().url
        
        streams = []
        _only_audio = utils.addon.getSettingInt("stream") == 1
        try:
            streams = YouTube('http://youtube.com/watch?v='+song_id).streams
        except VideoUnavailable:
            _only_audio = True
        for str in streams:
            utils.log(str)
        # return only audio stream?    
        if(_only_audio):
            selected = streams.filter(only_audio=True).order_by('bitrate').desc().first()
        else:
            selected = streams.filter(progressive=True).order_by('resolution').desc().first()
        utils.log("SELECTED: "+repr(selected))
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
            raise Exception('Login Failed '+repr(response_dump))

        if result.headers.get('content-type', '').startswith('application/json'):
            if json_data:
                return json_data
            else:
                return result.json()
        else:
            response_dump = self._get_response_dump(result, json_data)
            raise Exception('Login Failed: Unknown response '+repr(response_dump))


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
            raise Exception('Login Failed '+repr(response_dump))

        #utils.log("HEADERS: "+repr(result.headers))

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
