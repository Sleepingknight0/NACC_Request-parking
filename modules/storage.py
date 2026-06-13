from __future__ import annotations

from pathlib import Path


UPLOAD_DIR = Path("uploads")


def upload_file(file, folder: str, prefix: str) -> dict:
    """
    Local-development storage fallback.

    Production should replace this with Google Drive or Cloud Storage upload and
    keep the same return shape.
    """
    if file is None:
        return {"file_name": "", "file_url": "", "mime_type": "", "storage_key": ""}

    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    original_name = getattr(file, "name", "upload.bin")
    mime_type = getattr(file, "type", "")
    safe_name = "".join(ch for ch in original_name if ch.isalnum() or ch in "._- กขคงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮะาิีึืุูเแโใไำ่้๊๋์")
    file_name = f"{prefix}_{safe_name}".strip("_")
    path = target_dir / file_name

    if hasattr(file, "getbuffer"):
        path.write_bytes(bytes(file.getbuffer()))
    elif hasattr(file, "getvalue"):
        path.write_bytes(file.getvalue())
    else:
        content = file.read()
        path.write_bytes(content)

    return {
        "file_name": file_name,
        "file_url": str(path.as_posix()),
        "mime_type": mime_type,
        "storage_key": str(path.as_posix()),
    }
