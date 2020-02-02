# -*- coding: utf-8 -*-
# Copyright (C) 2019-2020 Lovac42
# Copyright (C) 2015-2019 Michal Krassowski <krassowski.michal@gmail.com>
# Support: https://github.com/lovac42/CCBC-Night-Mode
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from os import makedirs
from os.path import isfile, dirname, abspath, join
from PyQt4.QtGui import QIcon, QPixmap
from PyQt4.QtGui import QStyle


def inverted_icon(icon, width=32, height=32, as_image=False):
    pixmap = icon.pixmap(width, height)
    image = pixmap.toImage()
    image.invertPixels()
    if as_image:
        return image
    new_icon = QIcon(QPixmap.fromImage(image))
    return new_icon


class Icons:

    paths = {}

    def __init__(self, mw):

        add_on_path = dirname(abspath(__file__))
        icons_path = join(add_on_path, 'icons')

        arrow_icon_path = join(icons_path, 'arrow.png')
        arrow_icon_path = arrow_icon_path.replace('\\', '/')
        self.paths['arrow'] = arrow_icon_path

        search_icon_path = join(icons_path, 'search.png')
        search_icon_path = search_icon_path.replace('\\', '/')
        self.paths['search'] = search_icon_path

    @property
    def arrow(self):
        return self.paths['arrow']

    @property
    def search(self):
        return self.paths['search']
