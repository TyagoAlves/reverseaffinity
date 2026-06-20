import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QTabWidget, QDockWidget, QToolBar, QAction, QStatusBar,
    QMenuBar, QSplitter, QListWidget, QTreeWidget, QTreeWidgetItem,
    QPushButton, QSlider, QSpinBox, QComboBox, QToolButton,
    QFrame, QScrollArea, QGridLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

from reverseaffinity.i18n import _
from reverseaffinity.shared.resources import apply_dark_theme
from editor.timeline_widget import TimelineWidget
from editor.transport_bar import TransportBar


class SourceMonitor(QWidget):
    """Source/Preview monitor with video display"""
    def __init__(self, label="Preview", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumHeight(250)

        # Toolbar
        tb = QToolBar()
        tb.setIconSize(QSize(16, 16))
        tb.addAction(_("Import"), self.import_media)
        tb.addAction(_("Play"), self.toggle_play)
        tb.addAction(_("Loop"), self.toggle_loop)
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet("color: #aaa; padding: 2px 8px;")
        tb.addWidget(self.time_label)
        layout.addWidget(tb)

        # Video area
        self.video_label = QLabel(label)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(200)
        self.video_label.setStyleSheet("background-color: #0a0a0a; color: #444; font-size: 18px; border: 1px solid #222;")
        layout.addWidget(self.video_label, 1)

        # Timeline scrub
        self.scrub_slider = QSlider(Qt.Horizontal)
        self.scrub_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #333; }
            QSlider::handle:horizontal { background: #ff6b35; width: 12px; margin: -4px 0; border-radius: 6px; }
            QSlider::sub-page:horizontal { background: #ff6b35; }
        """)
        layout.addWidget(self.scrub_slider)

    def import_media(self): pass
    def toggle_play(self): pass
    def toggle_loop(self): pass


class EffectsPanel(QWidget):
    """Video effects list panel"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel(_("Effects")))
        self.search_box = QComboBox()
        self.search_box.setEditable(True)
        self.search_box.setPlaceholderText(_("Search effects..."))
        layout.addWidget(self.search_box)

        self.effects_list = QListWidget()
        self.effects_list.addItems([
            _("Color Correction"),
            _("Brightness/Contrast"),
            _("Color Balance"),
            _("HSL Adjust"),
            _("Curves"),
            _("Blur/Gaussian"),
            _("Sharpen"),
            _("Chroma Key"),
            _("Luma Key"),
            _("Transform"),
            _("Crop"),
            _("Opacity"),
        ])
        layout.addWidget(self.effects_list, 1)


class ProjectPanel(QWidget):
    """Project media browser"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        tb = QToolBar()
        tb.addAction(_("Import Media"), self.import_media)
        layout.addWidget(tb)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([_("Name"), _("Duration"), _("Type")])
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree, 1)

    def import_media(self): pass


class VideoMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_("reverseaffinity Video - [Untitled]"))
        screen = QApplication.primaryScreen().availableSize()
        self.resize(int(screen.width() * 0.85), int(screen.height() * 0.85))
        apply_dark_theme(self)

        self._setup_menus()
        self._setup_toolbars()
        self._setup_central()
        self._setup_docks()
        self.statusBar().showMessage(_("Ready"))

    def _setup_menus(self):
        mbar = self.menuBar()

        file_m = mbar.addMenu(_("&File"))
        file_m.addAction(_("&New Project"), self.new_project, "Ctrl+N")
        file_m.addAction(_("&Open Project..."), self.open_project, "Ctrl+O")
        file_m.addAction(_("&Save"), self.save_project, "Ctrl+S")
        file_m.addAction(_("Save &As..."), self.save_as, "Ctrl+Shift+S")
        file_m.addSeparator()
        file_m.addAction(_("&Export Media..."), self.export_media, "Ctrl+M")
        file_m.addSeparator()
        file_m.addAction(_("E&xit"), self.close, "Ctrl+Q")

        edit_m = mbar.addMenu(_("&Edit"))
        edit_m.addAction(_("&Undo"), self.undo, "Ctrl+Z")
        edit_m.addAction(_("&Redo"), self.redo, "Ctrl+Shift+Z")
        edit_m.addSeparator()
        edit_m.addAction(_("&Cut"), self.cut, "Ctrl+X")
        edit_m.addAction(_("&Copy"), self.copy, "Ctrl+C")
        edit_m.addAction(_("&Paste"), self.paste, "Ctrl+V")
        edit_m.addSeparator()
        edit_m.addAction(_("Select &All"), self.select_all, "Ctrl+A")

        clip_m = mbar.addMenu(_("&Clip"))
        clip_m.addAction(_("Split"), self.split_clip, "Ctrl+K")
        clip_m.addAction(_("Ripple Delete"), self.ripple_delete, "Shift+Del")
        clip_m.addAction(_("Add &Transition..."), self.add_transition)
        clip_m.addAction(_("Speed/Duration..."), self.speed_duration, "Ctrl+R")
        clip_m.addSeparator()
        clip_m.addAction(_("Group"), self.group_clips, "Ctrl+G")
        clip_m.addAction(_("Ungroup"), self.ungroup_clips, "Ctrl+Shift+G")

        timeline_m = mbar.addMenu(_("&Timeline"))
        timeline_m.addAction(_("Add Video Track"), self.add_video_track)
        timeline_m.addAction(_("Add Audio Track"), self.add_audio_track)
        timeline_m.addAction(_("Delete Track"), self.delete_track)

        view_m = mbar.addMenu(_("&View"))
        view_m.addAction(_("Toggle Fullscreen"), self.toggle_fullscreen, "F11")
        view_m.addAction(_("Zoom In"), self.zoom_in, "=")
        view_m.addAction(_("Zoom Out"), self.zoom_out, "-")
        view_m.addAction(_("Fit to Window"), self.zoom_fit, "\\")

    def _setup_toolbars(self):
        # Main editing toolbar
        main_tb = QToolBar(_("Editing"))
        main_tb.setIconSize(QSize(20, 20))
        main_tb.addAction(_("Selection"), self.tool_select, "V")
        main_tb.addAction(_("Cut"), self.tool_cut, "C")
        main_tb.addAction(_("Razor"), self.tool_razor, "R")
        main_tb.addAction(_("Hand"), self.tool_hand, "H")
        main_tb.addAction(_("Zoom"), self.tool_zoom, "Z")
        main_tb.addSeparator()
        main_tb.addAction(_("Snap"), self.toggle_snap)
        main_tb.addAction(_("Linked"), self.toggle_linked)
        self.addToolBar(main_tb)

        # Transport toolbar
        transport_tb = QToolBar(_("Transport"))
        transport_tb.setIconSize(QSize(18, 18))
        transport_tb.addAction(_("Go to Start"), self.go_start)
        transport_tb.addAction(_("Previous Frame"), self.prev_frame)
        transport_tb.addAction(_("Play"), self.toggle_play, "Space")
        transport_tb.addAction(_("Next Frame"), self.next_frame)
        transport_tb.addAction(_("Go to End"), self.go_end)
        transport_tb.addSeparator()
        transport_tb.addAction(_("Loop"), self.toggle_loop)
        self.addToolBar(transport_tb)

    def _setup_central(self):
        self.timeline = TimelineWidget()
        self.transport = TransportBar()

        # Top: Source + Program monitors side by side
        monitors = QSplitter(Qt.Horizontal)
        self.source_monitor = SourceMonitor(_("Source"))
        self.program_monitor = SourceMonitor(_("Program"))
        monitors.addWidget(self.source_monitor)
        monitors.addWidget(self.program_monitor)
        monitors.setSizes([400, 400])

        # Bottom: Timeline
        timeline_container = QWidget()
        tl_layout = QVBoxLayout(timeline_container)
        tl_layout.setContentsMargins(0, 0, 0, 0)
        tl_layout.setSpacing(0)
        tl_layout.addWidget(self.transport)
        tl_layout.addWidget(self.timeline, 1)

        # Main splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(monitors)
        splitter.addWidget(timeline_container)
        splitter.setSizes([350, 300])

        self.setCentralWidget(splitter)

    def _setup_docks(self):
        # Left: Project panel
        project_dock = QDockWidget(_("Project"), self)
        project_dock.setWidget(ProjectPanel())
        project_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.LeftDockWidgetArea, project_dock)

        # Right: Effects panel
        effects_dock = QDockWidget(_("Effects"), self)
        effects_dock.setWidget(EffectsPanel())
        effects_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.RightDockWidgetArea, effects_dock)

        # Right: Effect Controls
        efctrl_dock = QDockWidget(_("Effect Controls"), self)
        efctrl_dock.setWidget(QLabel(_("No clip selected")))
        efctrl_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.RightDockWidgetArea, efctrl_dock)

    # --- Actions ---
    def new_project(self): pass
    def open_project(self): pass
    def save_project(self): pass
    def save_as(self): pass
    def export_media(self): pass
    def undo(self): pass
    def redo(self): pass
    def cut(self): pass
    def copy(self): pass
    def paste(self): pass
    def select_all(self): pass
    def split_clip(self): pass
    def ripple_delete(self): pass
    def add_transition(self): pass
    def speed_duration(self): pass
    def group_clips(self): pass
    def ungroup_clips(self): pass
    def add_video_track(self): pass
    def add_audio_track(self): pass
    def delete_track(self): pass
    def toggle_fullscreen(self):
        self.showFullScreen() if not self.isFullScreen() else self.showNormal()
    def zoom_in(self): pass
    def zoom_out(self): pass
    def zoom_fit(self): pass
    def tool_select(self): pass
    def tool_cut(self): pass
    def tool_razor(self): pass
    def tool_hand(self): pass
    def tool_zoom(self): pass
    def toggle_snap(self): pass
    def toggle_linked(self): pass
    def go_start(self): pass
    def prev_frame(self): pass
    def toggle_play(self): pass
    def next_frame(self): pass
    def go_end(self): pass
    def toggle_loop(self): pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("reverseaffinity Video")
    win = VideoMainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
