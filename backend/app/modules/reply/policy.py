from __future__ import annotations

import re


_PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
_URL_RE = re.compile(r"https?://\S+")
_WECHAT_RE = re.compile(r"(微信|vx|Vx|VX)[:：]?\s*[A-Za-z0-9_-]{3,}")


def redact_sensitive(text: str) -> str:
    t = text or ""
    t = _URL_RE.sub("[链接已隐藏]", t)
    t = _PHONE_RE.sub("[号码已隐藏]", t)
    t = _WECHAT_RE.sub("[联系方式已隐藏]", t)
    return t


def enforce_style(text: str, max_len: int = 160) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"

