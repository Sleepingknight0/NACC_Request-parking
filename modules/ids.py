from __future__ import annotations

import random
import string
from datetime import datetime


def make_id(prefix: str, now: datetime | None = None) -> str:
    """Return an MVP-safe ID such as REQ-20260613-153012-A7K3."""
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix.upper()}-{timestamp}-{suffix}"
