# -*- coding: utf-8 -*-
"""DeepSeek API 密钥配置对话框。"""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from settings.app_settings import clear_deepseek_api_key, get_deepseek_api_key, set_deepseek_api_key


class DeepSeekApiKeyDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("DeepSeek API 密钥")
        self.setMinimumWidth(420)

        hint = QLabel(
            "密钥仅保存在本机配置中（注册表或配置文件，多为明文）。"
            "请勿在公共电脑上保存；更换密钥可覆盖保存。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#64748b;font-size:10pt;")

        self._edit = QLineEdit()
        self._edit.setEchoMode(QLineEdit.Password)
        self._edit.setPlaceholderText("粘贴 DeepSeek API Key…")
        self._edit.setClearButtonEnabled(True)

        form = QFormLayout()
        form.addRow("API 密钥：", self._edit)

        had = bool(get_deepseek_api_key())
        if had:
            note = QLabel("当前已保存过密钥；输入新内容并保存可覆盖；留空保存无效。")
            note.setWordWrap(True)
            note.setStyleSheet("color:#334155;font-size:10pt;")
        else:
            note = QLabel("尚未保存密钥。请从 DeepSeek 开放平台获取 API Key。")
            note.setWordWrap(True)
            note.setStyleSheet("color:#334155;font-size:10pt;")

        buttons = QDialogButtonBox()
        btn_save = QPushButton("保存")
        btn_clear = QPushButton("清除密钥")
        btn_cancel = QPushButton("取消")
        buttons.addButton(btn_save, QDialogButtonBox.AcceptRole)
        buttons.addButton(btn_clear, QDialogButtonBox.ActionRole)
        buttons.addButton(btn_cancel, QDialogButtonBox.RejectRole)
        btn_save.clicked.connect(self._on_save)
        btn_clear.clicked.connect(self._on_clear)
        btn_cancel.clicked.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addWidget(hint)
        lay.addWidget(note)
        lay.addLayout(form)
        lay.addWidget(buttons)

    def _on_save(self) -> None:
        key = self._edit.text().strip()
        if not key:
            QMessageBox.warning(self, "无法保存", "请输入非空的 API 密钥后再保存。")
            return
        set_deepseek_api_key(key)
        self._edit.clear()
        QMessageBox.information(self, "已保存", "密钥已保存到本机。实验教学页的助教将使用该密钥调用 DeepSeek。")
        self.accept()

    def _on_clear(self) -> None:
        ret = QMessageBox.question(
            self,
            "清除密钥",
            "确定要清除本机已保存的 DeepSeek API 密钥吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return
        clear_deepseek_api_key()
        self._edit.clear()
        QMessageBox.information(self, "已清除", "密钥已从本机配置中移除。")
        self.accept()
