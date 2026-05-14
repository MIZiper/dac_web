"""Config panel widget — shows project config in a tree view.

Extracted from desktop_app.py so it can be reused regardless of bridge backend.
"""

from __future__ import annotations

import json

from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)


class ConfigPanel(QWidget):
    """Right-side panel that displays a DAC project config in a tree.

    Calls `on_send_back(title: str, config_json: str)` when the user asks
    to send the (possibly edited) config back to the web for saving.
    """

    def __init__(self, on_send_back=None, parent=None):
        super().__init__(parent)
        self.on_send_back = on_send_back

        self._project_id: str | None = None
        self._title: str = ""
        self._wrapped: dict | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.title_label = QLabel(
            "No project loaded — click 'Open in Desktop' in the web view"
        )
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        meta = QGroupBox("Info")
        meta_form = QVBoxLayout(meta)
        self.meta_text = QLabel("")
        self.meta_text.setWordWrap(True)
        meta_form.addWidget(self.meta_text)
        layout.addWidget(meta)

        cfg = QGroupBox("DAC Config")
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
        save_btn = QPushButton("Send to Web  Save to Server")
        save_btn.clicked.connect(self._send_back)
        save_layout.addWidget(save_btn)
        layout.addWidget(save_group)

    # ── public API ──────────────────────────────────────────────────────

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
        self.meta_text.setText(
            f"ID: {project_id}\nCreator: {creator}\nVersion: {version}"
        )
        self._populate_tree(config)

    # ── internals ───────────────────────────────────────────────────────

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
                    disp = (
                        v.get("name", v.get("_class_", ""))
                        if isinstance(v, dict)
                        else json.dumps(v, ensure_ascii=False)
                    )
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
        if not self._wrapped or not self._project_id:
            return
        title = self.title_edit.text().strip() or self._title
        if isinstance(self._wrapped, dict):
            self._wrapped.setdefault("dac_web", {})["title"] = title
        payload = json.dumps(self._wrapped, ensure_ascii=False)
        if self.on_send_back:
            self.on_send_back(title, payload)
