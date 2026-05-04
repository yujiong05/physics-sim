# -*- coding: utf-8 -*-
"""应用级配置持久化（QSettings）。"""

from __future__ import annotations

from PyQt5.QtCore import QSettings

ORG_NAME = "MechanicsSim"
APP_NAME = "MechanicsSimPlatform"
KEY_DEEPSEEK_API = "deepseek/api_key"


def _settings() -> QSettings:
    return QSettings(ORG_NAME, APP_NAME)


def get_deepseek_api_key() -> str:
    v = _settings().value(KEY_DEEPSEEK_API, "", type=str)
    return (v or "").strip()


def set_deepseek_api_key(key: str) -> None:
    s = _settings()
    s.setValue(KEY_DEEPSEEK_API, key.strip())
    s.sync()


def clear_deepseek_api_key() -> None:
    s = _settings()
    s.remove(KEY_DEEPSEEK_API)
    s.sync()
