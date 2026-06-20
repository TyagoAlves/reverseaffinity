import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QDockWidget, QTreeWidget, QTreeWidgetItem, QToolBar, QAction, QStatusBar, QMenuBar, QSlider, QDoubleSpinBox, QGroupBox, QFormLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QKeySequence

from reverseaffinity.i18n import _
from reverseaffinity.shared.resources import apply_dark_theme


class EffectsMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_("reverseaffinity Effects - [Untitled Composition]"))
        screen = QApplication.primaryScreen().availableGeometry()
        max_w = min(int(screen.width() * 0.75), screen.width())
        max_h = min(int(screen.height() * 0.8), screen.height())
        self.resize(min(max_w, 1400), min(max_h, 900))
        self.setMaximumSize(screen.width(), screen.height())
        apply_dark_theme(self)

        mbar = self.menuBar()
        file_m = mbar.addMenu(_("&File"))
        file_m.addAction(self._action(_("&New Composition"), self.new_comp, "Ctrl+N"))
        file_m.addAction(self._action(_("&Save"), self.save_project, "Ctrl+S"))
        file_m.addSeparator()
        file_m.addAction(self._action(_("E&xit"), self.close, "Ctrl+Q"))

        comp_m = mbar.addMenu(_("&Composition"))
        comp_m.addAction(_("New &Layer"), self.new_layer)
        comp_m.addAction(_("New &Solid"), self.new_solid)
        comp_m.addAction(self._action(_("Pre-compose"), self.pre_compose, "Ctrl+Shift+C"))

        effect_m = mbar.addMenu(_("&Effect"))
        effect_m.addAction(_("Add &Effect..."), self.add_effect)

        # Central: Preview + Timeline
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Preview
        self.preview_label = QLabel(_("Composition Preview"))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("background-color: #111; color: #555; font-size: 24px;")
        main_layout.addWidget(self.preview_label, 3)

        # Timeline area placeholder
        self.timeline_label = QLabel(_("Timeline"))
        self.timeline_label.setAlignment(Qt.AlignCenter)
        self.timeline_label.setMinimumHeight(150)
        self.timeline_label.setStyleSheet("background-color: #1a1a1a; color: #555; border-top: 1px solid #333;")
        main_layout.addWidget(self.timeline_label, 1)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Right dock — Effect Controls
        dock = QDockWidget(_("Effect Controls"), self)
        self.effect_panel = QWidget()
        ef_layout = QVBoxLayout(self.effect_panel)
        ef_layout.addWidget(QLabel(_("No layer selected")))
        self.effect_panel.setLayout(ef_layout)
        dock.setWidget(self.effect_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Left dock — Project / Layers
        dock2 = QDockWidget(_("Project"), self)
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels([_("Name"), _("Type")])
        dock2.setWidget(self.project_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock2)

        self.statusBar().showMessage(_("Ready"))

    def new_comp(self): pass
    def save_project(self): pass
    def new_layer(self): pass
    def new_solid(self): pass
    def pre_compose(self): pass
    def add_effect(self): pass

    @staticmethod
    def _action(text, slot, shortcut=None):
        a = QAction(text)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        return a


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("reverseaffinity Effects")
    win = EffectsMainWindow()
    win.show()
    if QApplication.instance() is app:
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
