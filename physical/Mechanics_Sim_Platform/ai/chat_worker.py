# -*- coding: utf-8 -*-
"""后台线程调用 DeepSeek，避免阻塞 Qt UI。"""

from __future__ import annotations

from typing import Dict, List

from PyQt5.QtCore import QThread, pyqtSignal

from ai.deepseek_client import DeepSeekChatError, chat_completion


class DeepSeekChatWorker(QThread):
    finished_success = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, api_key: str, messages: List[Dict[str, str]], parent=None) -> None:
        super().__init__(parent)
        self._api_key = api_key
        self._messages = messages

    def run(self) -> None:
        try:
            text = chat_completion(self._api_key, self._messages)
            self.finished_success.emit(text)
        except DeepSeekChatError as exc:
            self.finished_error.emit(exc.user_message)
        except Exception as exc:  # noqa: BLE001 — 兜底展示
            self.finished_error.emit(f"请求异常：{exc}")
