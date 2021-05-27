def configure_csfd_artwork(details, settings):
    if 'available_art' not in details:
        return details

    art = details['available_art']
    fanart_enabled = settings.getSettingBool('fanart')
    if not fanart_enabled:
        if 'fanart' in art:
            del art['fanart']
        if 'set.fanart' in art:
            del art['set.fanart']

    return details

# pylint: disable=invalid-name
try:
    basestring
except NameError: # py2 / py3
    basestring = str

#pylint: disable=redefined-builtin
class PathSpecificSettings(object):
    # read-only shim for typed `xbmcaddon.Addon().getSetting*` methods
    def __init__(self, settings_dict, log_fn):
        self.data = settings_dict
        self.log = log_fn

    def getSettingBool(self, id):
        return self._inner_get_setting(id, bool, False)

    def getSettingInt(self, id):
        return self._inner_get_setting(id, int, 0)

    def getSettingNumber(self, id):
        return self._inner_get_setting(id, float, 0.0)

    def getSettingString(self, id):
        return self._inner_get_setting(id, basestring, '')

    def _inner_get_setting(self, setting_id, setting_type, default):
        value = self.data.get(setting_id)
        if isinstance(value, setting_type):
            return value
        self._log_bad_value(value, setting_id)
        return default

    def _log_bad_value(self, value, setting_id):
        if value is None:
            self.log("requested setting ({0}) was not found.".format(setting_id))
        else:
            self.log('failed to load value "{0}" for setting {1}'.format(value, setting_id))
