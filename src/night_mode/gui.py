# -*- coding: utf-8 -*-
# Copyright (C) 2019-2021 Lovac42
# Copyright (C) 2015-2019 Michal Krassowski <krassowski.michal@gmail.com>
# Support: https://github.com/lovac42/CCBC-Night-Mode
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from PyQt4.QtGui import QPushButton, QDialog

from .languages import _


class AddonDialog(QDialog):
    def __init__(self, *args, **kwargs):
        QDialog.__init__(*args, **kwargs)


def create_button(name, callback=None):
    button = QPushButton(_(name))
    if callback:
        button.clicked.connect(callback)
    return button


def iterate_widgets(layout):
    for i in reversed(range(layout.count())):
        yield layout.itemAt(i).widget()


def remove_layout(layout):
    for widget in iterate_widgets(layout):
        layout.removeWidget(widget)
        widget.deleteLater()

