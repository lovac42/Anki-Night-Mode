# -*- coding: utf-8 -*-
# Copyright (C) 2019-2020 Lovac42
# Copyright (C) 2015-2019 Michal Krassowski <krassowski.michal@gmail.com>
# Support: https://github.com/lovac42/CCBC-Night-Mode
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from aqt import mw
from anki.hooks import addHook


#addons should selectively load before or after a delay of 666
NM_RESERVED_DELAY = 66 #CCBC loads much faster

night_mode = None

def delayedLoader():
    """
        Delays loading of NM to avoid addon conflicts.
    """
    global night_mode
    from .night_mode import NightMode
    night_mode = NightMode()
    night_mode.load()
    mw.night_mode = night_mode

def onProfileLoaded():
    if not night_mode:
        mw.progress.timer(
            NM_RESERVED_DELAY, delayedLoader, False
        )
    else:
        night_mode.load()

addHook('profileLoaded', onProfileLoaded)
