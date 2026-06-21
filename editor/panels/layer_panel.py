from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QComboBox, QListWidget, QListWidgetItem,
    QToolButton, QAbstractItemView, QInputDialog, QMenu, QPushButton,
)
from ..layers import BLEND_MODES, AdjustmentLayer, GroupLayer
from ..i18n import _, get_translator


class LayerPanel(QWidget):
    layerChanged = pyqtSignal(int)

    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        mode_row = QHBoxLayout()
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(BLEND_MODES)
        self.blend_combo.setMinimumWidth(100)
        self.blend_combo.currentTextChanged.connect(self._blend_changed)
        mode_row.addWidget(self.blend_combo, 1)
        layout.addLayout(mode_row)

        props_row = QHBoxLayout()
        props_row.setSpacing(2)

        self.opacity_label = QLabel(_("Opacity:"))
        self.opacity_label.setFixedWidth(42)
        props_row.addWidget(self.opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._opacity_changed)
        props_row.addWidget(self.opacity_slider, 1)

        self.opacity_value = QLabel("100%")
        self.opacity_value.setFixedWidth(32)
        self.opacity_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        props_row.addWidget(self.opacity_value)

        layout.addLayout(props_row)

        fill_row = QHBoxLayout()
        fill_row.setSpacing(2)

        self.fill_label = QLabel(_("Fill:"))
        self.fill_label.setFixedWidth(42)
        fill_row.addWidget(self.fill_label)

        self.fill_slider = QSlider(Qt.Horizontal)
        self.fill_slider.setRange(0, 100)
        self.fill_slider.setValue(100)
        self.fill_slider.valueChanged.connect(self._fill_changed)
        fill_row.addWidget(self.fill_slider, 1)

        self.fill_value = QLabel("100%")
        self.fill_value.setFixedWidth(32)
        self.fill_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fill_row.addWidget(self.fill_value)

        layout.addLayout(fill_row)

        lock_row = QHBoxLayout()
        lock_row.setSpacing(2)

        self.lock_tp_btn = self._lock_button("\u25fb", _("Lock transparent pixels"))
        self.lock_tp_btn.clicked.connect(lambda: self._toggle_lock("transparent"))
        lock_row.addWidget(self.lock_tp_btn)

        self.lock_ip_btn = self._lock_button("\u270e", _("Lock image pixels"))
        self.lock_ip_btn.clicked.connect(lambda: self._toggle_lock("image"))
        lock_row.addWidget(self.lock_ip_btn)

        self.lock_pos_btn = self._lock_button("\u21f1", _("Lock position"))
        self.lock_pos_btn.clicked.connect(lambda: self._toggle_lock("position"))
        lock_row.addWidget(self.lock_pos_btn)

        self.lock_all_btn = self._lock_button("\U0001f512", _("Lock all"))
        self.lock_all_btn.clicked.connect(lambda: self._toggle_lock("all"))
        lock_row.addWidget(self.lock_all_btn)

        lock_row.addStretch()
        layout.addLayout(lock_row)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.currentRowChanged.connect(self._row_changed)
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.setSpacing(1)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget, 1)

        action_row = QHBoxLayout()
        action_row.setSpacing(1)

        self.link_btn = self._action_button("\U0001f517", _("Link layers"))
        action_row.addWidget(self.link_btn)

        self.fx_btn = self._action_button("fx", _("Layer styles"))
        self.fx_btn.setStyleSheet("font-weight: bold; font-style: italic;")
        action_row.addWidget(self.fx_btn)

        self.mask_btn = self._action_button("\u25d0", _("Add layer mask"))
        self.mask_btn.clicked.connect(self._add_mask)
        action_row.addWidget(self.mask_btn)

        self.adj_btn = self._action_button("\u25cf", _("New fill/adjustment layer"))
        self._setup_adj_menu()
        action_row.addWidget(self.adj_btn)

        self.group_btn = self._action_button("\U0001f4c1", _("New group"))
        self.group_btn.clicked.connect(self._add_group)
        action_row.addWidget(self.group_btn)

        action_row.addStretch()

        self.add_btn = self._action_button("\uff0b", _("New layer"))
        self.add_btn.clicked.connect(self._add_layer)
        action_row.addWidget(self.add_btn)

        self.del_btn = self._action_button("\U0001f5d1", _("Delete layer"))
        self.del_btn.clicked.connect(self._del_layer)
        action_row.addWidget(self.del_btn)

        layout.addLayout(action_row)

        get_translator().language_changed.connect(self.retranslate)

    def _lock_button(self, text, tooltip):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setFixedSize(24, 22)
        btn.setStyleSheet(
            "QToolButton { border: 1px solid #333; border-radius: 2px; padding: 1px; }"
            "QToolButton:checked { background-color: #444; border: 1px solid #f97316; }"
        )
        return btn

    def _action_button(self, text, tooltip):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(24, 22)
        btn.setStyleSheet(
            "QToolButton { border: none; border-radius: 2px; padding: 1px; }"
            "QToolButton:hover { background-color: #333; }"
        )
        return btn

    def _setup_adj_menu(self):
        self.adj_menu = QMenu(self)
        self.adj_menu.addAction(_("Brightness/Contrast"), lambda: self._add_adj("brightness_contrast"))
        self.adj_menu.addAction(_("Hue/Saturation"), lambda: self._add_adj("hsl"))
        self.adj_menu.addAction(_("Levels"), lambda: self._add_adj("levels"))
        self.adj_menu.addSeparator()
        self.adj_menu.addAction(_("Solid Color..."), lambda: self._add_adj("solid_color"))
        self.adj_menu.addAction(_("Gradient..."), lambda: self._add_adj("gradient"))
        self.adj_btn.setMenu(self.adj_menu)
        self.adj_btn.setPopupMode(QToolButton.InstantPopup)

    def retranslate(self):
        self.blend_combo.blockSignals(True)
        self.blend_combo.clear()
        self.blend_combo.addItems([_(m) for m in BLEND_MODES])
        self.blend_combo.blockSignals(False)
        self.opacity_label.setText(_("Opacity:"))
        self.fill_label.setText(_("Fill:"))
        self.lock_tp_btn.setToolTip(_("Lock transparent pixels"))
        self.lock_ip_btn.setToolTip(_("Lock image pixels"))
        self.lock_pos_btn.setToolTip(_("Lock position"))
        self.lock_all_btn.setToolTip(_("Lock all"))
        self.link_btn.setToolTip(_("Link layers"))
        self.fx_btn.setToolTip(_("Layer styles"))
        self.mask_btn.setToolTip(_("Add layer mask"))
        self.adj_btn.setToolTip(_("New fill/adjustment layer"))
        self.group_btn.setToolTip(_("New group"))
        self.add_btn.setToolTip(_("New layer"))
        self.del_btn.setToolTip(_("Delete layer"))

    def _make_layer_item_widget(self, i, layer):
        widget = QWidget()
        h = QHBoxLayout(widget)
        h.setContentsMargins(2, 1, 2, 1)
        h.setSpacing(4)

        thumb = QLabel()
        thumb.setFixedSize(32, 32)
        thumb.setScaledContents(True)
        thumb.setStyleSheet("border: 1px solid #333; border-radius: 1px;")
        try:
            thumb_img = layer.image.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb.setPixmap(QPixmap.fromImage(thumb_img))
        except Exception:
            pass
        h.addWidget(thumb)

        vis_btn = QToolButton()
        vis_btn.setFixedSize(18, 18)
        vis_btn.setText("\U0001f441" if layer.visible else " ")
        vis_btn.setToolTip(_("Toggle visibility"))
        vis_btn.clicked.connect(lambda checked, idx=i: self._toggle_visibility(idx))
        h.addWidget(vis_btn)

        name_label = QLabel(layer.name)
        name_label.setFixedHeight(22)
        if isinstance(layer, AdjustmentLayer):
            name_label.setText(f"\u26a1 {layer.name}")
        elif isinstance(layer, GroupLayer):
            name_label.setText(f"\U0001f4c1 {layer.name}")
        name_label.setStyleSheet("padding: 0px 2px;")
        h.addWidget(name_label, 1)

        return widget

    def refresh(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for i, layer in enumerate(canvas.layer_stack.layers):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, i)
            widget = self._make_layer_item_widget(i, layer)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
        if 0 <= canvas.layer_stack.active_index < self.list_widget.count():
            self.list_widget.setCurrentRow(canvas.layer_stack.active_index)
        self.list_widget.blockSignals(False)

        active = canvas.layer_stack.active
        if active:
            self.blend_combo.blockSignals(True)
            idx = self.blend_combo.findText(active.blend_mode)
            if idx >= 0:
                self.blend_combo.setCurrentIndex(idx)
            self.blend_combo.blockSignals(False)
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(int(active.opacity * 100))
            self.opacity_value.setText(f"{int(active.opacity * 100)}%")
            self.opacity_slider.blockSignals(False)
            self.fill_slider.blockSignals(True)
            self.fill_slider.setValue(int(active.fill * 100))
            self.fill_value.setText(f"{int(active.fill * 100)}%")
            self.fill_slider.blockSignals(False)

            self.lock_tp_btn.blockSignals(True)
            self.lock_tp_btn.setChecked(active.locked)
            self.lock_ip_btn.blockSignals(True)
            self.lock_ip_btn.setChecked(active.locked)
            self.lock_pos_btn.blockSignals(True)
            self.lock_pos_btn.setChecked(active.locked)
            self.lock_all_btn.blockSignals(True)
            self.lock_all_btn.setChecked(active.locked)
            self.lock_tp_btn.blockSignals(False)
            self.lock_ip_btn.blockSignals(False)
            self.lock_pos_btn.blockSignals(False)
            self.lock_all_btn.blockSignals(False)

    def _toggle_visibility(self, idx):
        canvas = self.get_canvas()
        if canvas and 0 <= idx < len(canvas.layer_stack.layers):
            layer = canvas.layer_stack.layers[idx]
            layer.visible = not layer.visible
            canvas._refresh()
            self.refresh()

    def _toggle_lock(self):
        canvas = self.get_canvas()
        if not canvas or not canvas.layer_stack.active:
            return
        canvas.layer_stack.active.locked = not canvas.layer_stack.active.locked
        self.refresh()

    def _row_changed(self, row):
        canvas = self.get_canvas()
        if canvas and row >= 0:
            canvas.layer_stack.active_index = row
            canvas._refresh()
            self.refresh()

    def _blend_changed(self, mode):
        canvas = self.get_canvas()
        if canvas and canvas.layer_stack.active:
            canvas.layer_stack.active.blend_mode = mode
            canvas._refresh()

    def _opacity_changed(self, val):
        canvas = self.get_canvas()
        if canvas and canvas.layer_stack.active:
            canvas.layer_stack.active.opacity = val / 100.0
            self.opacity_value.setText(f"{val}%")
            canvas._refresh()

    def _fill_changed(self, val):
        canvas = self.get_canvas()
        if canvas and canvas.layer_stack.active:
            canvas.layer_stack.active.fill = val / 100.0
            self.fill_value.setText(f"{val}%")
            canvas._refresh()

    def _add_layer(self):
        canvas = self.get_canvas()
        if canvas:
            canvas._save_state("New layer")
            canvas.layer_stack.add_layer()
            canvas._refresh()
            self.refresh()

    def _del_layer(self):
        canvas = self.get_canvas()
        if canvas:
            idx = self.list_widget.currentRow()
            if idx >= 0:
                canvas._save_state("Delete layer")
                canvas.layer_stack.remove_layer(idx)
                canvas._refresh()
                self.refresh()

    def _add_adj(self, adj_type):
        canvas = self.get_canvas()
        if canvas:
            canvas._save_state("Add adjustment")
            canvas._add_adjustment(adj_type)
            canvas._refresh()
            self.refresh()

    def _add_group(self):
        canvas = self.get_canvas()
        if canvas:
            canvas._save_state("New group")
            canvas.layer_stack.add_group()
            canvas._refresh()
            self.refresh()

    def _add_mask(self):
        canvas = self.get_canvas()
        if canvas and canvas.layer_stack.active:
            layer = canvas.layer_stack.active
            if layer.mask is None:
                layer.reveal_all_mask()
            else:
                layer.delete_mask()
            canvas._refresh()
            self.refresh()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        idx = item.data(Qt.UserRole)
        canvas = self.get_canvas()
        if not canvas:
            return

        menu = QMenu(self)

        rename_action = menu.addAction(_("Rename Layer..."))
        menu.addSeparator()
        dup_action = menu.addAction(_("Duplicate Layer"))
        del_action = menu.addAction(_("Delete Layer"))
        menu.addSeparator()
        merge_down_action = menu.addAction(_("Merge Down"))
        merge_visible_action = menu.addAction(_("Merge Visible"))
        flatten_action = menu.addAction(_("Flatten Image"))

        action = menu.exec_(self.list_widget.viewport().mapToGlobal(pos))

        if action == rename_action:
            current_name = canvas.layer_stack.layers[idx].name
            new_name, ok = QInputDialog.getText(self, _("Rename Layer"), _("Name:"), text=current_name)
            if ok and new_name:
                canvas.layer_stack.layers[idx].name = new_name
                self.refresh()
        elif action == dup_action:
            canvas._save_state("Duplicate layer")
            canvas.layer_stack.duplicate_layer(idx)
            canvas._refresh()
            self.refresh()
        elif action == del_action:
            if len(canvas.layer_stack.layers) > 1:
                canvas._save_state("Delete layer")
                canvas.layer_stack.remove_layer(idx)
                canvas._refresh()
                self.refresh()
        elif action == merge_down_action:
            if idx > 0:
                canvas._save_state("Merge down")
                below = idx - 1
                top_img = canvas.layer_stack.layers[idx].image
                bot_img = canvas.layer_stack.layers[below].image
                p = QPainter(bot_img)
                p.drawImage(0, 0, top_img)
                p.end()
                canvas.layer_stack.remove_layer(idx)
                canvas._refresh()
                self.refresh()
        elif action == merge_visible_action:
            canvas._save_state("Merge visible")
            canvas.layer_stack.merge_visible()
            canvas._refresh()
            self.refresh()
        elif action == flatten_action:
            canvas._save_state("Flatten")
            canvas.layer_stack.flatten()
            canvas._refresh()
            self.refresh()


class HistoryPanel(QWidget):
    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.count_label = QLabel(_("History: ") + "0" + _(" entries"))
        layout.addWidget(self.count_label)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.currentRowChanged.connect(self._row_changed)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

    def refresh(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        history = canvas.history
        self.list_widget.blockSignals(True)
        cur_row = self.list_widget.currentRow()
        self.list_widget.clear()
        for i, entry in enumerate(history.stack):
            item = QListWidgetItem(entry.description)
            item.setData(Qt.UserRole, i)
            thumb = entry.get_thumbnail()
            if thumb:
                item.setIcon(QIcon(thumb))
            self.list_widget.addItem(item)
        if 0 <= history.index < self.list_widget.count():
            self.list_widget.setCurrentRow(history.index)
        self.list_widget.blockSignals(False)
        self.count_label.setText(_("History: ") + str(len(history.stack)) + _(" entries"))

    def _row_changed(self, row):
        if row < 0:
            return
        canvas = self.get_canvas()
        if not canvas:
            return
        history = canvas.history
        if row != history.index:
            history.jump_to(canvas.layer_stack, row)
            canvas._refresh()

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        idx = item.data(Qt.UserRole)
        canvas = self.get_canvas()
        if not canvas or not canvas.history:
            return
        menu = QMenu(self)
        del_action = menu.addAction(_("Delete Entry"))
        clear_action = menu.addAction(_("Clear History"))
        action = menu.exec_(self.list_widget.viewport().mapToGlobal(pos))
        if action == del_action:
            canvas.history.delete_entry(idx)
            self.refresh()
        elif action == clear_action:
            canvas.history.clear()
            self.refresh()

    def set_canvas(self, canvas_getter):
        self.get_canvas = canvas_getter
