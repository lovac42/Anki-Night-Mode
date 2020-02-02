# -*- coding: utf-8 -*-
# Copyright (C) 2019-2020 Lovac42
# Copyright (C) 2015-2019 Michal Krassowski <krassowski.michal@gmail.com>
# Support: https://github.com/lovac42/CCBC-Night-Mode
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from aqt import mw
from .internals import Setting


class Config:

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix
        self.settings = {}

    # has to be separately from __init__ to avoid circular reference
    def init_settings(self):
        for setting_class in Setting.members:
            setting = setting_class(self.app)
            self.settings[setting.name] = setting

    def __getattr__(self, attr):
        return self.settings[attr]

    def stored_name(self, name):
        return self.prefix + name

    def load(self):
        for name, setting in self.settings.items():
            key = self.stored_name(name)
            value = mw.pm.profile.get(key, setting.default_value)

            setting.value = value

        for setting in self.settings.values():
            setting.on_load()

    def save(self):
        """
        Saves configurable variables into profile, so they can
        be used to restore previous state after Anki restart.
        """
        for name, setting in self.settings.items():
            key = self.stored_name(name)
            mw.pm.profile[key] = setting.value

        for setting in self.settings.values():
            setting.on_save()


class ConfigValueGetter:

    def __init__(self, config):
        self.config = config

    def __getattr__(self, attr):
        setting = getattr(self.config, attr)
        return setting.value
