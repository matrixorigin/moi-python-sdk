"""回环 HTTP fixture 的代理环境，复用原 SDK 测试合同。"""

import os
from unittest.mock import patch

_LOCALHOST_NO_PROXY = ("127.0.0.1", "localhost", "::1")


def _with_localhost_no_proxy(value):
    entries = []
    seen = set()
    for item in (value or "").split(","):
        item = item.strip()
        if item and item not in seen:
            entries.append(item)
            seen.add(item)
    for item in _LOCALHOST_NO_PROXY:
        if item not in seen:
            entries.append(item)
            seen.add(item)
    return ",".join(entries)


def loopback_proxy_environment():
    return patch.dict(os.environ, {
        key: _with_localhost_no_proxy(os.environ.get(key))
        for key in ("NO_PROXY", "no_proxy")
    })
