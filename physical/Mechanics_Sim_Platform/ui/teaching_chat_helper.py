# -*- coding: utf-8 -*-
"""教学页 DeepSeek 助教：发送、线程、禁用控件。"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QLineEdit, QMessageBox, QTextBrowser, QWidget

from ai.chat_worker import DeepSeekChatWorker
from ai.teaching_system_prompt import lab_system_prompt
from settings.app_settings import get_deepseek_api_key
from ui.chat_bubbles import assistant_bubble_html, error_hint_html, user_bubble_html


class TeachingChatHelper:
    """挂接到 QTextBrowser + QLineEdit + 发送按钮。"""

    def __init__(self, parent: QWidget, lab_key: str) -> None:
        self._parent = parent
        self._lab_key = lab_key
        self._log: Optional[QTextBrowser] = None
        self._inp: Optional[QLineEdit] = None
        self._btn: Optional[QWidget] = None
        self._placeholder_original = ""
        self._worker: Optional[DeepSeekChatWorker] = None

    def attach(self, log: QTextBrowser, inp: QLineEdit, send_btn: QWidget) -> None:
        self._log = log
        self._inp = inp
        self._btn = send_btn
        self._placeholder_original = inp.placeholderText()

    def on_send(self) -> None:
        if self._log is None or self._inp is None or self._btn is None:
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

        self._log.append(user_bubble_html(text))
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

    def _on_success(self, reply: str) -> None:
        if self._log is not None:
            self._log.append(assistant_bubble_html(reply))

    def _on_error(self, message: str) -> None:
        if self._log is not None:
            self._log.append(error_hint_html(message))

    def _on_thread_finished(self) -> None:
        if self._btn is not None:
            self._btn.setEnabled(True)
        if self._inp is not None:
            self._inp.setReadOnly(False)
            self._inp.setPlaceholderText(self._placeholder_original)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
