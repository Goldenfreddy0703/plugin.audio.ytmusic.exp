import sys
import xbmc, xbmcgui
import utils
import urllib.parse

if __name__ == "__main__":
    utils.log(" ARGV: " + repr(sys.argv))

    params = utils.paramsToDict(sys.argv[2])
    action = params.pop('action', '')
    return_params = dict(urllib.parse.parse_qsl(params.pop('return_params'))) if 'return_params' in params else {}

    if action == 'play_song':

        from playsong import PlaySong
        PlaySong().play(params)

    else:

        libgen = None
        libgenUp = None
        pDialog = None
        count = 0

        if utils.get_system_version() < (19, 0):
            dialog = xbmcgui.Dialog()
            dialog.ok("Version Check", "This addon is compatible with Kodi 19 or later")
            raise Exception

        # if new version trigger init cache db
        if (not utils.addon.getSetting('version') or
                utils.addon.getSetting('version') != utils.addon.getAddonInfo('version')):
            utils.addon.setSetting('version', utils.addon.getAddonInfo('version'))
            from storage import storage
            storage.clearCache()
            storage.init_database()

        utils.log("#1# INIT STARTED :"+repr(utils.get_mem_cache('init_started'))+" - FETCHED TIME: "+str(utils.addon.getSettingInt('fetched_time')))

        if utils.addon.getSettingInt('fetched_time') == 0 and utils.get_mem_cache('init_started') != '1':
            # starts loading library
            utils.log("Initing addon data")
            utils.set_mem_cache('init_started', '1')

            from api import Api
            try:
                libgen = Api().getApi().get_library_songs_incremental()
                chunk1 = next(libgen)
            except:
                chunk1=[]
                utils.log("YTMUSIC Unexpected error:"+repr(sys.exc_info()[0]))

            try:
                libgenUp = Api().getApi().get_library_upload_songs_incremental()
                chunk2 = next(libgenUp)
            except:
                chunk2=[]
                utils.log("UPLOADS Unexpected error:"+repr(sys.exc_info()[0]))

            count = len(chunk1) + len(chunk2)

            if count > 0:
                from xbmcgui import DialogProgressBG
                pDialog = DialogProgressBG()
                pDialog.create(utils.addon.getLocalizedString(30420), str(count)+" "+utils.addon.getLocalizedString(30213))

                from storage import storage
                storage.storeInAllSongs(chunk1,0)
                storage.storeInAllSongs(chunk2,2)
            else:
                utils.addon.setSettingInt("fetched_count", count)
                # import time
                # utils.addon.setSettingInt("fetched_time", int(time.time()))
                utils.addon.setSettingInt("fetched_time", 0)
                utils.set_mem_cache('init_started', '0')
                utils.log("No tracks found")

            if count == 0:
                xbmc.executebuiltin("Notification(%s,%s,5000,%s)" % (utils.plugin, "No tracks found", utils.addon.getAddonInfo('icon')))

        if action:
            # execute action
            from actions import Actions
            Actions().executeAction(action, params, return_params)

        else:
            # show navigation menus
            from navigation import Navigation
            Navigation().listMenu(params, return_params)

        if pDialog:
            # finish loading library in background
            try:
                for chunk1 in libgen:
                    storage.storeInAllSongs(chunk1, 0)
                    count = count + len(chunk1)
                    pDialog.update(40, message=str(count) + " " + utils.addon.getLocalizedString(30213))
                    #if (count > 1000):
                    #    break
            except:
                utils.log("Unexpected error:"+repr(sys.exc_info()[0]))
                pass

            try:
                for chunk2 in libgenUp:
                    storage.storeInAllSongs(chunk2, 2)
                    count = count + len(chunk2)
                    pDialog.update(70, message=str(count) + " " + utils.addon.getLocalizedString(30213))
                    #if (count > 1000):
                    #    break
            except:
                utils.log("Unexpected error:"+repr(sys.exc_info()[0]))
                pass

            pDialog.update(90, message=utils.addon.getLocalizedString(30202))
            try:
                from api import Api
                Api().load_playlists()
            except:
                utils.set_mem_cache('init_started', '0')
                pDialog.close()
                utils.log("Unexpected error:"+repr(sys.exc_info()[0]))
                raise 

            pDialog.close()
            import time
            utils.addon.setSettingInt("fetched_time", int(time.time()))
            utils.addon.setSettingInt("fetched_count", count)
            utils.set_mem_cache('init_started', '0')
            utils.log("Finished loading data")

            # utils.log("#2# INIT STARTED :"+repr(utils.get_mem_cache('init_started'))+" - FETCHED TIME: "+str(utils.addon.getSettingInt('fetched_time')))





