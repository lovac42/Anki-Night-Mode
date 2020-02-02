# -*- coding: utf-8 -*-
# Copyright (C) 2019-2020 Lovac42
# Copyright (C) 2015-2019 Michal Krassowski <krassowski.michal@gmail.com>
# Support: https://github.com/lovac42/CCBC-Night-Mode
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


import gettext
from os import path

from anki.lang import getLang, _ as fallback_translation

lang = getLang()
this_dir = path.dirname(path.abspath(__file__))
locale_dir = path.join(this_dir, 'locale')
trans = gettext.translation('Anki-Night-Mode', locale_dir, languages=[lang], fallback=True)
# See: http://www.loc.gov/standards/iso639-2/php/code_list.php for language codes


def _(text):
    try:
        return trans.gettext(text)
    except Exception as e:
        print(e)
        return fallback_translation(text)
