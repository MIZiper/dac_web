"""QtWebEngineBridge — embeds a QWebEngineView as a PyQt widget.

Uses console.log interception for Web → Desktop and runJavaScript for
Desktop → Web communication.

This is the original bridge approach extracted from desktop_app.py.
"""

from __future__ import annotations

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

from .bridge import (
    BridgeMessage, BaseBridge, OnMessageCallback, OnClosedCallback,
    TYPE_RECEIVE_CONFIG, ACTION_SEND_TO_WEB,
)

BRIDGE_PREFIX = "DAC_BRIDGE:"


class _BridgePage(QWebEnginePage):
    """Intercepts console.log messages prefixed with DAC_BRIDGE:"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge_message_received = None

    def javaScriptConsoleMessage(self, level, msg, line, source):
        if msg.startswith(BRIDGE_PREFIX):
            payload = msg[len(BRIDGE_PREFIX):]
            if self.bridge_message_received:
                self.bridge_message_received(payload)


class QtWebEngineBridge(BaseBridge):
    """Embeds a QWebEngineView widget.

    Provides get_widget() so the caller can place the web view in a layout.
    """

    def __init__(self, on_message: OnMessageCallback,
                 on_closed: OnClosedCallback):
        self._on_message = on_message
        self._on_closed = on_closed

        self._page = _BridgePage()
        self._page.bridge_message_received = self._on_bridge_raw

        self._web_view = QWebEngineView()
        self._web_view.setPage(self._page)
        self._web_view.setMinimumWidth(400)

        self._url = ""
        self._started = False

    # ── BaseBridge interface ────────────────────────────────────────────

    def start(self, url: str, title: str = "DAC Desktop",
              width: int = 800, height: int = 600):
        if self._started:
            return
        self._started = True
        self._url = url

        # Load the base URL (without hash fragment) so the server returns index.html.
        # After page load, we inject JS to set window.location.hash to route to DesktopPage.
        base_url = url.split("#")[0] if "#" in url else url
        if base_url.endswith("/"):
            base_url = base_url.rstrip("/")

        self._web_view.loadFinished.connect(self._on_page_loaded)
        self._web_view.setUrl(QUrl(base_url))

    def send_to_web(self, msg_type: str, data: dict):
        js = (
            "window.__desktopBridgeReceive("
            + _js_obj({"type": msg_type, **data})
            + ");"
        )
        self._web_view.page().runJavaScript(js)

    def set_window_title(self, title: str):
        pass  # embedded — no separate window

    def set_window_size(self, width: int, height: int):
        pass  # embedded — layout controlled

    def close(self):
        pass  # cleanup handled by Qt

    # ── Widget access ───────────────────────────────────────────────────

    def get_widget(self) -> QWidget:
        return self._web_view

    # ── Internals ───────────────────────────────────────────────────────

    def _on_page_loaded(self, ok: bool):
        if not ok:
            self._on_closed()
            return

        # Route to the correct SPA page by setting the hash fragment
        hash_fragment = ""
        if "#" in self._url:
            hash_fragment = self._url.split("#", 1)[1]

        js_inject = """
window.dacDesktop = {
    loadConfig: function(projectId, title, configJson) {
        var msg = JSON.stringify({
            action: "message",
            type: "loadConfig",
            data: {
                projectId: projectId,
                title: title,
                configJson: configJson
            }
        });
        console.log("DAC_BRIDGE:" + msg);
    }
};
window.__desktopBridgeReceive = function(data) {
    if (typeof window.desktopReceiveConfig === 'function' && data.type === 'receiveConfig') {
        window.desktopReceiveConfig(data.title, data.configJson);
    }
};
"""
        if hash_fragment:
            js_inject += f"window.location.hash = {_js_str(hash_fragment)};"

        self._web_view.page().runJavaScript(js_inject)

    def _on_bridge_raw(self, payload: str):
        msg = BridgeMessage.from_json(payload)
        if msg:
            self._on_message(msg)


def _js_obj(d: dict) -> str:
    import json as _json
    return _json.dumps(d, ensure_ascii=False)


def _js_str(s: str) -> str:
    import json as _json
    return _json.dumps(s, ensure_ascii=False)
