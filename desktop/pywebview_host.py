"""pywebview subprocess host.

Entry point spawned by PyWebViewBridge. It:
  - Reads JSON Lines from stdin and dispatches to the web view.
  - Exposes a `sendToDesktop` JS API for the web page.
  - Notifies the parent on window close.

Usage:
    python desktop/pywebview_host.py --url http://server/#/desktop
                                     [--title "DAC"] [--width 800] [--height 600]
"""

from __future__ import annotations

import argparse
import json
import sys
import threading


class _WebViewHost:
    """Wraps pywebview and handles stdin/stdout IPC."""

    def __init__(self):
        self._window = None
        self._running = True

    # ── pywebview JS API (exposed as pywebview.api.*) ───────────────────

    def sendToDesktop(self, msg_json: str):
        """Called from JS: pywebview.api.sendToDesktop(JSON.stringify({type, ...}))"""
        try:
            data = json.loads(msg_json)
        except json.JSONDecodeError:
            return
        msg = {"action": "message", "type": data.get("type", ""), "data": data}
        _emit(msg)

    # ── lifecycle ───────────────────────────────────────────────────────

    def run(self, url: str, title: str, width: int, height: int):
        import webview

        self._window = webview.create_window(
            title=title,
            url=url,
            width=width,
            height=height,
            js_api=self,
        )
        self._window.events.closed += self._on_closed

        # Start stdin reader in a background thread
        stdin_thread = threading.Thread(target=self._read_stdin, daemon=True)
        stdin_thread.start()

        webview.start()

    # ── internals ───────────────────────────────────────────────────────

    def _read_stdin(self):
        """Read JSON Lines from stdin and dispatch."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            action = msg.get("action", "")
            if action == "sendToWeb":
                self._dispatch_to_web(msg)
            elif action == "setWindowTitle":
                self._set_title(msg.get("title", ""))
            elif action == "setWindowSize":
                self._set_size(msg.get("width", 800), msg.get("height", 600))
            elif action == "close":
                self._close_window()
                break
            # Ignore unknown actions

    def _dispatch_to_web(self, msg: dict):
        if not self._window:
            return
        data = msg.get("data", {})
        msg_type = msg.get("type", "")
        payload = json.dumps({"type": msg_type, **data}, ensure_ascii=False)
        js = f"window.__desktopBridgeReceive({payload});"
        try:
            self._window.evaluate_js(js)
        except Exception:
            pass

    def _set_title(self, title: str):
        if self._window:
            try:
                self._window.set_title(title)
            except Exception:
                pass

    def _set_size(self, width: int, height: int):
        if self._window:
            try:
                self._window.resize(width, height)
            except Exception:
                pass

    def _close_window(self):
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
        self._running = False

    def _on_closed(self):
        _emit({"action": "windowClosed"})


def _emit(obj: dict):
    """Write a JSON line to stdout (IPC back to parent process)."""
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description="pywebview host for DAC Desktop")
    parser.add_argument("--url", required=True, help="Web app URL to load")
    parser.add_argument("--title", default="DAC Desktop", help="Window title")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    args = parser.parse_args()

    host = _WebViewHost()
    host.run(args.url, args.title, args.width, args.height)


if __name__ == "__main__":
    main()
