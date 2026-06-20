import sys
import traceback
import io
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor, QKeySequence
from PyQt5.QtWidgets import (
    QDockWidget, QPlainTextEdit, QWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QAction, QApplication,
)


class ScriptConsole(QDockWidget):
    def __init__(self, canvas_getter, parent=None):
        super().__init__("OpenCode Console", parent)
        self.get_canvas = canvas_getter
        self._locals = {"canvas": None, "layers": None, "tools": None}

        widget = QWidget()
        self.setWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(1000)
        monofont = QFont("Monospace", 10)
        monofont.setStyleHint(QFont.Monospace)
        self.output.setFont(monofont)
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: 1px solid #333;
                selection-background-color: #4a4a6a;
            }
        """)
        layout.addWidget(self.output)

        self.input = QPlainTextEdit()
        self.input.setMaximumBlockCount(1)
        self.input.setPlaceholderText(">>> type Python code and press Ctrl+Enter")
        self.input.setFont(monofont)
        self.input.setFixedHeight(60)
        self.input.setStyleSheet("""
            QPlainTextEdit {
                background-color: #16213e;
                color: #00ff88;
                border: 1px solid #333;
                selection-background-color: #4a4a6a;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.input)

        btn_row = QHBoxLayout()
        run_btn = QPushButton("Run (Ctrl+Enter)")
        run_btn.clicked.connect(self._execute)
        btn_row.addWidget(run_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.output.clear)
        btn_row.addWidget(clear_btn)
        refresh_btn = QPushButton("Refresh Context")
        refresh_btn.clicked.connect(self._refresh_context)
        btn_row.addWidget(refresh_btn)
        layout.addLayout(btn_row)

        short = QAction(self)
        short.setShortcut(QKeySequence("Ctrl+Return"))
        short.triggered.connect(self._execute)
        self.input.addAction(short)

        self._print_banner()

    def _print_banner(self):
        banner = (
            "OpenCode Scripting Console for reverseaffinite\n"
            "Type Python code and press Ctrl+Enter to execute.\n"
            "Available context: canvas, layers, tools, np (numpy), QColor, Qt, QImage\n"
            "Type help() for more info.\n"
            "---"
        )
        self.output.appendPlainText(banner)

    def _refresh_context(self):
        c = self.get_canvas()
        if c:
            self._locals["canvas"] = c
            self._locals["layers"] = c.layer_stack
            self._locals["tools"] = c.tool
            self.output.appendPlainText("Context refreshed: canvas, layers, tools")
        else:
            self.output.appendPlainText("No active canvas")

    def _execute(self):
        code = self.input.toPlainText().strip()
        if not code:
            return
        self.input.clear()
        self.output.appendPlainText(">>> " + code)
        self._refresh_context()
        try:
            self._locals["np"] = __import__("numpy")
        except ImportError:
            self._locals["np"] = None
            self.output.appendPlainText("  (numpy not available, install with: pip install numpy)")
        from PyQt5.QtGui import QColor, QImage
        self._locals["QColor"] = QColor
        self._locals["QImage"] = QImage
        from PyQt5.QtCore import Qt
        self._locals["Qt"] = Qt
        self._locals["help"] = lambda: self.output.appendPlainText(
            "Available: canvas (CanvasView), layers (LayerStack), tools (current tool),\n"
            "np (numpy), QColor, Qt, QImage, QPointF, QRect.\n"
            "Examples:\n"
            "  canvas.new_image(200, 200, QColor(Qt.red))\n"
            "  layers.add_layer('Scripted')\n"
            "  from editor.filters import grayscale; canvas.apply_filter(grayscale)\n"
            "  canvas.save_image('/tmp/output.png')"
        )
        self._locals["QPointF"] = __import__("PyQt5.QtCore", fromlist=["QPointF"]).QPointF
        self._locals["QRect"] = __import__("PyQt5.QtCore", fromlist=["QRect"]).QRect
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured = io.StringIO()
        sys.stdout = captured
        sys.stderr = captured
        try:
            result = eval(code, self._locals)
            if result is not None:
                print(repr(result))
        except SyntaxError:
            try:
                exec(code, self._locals)
            except Exception:
                print(traceback.format_exc().rstrip())
        except Exception:
            print(traceback.format_exc().rstrip())
        else:
            pass
        out = captured.getvalue()
        if out:
            self.output.appendPlainText(out.rstrip())
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        captured.close()

    def focus_input(self):
        self.input.setFocus()


def install_console(main_window, canvas_getter):
    dock = ScriptConsole(canvas_getter, main_window)
    main_window.addDockWidget(Qt.BottomDockWidgetArea, dock)

    action = dock.toggleViewAction()
    action.setText("OpenCode Console")
    action.setShortcut(QKeySequence("Ctrl+`"))
    main_window.console_action = action

    from PyQt5.QtWidgets import QMenu
    mb = main_window.menuBar()
    for child in mb.children():
        if isinstance(child, QMenu) and child.title() in ("&View", "View"):
            child.addSeparator()
            child.addAction(dock.toggleViewAction())
            break

    return dock
