"""Desktop bridge abstraction layer.

Defines the IPC protocol and abstract base classes for connecting
a PyQt desktop application with a web frontend running in a WebView.

Protocol (JSON Lines over stdin/stdout for pywebview subprocess):

    PyQt → Web:
      {"action":"sendToWeb","type":"<type>","data":{...}}
      {"action":"setWindowTitle","title":"..."}
      {"action":"setWindowSize","width":800,"height":600}
      {"action":"close"}

    Web → PyQt:
      {"action":"message","type":"<type>","data":{...}}
      {"action":"windowClosed"}
      {"action":"error","message":"..."}
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

# ── Protocol constants ───────────────────────────────────────────────────

ACTION_MESSAGE = "message"
ACTION_WINDOW_CLOSED = "windowClosed"
ACTION_ERROR = "error"

ACTION_SEND_TO_WEB = "sendToWeb"
ACTION_SET_TITLE = "setWindowTitle"
ACTION_SET_SIZE = "setWindowSize"
ACTION_CLOSE = "close"

# Known web → desktop message types
TYPE_LOAD_CONFIG = "loadConfig"

# Known desktop → web message types
TYPE_RECEIVE_CONFIG = "receiveConfig"


@dataclass
class BridgeMessage:
    """Normalised bridge message regardless of backend."""
    action: str
    msg_type: str = ""
    data: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, raw: str | bytes) -> BridgeMessage | None:
        try:
            obj = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
        return cls(
            action=obj.get("action", ""),
            msg_type=obj.get("type", ""),
            data=obj.get("data", {}),
        )

    @classmethod
    def from_dict(cls, obj: dict) -> BridgeMessage | None:
        if not isinstance(obj, dict):
            return None
        return cls(
            action=obj.get("action", ""),
            msg_type=obj.get("type", ""),
            data=obj.get("data", {}),
        )

    def to_dict(self) -> dict:
        d: dict = {"action": self.action, "type": self.msg_type, "data": self.data}
        # Remove empty fields for compactness
        if not self.msg_type:
            del d["type"]
        if not self.data:
            del d["data"]
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ── Abstract bridge ──────────────────────────────────────────────────────

class BaseBridge(ABC):
    """Abstract bridge between desktop app and web frontend.

    Subclasses implement the specific IPC mechanism (Qt WebEngine, pywebview, …).
    """

    @abstractmethod
    def start(self, url: str, title: str = "DAC Desktop",
              width: int = 800, height: int = 600):
        """Launch the web view and begin listening for messages."""

    @abstractmethod
    def send_to_web(self, msg_type: str, data: dict):
        """Push a typed message into the web frontend."""

    @abstractmethod
    def set_window_title(self, title: str):
        """Change the web view window title."""

    @abstractmethod
    def set_window_size(self, width: int, height: int):
        """Resize the web view window."""

    @abstractmethod
    def close(self):
        """Close the web view and release resources."""


# ── Callback types ───────────────────────────────────────────────────────

OnMessageCallback = Callable[[BridgeMessage], None]
OnClosedCallback = Callable[[], None]


# ── Factory ──────────────────────────────────────────────────────────────

class BridgeFactory:
    """Creates the appropriate bridge backend."""

    @staticmethod
    def create(backend: str, on_message: OnMessageCallback,
               on_closed: OnClosedCallback) -> BaseBridge:
        if backend == "qt":
            from .qt_bridge import QtWebEngineBridge
            return QtWebEngineBridge(on_message, on_closed)
        elif backend == "pywebview":
            from .pywebview_bridge import PyWebViewBridge
            return PyWebViewBridge(on_message, on_closed)
        else:
            raise ValueError(f"Unknown bridge backend: {backend}")

    @staticmethod
    def available_backends() -> list[str]:
        backends: list[str] = []
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView  # noqa: F401
            backends.append("qt")
        except ImportError:
            pass
        try:
            import webview  # noqa: F401
            backends.append("pywebview")
        except ImportError:
            pass
        return backends or ["qt"]
