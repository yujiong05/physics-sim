# -*- coding: utf-8 -*-
"""DeepSeek Chat Completions（OpenAI 兼容接口），不含界面代码。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 60.0


class DeepSeekChatError(Exception):
    """面向用户的简短说明；可选附加 detail 供调试（勿展示给用户）。"""

    def __init__(self, message: str, *, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.user_message = message
        self.detail = detail


def chat_completion(
    api_key: str,
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
    timeout: Optional[float] = None,
) -> str:
    """
    调用 DeepSeek chat completions，返回助手文本内容。

    Parameters
    ----------
    api_key :
        Bearer 令牌；勿写入日志。
    messages :
        OpenAI 格式，如 [{"role":"system","content":"..."}, {"role":"user","content":"..."}]。
    """
    key = (api_key or "").strip()
    if not key:
        raise DeepSeekChatError("未配置 API 密钥，请先在菜单「设置 → DeepSeek API 密钥」中保存。")

    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    payload: Dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    t_out = float(timeout if timeout is not None else DEFAULT_TIMEOUT)

    try:
        with httpx.Client(timeout=t_out) as client:
            resp = client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException:
        raise DeepSeekChatError("请求超时，请稍后重试或检查网络。") from None
    except httpx.RequestError as exc:
        raise DeepSeekChatError("网络错误，无法连接 DeepSeek 服务。", detail=str(exc)) from None

    try:
        data = resp.json()
    except ValueError:
        raise DeepSeekChatError(
            "服务返回了无法解析的内容。",
            detail=resp.text[:500] if resp.text else None,
        ) from None

    if resp.status_code >= 400:
        err = data.get("error") if isinstance(data, dict) else None
        msg = None
        if isinstance(err, dict):
            msg = err.get("message")
        if not msg and isinstance(data, dict):
            msg = data.get("message")
        user = "请求被拒绝或密钥无效，请检查密钥与账户额度。"
        if resp.status_code == 401:
            user = "密钥无效或未授权，请在设置中核对 DeepSeek API 密钥。"
        elif resp.status_code == 429:
            user = "请求过于频繁或额度不足，请稍后再试。"
        raise DeepSeekChatError(user, detail=str(msg or resp.text)[:800])

    if not isinstance(data, dict):
        raise DeepSeekChatError("响应格式异常。", detail=str(type(data)))

    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise DeepSeekChatError("响应中无有效回复。", detail=str(data)[:500])

    first = choices[0]
    if not isinstance(first, dict):
        raise DeepSeekChatError("响应格式异常。", detail=str(first))

    message = first.get("message")
    if not isinstance(message, dict):
        raise DeepSeekChatError("响应格式异常。", detail=str(first))

    content = message.get("content")
    if content is None:
        raise DeepSeekChatError("模型未返回文本内容。", detail=str(message))

    text = str(content).strip()
    if not text:
        raise DeepSeekChatError("模型返回空内容，请换种方式提问。")

    return text
