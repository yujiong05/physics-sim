# -*- coding: utf-8 -*-
"""
教材长图：按所在滚动区宽度动态缩放，减少宽屏下两侧留白。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class ScalableTextbookImage(QWidget):
    """
    若 ``image_path`` 存在且可解码，则保留原始 QPixmap，在 ``resizeEvent`` 中
    ``scaledToWidth``；否则显示占位文字。
    """

    def __init__(
        self,
        image_path: Path,
        *,
        decode_fail_text: str,
        missing_file_text: str,
        horizontal_margin: int = 24,
        max_width: int = 1280,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._horizontal_margin = horizontal_margin
        self._max_width = max_width
        self._orig: Optional[QPixmap] = None
        self._has_image = False

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        if image_path.is_file():
            pix = QPixmap(str(image_path))
            if pix.isNull():
                self._label.setWordWrap(True)
                self._label.setText(decode_fail_text)
            else:
                self._orig = pix
                self._has_image = True
                self._label.setScaledContents(False)
        else:
            self._label.setWordWrap(True)
            self._label.setText(missing_file_text)

    def showEvent(self, event) -> None:  # noqa: ANN001
        super().showEvent(event)
        if self._has_image and self._orig is not None:
            self._apply_scale()

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        if self._has_image and self._orig is not None:
            self._apply_scale()

    def _apply_scale(self) -> None:
        assert self._orig is not None
        w_avail = max(1, self.width())
        candidate = max(0, w_avail - self._horizontal_margin)
        if candidate <= 0:
            return
        target_w = int(min(max(candidate, 120), self._max_width))
        scaled = self._orig.scaledToWidth(target_w, Qt.SmoothTransformation)
        self._label.setPixmap(scaled)
