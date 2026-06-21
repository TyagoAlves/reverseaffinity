import json
import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QColorDialog, QListWidget, QListWidgetItem,
    QSpinBox, QGridLayout, QToolButton, QAbstractItemView,
    QMenu, QLineEdit,
)
from ..i18n import _


class ColorSwatch(QPushButton):
    colorPicked = pyqtSignal(QColor)

    def __init__(self, color=QColor(0, 0, 0), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._pick)

    def _update_style(self):
        r, g, b = self._color.red(), self._color.green(), self._color.blue()
        lum = (r * 299 + g * 587 + b * 114) / 1000
        border = "#333" if lum > 128 else "#999"
        self.setStyleSheet(
            f"background-color: {self._color.name()}; "
            f"border: 2px solid {border}; border-radius: 4px;"
        )

    def set_color(self, c):
        self._color = c
        self._update_style()

    def color(self):
        return self._color

    def _pick(self):
        d = QColorDialog(self._color, self)
        d.setWindowTitle(_("Select Color"))
        d.setOptions(QColorDialog.DontUseNativeDialog)
        d.setStyleSheet("""
            QColorDialog { background-color: #1a1a1a; color: #e0e0e0; }
            QColorDialog QLabel { color: #c0c0c0; }
            QColorDialog QSpinBox { background: #222; color: #d0d0d0; border: 1px solid #444; }
            QColorDialog QLineEdit { background: #222; color: #d0d0d0; border: 1px solid #444; }
            QColorDialog QPushButton { background: #333; color: #d0d0d0; border: 1px solid #555; padding: 4px 12px; border-radius: 3px; }
            QColorDialog QPushButton:hover { background: #444; }
            QColorDialog QComboBox { background: #222; color: #d0d0d0; border: 1px solid #444; }
            QColorDialog QComboBox QAbstractItemView { background: #222; color: #d0d0d0; selection-background-color: #3a8ac4; }
        """)
        if d.exec_() == QColorDialog.Accepted:
            c = d.selectedColor()
            self._color = c
            self._update_style()
            self.colorPicked.emit(c)


class ColorPanel(QWidget):
    colorChanged = pyqtSignal(QColor)
    bgColorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        swatch_row = QHBoxLayout()
        swatch_row.addWidget(QLabel(_("FG:")))
        self.fg = ColorSwatch(QColor(0, 0, 0))
        swatch_row.addWidget(self.fg)
        swatch_row.addWidget(QLabel(_("BG:")))
        self.bg = ColorSwatch(QColor(255, 255, 255))
        swatch_row.addWidget(self.bg)
        swap_btn = QPushButton("\u2194")
        swap_btn.setFixedSize(24, 24)
        swap_btn.clicked.connect(self._swap)
        swatch_row.addWidget(swap_btn)
        layout.addLayout(swatch_row)

        self.fg.colorPicked.connect(lambda c: self.colorChanged.emit(c))
        self.bg.colorPicked.connect(lambda c: self.bgColorChanged.emit(c))

        grid = QGridLayout()
        grid.setSpacing(2)

        self.r_spin = self._spin(0, 255)
        self.g_spin = self._spin(0, 255)
        self.b_spin = self._spin(0, 255)
        self.h_spin = self._spin(0, 360)
        self.s_spin = self._spin(0, 100)
        self.l_spin = self._spin(0, 100)
        self.hex_edit = QLineEdit("000000")
        self.hex_edit.setMaxLength(6)
        self.hex_edit.textChanged.connect(self._hex_changed)

        grid.addWidget(QLabel("R:"), 0, 0); grid.addWidget(self.r_spin, 0, 1)
        grid.addWidget(QLabel("G:"), 1, 0); grid.addWidget(self.g_spin, 1, 1)
        grid.addWidget(QLabel("B:"), 2, 0); grid.addWidget(self.b_spin, 2, 1)
        grid.addWidget(QLabel("H:"), 3, 0); grid.addWidget(self.h_spin, 3, 1)
        grid.addWidget(QLabel("S:"), 4, 0); grid.addWidget(self.s_spin, 4, 1)
        grid.addWidget(QLabel("L:"), 5, 0); grid.addWidget(self.l_spin, 5, 1)
        grid.addWidget(QLabel("#"), 6, 0); grid.addWidget(self.hex_edit, 6, 1)

        layout.addLayout(grid)

        for s in [self.r_spin, self.g_spin, self.b_spin]:
            s.valueChanged.connect(self._rgb_changed)
        for s in [self.h_spin, self.s_spin, self.l_spin]:
            s.valueChanged.connect(self._hsl_changed)

        self._updating = False

    def _spin(self, lo, hi):
        s = QSpinBox()
        s.setRange(lo, hi)
        s.setFixedHeight(20)
        return s

    def _swap(self):
        fg, bg = self.fg.color(), self.bg.color()
        self.fg.set_color(bg)
        self.bg.set_color(fg)
        self.colorChanged.emit(self.fg.color())
        self.bgColorChanged.emit(self.bg.color())

    def _rgb_changed(self):
        if self._updating:
            return
        c = QColor(self.r_spin.value(), self.g_spin.value(), self.b_spin.value())
        self._sync_fg(c)
        self.colorChanged.emit(c)

    def _hsl_changed(self):
        if self._updating:
            return
        c = QColor()
        c.setHsl(self.h_spin.value(), self.s_spin.value(), self.l_spin.value())
        self._sync_fg(c)
        self.colorChanged.emit(c)

    def _hex_changed(self, text):
        if self._updating:
            return
        if len(text) == 6:
            try:
                c = QColor(f"#{text}")
                if c.isValid():
                    self._sync_fg(c)
                    self.colorChanged.emit(c)
            except Exception:
                pass

    def _sync_fg(self, c):
        self._updating = True
        self.r_spin.setValue(c.red())
        self.g_spin.setValue(c.green())
        self.b_spin.setValue(c.blue())
        self.h_spin.setValue(max(0, c.hue()))
        self.s_spin.setValue(c.saturation())
        self.l_spin.setValue(c.lightness())
        self.hex_edit.setText(c.name().lstrip("#"))
        self._updating = False
        self.fg.set_color(c)

    def set_color(self, c):
        self._sync_fg(c)

    def set_bg_color(self, c):
        self.bg.set_color(c)


class SwatchesPanel(QWidget):
    colorSelected = pyqtSignal(QColor)
    bgColorSelected = pyqtSignal(QColor)

    def __init__(self, canvas_getter=None, parent=None):
        super().__init__(parent)
        self.canvas_getter = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel(_("Click: FG  |  Right-click: BG")))
        layout.addLayout(mode_row)

        self._swatches = [
            ["#000000", "Black"], ["#434343", "Dark Gray 3"], ["#666666", "Dark Gray 2"],
            ["#999999", "Dark Gray 1"], ["#b7b7b7", "Gray"], ["#cccccc", "Light Gray 1"],
            ["#d9d9d9", "Light Gray 2"], ["#efefef", "Light Gray 3"], ["#f3f3f3", "Light Gray 4"],
            ["#ffffff", "White"],
            ["#d9d9d9", "Gray 10%"], ["#bfbfbf", "Gray 20%"], ["#a6a6a6", "Gray 30%"],
            ["#8c8c8c", "Gray 40%"], ["#737373", "Gray 50%"], ["#595959", "Gray 60%"],
            ["#404040", "Gray 70%"], ["#262626", "Gray 80%"], ["#0d0d0d", "Gray 90%"],
            ["#ff0000", "Red"], ["#ff6600", "Orange"], ["#ffff00", "Yellow"],
            ["#00ff00", "Green"], ["#00ffff", "Cyan"], ["#0066ff", "Blue"],
            ["#6600ff", "Purple"], ["#ff00ff", "Magenta"], ["#cc0066", "Pink"],
            ["#ffcccc", "Light Red"], ["#ffcc99", "Light Orange"], ["#ffffcc", "Light Yellow"],
            ["#ccffcc", "Light Green"], ["#ccffff", "Light Cyan"], ["#99ccff", "Light Blue"],
            ["#cc99ff", "Light Purple"], ["#ffccff", "Light Magenta"],
            ["#993300", "Brown"], ["#669900", "Olive"], ["#003366", "Dark Blue"],
            ["#330066", "Dark Purple"], ["#660033", "Dark Red"],
        ]

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        layout.addLayout(self.grid_layout)

        self._rebuild_grid()

        btn_row = QHBoxLayout()
        add_btn = QPushButton(_("Add to Swatches"))
        add_btn.clicked.connect(self._add_foreground)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)

        file_row = QHBoxLayout()
        save_btn = QPushButton(_("Save Swatches"))
        save_btn.clicked.connect(self._save_swatches)
        file_row.addWidget(save_btn)
        load_btn = QPushButton(_("Load Swatches"))
        load_btn.clicked.connect(self._load_swatches)
        file_row.addWidget(load_btn)
        layout.addLayout(file_row)

        layout.addStretch()

    def _rebuild_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, (hex_color, name) in enumerate(self._swatches):
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setToolTip(name)
            btn.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #333; "
                f"border-radius: 2px;"
            )
            r, c = divmod(i, 9)
            btn.clicked.connect(lambda checked, h=hex_color: self._select_color(h, False))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, btn=btn, h=hex_color: self._show_swatch_menu(btn, pos, h)
            )
            self.grid_layout.addWidget(btn, r, c)

    def _show_swatch_menu(self, btn, pos, hex_color):
        menu = QMenu(self)
        menu.addAction(_("Set as Foreground"), lambda: self._select_color(hex_color, False))
        menu.addAction(_("Set as Background"), lambda: self._select_color(hex_color, True))
        menu.addSeparator()
        menu.addAction(_("Delete Swatch"), lambda: self._delete_swatch(hex_color))
        menu.exec_(btn.mapToGlobal(pos))

    def _delete_swatch(self, hex_color):
        for i, (h, n) in enumerate(self._swatches):
            if h == hex_color:
                del self._swatches[i]
                break
        self._rebuild_grid()

    def _add_foreground(self):
        if self.canvas_getter:
            canvas = self.canvas_getter()
            if canvas:
                c = canvas.tool_color
                hex_color = c.name()
                for h, n in self._swatches:
                    if h == hex_color:
                        return
                self._swatches.append([hex_color, hex_color])
                self._rebuild_grid()

    def _select_color(self, hex_color, is_bg=False):
        c = QColor(hex_color)
        if c.isValid():
            if is_bg:
                self.bgColorSelected.emit(c)
            else:
                self.colorSelected.emit(c)

    def _save_swatches(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "reverseaffinity")
        os.makedirs(config_dir, exist_ok=True)
        path = os.path.join(config_dir, "swatches.json")
        with open(path, "w") as f:
            json.dump(self._swatches, f)

    def _load_swatches(self):
        config_dir = os.path.join(os.path.expanduser("~"), ".config", "reverseaffinity")
        path = os.path.join(config_dir, "swatches.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                if isinstance(data, list):
                    self._swatches = data
                    self._rebuild_grid()


class ChannelsPanel(QWidget):
    channelSelectionChanged = pyqtSignal(list)

    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        layout.addWidget(QLabel(_("Channels:")), 0, Qt.AlignLeft)

        self.channels = [
            {"name": "RGB", "color": None, "visible": True, "selected": True},
            {"name": "Red",   "color": "#ff0000", "visible": True, "selected": False},
            {"name": "Green", "color": "#00ff00", "visible": True, "selected": False},
            {"name": "Blue",  "color": "#0000ff", "visible": True, "selected": False},
        ]

        self._rows = []
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setSpacing(1)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.currentRowChanged.connect(self._selection_changed)
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton(_("Load as Selection"))
        self.load_btn.clicked.connect(self._load_selection)
        btn_row.addWidget(self.load_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def refresh(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for i, ch in enumerate(self.channels):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, i)

            widget = QWidget()
            h = QHBoxLayout(widget)
            h.setContentsMargins(2, 1, 2, 1)
            h.setSpacing(4)

            vis_btn = QToolButton()
            vis_btn.setFixedSize(18, 18)
            vis_btn.setText("\U0001f441" if ch["visible"] else " ")
            vis_btn.setToolTip(_("Toggle channel visibility"))
            vis_btn.clicked.connect(lambda checked, c=ch: self._toggle_visibility(c))
            h.addWidget(vis_btn)

            color_box = QLabel()
            color_box.setFixedSize(14, 14)
            if ch["color"]:
                color_box.setStyleSheet(
                    f"background-color: {ch['color']}; border: 1px solid #555; border-radius: 2px;"
                )
            else:
                color_box.setStyleSheet(
                    "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                    "stop:0 #ff0000, stop:0.33 #00ff00, stop:0.66 #0000ff, stop:1 #ffffff);"
                    "border: 1px solid #555; border-radius: 2px;"
                )
            h.addWidget(color_box)

            name_label = QLabel(ch["name"])
            h.addWidget(name_label, 1)

            if ch["name"] != "RGB":
                icon_label = QLabel("\U0001f441" if ch["visible"] else " ")
                icon_label.setFixedSize(14, 14)
                h.addWidget(icon_label)

            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        self.list_widget.blockSignals(False)

    def _toggle_visibility(self, ch):
        if ch["name"] == "RGB":
            return
        ch["visible"] = not ch["visible"]
        self.refresh()
        canvas = self.get_canvas()
        if canvas:
            canvas._refresh()

    def _selection_changed(self, row):
        for i, ch in enumerate(self.channels):
            ch["selected"] = (i == row)
        self.channelSelectionChanged.emit([c["name"] for c in self.channels if c["selected"]])

    def _load_selection(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        ch = self.channels[row]
        canvas = self.get_canvas()
        if not canvas or not canvas.layer_stack.active:
            return
        path = QPainterPath()
        if canvas.selection_path and not canvas.selection_path.isEmpty():
            path = canvas.selection_path
        else:
            w = canvas.layer_stack.active.image.width()
            h = canvas.layer_stack.active.image.height()
            path.addRect(0, 0, w, h)
        canvas.selection_path = path
        canvas.selection_mask = None
        canvas._refresh()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        row = item.data(Qt.UserRole)
        if row < 0:
            return
        ch = self.channels[row]
        menu = QMenu(self)
        if ch["name"] not in ("RGB",):
            vis_action = menu.addAction(
                _("Hide Channel") if ch["visible"] else _("Show Channel")
            )
            del_action = menu.addAction(_("Delete Channel"))
        else:
            menu.addAction(_("Duplicate Channel"))

        action = menu.exec_(self.list_widget.viewport().mapToGlobal(pos))
        if ch["name"] not in ("RGB",):
            if action == vis_action:
                self._toggle_visibility(ch)
            elif action == del_action:
                self._delete_channel(row)

    def _delete_channel(self, row):
        if 0 <= row < len(self.channels):
            ch = self.channels[row]
            if ch["name"] != "RGB":
                del self.channels[row]
                self.refresh()
                canvas = self.get_canvas()
                if canvas:
                    canvas._refresh()

    def visible_channels(self):
        return [c["name"] for c in self.channels if c["visible"]]

    def active_channels(self):
        return [c["name"] for c in self.channels if c["selected"]]
