import os
import xbmcvfs
import utils

def resource_filename(*args): 
    return os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('path')), 'resources', 'lib', args[0], args[1])


def resource_listdir(*args):
    return os.listdir(os.path.join(xbmcvfs.translatePath(utils.addon.getAddonInfo('path')), 'resources', 'lib', args[0], args[1]))
