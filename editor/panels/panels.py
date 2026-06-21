import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontDatabase, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSpinBox, QComboBox, QToolButton,
    QFrame, QListWidget, QListWidgetItem, QCheckBox, QInputDialog,
)
from ..i18n import _
from ..brushengine import load_preset, save_preset, list_presets, PRESET_DIR


class ToolOptionsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        layout.addWidget(QLabel(_("Size:")))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 5000)
        self.size_spin.setValue(3)
        self.size_spin.setFixedWidth(60)
        layout.addWidget(self.size_spin)

        layout.addWidget(QLabel(_("Opacity:")))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(1, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(80)
        layout.addWidget(self.opacity_slider)

        layout.addWidget(QLabel(_("Flow:")))
        self.flow_slider = QSlider(Qt.Horizontal)
        self.flow_slider.setRange(1, 100)
        self.flow_slider.setValue(100)
        self.flow_slider.setFixedWidth(80)
        layout.addWidget(self.flow_slider)

        layout.addWidget(QLabel(_("Font:")))
        self.font_combo = QComboBox()
        self.font_combo.addItems(QFontDatabase().families())
        self.font_combo.setCurrentText("Arial")
        self.font_combo.setFixedWidth(120)
        layout.addWidget(self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(1, 999)
        self.font_size_spin.setValue(32)
        self.font_size_spin.setFixedWidth(50)
        layout.addWidget(self.font_size_spin)

        self.bold_btn = QToolButton()
        self.bold_btn.setText(_("B"))
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedSize(24, 24)
        layout.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setText(_("I"))
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedSize(24, 24)
        layout.addWidget(self.italic_btn)

        self.underline_btn = QToolButton()
        self.underline_btn.setText(_("U"))
        self.underline_btn.setCheckable(True)
        self.underline_btn.setFixedSize(24, 24)
        layout.addWidget(self.underline_btn)

        layout.addStretch()


class NavigatorPanel(QWidget):
    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(120, 90)
        self.preview_label.setStyleSheet("""
            QLabel {
                background: #0a0a0a;
                border: 1px solid #222;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.preview_label)

        zoom_row = QHBoxLayout()
        zoom_out_btn = QPushButton("\u2212")
        zoom_out_btn.setFixedSize(24, 24)
        zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_row.addWidget(zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_row.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(24, 24)
        zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_row.addWidget(zoom_in_btn)

        fit_btn = QPushButton(_("Fit"))
        fit_btn.setFixedSize(36, 24)
        fit_btn.clicked.connect(self._zoom_fit)
        zoom_row.addWidget(fit_btn)

        layout.addLayout(zoom_row)

    def refresh(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        composite = canvas.layer_stack.composite()
        if composite and not composite.isNull():
            preview = composite.scaled(160, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(QPixmap.fromImage(preview))
        self.zoom_label.setText(f"{canvas.zoom_level * 100:.0f}%")

    def set_zoom(self, zoom):
        self.zoom_label.setText(f"{zoom * 100:.0f}%")

    def _zoom_in(self):
        canvas = self.get_canvas()
        if canvas:
            canvas.zoom_in()

    def _zoom_out(self):
        canvas = self.get_canvas()
        if canvas:
            canvas.zoom_out()

    def _zoom_fit(self):
        canvas = self.get_canvas()
        if canvas:
            canvas.zoom_fit()


class GradientPanel(QWidget):
    gradientChanged = pyqtSignal()

    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        from ..gradient_editor import GradientEditorWidget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.editor = GradientEditorWidget()
        self.editor.gradientChanged.connect(self._on_gradient_changed)
        layout.addWidget(self.editor)

    def _on_gradient_changed(self):
        canvas = self.get_canvas()
        if canvas:
            canvas.gradient_obj = self.editor.get_gradient()
        self.gradientChanged.emit()

    def refresh(self):
        canvas = self.get_canvas()
        if canvas and hasattr(canvas, 'gradient_obj'):
            self.editor.set_gradient(canvas.gradient_obj)


class BrushPanel(QWidget):
    brushSettingsChanged = pyqtSignal()

    def __init__(self, canvas_getter=None, parent=None):
        super().__init__(parent)
        self.canvas_getter = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        tip_row = QHBoxLayout()
        tip_row.addWidget(QLabel("Tip:"))
        self.tip_combo = QComboBox()
        self.tip_combo.addItems(["Circle", "Square", "Texture"])
        self.tip_combo.currentTextChanged.connect(self._on_change)
        tip_row.addWidget(self.tip_combo)
        layout.addLayout(tip_row)

        hard_row = QHBoxLayout()
        hard_row.addWidget(QLabel("Hardness:"))
        self.hardness_slider = QSlider(Qt.Horizontal)
        self.hardness_slider.setRange(0, 100)
        self.hardness_slider.setValue(100)
        self.hardness_slider.valueChanged.connect(self._on_change)
        hard_row.addWidget(self.hardness_slider)
        self.hardness_label = QLabel("100%")
        self.hardness_label.setFixedWidth(32)
        hard_row.addWidget(self.hardness_label)
        layout.addLayout(hard_row)
        self.hardness_slider.valueChanged.connect(
            lambda v: self.hardness_label.setText(f"{v}%")
        )

        space_row = QHBoxLayout()
        space_row.addWidget(QLabel("Spacing:"))
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(1, 100)
        self.spacing_slider.setValue(25)
        self.spacing_slider.valueChanged.connect(self._on_change)
        space_row.addWidget(self.spacing_slider)
        self.spacing_label = QLabel("25%")
        self.spacing_label.setFixedWidth(32)
        space_row.addWidget(self.spacing_label)
        layout.addLayout(space_row)
        self.spacing_slider.valueChanged.connect(
            lambda v: self.spacing_label.setText(f"{v}%")
        )

        flow_row = QHBoxLayout()
        flow_row.addWidget(QLabel("Flow:"))
        self.flow_slider = QSlider(Qt.Horizontal)
        self.flow_slider.setRange(1, 100)
        self.flow_slider.setValue(100)
        self.flow_slider.valueChanged.connect(self._on_change)
        flow_row.addWidget(self.flow_slider)
        self.flow_label = QLabel("100%")
        self.flow_label.setFixedWidth(32)
        flow_row.addWidget(self.flow_label)
        layout.addLayout(flow_row)
        self.flow_slider.valueChanged.connect(
            lambda v: self.flow_label.setText(f"{v}%")
        )

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(80, 80)
        self.preview_label.setStyleSheet("border: 1px solid #555; border-radius: 4px;")
        layout.addWidget(self.preview_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #333;")
        layout.addWidget(sep)

        preset_header = QLabel("Presets:")
        preset_header.setStyleSheet("font-weight: bold; color: #aaa;")
        layout.addWidget(preset_header)

        self.preset_list = QListWidget()
        self.preset_list.setFixedHeight(80)
        self.preset_list.currentRowChanged.connect(self._preset_selected)
        layout.addWidget(self.preset_list)

        preset_btn_row = QHBoxLayout()
        self.save_preset_btn = QPushButton("Save")
        self.save_preset_btn.clicked.connect(self._save_preset)
        preset_btn_row.addWidget(self.save_preset_btn)
        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self._delete_preset)
        preset_btn_row.addWidget(self.delete_preset_btn)
        layout.addLayout(preset_btn_row)

        self._brush_engine = None
        self._refresh_preset_list()

    def set_brush_engine(self, engine):
        self._brush_engine = engine
        self._sync_from_engine()

    def _sync_from_engine(self):
        if not self._brush_engine:
            return

    def _on_change(self):
        if self._brush_engine:
            tip_name = self.tip_combo.currentText()
            hardness = self.hardness_slider.value() / 100.0
            if tip_name == "Circle":
                self._brush_engine.set_circle_tip(hardness)
            elif tip_name == "Square":
                self._brush_engine.set_square_tip(hardness)
            self._brush_engine.spacing = self.spacing_slider.value() / 100.0
            self._brush_engine.flow = self.flow_slider.value() / 100.0
            self._update_preview()
        self.brushSettingsChanged.emit()

    def _update_preview(self):
        if not self._brush_engine:
            return
        pix = self._brush_engine.make_preview(60)
        self.preview_label.setPixmap(pix)

    def _current_settings(self):
        return {
            "tip": self.tip_combo.currentText(),
            "hardness": self.hardness_slider.value() / 100.0,
            "spacing": self.spacing_slider.value() / 100.0,
            "flow": self.flow_slider.value() / 100.0,
        }

    def _apply_settings(self, data):
        self.tip_combo.blockSignals(True)
        self.hardness_slider.blockSignals(True)
        self.spacing_slider.blockSignals(True)
        self.flow_slider.blockSignals(True)
        idx = self.tip_combo.findText(data.get("tip", "Circle"))
        if idx >= 0:
            self.tip_combo.setCurrentIndex(idx)
        self.hardness_slider.setValue(int(data.get("hardness", 1.0) * 100))
        self.spacing_slider.setValue(int(data.get("spacing", 0.25) * 100))
        self.flow_slider.setValue(int(data.get("flow", 1.0) * 100))
        self.tip_combo.blockSignals(False)
        self.hardness_slider.blockSignals(False)
        self.spacing_slider.blockSignals(False)
        self.flow_slider.blockSignals(False)
        self._on_change()

    def _refresh_preset_list(self):
        self.preset_list.blockSignals(True)
        self.preset_list.clear()
        for name in list_presets():
            self.preset_list.addItem(name)
        self.preset_list.blockSignals(False)

    def _preset_selected(self, row):
        if row < 0:
            return
        name = self.preset_list.item(row).text()
        data = load_preset(name)
        if data:
            self._apply_settings(data)

    def _save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            data = self._current_settings()
            data["name"] = name
            save_preset(name, data)
            self._refresh_preset_list()
            for i in range(self.preset_list.count()):
                if self.preset_list.item(i).text() == name:
                    self.preset_list.setCurrentRow(i)
                    break

    def _delete_preset(self):
        row = self.preset_list.currentRow()
        if row < 0:
            return
        name = self.preset_list.item(row).text()
        preset_path = os.path.join(PRESET_DIR, name + ".json")
        if os.path.exists(preset_path):
            os.remove(preset_path)
        self._refresh_preset_list()


class PathPanel(QWidget):
    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        layout.addWidget(QLabel("Paths:"))
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._row_changed)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.del_btn = QPushButton("Delete")
        self.del_btn.clicked.connect(self._delete_path)
        btn_row.addWidget(self.del_btn)

        self.fill_cb = QCheckBox("Fill")
        self.fill_cb.setChecked(True)
        self.fill_cb.stateChanged.connect(self._toggle_fill)
        btn_row.addWidget(self.fill_cb)

        self.stroke_cb = QCheckBox("Stroke")
        self.stroke_cb.stateChanged.connect(self._toggle_stroke)
        btn_row.addWidget(self.stroke_cb)

        self.vis_btn = QPushButton("Hide")
        self.vis_btn.clicked.connect(self._toggle_visible)
        btn_row.addWidget(self.vis_btn)

        layout.addLayout(btn_row)

        action_row = QHBoxLayout()
        self.to_sel_btn = QPushButton("To Selection")
        self.to_sel_btn.clicked.connect(self._to_selection)
        action_row.addWidget(self.to_sel_btn)

        self.stroke_btn = QPushButton("Stroke Path")
        self.stroke_btn.clicked.connect(self._stroke_path)
        action_row.addWidget(self.stroke_btn)

        layout.addLayout(action_row)

    def refresh(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        paths = canvas.get_active_paths()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for i, path in enumerate(paths):
            vis = "V" if path.visible else "H"
            fill = "F" if path.fill else "NF"
            stroke = "S" if path.stroke else "NS"
            item = QListWidgetItem(f"Path {i+1} [{vis}|{fill}|{stroke}]")
            item.setData(Qt.UserRole, i)
            self.list_widget.addItem(item)
        lid = id(canvas.layer_stack.active) if canvas.layer_stack.active else -1
        idx = canvas.active_path_index.get(lid, 0)
        if 0 <= idx < self.list_widget.count():
            self.list_widget.setCurrentRow(idx)
        self.list_widget.blockSignals(False)
        self._update_controls()

    def _update_controls(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        path = canvas.get_active_path()
        if path:
            self.fill_cb.blockSignals(True)
            self.fill_cb.setChecked(path.fill)
            self.fill_cb.blockSignals(False)
            self.stroke_cb.blockSignals(True)
            self.stroke_cb.setChecked(path.stroke)
            self.stroke_cb.blockSignals(False)
            self.vis_btn.setText("Hide" if path.visible else "Show")

    def _row_changed(self, row):
        canvas = self.get_canvas()
        if canvas and row >= 0:
            lid = id(canvas.layer_stack.active)
            canvas.active_path_index[lid] = row
            canvas.update()
            self._update_controls()

    def _delete_path(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        paths = canvas.get_active_paths()
        idx = self.list_widget.currentRow()
        if 0 <= idx < len(paths):
            del paths[idx]
            canvas.update()
            self.refresh()

    def _toggle_fill(self, state):
        canvas = self.get_canvas()
        if not canvas:
            return
        path = canvas.get_active_path()
        if path:
            path.fill = bool(state)
            canvas.update()
            self.refresh()

    def _toggle_stroke(self, state):
        canvas = self.get_canvas()
        if not canvas:
            return
        path = canvas.get_active_path()
        if path:
            path.stroke = bool(state)
            canvas.update()
            self.refresh()

    def _toggle_visible(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        path = canvas.get_active_path()
        if path:
            path.visible = not path.visible
            canvas.update()
            self.refresh()

    def _to_selection(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        path = canvas.get_active_path()
        if path:
            qp = path.to_qpainterpath()
            canvas.selection_path = qp
            canvas.selection_mask = canvas._selection_mask_from_path(qp)
            canvas.selection_phase = 0
            canvas.viewport().update()

    def _stroke_path(self):
        canvas = self.get_canvas()
        if not canvas:
            return
        layer = canvas.layer_stack.active
        if not layer or layer.locked:
            return
        path = canvas.get_active_path()
        if not path:
            return
        qp = path.to_qpainterpath()
        p = QPainter(layer.image)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(canvas.tool_color)
        c.setAlpha(int(255 * canvas.tool_opacity))
        pen = QPen(c, canvas.tool_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.strokePath(qp, pen)
        p.end()
        canvas._refresh()
