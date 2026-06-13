from __future__ import annotations

import json
from datetime import datetime

from modules.constants import ID_PREFIXES
from modules.ids import make_id
from modules.sheets import append_rows


def write_audit_log(
    action: str,
    target_table: str,
    target_id: str,
    old_value: dict | list | str | None = None,
    new_value: dict | list | str | None = None,
    user: str | None = None,
) -> None:
    def serialize(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    append_rows(
        "Audit_Log",
        [
            {
                "log_id": make_id(ID_PREFIXES["Audit_Log"]),
                "action": action,
                "target_table": target_table,
                "target_id": target_id,
                "old_value": serialize(old_value),
                "new_value": serialize(new_value),
                "user": user or "",
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        ],
    )
