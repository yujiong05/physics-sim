# -*- coding: utf-8 -*-
"""教学页 DeepSeek 助教：发送、线程、禁用控件。"""

from __future__ import annotations

from typing import List, Optional, Union

from PyQt5.QtWidgets import QLineEdit, QMessageBox, QTextBrowser, QWidget

from ai.chat_worker import DeepSeekChatWorker
from ai.teaching_system_prompt import lab_system_prompt
from settings.app_settings import get_deepseek_api_key
from ui.markdown_viewer import MarkdownFormulaViewer


class TeachingChatHelper:
    """挂接到 MarkdownFormulaViewer + QLineEdit + 发送按钮。"""

    def __init__(self, parent: QWidget, lab_key: str) -> None:
        self._parent = parent
        self._lab_key = lab_key
        self._viewer: Optional[Union[QTextBrowser, MarkdownFormulaViewer]] = None
        self._inp: Optional[QLineEdit] = None
        self._btn: Optional[QWidget] = None
        self._placeholder_original = ""
        self._worker: Optional[DeepSeekChatWorker] = None
        self._history: List[str] = []

    def attach(self, viewer: Union[QTextBrowser, MarkdownFormulaViewer], inp: QLineEdit, send_btn: QWidget) -> None:
        self._viewer = viewer
        self._inp = inp
        self._btn = send_btn
        self._placeholder_original = inp.placeholderText()

    def on_send(self) -> None:
        if self._viewer is None or self._inp is None or self._btn is None:
            return
        text = self._inp.text().strip()
        if not text:
            return
        if self._worker is not None and self._worker.isRunning():
            return

        api_key = get_deepseek_api_key()
        if not api_key:
            QMessageBox.information(
                self._parent,
                "需要 API 密钥",
                "请先在主窗口菜单「设置 → DeepSeek API 密钥」中保存您的密钥后再提问。",
            )
            return

        # 追加用户消息
        if isinstance(self._viewer, MarkdownFormulaViewer):
            self._viewer.append_markdown(text, role="user")
        else:
            self._history.append(f"### 👤 我\n{text}\n")
            self._refresh_viewer()
            
        self._inp.clear()

        self._btn.setEnabled(False)
        self._inp.setReadOnly(True)
        self._inp.setPlaceholderText("正在生成回复…")

        system_content = lab_system_prompt(self._lab_key)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": text},
        ]

        worker = DeepSeekChatWorker(api_key, messages, parent=self._parent)
        self._worker = worker
        worker.finished_success.connect(self._on_success)
        worker.finished_error.connect(self._on_error)
        worker.finished.connect(self._on_thread_finished)
        worker.start()

    def _refresh_viewer(self, scroll: bool = False) -> None:
        """此方法主要用于初始化或兼容旧模式。"""
        if self._viewer is None:
            return
        full_md = "\n---\n".join(self._history)
        if isinstance(self._viewer, MarkdownFormulaViewer):
            self._viewer.set_markdown(full_md)
        else:
            self._viewer.setText(full_md)

    def _on_success(self, reply: str) -> None:
        if isinstance(self._viewer, MarkdownFormulaViewer):
            self._viewer.append_markdown(reply, role="assistant")
        else:
            self._history.append(f"### 🤖 AI 助教\n{reply}\n")
            self._refresh_viewer(scroll=True)

    def _on_error(self, message: str) -> None:
        error_msg = f"请求失败：{message}"
        if isinstance(self._viewer, MarkdownFormulaViewer):
            self._viewer.append_markdown(error_msg, role="system")
        else:
            self._history.append(f"> ❌ {error_msg}\n")
            self._refresh_viewer(scroll=True)

    def _on_thread_finished(self) -> None:
        if self._btn is not None:
            self._btn.setEnabled(True)
        if self._inp is not None:
            self._inp.setReadOnly(False)
            self._inp.setPlaceholderText(self._placeholder_original)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
