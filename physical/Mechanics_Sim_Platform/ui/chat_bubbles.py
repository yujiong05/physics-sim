# -*- coding: utf-8 -*-
"""聊天区 HTML 气泡（转义防 XSS）。"""

from __future__ import annotations

import html


def user_bubble_html(text: str) -> str:
    esc = html.escape(text)
    return (
        "<div style='margin:8px 0;text-align:right;'>"
        "<span style='display:inline-block;background:#dbeafe;color:#1e3a8a;"
        "padding:10px 12px;border-radius:12px;max-width:92%;word-break:break-word;'>"
        f"{esc}</span></div>"
    )


def assistant_bubble_html(text: str) -> str:
    body = html.escape(text).replace("\n", "<br/>")
    return (
        "<div style='margin:8px 0;text-align:left;'>"
        "<span style='display:inline-block;background:#fff;color:#334155;border:1px solid #e2e8f0;"
        "padding:10px 12px;border-radius:12px;max-width:92%;word-break:break-word;'>"
        f"{body}</span></div>"
    )


def error_hint_html(message: str) -> str:
    body = html.escape(message).replace("\n", "<br/>")
    return (
        "<div style='margin:8px 0;text-align:left;'>"
        "<span style='display:inline-block;background:#fef2f2;color:#991b1b;border:1px solid #fecaca;"
        "padding:10px 12px;border-radius:12px;max-width:92%;word-break:break-word;'>"
        f"{body}</span></div>"
    )
