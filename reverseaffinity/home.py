import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt

from reverseaffinity import __version__
from reverseaffinity.shared.resources import apply_dark_theme
from reverseaffinity.i18n import _


APP_CARDS = [
    {
        "id": "photo",
        "name": _("reverseaffinity Photo"),
        "desc": _("Image editing & compositing"),
        "icon": "\U0001F4F7",
        "module": "reverseaffinity.photo",
        "window_cls": None,
        "title": _("reverseaffinity Photo - [Untitled]"),
    },
    {
        "id": "video",
        "name": _("reverseaffinity Video"),
        "desc": _("Video editing & timeline"),
        "icon": "\U0001F3AC",
        "module": "reverseaffinity.video",
        "window_cls": None,
        "title": _("reverseaffinity Video - [Untitled]"),
    },
    {
        "id": "effects",
        "name": _("reverseaffinity Effects"),
        "desc": _("Motion graphics & compositing"),
        "icon": "\U0001F3A8",
        "module": "reverseaffinity.effects",
        "window_cls": None,
        "title": _("reverseaffinity Effects - [Untitled Composition]"),
    },
]


class AppCard(QFrame):
    def __init__(self, app_info, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self.setMinimumSize(260, 200)
        self.setMaximumSize(320, 260)
        self.setStyleSheet("""
            AppCard {
                background: #1e1e24;
                border: 1px solid #333;
                border-radius: 16px;
            }
            AppCard:hover {
                background: #2a2a32;
                border: 1px solid #5a7aff;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        icon_label = QLabel(app_info["icon"])
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        name_label = QLabel(app_info["name"])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #eee;")
        layout.addWidget(name_label)

        desc_label = QLabel(app_info["desc"])
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; color: #999;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self.open_btn = QPushButton(_("Open"))
        self.open_btn.setFixedWidth(100)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: #5a7aff; color: white; border: none;
                border-radius: 8px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background: #6b8aff; }
        """)
        layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)

    def mousePressEvent(self, event):
        parent_win = self.window()
        if hasattr(parent_win, 'open_app'):
            parent_win.open_app(self.app_info)


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_("reverseaffinity Home"))
        screen = QApplication.primaryScreen().availableSize()
        self.resize(int(screen.width() * 0.5), int(screen.height() * 0.55))
        self.setMinimumSize(700, 450)
        self._sub_windows = []
        apply_dark_theme(self)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel(_("reverseaffinity"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #fff; letter-spacing: 2px;")
        layout.addWidget(title)

        subtitle = QLabel(_("Choose an application"))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #888; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignCenter)
        cards_layout.setSpacing(24)
        self.cards = []
        for info in APP_CARDS:
            card = AppCard(info)
            card.open_btn.clicked.connect(lambda checked, i=info: self.open_app(i))
            self.cards.append(card)
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)

        ver_label = QLabel(f"v{__version__}")
        ver_label.setAlignment(Qt.AlignCenter)
        ver_label.setStyleSheet("color: #555; font-size: 11px; margin-top: 20px;")
        layout.addWidget(ver_label)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def open_app(self, app_info):
        app_id = app_info["id"]
        if app_id == "photo":
            from editor.app_ui import MainWindow as Cls
        elif app_id == "video":
            from reverseaffinity.video.video_app import VideoMainWindow as Cls
        elif app_id == "effects":
            from reverseaffinity.effects.effects_app import EffectsMainWindow as Cls
        else:
            return
        win = Cls()
        win.setWindowTitle(app_info["title"])
        self._sub_windows.append(win)
        win.show()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("reverseaffinity Home")
    win = HomeWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
