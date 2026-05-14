"""Desktop DAC — PyQt demo with pluggable web bridge.

Supports two backends:
  --backend qt          Embeds QWebEngineView as a PyQt widget (default)
  --backend pywebview   Launches pywebview in a separate window (smaller package)

The web page (DesktopPage.svelte) handles all auth + API calls.
The desktop app receives/sends config via the bridge.

Usage:
    python desktop/desktop_app.py [--backend qt|pywebview] [dac_web_url]

    dac_web_url defaults to http://localhost:8000
"""

from __future__ import annotations

import os
import sys

# Allow direct script execution: python desktop/desktop_app.py
if __name__ == "__main__" and __package__ is None:
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, _parent)
    __package__ = "desktop"

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAction, QApplication, QMainWindow, QSplitter, QStatusBar,
    QToolBar, QWidget,
)

from .bridge import BridgeFactory, BridgeMessage
from .config_panel import ConfigPanel


class MainWindow(QMainWindow):
    def __init__(self, dac_web_url: str, backend: str):
        super().__init__()
        self.setWindowTitle("DAC Desktop")
        self.resize(1080, 700)
        self._dac_web_url = dac_web_url.rstrip("/")
        self._backend = backend

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Toolbar for webview controls (pywebview detached mode)
        self._toolbar = QToolBar("Web View")
        self._toolbar.setMovable(False)
        self._toggle_webview_action = QAction("Show/Hide WebView", self)
        self._toggle_webview_action.setCheckable(True)
        self._toggle_webview_action.setChecked(True)
        self._toggle_webview_action.triggered.connect(self._toggle_webview)
        self._toolbar.addAction(self._toggle_webview_action)
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)
        self._toolbar.setVisible(backend == "pywebview")

        # Config panel (shared across backends)
        self.config_panel = ConfigPanel(on_send_back=self._on_send_back)

        # Bridge
        self.bridge = BridgeFactory.create(
            backend,
            on_message=self._on_bridge_message,
            on_closed=self._on_bridge_closed,
        )

        if backend == "qt":
            self._setup_embedded()
        else:
            self._setup_detached()

        # Load the desktop page
        desktop_url = f"{self._dac_web_url}/desktop"
        self.bridge.start(desktop_url, title=f"DAC Desktop — {self._dac_web_url}",
                         width=800, height=600)

    # ── Layout setup ────────────────────────────────────────────────────

    def _setup_embedded(self):
        """QtWebEngineView is embedded as a widget in a splitter."""
        from .qt_bridge import QtWebEngineBridge
        qt_bridge = self.bridge  # type: QtWebEngineBridge
        splitter = QSplitter()
        splitter.addWidget(qt_bridge.get_widget())
        splitter.addWidget(self.config_panel)
        splitter.setSizes([520, 560])
        self.setCentralWidget(splitter)
        self.status_bar.showMessage(
            f"Connecting to {self._dac_web_url} ..."
        )

    def _setup_detached(self):
        """pywebview runs in its own window; PyQt shows only the config panel."""
        self.setCentralWidget(self.config_panel)
        self.status_bar.showMessage(
            f"Connecting to {self._dac_web_url}. Web view will open in a separate window."
        )

    # ── Bridge callbacks ────────────────────────────────────────────────

    def _on_bridge_message(self, msg: BridgeMessage):
        if msg.msg_type == "loadConfig":
            data = msg.data
            self.config_panel.load_config(
                data["projectId"], data["title"], data["configJson"]
            )
            self.status_bar.showMessage(f"Loaded: {data.get('title', '')}")
        elif msg.msg_type == "bridgeError":
            err = msg.data.get("message", "Unknown bridge error")
            self.status_bar.showMessage(f"Bridge error: {err}")
            self.config_panel.title_label.setText(f"Error: {err}")

    def _on_bridge_closed(self):
        if self._backend == "pywebview":
            bridge = self.bridge
            err = getattr(bridge, "last_error", "")
            if err:
                self.status_bar.showMessage(f"Web view failed: {err}")
                self.config_panel.title_label.setText(f"Web view failed:\n{err}")
            else:
                self.status_bar.showMessage("Web view closed.")
        else:
            self.status_bar.showMessage("Web view failed to load. Is the server running?")

    def _on_send_back(self, title: str, config_json: str):
        self.bridge.send_to_web("receiveConfig", {
            "title": title,
            "configJson": config_json,
        })
        self.status_bar.showMessage(f"Sent '{title}' back to web for saving.")

    def _toggle_webview(self, checked: bool):
        if checked:
            self.bridge.show_window()
            self.status_bar.showMessage("Web view shown.")
        else:
            self.bridge.hide_window()
            self.status_bar.showMessage("Web view hidden.")

    # ── Lifecycle ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.bridge.close()
        super().closeEvent(event)


def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="DAC Desktop — PyQt desktop app with pluggable web bridge",
    )
    parser.add_argument(
        "--backend", "-b",
        choices=["qt", "pywebview"],
        default=None,
        help="Web bridge backend (default: first available of qt, pywebview)",
    )
    parser.add_argument(
        "dac_web_url",
        nargs="?",
        default="http://localhost:8000",
        help="URL of the dac_web server",
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    backend = args.backend
    if backend is None:
        available = BridgeFactory.available_backends()
        backend = available[0]

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow(args.dac_web_url, backend)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
