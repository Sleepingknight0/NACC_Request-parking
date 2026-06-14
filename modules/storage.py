from __future__ import annotations

import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from modules.sheets import GSHEETS_SCOPES, _normalize_private_key

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

try:
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover
    Credentials = None

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
except Exception:  # pragma: no cover
    build = None
    MediaIoBaseUpload = None


UPLOAD_DIR = Path("uploads")
DRIVE_MISSING_CONFIG_MESSAGE = "ยังไม่ได้ตั้งค่า Google Drive สำหรับเก็บไฟล์"
DRIVE_UPLOAD_FAILED_MESSAGE = "อัปโหลดไฟล์ไป Google Drive ไม่สำเร็จ"
DRIVE_FOLDER_KEYS = ("book_files", "guard_submissions", "generated_pdfs", "other")
DEFAULT_DRIVE_FOLDER_IDS = {
    "book_files": "1mhxxhIUUUse3_kUPJ8qA6xLIN0h1pOmx",
    "guard_submissions": "1Hi9EVC7sWk7ZnnhlUdp58s3mwjH1L7dQ",
    "generated_pdfs": "",
    "other": "",
}


class DriveStorageConfigError(RuntimeError):
    """Raised when Google Drive storage is selected but not configured."""


def describe_drive_upload_error(exc: Exception) -> str:
    text = str(exc or "")
    lower_text = text.lower()

    if "storagequotaexceeded" in lower_text or "service accounts do not have storage quota" in lower_text:
        return (
            "Service account ไม่มีพื้นที่เก็บไฟล์บน My Drive "
            "ต้องย้ายโฟลเดอร์ปลายทางไป Google Shared Drive หรือใช้ OAuth/domain-wide delegation"
        )

    if "insufficientfilepermissions" in lower_text or "permission" in lower_text or "403" in lower_text:
        return (
            "สิทธิ์ Google Drive ไม่พอ กรุณาแชร์โฟลเดอร์ให้ service account "
            "และให้สิทธิ์อัปโหลดไฟล์"
        )

    if "file not found" in lower_text or "404" in lower_text or "notfound" in lower_text:
        return "ไม่พบโฟลเดอร์ Google Drive กรุณาตรวจ folder ID"

    if "drive api" in lower_text and ("disabled" in lower_text or "not been used" in lower_text):
        return "ยังไม่ได้เปิดใช้งาน Google Drive API สำหรับโปรเจกต์นี้"

    return "กรุณาตรวจการตั้งค่า Google Drive และลองใหม่อีกครั้ง"


def _empty_file_meta() -> dict:
    return {
        "file_name": "",
        "file_url": "",
        "mime_type": "",
        "storage_key": "",
        "storage_backend": "",
        "drive_file_id": "",
    }


def _secret_get(*keys: str, default: Any = "") -> Any:
    if st is None:
        return default

    try:
        current: Any = st.secrets
        for key in keys:
            if hasattr(current, "get"):
                current = current.get(key, default)
            else:
                return default
        return current
    except Exception:
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _normalize_backend(value: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    if text in {"gdrive", "drive", "google_drive"}:
        return "google_drive"
    if text in {"local", "filesystem", "file_system"}:
        return "local"
    return text


def _app_storage_backend() -> str:
    env_value = os.getenv("PARKING_APP_STORAGE_BACKEND", "").strip()
    if env_value:
        return env_value.lower().replace("-", "_")
    return str(_secret_get("app", "storage_backend", default="csv") or "csv").strip().lower().replace("-", "_")


def get_drive_config() -> dict:
    connection = _secret_get("connections", "gdrive", default={}) or {}
    if not isinstance(connection, dict):
        connection = dict(connection)

    folder_config = connection.get("folders", {}) if hasattr(connection, "get") else {}
    if not isinstance(folder_config, dict):
        folder_config = dict(folder_config)

    folder_ids = {}
    env_keys = {
        "book_files": "PARKING_APP_GDRIVE_BOOK_FILES_FOLDER_ID",
        "guard_submissions": "PARKING_APP_GDRIVE_GUARD_SUBMISSIONS_FOLDER_ID",
        "generated_pdfs": "PARKING_APP_GDRIVE_GENERATED_PDFS_FOLDER_ID",
        "other": "PARKING_APP_GDRIVE_OTHER_FOLDER_ID",
    }
    for key in DRIVE_FOLDER_KEYS:
        folder_ids[key] = str(
            os.getenv(env_keys[key], "")
            or folder_config.get(key, "")
            or connection.get(f"{key}_folder_id", "")
            or DEFAULT_DRIVE_FOLDER_IDS.get(key, "")
            or ""
        ).strip()

    share_value = os.getenv("PARKING_APP_GDRIVE_SHARE_UPLOADED_FILES", "")
    if share_value == "":
        share_value = connection.get("share_uploaded_files", False)

    return {
        "root_folder_id": str(
            os.getenv("PARKING_APP_GDRIVE_ROOT_FOLDER_ID", "")
            or connection.get("root_folder_id", "")
            or ""
        ).strip(),
        "folders": folder_ids,
        "share_uploaded_files": _as_bool(share_value, default=False),
    }


def _has_drive_config() -> bool:
    config = get_drive_config()
    return bool(config["root_folder_id"] or any(config["folders"].values()))


def get_file_storage_backend() -> str:
    """
    File storage backend priority:
    1. Environment variable PARKING_APP_FILE_STORAGE_BACKEND
    2. Streamlit secrets [app].file_storage_backend
    3. Google Drive when the app itself uses Google Sheets
    4. Google Drive when Drive folder config is present
    5. Local filesystem fallback for development
    """
    env_value = os.getenv("PARKING_APP_FILE_STORAGE_BACKEND", "").strip()
    if env_value:
        return _normalize_backend(env_value)

    secret_value = _secret_get("app", "file_storage_backend", default="")
    if secret_value:
        return _normalize_backend(str(secret_value))

    if _app_storage_backend() in {"gsheets", "google_sheets", "google_sheets_connection"}:
        return "google_drive"

    if _has_drive_config():
        return "google_drive"

    return "local"


def is_local_upload_url(url: str | None) -> bool:
    text = str(url or "").strip()
    if not text:
        return False
    return text.startswith("uploads/") or text.startswith("uploads\\")


def is_drive_url(url: str | None) -> bool:
    text = str(url or "").strip().lower()
    if not text:
        return False
    if "drive.google.com" not in text:
        return False
    return any(marker in text for marker in ("/file/d/", "open?id=", "uc?id=", "uc?"))


def _sanitize_filename_part(value: str, *, allow_dot: bool = True) -> str:
    allowed_dot = "." if allow_dot else ""
    cleaned = re.sub(rf"[^\wก-๙{re.escape(allowed_dot)}-]+", "_", str(value or ""), flags=re.UNICODE)
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    cleaned = re.sub(r"_+", "_", cleaned).strip("._-")
    return cleaned or "file"


def make_safe_file_name(
    prefix: str,
    original_name: str,
    *,
    timestamp: str | None = None,
    max_length: int = 180,
) -> str:
    timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    original = str(original_name or "upload.bin").replace("\\", "/").split("/")[-1]
    suffix = Path(original).suffix
    suffix = suffix if re.fullmatch(r"\.[A-Za-z0-9]{1,12}", suffix or "") else ""
    stem = original[: -len(suffix)] if suffix else original

    clean_prefix = _sanitize_filename_part(prefix or "upload", allow_dot=False)
    clean_stem = _sanitize_filename_part(stem or "file")
    clean_name = f"{clean_prefix}_{timestamp}_{clean_stem}{suffix.lower()}"

    if len(clean_name) <= max_length:
        return clean_name

    suffix_len = len(suffix)
    base_budget = max(20, max_length - suffix_len)
    base = clean_name[:base_budget].rstrip("._-")
    return f"{base}{suffix.lower()}"


def _read_uploaded_file_bytes(file) -> bytes:
    if hasattr(file, "seek"):
        try:
            file.seek(0)
        except Exception:
            pass

    if hasattr(file, "getbuffer"):
        data = bytes(file.getbuffer())
    elif hasattr(file, "getvalue"):
        data = file.getvalue()
    else:
        data = file.read()

    if isinstance(data, str):
        data = data.encode("utf-8")

    if hasattr(file, "seek"):
        try:
            file.seek(0)
        except Exception:
            pass

    return bytes(data)


def _service_account_info() -> dict:
    if st is None or Credentials is None:
        raise RuntimeError("Google API backend is not available")

    try:
        service_account_info = dict(st.secrets.get("google_service_account", {}))
        if not service_account_info:
            connection_info = dict(st.secrets.get("connections", {}).get("gsheets", {}))
            if connection_info.get("type") == "service_account":
                service_account_info = connection_info
    except Exception as exc:
        raise RuntimeError("missing service account secrets") from exc

    if not service_account_info:
        raise RuntimeError("missing service account secrets")

    service_account_info["private_key"] = _normalize_private_key(service_account_info.get("private_key", ""))
    service_account_info.pop("spreadsheet", None)
    return service_account_info


def get_drive_service():
    if build is None or MediaIoBaseUpload is None or Credentials is None:
        raise RuntimeError("Google Drive API client is not installed")

    credentials = Credentials.from_service_account_info(
        _service_account_info(),
        scopes=list(GSHEETS_SCOPES),
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def get_service_account_email() -> str:
    try:
        return str(_service_account_info().get("client_email", "") or "")
    except Exception:
        return ""


def _folder_key(folder: str) -> str:
    key = str(folder or "other").replace("\\", "/").strip("/").split("/")[0]
    return key if key in DRIVE_FOLDER_KEYS else "other"


def _drive_query_escape(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace("'", "\\'")


def ensure_or_get_folder(folder: str, parent_id: str | None = None) -> str:
    """
    Return the configured Drive folder ID for a storage bucket.

    If a root folder is configured but a child folder ID is omitted, create or
    reuse a direct child folder under the root. This keeps setup simple while
    still avoiding service-account root uploads.
    """
    config = get_drive_config()
    key = _folder_key(folder)
    configured_folder_id = config["folders"].get(key, "")
    if configured_folder_id:
        return configured_folder_id

    root_folder_id = str(parent_id or config["root_folder_id"] or "").strip()
    if not root_folder_id:
        raise DriveStorageConfigError(DRIVE_MISSING_CONFIG_MESSAGE)

    service = get_drive_service()
    folder_name = key
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        "and trashed=false "
        f"and name='{_drive_query_escape(folder_name)}' "
        f"and '{_drive_query_escape(root_folder_id)}' in parents"
    )
    result = service.files().list(
        q=query,
        fields="files(id,name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=1,
    ).execute()
    files = result.get("files", [])
    if files:
        return files[0]["id"]

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [root_folder_id],
    }
    created = service.files().create(
        body=folder_metadata,
        fields="id",
        supportsAllDrives=True,
    ).execute()
    return created["id"]


def upload_file_to_local(file, folder: str, prefix: str) -> dict:
    if file is None:
        return _empty_file_meta()

    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    original_name = getattr(file, "name", "upload.bin")
    mime_type = str(getattr(file, "type", "") or "")
    file_name = make_safe_file_name(prefix, original_name)
    path = target_dir / file_name
    path.write_bytes(_read_uploaded_file_bytes(file))
    file_url = str(path.as_posix())

    return {
        "file_name": file_name,
        "file_url": file_url,
        "mime_type": mime_type,
        "storage_key": file_url,
        "storage_backend": "local",
        "drive_file_id": "",
    }


def upload_file_to_drive(file, folder: str, prefix: str) -> dict:
    if file is None:
        return _empty_file_meta()

    folder_id = ensure_or_get_folder(folder)
    service = get_drive_service()
    original_name = getattr(file, "name", "upload.bin")
    mime_type = str(getattr(file, "type", "") or "application/octet-stream")
    file_name = make_safe_file_name(prefix, original_name)
    media = MediaIoBaseUpload(
        io.BytesIO(_read_uploaded_file_bytes(file)),
        mimetype=mime_type,
        resumable=False,
    )
    body = {
        "name": file_name,
        "parents": [folder_id],
    }
    if mime_type:
        body["mimeType"] = mime_type

    created = service.files().create(
        body=body,
        media_body=media,
        fields="id,name,mimeType,webViewLink",
        supportsAllDrives=True,
    ).execute()
    file_id = created["id"]

    if get_drive_config()["share_uploaded_files"]:
        service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
            supportsAllDrives=True,
        ).execute()

    file_url = created.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"
    return {
        "file_name": created.get("name", file_name),
        "file_url": file_url,
        "mime_type": created.get("mimeType", mime_type),
        "storage_key": file_id,
        "storage_backend": "google_drive",
        "drive_file_id": file_id,
    }


def upload_file(file, folder: str, prefix: str) -> dict:
    """
    Upload a Streamlit UploadedFile and return metadata used by db.py.

    Return shape:
    {
      "file_name": str,
      "file_url": str,
      "mime_type": str,
      "storage_key": str,
      "storage_backend": str,
      "drive_file_id": str,
    }
    """
    if file is None:
        return _empty_file_meta()

    backend = get_file_storage_backend()
    if backend == "local":
        return upload_file_to_local(file, folder, prefix)
    if backend != "google_drive":
        raise RuntimeError(f"ไม่รองรับที่เก็บไฟล์: {backend}")

    try:
        return upload_file_to_drive(file, folder, prefix)
    except DriveStorageConfigError:
        raise
    except Exception as exc:
        raise RuntimeError(f"{DRIVE_UPLOAD_FAILED_MESSAGE}: {describe_drive_upload_error(exc)}") from exc


def check_drive_connection() -> dict:
    config = get_drive_config()
    target_folder_id = config["root_folder_id"] or next(
        (folder_id for folder_id in config["folders"].values() if folder_id),
        "",
    )
    if not target_folder_id:
        return {"ok": False, "error": DRIVE_MISSING_CONFIG_MESSAGE, "folders": {}}

    try:
        service = get_drive_service()
        root = service.files().get(
            fileId=target_folder_id,
            fields="id,name,mimeType",
            supportsAllDrives=True,
        ).execute()
        folder_results = {}
        for key, folder_id in config["folders"].items():
            if not folder_id:
                folder_results[key] = {"configured": False, "ok": False, "name": ""}
                continue
            meta = service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType",
                supportsAllDrives=True,
            ).execute()
            folder_results[key] = {"configured": True, "ok": True, "name": meta.get("name", "")}
        return {
            "ok": True,
            "root_name": root.get("name", ""),
            "root_configured": bool(config["root_folder_id"]),
            "share_uploaded_files": config["share_uploaded_files"],
            "folders": folder_results,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "folders": {}}


def check_drive_write_access(folder: str = "book_files") -> dict:
    try:
        folder_id = ensure_or_get_folder(folder)
        service = get_drive_service()
        file_name = f"nacc_drive_healthcheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        media = MediaIoBaseUpload(
            io.BytesIO(b"NACC Drive health check"),
            mimetype="text/plain",
            resumable=False,
        )
        created = service.files().create(
            body={"name": file_name, "parents": [folder_id]},
            media_body=media,
            fields="id,name,webViewLink",
            supportsAllDrives=True,
        ).execute()
        trashed = False
        try:
            service.files().update(
                fileId=created["id"],
                body={"trashed": True},
                fields="id,trashed",
                supportsAllDrives=True,
            ).execute()
            trashed = True
        except Exception:
            trashed = False
        return {
            "ok": True,
            "folder": _folder_key(folder),
            "file_id": created.get("id", ""),
            "file_name": created.get("name", file_name),
            "web_url": created.get("webViewLink", ""),
            "trashed": trashed,
        }
    except Exception as exc:
        return {
            "ok": False,
            "folder": _folder_key(folder),
            "error": describe_drive_upload_error(exc),
            "technical_error": str(exc),
        }


def get_drive_config_status() -> dict:
    config = get_drive_config()
    return {
        "file_storage_backend": get_file_storage_backend(),
        "root_folder_configured": bool(config["root_folder_id"]),
        "folder_configured": {key: bool(value) for key, value in config["folders"].items()},
        "share_uploaded_files": config["share_uploaded_files"],
    }
