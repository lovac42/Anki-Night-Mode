
#addons should selectively load before or after a delay of 666
NM_RESERVED_DELAY = 666


try: #travis

    from anki_testing import anki_running
    from .night_mode import NightMode
    night_mode = NightMode()

except ModuleNotFoundError:

    from aqt import mw
    from anki.hooks import addHook, remHook

    def delayedLoader():
        from .night_mode import NightMode
        night_mode = NightMode()
        night_mode.load() #Manual loading first profile

    def onProfileLoaded():
        remHook("profileLoaded", onProfileLoaded)
        mw.progress.timer(
            NM_RESERVED_DELAY, delayedLoader, False
        )

    addHook('profileLoaded', onProfileLoaded)
