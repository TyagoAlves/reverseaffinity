#!/usr/bin/env python3
"""reverseaffinity — Launcher / Entry Point

Usage:
    python main.py [photo|video|effects|home]

Also importable:
    from main import run_photo, run_video, run_effects
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("reverseaffinity")
        app.setOrganizationName("reverseaffinity")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.svg")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    return app


def run_photo():
    app = _get_app()
    from editor.app_ui import MainWindow
    from editor.resources import apply_dark_theme
    from editor.i18n import _

    app.setApplicationDisplayName("reverseaffinity Photo")
    apply_dark_theme(app)

    win = MainWindow()
    win.setWindowTitle(_("reverseaffinity Photo - [Untitled]"))
    win.show()
    if QApplication.instance() is app:
        sys.exit(app.exec_())


def run_video():
    app = _get_app()
    from reverseaffinity.video.video_app import VideoMainWindow
    from reverseaffinity.shared.resources import apply_dark_theme
    from reverseaffinity.i18n import _

    app.setApplicationDisplayName("reverseaffinity Video")
    apply_dark_theme(app)

    win = VideoMainWindow()
    win.setWindowTitle(_("reverseaffinity Video - [Untitled]"))
    win.show()
    if QApplication.instance() is app:
        sys.exit(app.exec_())


def run_effects():
    app = _get_app()
    from reverseaffinity.effects.effects_app import EffectsMainWindow
    from reverseaffinity.shared.resources import apply_dark_theme
    from reverseaffinity.i18n import _

    app.setApplicationDisplayName("reverseaffinity Effects")
    apply_dark_theme(app)

    win = EffectsMainWindow()
    win.setWindowTitle(_("reverseaffinity Effects - [Untitled Composition]"))
    win.show()
    if QApplication.instance() is app:
        sys.exit(app.exec_())


def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "home"

    if mode in ("--help", "-h", "help"):
        print(__doc__)
        return

    runners = {
        "photo": run_photo, "editor": run_photo, "p": run_photo,
        "video": run_video, "v": run_video,
        "effects": run_effects, "e": run_effects,
    }

    if mode in runners:
        runners[mode]()
    else:
        app = _get_app()
        from reverseaffinity.home import HomeWindow
        from reverseaffinity.shared.resources import apply_dark_theme
        apply_dark_theme(app)
        win = HomeWindow()
        win.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
