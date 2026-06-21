from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QSpinBox, QPushButton, QWidget, QGroupBox, QSlider,
    QInputDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QMessageBox, QFileDialog,
)
from .i18n import _


class GuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("New Guide"))
        self.resize(280, 120)
        self.setStyleSheet("QDialog { background: #121212; }")

        layout = QVBoxLayout(self)
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems([_("Horizontal"), _("Vertical")])
        layout.addWidget(QLabel(_("Orientation:")))
        layout.addWidget(self.orientation_combo)

        self.position_spin = QSpinBox()
        self.position_spin.setRange(0, 50000)
        self.position_spin.setValue(100)
        layout.addWidget(QLabel(_("Position (px):")))
        layout.addWidget(self.position_spin)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(_("OK"))
        cancel_btn = QPushButton(_("Cancel"))
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.result_data = None
        ok_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self.reject)

    def _accept(self):
        orient = Qt.Horizontal if self.orientation_combo.currentIndex() == 0 else Qt.Vertical
        self.result_data = (orient, self.position_spin.value())
        self.accept()


class FilterGalleryDialog(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle(_("Filter Gallery"))
        self.resize(800, 500)
        self.setStyleSheet("QDialog { background: #121212; }")

        layout = QHBoxLayout(self)

        left_panel = QWidget()
        left_panel.setStyleSheet("background: #121212;")
        left_layout = QVBoxLayout(left_panel)

        categories = {
            _("Adjustments"): [
                (_("Brightness / Contrast"), self._bc),
                (_("Hue / Saturation"), self._hs),
                (_("Levels"), self._levels),
                (_("Grayscale"), lambda: self._apply_filter("grayscale")),
                (_("Invert"), lambda: self._apply_filter("invert")),
                (_("Sepia"), lambda: self._apply_filter("sepia")),
            ],
            _("Blur"): [
                (_("Gaussian Blur"), self._blur),
            ],
            _("Sharpen"): [
                (_("Sharpen"), self._sharpen),
                (_("Edge Detect"), lambda: self._apply_filter("edge_detect")),
            ],
            _("Stylize"): [
                (_("Pixelate"), self._pixelate),
                (_("Posterize"), self._posterize),
            ],
        }

        for cat_name, items in categories.items():
            grp = QGroupBox(cat_name)
            grp_layout = QVBoxLayout(grp)
            for btn_name, callback in items:
                btn = QPushButton(btn_name)
                btn.clicked.connect(callback)
                grp_layout.addWidget(btn)
            left_layout.addWidget(grp)

        left_layout.addStretch()

        self.preview_label = QLabel(_("Preview"))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: #0a0a0a; border: 1px solid #333; color: #666;")

        layout.addWidget(left_panel, 1)
        layout.addWidget(self.preview_label, 2)

    def _apply_filter(self, name):
        from . import filters as f
        func = getattr(f, name, None)
        if func and self.canvas.layer_stack.active:
            self.canvas._save_state(name.replace("_", " ").title())
            self.canvas.layer_stack.active.image = func(self.canvas.layer_stack.active.image)
            self.canvas._refresh()

    def _bc(self):
        self._show_slider_dialog(_("Brightness / Contrast"), [
            (_("Brightness"), -255, 255, 0),
            (_("Contrast"), 0, 300, 100),
        ], lambda vals: self._apply_multi([
            ("brightness", vals[0]),
            ("contrast", vals[1] / 100.0),
        ]))

    def _hs(self):
        self._show_slider_dialog(_("Hue / Saturation"), [
            (_("Hue"), -180, 180, 0),
            (_("Saturation"), 0, 300, 100),
            (_("Lightness"), -100, 100, 0),
        ], lambda vals: self._apply_multi([
            ("hue_saturation", vals[0], vals[1] / 100.0, vals[2]),
        ]))

    def _levels(self):
        self._show_slider_dialog(_("Levels"), [
            (_("Shadow"), 0, 255, 0),
            (_("Mid (gamma)"), 10, 990, 100),
            (_("Highlight"), 0, 255, 255),
        ], lambda vals: self._apply_multi([
            ("levels", vals[0], vals[1] / 100.0, vals[2]),
        ]))

    def _blur(self):
        r, ok = QInputDialog.getInt(self, _("Gaussian Blur"), _("Radius:"), 3, 1, 100)
        if ok:
            self._apply_filter_arg("gaussian_blur", r)

    def _sharpen(self):
        a, ok = QInputDialog.getDouble(self, _("Sharpen"), _("Amount:"), 1.0, 0.1, 10.0)
        if ok:
            self._apply_filter_arg("sharpen", a)

    def _pixelate(self):
        s, ok = QInputDialog.getInt(self, _("Pixelate"), _("Block Size:"), 8, 2, 200)
        if ok:
            self._apply_filter_arg("pixelate", s)

    def _posterize(self):
        l, ok = QInputDialog.getInt(self, _("Posterize"), _("Levels:"), 4, 2, 64)
        if ok:
            self._apply_filter_arg("posterize", l)

    def _apply_filter_arg(self, name, *args):
        from . import filters as f
        func = getattr(f, name, None)
        if func and self.canvas.layer_stack.active:
            self.canvas._save_state(name.replace("_", " ").title())
            self.canvas.layer_stack.active.image = func(self.canvas.layer_stack.active.image, *args)
            self.canvas._refresh()

    def _apply_multi(self, steps):
        from . import filters as f
        layer = self.canvas.layer_stack.active
        if not layer:
            return
        self.canvas._save_state("Filter")
        img = layer.image
        for name, *args in steps:
            func = getattr(f, name, None)
            if func:
                img = func(img, *args)
        layer.image = img
        self.canvas._refresh()

    def _show_slider_dialog(self, title, sliders, on_apply):
        dialog = QDialog(self)
        dialog.setWindowTitle(_(title))
        layout = QVBoxLayout(dialog)

        spinboxes = []
        for label, lo, hi, default in sliders:
            row = QHBoxLayout()
            row.addWidget(QLabel(_(label) + ":"))
            s = QSlider(Qt.Horizontal)
            s.setRange(lo, hi)
            s.setValue(default)
            row.addWidget(s)
            layout.addLayout(row)
            spinboxes.append(s)

        btn = QPushButton(_("Apply"))
        btn.clicked.connect(lambda: (on_apply([s.value() for s in spinboxes]), dialog.close()))
        layout.addWidget(btn)
        dialog.exec_()


class ExportDialog(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle(_("Export Image"))
        self.resize(450, 300)
        self.setStyleSheet("QDialog { background: #121212; }")

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItem(_("PNG (.png)"), '.png')
        self.format_combo.addItem(_("JPEG (.jpg)"), '.jpg')
        self.format_combo.addItem(_("WebP (.webp)"), '.webp')
        self.format_combo.addItem(_("TIFF (.tiff)"), '.tiff')
        self.format_combo.addItem(_("BMP (.bmp)"), '.bmp')
        self.format_combo.addItem(_("Photoshop PSD (.psd)"), '.psd')
        self.format_combo.currentIndexChanged.connect(self._update_options)
        form.addRow(_("Format:"), self.format_combo)

        self.quality_layout = QVBoxLayout()
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(95)
        self.quality_label = QLabel("95")
        self.quality_slider.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        q_row = QHBoxLayout()
        q_row.addWidget(self.quality_slider)
        q_row.addWidget(self.quality_label)
        self.quality_group = QGroupBox(_("Quality"))
        self.quality_group.setLayout(q_row)
        self.quality_layout.addWidget(self.quality_group)

        self.compression_layout = QVBoxLayout()
        self.compression_slider = QSlider(Qt.Horizontal)
        self.compression_slider.setRange(0, 9)
        self.compression_slider.setValue(6)
        self.compression_label = QLabel("6")
        self.compression_slider.valueChanged.connect(lambda v: self.compression_label.setText(str(v)))
        c_row = QHBoxLayout()
        c_row.addWidget(self.compression_slider)
        c_row.addWidget(self.compression_label)
        self.compression_group = QGroupBox(_("Compression"))
        self.compression_group.setLayout(c_row)
        self.compression_layout.addWidget(self.compression_group)

        self.tiff_comp_combo = QComboBox()
        self.tiff_comp_combo.addItems(['none', 'lzw', 'zip'])
        self.tiff_comp_group = QGroupBox(_("TIFF Compression"))
        t_row = QHBoxLayout()
        t_row.addWidget(self.tiff_comp_combo)
        self.tiff_comp_group.setLayout(t_row)
        self.compression_layout.addWidget(self.tiff_comp_group)

        self.options_widget = QWidget()
        self.options_widget.setStyleSheet("background: transparent;")
        opts_layout = QVBoxLayout(self.options_widget)
        opts_layout.addLayout(self.quality_layout)
        opts_layout.addLayout(self.compression_layout)
        form.addRow("Options:", self.options_widget)

        self.path_edit = QLineEdit()
        browse_btn = QPushButton(_("Browse..."))
        browse_btn.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)
        form.addRow(_("Output:"), path_row)

        layout.addLayout(form)

        self.size_label = QLabel(_("Estimated size: --"))
        layout.addWidget(self.size_label)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._export)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._update_options()

    def _update_options(self):
        ext = self.format_combo.currentData()
        try:
            from .file_io import get_export_options_for_format, FORMAT_REGISTRY
            opts = get_export_options_for_format(ext)
        except ImportError:
            return

        has_quality = 'quality' in opts
        has_compression = 'compression' in opts
        has_tiff_comp = ext in ('.tiff', '.tif') and 'compression' in opts

        self.quality_group.setVisible(has_quality)
        self.compression_group.setVisible(has_compression and not has_tiff_comp)
        self.tiff_comp_group.setVisible(has_tiff_comp)
        self.options_widget.setVisible(has_quality or has_compression or has_tiff_comp)

        if has_quality:
            lo, hi, default = opts['quality']
            self.quality_slider.setRange(lo, hi)
            self.quality_slider.setValue(default)
            self.quality_label.setText(str(default))

        if has_compression and not has_tiff_comp:
            lo, hi, default = opts['compression']
            self.compression_slider.setRange(lo, hi)
            self.compression_slider.setValue(default)
            self.compression_label.setText(str(default))

        self._update_size_estimate()

    def _update_size_estimate(self):
        composite = self.canvas.layer_stack.composite()
        w, h = composite.width(), composite.height()
        bpp = 4
        ext = self.format_combo.currentData()
        if ext == '.jpg':
            bpp = 3
        raw_size = w * h * bpp
        ratio = 0.3 if ext in ('.jpg', '.webp') else 0.5 if ext == '.png' else 1.0
        if ext == '.psd':
            try:
                from .file_io import FORMAT_REGISTRY
            except ImportError:
                pass
            num_layers = len(self.canvas.layer_stack.layers)
            estimated = raw_size * (1 + 0.3 * num_layers)
        else:
            estimated = raw_size * ratio
        if estimated > 1024 * 1024:
            self.size_label.setText(_("Estimated size: ") + f"{estimated / (1024*1024):.1f} MB")
        else:
            self.size_label.setText(_("Estimated size: ") + f"{estimated / 1024:.0f} KB")

    def _browse(self):
        ext = self.format_combo.currentData()
        try:
            from .file_io import FORMAT_REGISTRY
            info = FORMAT_REGISTRY.get(ext, {})
            name = info.get('name', ext.upper())
        except ImportError:
            name = ext.upper()
        path, _filter = QFileDialog.getSaveFileName(self, _("Export As"), "", f"{_(name)} (*{ext})")
        if path:
            self.path_edit.setText(path)
            self._update_size_estimate()

    def get_options(self):
        ext = self.format_combo.currentData()
        opts = {}
        try:
            from .file_io import FORMAT_REGISTRY
            info = FORMAT_REGISTRY.get(ext, {})
            export_opts = info.get('export_options', {})
        except ImportError:
            export_opts = {}

        if 'quality' in export_opts:
            opts['quality'] = self.quality_slider.value()
        if 'compression' in export_opts:
            if ext in ('.tiff', '.tif'):
                opts['compression'] = self.tiff_comp_combo.currentText()
            else:
                opts['compression'] = self.compression_slider.value()
        return ext, opts

    def _export(self):
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, _("Export"), _("Please select an output path."))
            return
        ext, opts = self.get_options()
        if not path.lower().endswith(ext):
            path += ext
        if self.canvas.save_image(path, opts):
            QMessageBox.information(self, _("Export"), _("Exported successfully to:") + f"\n{path}")
            self.accept()
        else:
            QMessageBox.critical(self, _("Export"), _("Export failed."))
