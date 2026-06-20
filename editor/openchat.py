import json
import os
import subprocess
import threading
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QColor, QFont, QTextCursor, QPixmap, QPainter
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextBrowser, QLineEdit, QComboBox,
    QCheckBox, QGroupBox, QFormLayout, QSpinBox,
    QSplitter, QFrame, QProgressBar, QMessageBox,
    QScrollArea, QToolButton, QDialog, QDialogButtonBox,
)


_LLM_CONFIG = None


def get_llm_config():
    global _LLM_CONFIG
    if _LLM_CONFIG is None:
        s = QSettings()
        _LLM_CONFIG = {
            "provider": s.value("openchat/provider", "openai"),
            "endpoint": s.value("openchat/endpoint", "https://api.openai.com/v1"),
            "api_key": s.value("openchat/api_key", ""),
            "model": s.value("openchat/model", "gpt-4o"),
            "system_prompt": s.value("openchat/system_prompt",
                "You are an AI assistant for reverseaffinite photo editor. "
                "Help the user edit images, explain tools, suggest adjustments, "
                "and write Python scripts for the console. Be concise and practical."
            ),
        }
    return _LLM_CONFIG


def save_llm_config(cfg):
    global _LLM_CONFIG
    _LLM_CONFIG = cfg
    s = QSettings()
    for k, v in cfg.items():
        s.setValue(f"openchat/{k}", v)


class LLMConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant Settings")
        self.resize(480, 360)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.provider = QComboBox()
        self.provider.addItems(["openai", "anthropic", "local", "custom"])
        self.provider.currentTextChanged.connect(self._on_provider)
        form.addRow("Provider:", self.provider)
        self.endpoint = QLineEdit()
        form.addRow("Endpoint:", self.endpoint)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        form.addRow("API Key:", self.api_key)
        self.model = QLineEdit()
        form.addRow("Model:", self.model)
        self.sp = QTextBrowser()
        self.sp.setMaximumHeight(100)
        form.addRow("System Prompt:", self.sp)
        layout.addLayout(form)
        cfg = get_llm_config()
        idx = self.provider.findText(cfg["provider"])
        if idx >= 0:
            self.provider.setCurrentIndex(idx)
        self.endpoint.setText(cfg["endpoint"])
        self.api_key.setText(cfg["api_key"])
        self.model.setText(cfg["model"])
        self.sp.setPlainText(cfg["system_prompt"])
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_provider(self, p):
        defaults = {
            "openai": ("https://api.openai.com/v1", "gpt-4o"),
            "anthropic": ("https://api.anthropic.com/v1", "claude-3-5-sonnet-20241022"),
            "local": ("http://localhost:11434/v1", "llama3"),
            "custom": ("", ""),
        }
        if p in defaults:
            ep, mod = defaults[p]
            if not self.endpoint.text() or self.endpoint.text() in [
                "https://api.openai.com/v1", "https://api.anthropic.com/v1",
                "http://localhost:11434/v1"
            ]:
                self.endpoint.setText(ep)
            if not self.model.text() or self.model.text() in [
                "gpt-4o", "claude-3-5-sonnet-20241022", "llama3"
            ]:
                self.model.setText(mod)

    def _save(self):
        save_llm_config({
            "provider": self.provider.currentText(),
            "endpoint": self.endpoint.text().rstrip("/"),
            "api_key": self.api_key.text(),
            "model": self.model.text(),
            "system_prompt": self.sp.toPlainText(),
        })
        self.accept()


class MessageBubble(QLabel):
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        if is_user:
            html = f'<div style="background:#2d2d5e; color:#e0e0ff; padding:8px 12px; border-radius:8px; margin:2px 0;">{text}</div>'
        else:
            html = f'<div style="background:#1e3a3a; color:#e0ffe0; padding:8px 12px; border-radius:8px; margin:2px 0;">{text}</div>'
        self.setTextFormat(Qt.RichText)
        self.setText(html)
        self.setWordWrap(True)
        self.setMaximumWidth(400)


def _ask_llm(messages, config, timeout=30):
    provider = config["provider"]
    endpoint = config["endpoint"]
    api_key = config["api_key"]
    model = config["model"]
    if not api_key and provider in ("openai", "anthropic", "custom"):
        return None
    if provider == "anthropic":
        return _ask_anthropic(messages, config, timeout)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7,
    }
    try:
        import urllib.request
        import urllib.error
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{endpoint}/chat/completions",
            data=data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Error: {e}]"


def _ask_anthropic(messages, config, timeout=30):
    api_key = config["api_key"]
    model = config["model"]
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    system = ""
    msgs = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            msgs.append({"role": m["role"], "content": m["content"]})
    body = {
        "model": model,
        "max_tokens": 1024,
        "messages": msgs,
    }
    if system:
        body["system"] = system
    try:
        import urllib.request
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
        return result["content"][0]["text"]
    except Exception as e:
        return f"[Error: {e}]"


class AIChatPanel(QWidget):
    def __init__(self, canvas_getter, parent=None):
        super().__init__(parent)
        self.get_canvas = canvas_getter
        self._messages = []
        self._responding = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.chat = QTextBrowser()
        self.chat.setReadOnly(True)
        self.chat.setOpenExternalLinks(False)
        self.chat.setStyleSheet("""
            QTextBrowser {
                background-color: #121220;
                color: #d0d0d0;
                border: none;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.chat, 1)
        input_row = QHBoxLayout()
        input_row.setContentsMargins(4, 4, 4, 4)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask the AI assistant...")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a30;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)
        self.input.returnPressed.connect(self._send)
        input_row.addWidget(self.input, 1)
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a5a8a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4a7aaa; }
            QPushButton:pressed { background-color: #2a4a7a; }
        """)
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.send_btn)
        self.settings_btn = QToolButton()
        self.settings_btn.setText("\u2699")
        self.settings_btn.setToolTip("AI Settings")
        self.settings_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                color: #aaa;
                border: none;
                font-size: 18px;
                padding: 4px;
            }
            QToolButton:hover { color: #fff; }
        """)
        self.settings_btn.clicked.connect(self._show_settings)
        input_row.addWidget(self.settings_btn)
        layout.addLayout(input_row)
        self._print_welcome()

    def _print_welcome(self):
        welcome = (
            "<div style='padding:16px;'>"
            "<h3 style='color:#8ab4f8; margin:0 0 8px 0;'>AI Assistant</h3>"
            "<p style='color:#aaa; margin:0;'>Ask me anything about editing your image.<br>"
            "Examples: <i>\"make it warmer\"</i>, <i>\"add a blur\"</i>, "
            "<i>\"create a new layer with a gradient\"</i></p>"
            "</div>"
        )
        self.chat.setHtml(welcome)

    def _append_message(self, text, role):
        self._messages.append({"role": role, "content": text})
        prefix = "<b style='color:#8ab4f8;'>You:</b>" if role == "user" else "<b style='color:#6fcf97;'>AI:</b>"
        html = f"<div style='margin:6px 10px;'>{prefix}<br>{text}</div>"
        self.chat.append(html)
        self.chat.verticalScrollBar().setValue(
            self.chat.verticalScrollBar().maximum()
        )

    def _send(self):
        txt = self.input.text().strip()
        if not txt or self._responding:
            return
        self.input.clear()
        self._append_message(txt, "user")
        self._responding = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("...")
        self.input.setPlaceholderText("AI is thinking...")
        canvas = self.get_canvas()
        context = ""
        if canvas:
            lstack = canvas.layer_stack
            n = lstack.count()
            layers_info = []
            for i in range(n):
                l = lstack.at(i)
                layers_info.append(
                    f"{'<active>' if l == lstack.active() else ''} "
                    f"Layer {i}: {l.name}, {l.image.width()}x{l.image.height()}, "
                    f"visible={l.visible}, locked={l.locked}"
                )
            context = (
                f"Current canvas: {canvas.image_size[0]}x{canvas.image_size[1]}px\n"
                f"Layers ({n}):\n" + "\n".join(layers_info) + "\n"
                f"Active tool: {canvas.tool_name}\n"
                f"Foreground color: {canvas.fg_color.name() if canvas.fg_color else '#000000'}\n"
            )
        full_messages = [
            {"role": "system", "content": get_llm_config()["system_prompt"] + f"\n\nCurrent document state:\n{context}"},
        ]
        for m in self._messages[-20:]:
            full_messages.append(m)
        config = get_llm_config()
        threading.Thread(target=self._do_ask, args=(full_messages, config), daemon=True).start()

    def _do_ask(self, messages, config):
        reply = _ask_llm(messages, config)
        QTimer.singleShot(0, lambda: self._on_reply(reply))

    def _on_reply(self, reply):
        self._responding = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send")
        self.input.setPlaceholderText("Ask the AI assistant...")
        if reply is None:
            self._append_message(
                "AI assistant not configured. Click the gear icon to set up your API key.",
                "assistant"
            )
            return
        self._append_message(reply, "assistant")

    def _show_settings(self):
        dlg = LLMConfigDialog(self)
        dlg.exec_()
