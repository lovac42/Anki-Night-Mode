# -*- coding: utf-8 -*-
# Copyright (C) 2019-2020 Lovac42
# Copyright (C) 2015-2019 Michal Krassowski <krassowski.michal@gmail.com>
# Support: https://github.com/lovac42/CCBC-Night-Mode
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from PyQt4.QtCore import Qt
from PyQt4 import QtGui as QtWidgets

import ccbc
import aqt
from anki.stats import CollectionStats
from aqt import mw, editor, QPixmap
from aqt.addcards import AddCards
from aqt.browser import Browser
from aqt.clayout import CardLayout
from aqt.editcurrent import EditCurrent
from aqt.editor import Editor
from aqt.tagedit import TagEdit
from aqt.progress import ProgressManager
from aqt.stats import DeckStats
from aqt.addons import AddonsDialog, ConfigEditor

from .gui import AddonDialog, iterate_widgets
from .config import ConfigValueGetter
from .css_class import inject_css_class
from .internals import percent_escaped, move_args_to_kwargs, from_utf8, PropertyDescriptor
from .internals import style_tag, wraps, appends_in_night_mode, replaces_in_night_mode, css
from .styles import SharedStyles, ButtonsStyle, ImageStyle, DeckStyle, LatexStyle, DialogStyle
from .internals import SnakeNameMixin, StylerMetaclass, abstract_property
from .internals import RequiringMixin

import ccbc.css


class Styler(RequiringMixin, SnakeNameMixin, metaclass=StylerMetaclass):

    def __init__(self, app):
        RequiringMixin.__init__(self, app)
        self.app = app
        self.config = ConfigValueGetter(app.config)
        self.original_attributes = {}

    @abstract_property
    def target(self):
        return None

    @property
    def is_active(self):
        return self.name not in self.config.disabled_stylers

    @property
    def friendly_name(self):
        name = self.name.replace('_styler', '')
        return name.replace('_', ' ').title()

    def get_or_create_original(self, key):
        if key not in self.original_attributes:
            original = getattr(self.target, key)
            self.original_attributes[key] = original
        else:
            original = self.original_attributes[key]

        return original

    def replace_attributes(self):
        try:
            for key, addition in self.additions.items():
                original = self.get_or_create_original(key)
                setattr(self.target, key, original + addition.value(self))

            for key, replacement in self.replacements.items():
                self.get_or_create_original(key)

                if isinstance(replacement, PropertyDescriptor):
                    replacement = replacement.value(self)

                setattr(self.target, key, replacement)

        except (AttributeError, TypeError):
            print('Failed to inject style to:', self.target, key, self.name)
            raise

    def restore_attributes(self):
        for key, original in self.original_attributes.items():
            setattr(self.target, key, original)


class ToolbarStyler(Styler):

    target = mw.toolbar
    require = {
        SharedStyles
    }

    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def _body(self):
        if not self.config.state_on:
            return ""
        return self.shared.top


class StyleSetter:

    def __init__(self, target):
        self.target = target

    @property
    def css(self):
        return self.target.styleSheet()

    @css.setter
    def css(self, value):
        self.target.setStyleSheet(value)


class MenuStyler(Styler):
    target = StyleSetter(mw)

    @appends_in_night_mode
    def css(self):
        if not self.config.state_on:
            return ""
        return self.shared.menu


class ReviewerStyler(Styler):

    target = mw.reviewer
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps(position='around')
    def _bottomHTML(self, reviewer, _old):
        if not self.config.state_on:
            return _old(reviewer)
        return _old(reviewer) + style_tag(percent_escaped(self.bottom_css))

    @property
    def bottom_css(self):
        return self.buttons.html + self.shared.colors_replacer + """
        body, #outer
        {
            background:-webkit-gradient(linear, left top, left bottom, from(#333), to(#222));
            border-top-color:#222
        }
        .stattxt
        {
            color:#ccc
        }
        /* Make the color above "Again" "Hard" "Easy" and so on buttons readable */
        .nobold
        {
            color:#ddd
        }
        """


class ReviewerCards(Styler):

    target = mw.reviewer
    require = {
        LatexStyle,
        ImageStyle
    }

    # TODO: it can be implemented with a nice decorator
    @wraps(position='around')
    def revHtml(self, reviewer, _old):
        if not self.config.state_on:
            return _old(reviewer)
        return _old(reviewer) + style_tag(percent_escaped(self.body))

    @css
    def body(self):
        # Invert images and latex if needed

        css_body = """
        .card input
        {
            background-color:black!important;
            border-color:#444!important;
            color:#eee!important
        }
        .card input::selection
        {
            color: """ + self.config.color_t + """;
            background: #0864d4
        }
        .typeGood
        {
            color:black;
            background:#57a957
        }
        .typeBad
        {
            color:black;
            background:#c43c35
        }
        .typeMissed
        {
            color:black;
            background:#ccc
        }
        #answer
        {
            height:0;
            border:0;
            border-bottom: 2px solid #333;
            border-top: 2px solid black
        }
        img#star
        {
            -webkit-filter:invert(0%)!important
        }
        .cloze
        {
            color:#5566ee!important
        }
        a
        {
            color:#0099CC
        }
        """

        card_color = """
        .card{
            color:""" + self.config.color_t + """!important;
        }
        """

        css = css_body + card_color + self.shared.user_color_map + self.shared.body_colors

        if self.config.invert_image:
            css += self.image.invert
        if self.config.invert_latex:
            css += self.latex.invert

        return css


class DeckBrowserStyler(Styler):

    target = mw.deckBrowser
    require = {
        SharedStyles,
        DeckStyle
    }

    @appends_in_night_mode
    def _body(self):
        if not self.config.state_on:
            return ""
        styles_html = style_tag(percent_escaped(self.deck.style + self.shared.body_colors))
        return inject_css_class(True, styles_html)


class DeckBrowserBottomStyler(Styler):

    target = mw.deckBrowser.bottom
    require = {
        DeckStyle
    }

    @appends_in_night_mode
    def _centerBody(self):
        if not self.config.state_on:
            return ""
        styles_html = style_tag(percent_escaped(self.deck.bottom))
        return inject_css_class(True, styles_html)


class OverviewStyler(Styler):

    target = mw.overview
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @appends_in_night_mode
    def _body(self):
        if not self.config.state_on:
            return ""
        styles_html = style_tag(percent_escaped(self.css))
        return inject_css_class(True, styles_html)

    @css
    def css(self):
        return f"""
        {self.buttons.html}
        {self.shared.colors_replacer}
        {self.shared.body_colors}
        .descfont
        {{
            color: {self.config.color_t}
        }}
        """


class OverviewBottomStyler(Styler):

    target = mw.overview.bottom
    require = {
        DeckStyle
    }

    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def _centerBody(self):
        if self.config.state_on:
            return self.deck.bottom
        return ""



class AnkiWebViewStyler(Styler):

    target = mw.web
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps(position='around')
    def stdHtml(self, web, *args, **kwargs):
        old = kwargs.pop('_old')

        args, kwargs = move_args_to_kwargs(old, [web] + list(args), kwargs)

        kwargs['head'] = kwargs.get('head', '')

        if self.config.state_on:
            kwargs['head'] += style_tag(self.waiting_screen)

        return old(web, *args[1:], **kwargs)

    @css
    def waiting_screen(self):
        return self.buttons.html + self.shared.body_colors


class BrowserPackageStyler(Styler):

    target = aqt.browser

    @replaces_in_night_mode
    def COLOUR_MARKED(self):
        if self.config.state_on:
            return '#735083'
        return 'yellow'

    @replaces_in_night_mode
    def COLOUR_SUSPENDED(self):
        if self.config.state_on:
            return '#777750'
        return '#FFFFB2'


class BrowserStyler(Styler):

    target = Browser
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps
    def init(self, browser, mw, *args, **kwargs):
        self.basic_css = browser.styleSheet()
        state = self.config.state_on
        self.changeToNightMode(
            browser,
            state and self.config.enable_in_dialogs
        )

    @wraps
    def changeToNightMode(self, browser, b):
        if not self.config.enable_in_dialogs:
            return
        try:
            if b:
                self.makeDark(browser)
            else:
                self.makeLight(browser)
        except RuntimeError:
            pass

    def makeLight(self, browser):
        browser.setStyleSheet("")
        browser.form.tableView.setStyleSheet("")
        browser.form.tableView.horizontalHeader().setStyleSheet("")
        browser.form.searchEdit.setStyleSheet("")
        browser.form.searchButton.setText("Search")
        browser.form.searchButton.setStyleSheet("")

        browser.sidebarTree.setStyleSheet("")
        browser.editor.widget.setStyleSheet("")

        browser.toolbar.web.eval('document.body.className.replace(/\bnight_mode\b/g, "");')
        browser.toolbar._css = ccbc.css.browser_toolbar
        browser.toolbar.draw()

        if browser._previewWindow:
            browser._previewWindow.setStyleSheet("")
            browser._previewWeb.eval('document.body.className.replace(/\bnight_mode\b/g, "");')
            mw.reviewer._css = ccbc.css.reviewer

    def makeDark(self, browser):
        global_style = '#' + browser.form.centralwidget.objectName() + '{' + self.shared.colors + '}'
        browser.setStyleSheet(self.shared.menu + self.buttons.qt + self.style + self.basic_css + global_style)

        browser.form.tableView.setStyleSheet(self.table)
        browser.form.tableView.horizontalHeader().setStyleSheet(self.table_header)

        browser.form.searchEdit.setStyleSheet(self.search_box)
        browser.form.searchEdit.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToMinimumContentsLength)

        browser.form.searchButton.setText("")
        browser.form.searchButton.setStyleSheet(self.search_button)

        browser.sidebarTree.setStyleSheet(self.style)

        #Added for ccbc qt4 port
        browser.toolbar.web.eval('document.body.className+=" night_mode";')
        browser.toolbar._css = ccbc.css.browser_toolbar + self.shared.top
        browser.toolbar.draw()

        if browser._previewWindow:
            return self._renderPreview(browser)

    # @wraps
    # def onContextMenu(self, browser, _point):
        # browser.rClickMenu.setStyleSheet("background-color:red;")
        # browser.rClickMenu.popup.setStyleSheet("background-color:red;")

    @wraps(position='around')
    def _renderPreview(self, browser, cardChanged=False, _old=None):
        state = self.config.state_on
        if state and browser._previewWindow:
            # self.app.take_care_of_night_class(web_object=browser._previewWeb)
            browser._previewWindow.setStyleSheet(self.shared.menu+self.style)
            browser._previewWeb.eval('document.body.className+=" night_mode";')
            global_style = '.card {' + self.shared.colors + '}'
            mw.reviewer._css = self.shared.body_colors + global_style
        else:
            mw.reviewer._css = ccbc.css.reviewer
        if _old:
            return _old(browser, cardChanged)

    @wraps(position='around')
    def _cardInfoData(self, browser, _old):
        rep, cs = _old(browser)

        state = self.config.state_on
        if state and self.config.enable_in_dialogs:
            rep += style_tag("""
                *
                {
                    """ + self.shared.colors + """
                }
                div
                {
                    border-color:#fff!important
                }
                """ + self.shared.colors_replacer + """
                """)
        return rep, cs

    @css
    def style(self):
        return """
        QSplitter::handle
        {
            /* handled below as QWidget */
        }
        #""" + from_utf8("widget") + """, QTreeView
        {
            """ + self.shared.colors + """
        }
        QTreeView::item:selected:active, QTreeView::branch:selected:active
        {
            color: """ + self.config.color_t + """;
            background-color:""" + self.config.color_a + """
        }
        QTreeView::item:selected:!active, QTreeView::branch:selected:!active
        {
            color: """ + self.config.color_t + """;
            background-color:""" + self.config.color_a + """
        }
        """ + (
            """
            /* make the splitter light-dark (match all widgets as selecting with QSplitter does not work) */
            QWidget{
                background-color: """ + self.config.color_s + """;
                color: """ + self.config.color_t + """;
            }
            /* make sure that no other important widgets - like tags box - are light-dark */
            QGroupBox{
                background-color: """ + self.config.color_b + """;
            }
            """
            if self.config.style_scroll_bars else
            ''
        )

    @css
    def table(self):
        return f"""
            QTableView
            {{
                selection-color: {self.config.color_t};
                alternate-background-color: {self.config.color_s};
                gridline-color: {self.config.color_s};
                {self.shared.colors}
                selection-background-color: {self.config.color_a}
            }}
            """

    @css
    def table_header(self):
        return """
            QHeaderView, QHeaderView::section
            {
                """ + self.shared.colors + """
                border:1px solid """ + self.config.color_s + """
            }
            """

    @css
    def search_box(self):
        return """
        QComboBox
        {
            border:1px solid """ + self.config.color_s + """;
            border-radius:3px;
            padding:0px 4px;
            """ + self.shared.colors + """
        }

        QComboBox:!editable
        {
            background:""" + self.config.color_a + """
        }

        QComboBox QAbstractItemView
        {
            border:1px solid #111;
            """ + self.shared.colors + """
            background:#444
        }

        QComboBox::drop-down, QComboBox::drop-down:editable
        {
            """ + self.shared.colors + """
            width:24px;
            border-left:1px solid #444;
            border-top-right-radius:3px;
            border-bottom-right-radius:3px;
            background:qlineargradient(x1: 0.0, y1: 0.0, x2: 0.0, y2: 1.0, radius: 1, stop: 0.03 #3D4850, stop: 0.04 #313d45, stop: 1 #232B30);
        }

        QComboBox::down-arrow
        {
            top:1px;
            image: url('""" + self.app.icons.arrow + """')
        }
        """

    @css
    def search_button(self):
        return """
        QPushButton
        {
            width: 16px;
            image: url('""" + self.app.icons.search + """');
        }
        """





class AddCardsStyler(Styler):

    target = AddCards
    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle,
    }

    @wraps
    def init(self, add_cards, mw):
        state = self.config.state_on
        self.changeToNightMode(
            add_cards,
            state and self.config.enable_in_dialogs
        )

    @wraps
    def changeToNightMode(self, add_cards, b):
        if not self.config.enable_in_dialogs:
            return
        try:
            if b:
                self.makeDark(add_cards)
            else:
                self.makeLight(add_cards)
        except RuntimeError:
            pass

    def makeLight(self, add_cards):
            add_cards.setStyleSheet("")
            # style add/history button
            add_cards.form.buttonBox.setStyleSheet("")
            self.set_style_to_objects_inside(add_cards.form.horizontalLayout, "")
            # style the single line which has some bright color
            add_cards.form.line.setStyleSheet("")
            add_cards.form.fieldsArea.setAutoFillBackground(True)

            add_cards.form.fieldsArea.setStyleSheet("")

    def makeDark(self, add_cards):
            add_cards.setStyleSheet(self.buttons.qt + self.dialog.style)
            # style add/history button
            add_cards.form.buttonBox.setStyleSheet(self.buttons.qt)
            self.set_style_to_objects_inside(add_cards.form.horizontalLayout, self.buttons.qt)
            # style the single line which has some bright color
            add_cards.form.line.setStyleSheet('#' + from_utf8('line') + '{border: 0px solid #333}')
            add_cards.form.fieldsArea.setAutoFillBackground(False)

    @staticmethod
    def set_style_to_objects_inside(layout, style):
        for widget in iterate_widgets(layout):
            widget.setStyleSheet(style)


class EditCurrentStyler(Styler):

    target = EditCurrent
    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle,
    }

    @wraps
    def init(self, edit_current, mw):
        state = self.config.state_on
        self.changeToNightMode(
            edit_current,
            state and self.config.enable_in_dialogs
        )

    @wraps
    def changeToNightMode(self, edit_current, b):
        if not self.config.enable_in_dialogs:
            return
        try:
            if b:
                self.makeDark(edit_current)
            else:
                self.makeLight(edit_current)
        except RuntimeError:
            pass

    def makeLight(self, edit_current):
            edit_current.setStyleSheet("")
            edit_current.form.buttonBox.setStyleSheet("")
            edit_current.form.fieldsArea.setStyleSheet("")

    def makeDark(self, edit_current):
            edit_current.setStyleSheet(self.buttons.qt + self.dialog.style)
            edit_current.form.fieldsArea.setStyleSheet(self.buttons.qt)
            edit_current.form.buttonBox.setStyleSheet(self.buttons.qt)




class ProgressStyler(Styler):

    target = None
    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle
    }

    def init(self, progress, *args, **kwargs):
        state = self.config.state_on
        if state and self.config.enable_in_dialogs:
            progress.setStyleSheet(self.buttons.qt + self.dialog.style)


if hasattr(ProgressManager, 'ProgressNoCancel'):
    # before beta 31
    class LegacyProgressStyler(Styler):

        target = None
        require = {
            SharedStyles,
            DialogStyle,
            ButtonsStyle
        }

        def init(self, progress, label='', *args, **kwargs):
            state = self.config.state_on
            if state and self.config.enable_in_dialogs:
                # Set label and its styles explicitly (otherwise styling does not work)
                label = aqt.QLabel(label)
                progress.setLabel(label)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet(self.dialog.style)

                progress.setStyleSheet(self.buttons.qt + self.dialog.style)

    class ProgressNoCancel(Styler):

        target = ProgressManager.ProgressNoCancel
        require = {LegacyProgressStyler}

        # so this bit is required to enable init wrapping of Qt objects
        def init(cls, label='', *args, **kwargs):
            if self.config.state_on:
                aqt.QProgressDialog.__init__(cls, label, *args, **kwargs)

        target.__init__ = init

        @wraps
        def init(self, progress, *args, **kwargs):
            if self.config.state_on:
                self.legacy_progress_styler.init(progress, *args, **kwargs)


    class ProgressCancelable(Styler):

        target = ProgressManager.ProgressCancellable
        require = {LegacyProgressStyler}

        @wraps
        def init(self, progress, *args, **kwargs):
            if self.config.state_on:
                self.legacy_progress_styler.init(progress, *args, **kwargs)

else:
    # beta 31 or newer

    class ProgressDialog(Styler):

        target = ProgressManager.ProgressDialog
        require = {ProgressStyler}

        @wraps
        def init(self, progress, *args, **kwargs):
            if self.config.state_on:
                self.progress_styler.init(progress, *args, **kwargs)


class StatsWindowStyler(Styler):

    target = DeckStats

    require = {
        DialogStyle,
        ButtonsStyle
    }

    @wraps
    def init(self, stats, *args, **kwargs):
        state = self.config.state_on
        self.changeToNightMode(
            stats,
            state and self.config.enable_in_dialogs
        )

    @wraps
    def changeToNightMode(self, stats, b):
        if not self.config.enable_in_dialogs:
            return
        try:
            if b:
                css = self.buttons.qt + self.dialog.style
                stats.setStyleSheet(css)
            else:
                stats.setStyleSheet(ccbc.css.stats)

            mw.progress.start(immediate=True)
            try:
                stats._refresh()
            finally:
                stats.refreshLock = False
                mw.progress.finish()
        except RuntimeError:
            pass



class StatsReportStyler(Styler):

    target = CollectionStats

    require = {
        SharedStyles,
        DialogStyle
    }

    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def css(self):
        return (
            self.shared.user_color_map + self.shared.body_colors + """
            body{background-image: none}
            """
        )


class EditorStyler(Styler):

    target = Editor

    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle
    }

    # TODO: this would make more sense if we add some styling to .editor-btn
    def _addButton(self, editor, icon, command, *args, **kwargs):
        original_function = kwargs.pop('_old')
        button = original_function(editor, icon, command, *args, **kwargs)
        return button.replace('<button>', '<button class="editor-btn">')

    @wraps
    def init(self, editor, mw, widget, parentWindow, addMode=False):
        self.tagWidget = widget
        state = self.config.state_on
        if state and self.config.enable_in_dialogs:

            editor_css = self.dialog.style + self.buttons.qt

            editor_css += '#' + widget.objectName() + '{' + self.shared.colors + '}'

            editor.parentWindow.setStyleSheet(editor_css)

            editor.tags.completer.popup().setStyleSheet(self.completer)

            widget.setStyleSheet(
                self.qt_mid_buttons +
                self.buttons.advanced_qt(restrict_to='#' + self.encode_class_name('fields')) +
                self.buttons.advanced_qt(restrict_to='#' + self.encode_class_name('layout'))
            )

    @staticmethod
    def encode_class_name(string):
        return "ID"+"".join(map(str, map(ord, string)))

    @css
    def completer(self):
        return """
            background-color:#151515;
            border-color:#444;
            color:#eee;
        """

    @css
    def qt_mid_buttons(self):
        return f"""
        QLineEdit
        {{
            {self.completer}
        }}
        """


class TagEditStyler(Styler):

    target = TagEdit
    require = {
        SharedStyles,
    }

    @wraps
    def init(self, tag_edit, *args, **kwargs):
        state = self.config.state_on
        self.changeToNightMode(
            tag_edit,
            state and self.config.enable_in_dialogs
        )

    @wraps
    def changeToNightMode(self, tag_edit, b):
        if not self.config.enable_in_dialogs:
            return
        try:
            if b:
                tag_edit.setStyleSheet(self.completer)
            else:
                tag_edit.setStyleSheet("")
        except RuntimeError:
            pass

    @css
    def completer(self):
        return """
            background-color:#151515;
            border-color:#444;
            color:#eee;
        """


class CardLayoutStyler(Styler):
    """Card Types modal window"""

    target = CardLayout
    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle
    }

    @wraps
    def init(self, card_layout, *args, **kwargs):
        state = self.config.state_on
        if state and self.config.enable_in_dialogs:
            card_layout.mainArea.setStyleSheet(self.qt_style)

    @wraps
    def setupTabs(self, card_layout, *args, **kwargs):
        state = self.config.state_on
        if state and self.config.enable_in_dialogs:
            card_layout.tabs.setStyleSheet(self.qt_style)
            card_layout.setStyleSheet(
                self.buttons.qt + self.dialog.style +
                'QDialog, QCheckBox, QLabel, QTimeEdit{' + self.shared.colors + '}'
            )

    @css
    def qt_style(self):
        return f"""
        QGroupBox::title
        {{
            {self.shared.colors}
        }}
        QTextEdit
        {{
            color: {self.config.color_t};
            background-color: {self.config.color_s}
        }}
        """


class EditorWebViewStyler(Styler):

    target = editor
    require = {
        ButtonsStyle,
        ImageStyle,
        LatexStyle
    }

    # TODO: currently restart is required for this to take effect after configuration change
    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def _html(self):
        state = self.config.state_on
        if state and self.config.enable_in_dialogs:

            custom_css = f"""
            #topbuts {self.buttons.html}
            #topbutsright button
            {{
                padding: inherit;
                margin-left: 1px
            }}
            #topbuts img
            {{
                filter: invert(1);
                -webkit-filter: invert(1)
            }}
            a
            {{
                color: 00BBFF
            }}
            html, body, #topbuts, .field, .fname, #topbutsOuter
            {{
                color: {self.config.color_t}!important;
                background: {self.config.color_b}!important
            }}
            """

            if self.config.invert_image:
                custom_css += ".field " + self.image.invert
            if self.config.invert_latex:
                custom_css += ".field " + self.latex.invert

            return custom_css
        return ''



# .gui.AddonDialog, not part of aqt
class AddonDialogStyler(Styler):

    target = AddonDialog
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps
    def init(self, window, *args, **kwargs):
        state = self.config.state_on
        if state and self.config.enable_in_dialogs:
            self.style(window)

    def style(self, window):
        window.setStyleSheet(
            self.buttons.qt +
            'QDialog, QCheckBox, QLabel, QTimeEdit, QTextBrowser{' + self.shared.colors + '}'
        )
