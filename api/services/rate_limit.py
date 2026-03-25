from __future__ import annotations

import time
from collections import deque

WINDOW_SECONDS = 60.0
MAX_REQUESTS = 30
_REQUESTS: dict[str, deque[float]] = {}


def check_rate_limit(identity: str) -> bool:
    now = time.time()
    q = _REQUESTS.setdefault(identity, deque())
    while q and (now - q[0]) > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= MAX_REQUESTS:
        return False
    q.append(now)
    return True
