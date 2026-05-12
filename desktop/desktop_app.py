"""Desktop DAC — PyQt demo with JavaScript bridge.

Loads dac_web's /desktop page in a WebView. The web page handles all
auth + API calls. The desktop app receives/sends config via JS bridge.

Bridge protocol:
  Web → Desktop:  console.log("DAC_BRIDGE:" + JSON.stringify({...}))
  Desktop → Web:  page.runJavaScript("window.desktopReceiveConfig(...)")

Usage:
    python desktop/desktop_app.py [dac_web_url]

    dac_web_url defaults to http://localhost:8000
"""

import json
import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSplitter,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QGroupBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLineEdit, QStatusBar,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage


# ──────────────────────────────────────────────────────────────────────
# WebView with console.log bridge interception
# ──────────────────────────────────────────────────────────────────────

BRIDGE_PREFIX = "DAC_BRIDGE:"


class BridgePage(QWebEnginePage):
    """Intercepts console.log messages prefixed with DAC_BRIDGE:"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge_message_received = None  # set by MainWindow

    def javaScriptConsoleMessage(self, level, msg, line, source):
        if msg.startswith(BRIDGE_PREFIX):
            payload = msg[len(BRIDGE_PREFIX):]
            if self.bridge_message_received:
                self.bridge_message_received(payload)


# ──────────────────────────────────────────────────────────────────────
# Config detail panel (right side)
# ──────────────────────────────────────────────────────────────────────

class ConfigPanel(QWidget):
    def __init__(self, web_view: QWebEngineView, parent=None):
        super().__init__(parent)
        self._web_view = web_view
        self._project_id: str | None = None
        self._title: str = ""
        self._wrapped: dict | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.title_label = QLabel("No project loaded — click 'Open in Desktop' on the left")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        meta = QGroupBox("Info")
        meta_form = QVBoxLayout(meta)
        self.meta_text = QLabel("")
        self.meta_text.setWordWrap(True)
        meta_form.addWidget(self.meta_text)
        layout.addWidget(meta)

        cfg = QGroupBox("DAC Config (read-only view)")
        cfg_layout = QVBoxLayout(cfg)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cfg_layout.addWidget(self.tree)
        layout.addWidget(cfg)

        save_group = QGroupBox("Send Back to Web for Saving")
        save_layout = QHBoxLayout(save_group)
        save_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        save_layout.addWidget(self.title_edit)
        save_btn = QPushButton("Send to Web → Save to Server")
        save_btn.clicked.connect(self._send_back)
        save_layout.addWidget(save_btn)
        layout.addWidget(save_group)

    def load_config(self, project_id: str, title: str, config_json: str):
        self._project_id = project_id
        self._title = title
        try:
            self._wrapped = json.loads(config_json)
            config = self._wrapped.get("config", self._wrapped)
        except json.JSONDecodeError:
            config = {"error": "invalid json"}
            self._wrapped = None

        self.title_label.setText(f"Project: {title}")
        self.title_edit.setText(title)
        creator = (self._wrapped or {}).get("creator_name", "-") if self._wrapped else "-"
        version = (self._wrapped or {}).get("version", "-") if self._wrapped else "-"
        self.meta_text.setText(f"ID: {project_id}\nCreator: {creator}\nVersion: {version}")
        self._populate_tree(config)

    def _populate_tree(self, obj):
        self.tree.clear()

        def add(parent, key, val):
            if isinstance(val, dict):
                node = QTreeWidgetItem([key, ""])
                parent.addChild(node)
                for k, v in val.items():
                    add(node, k, v)
            elif isinstance(val, list):
                node = QTreeWidgetItem([key, f"[{len(val)} items]"])
                parent.addChild(node)
                for i, v in enumerate(val):
                    disp = v.get("name", v.get("_class_", "")) if isinstance(v, dict) else json.dumps(v, ensure_ascii=False)
                    add(node, f"[{i}]", v)
            else:
                s = json.dumps(val, ensure_ascii=False)
                if len(s) > 120:
                    s = s[:120] + "..."
                parent.addChild(QTreeWidgetItem([key, s]))

        for k, v in obj.items():
            top = QTreeWidgetItem([k, ""])
            self.tree.addTopLevelItem(top)
            add(top, k, v)
            top.setExpanded(True)

    def _send_back(self):
        if not self._wrapped or not self._web_view or not self._project_id:
            return
        title = self.title_edit.text().strip() or self._title
        if isinstance(self._wrapped, dict):
            self._wrapped.setdefault("dac_web", {})["title"] = title
        payload = json.dumps(self._wrapped, ensure_ascii=False)
        js = "window.desktopReceiveConfig("
        js += json.dumps(title) + ","
        js += json.dumps(payload) + ");"
        self._web_view.page().runJavaScript(js)


# ──────────────────────────────────────────────────────────────────────
# Main Window
# ──────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, dac_web_url: str):
        super().__init__()
        self.setWindowTitle("DAC Desktop")
        self.resize(1080, 700)

        self._dac_web_url = dac_web_url.rstrip("/")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Connecting to {self._dac_web_url} ...")

        splitter = QSplitter()

        self.page = BridgePage()
        self.page.bridge_message_received = self._on_bridge_message

        self.web_view = QWebEngineView()
        self.web_view.setPage(self.page)
        self.web_view.setMinimumWidth(400)

        self.web_view.loadFinished.connect(self._on_page_loaded)
        desktop_url = f"{self._dac_web_url}/desktop"
        self.web_view.setUrl(QUrl(desktop_url))
        splitter.addWidget(self.web_view)

        self.config_panel = ConfigPanel(self.web_view)
        splitter.addWidget(self.config_panel)

        splitter.setSizes([520, 560])
        self.setCentralWidget(splitter)

    def _on_page_loaded(self, ok: bool):
        if ok:
            self.status_bar.showMessage(
                f"Connected to {self._dac_web_url} — Log in via Keycloak, then open a project"
            )
            # Inject the bridge object so DesktopPage can call dacDesktop.loadConfig()
            self.page.runJavaScript("""
window.dacDesktop = {
    loadConfig: function(projectId, title, configJson) {
        var msg = JSON.stringify({
            action: "loadConfig",
            projectId: projectId,
            title: title,
            configJson: configJson
        });
        console.log("DAC_BRIDGE:" + msg);
    }
};
            """)

    def _on_bridge_message(self, payload: str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return
        action = data.get("action")
        if action == "loadConfig":
            self.config_panel.load_config(
                data["projectId"], data["title"], data["configJson"]
            )
            self.status_bar.showMessage(f"Loaded: {data['title']}")


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

def main():
    dac_web_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow(dac_web_url)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
