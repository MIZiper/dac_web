"""Config panel widget — editable JSON view of project config.

Extracted from desktop_app.py so it can be reused regardless of bridge backend.
"""

from __future__ import annotations

import json

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)


class ConfigPanel(QWidget):
    """Panel that displays and lets the user edit a DAC project config.

    Shows project metadata, a raw JSON editor for the config, a title
    field, and a button to send the edited config back to the web for saving.

    Calls `on_send_back(title: str, config_json: str)` when the user clicks send.
    """

    def __init__(self, on_send_back=None, parent=None):
        super().__init__(parent)
        self.on_send_back = on_send_back

        self._project_id: str | None = None
        self._title: str = ""
        self._raw_config_json: str = ""
        self._wrapped: dict | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title label
        self.title_label = QLabel(
            "No project loaded — click 'Open in Desktop' in the web view"
        )
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Info
        meta = QGroupBox("Info")
        meta_form = QVBoxLayout(meta)
        self.meta_text = QLabel("")
        self.meta_text.setWordWrap(True)
        meta_form.addWidget(self.meta_text)
        layout.addWidget(meta)

        # Editable JSON
        cfg = QGroupBox("DAC Config (JSON — editable)")
        cfg_layout = QVBoxLayout(cfg)
        self.json_editor = QPlainTextEdit()
        self.json_editor.setFont(QFont("monospace", 10))
        self.json_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.json_editor.setTabStopDistance(20)
        cfg_layout.addWidget(self.json_editor)
        layout.addWidget(cfg, stretch=1)

        # Send-back bar
        save_group = QGroupBox("Send Back to Web for Saving")
        save_layout = QHBoxLayout(save_group)
        save_layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        save_layout.addWidget(self.title_edit)
        self.json_status = QLabel("")
        save_layout.addWidget(self.json_status)
        save_layout.addStretch()
        save_btn = QPushButton("Send to Web  Save to Server")
        save_btn.clicked.connect(self._send_back)
        save_layout.addWidget(save_btn)
        layout.addWidget(save_group)

    # ── public API ──────────────────────────────────────────────────────

    def load_config(self, project_id: str, title: str, config_json: str):
        self._project_id = project_id
        self._title = title
        self._raw_config_json = config_json

        # Parse for metadata
        try:
            self._wrapped = json.loads(config_json)
        except json.JSONDecodeError:
            self._wrapped = None

        self.title_label.setText(f"Project: {title}")
        self.title_edit.setText(title)

        creator = (self._wrapped or {}).get("creator_name", "-") if self._wrapped else "-"
        version = (self._wrapped or {}).get("version", "-") if self._wrapped else "-"
        self.meta_text.setText(
            f"ID: {project_id}\nCreator: {creator}\nVersion: {version}"
        )

        # Show pretty-printed JSON in the editor
        try:
            pretty = json.dumps(json.loads(config_json), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pretty = config_json
        self.json_editor.setPlainText(pretty)
        self._update_json_status()
        self.json_editor.document().contentsChanged.connect(self._update_json_status)

    # ── internals ───────────────────────────────────────────────────────

    def _update_json_status(self):
        text = self.json_editor.toPlainText()
        try:
            json.loads(text)
            self.json_status.setText(" Valid JSON")
            self.json_status.setStyleSheet("color: green;")
        except json.JSONDecodeError as e:
            self.json_status.setText(f" Invalid: {e}")
            self.json_status.setStyleSheet("color: red;")

    def _send_back(self):
        if not self._project_id:
            return
        title = self.title_edit.text().strip() or self._title
        config_json = self.json_editor.toPlainText().strip()

        # Validate
        try:
            parsed = json.loads(config_json)
        except json.JSONDecodeError as e:
            self.json_status.setText(f" Cannot send: invalid JSON ({e})")
            self.json_status.setStyleSheet("color: red; font-weight: bold;")
            return

        self._wrapped = parsed
        # Inject updated title
        if isinstance(parsed, dict):
            parsed.setdefault("dac_web", {})["title"] = title
            config_json = json.dumps(parsed, ensure_ascii=False)

        if self.on_send_back:
            self.on_send_back(title, config_json)
