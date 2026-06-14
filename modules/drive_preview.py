from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from modules.storage import get_drive_service, is_local_upload_url

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
PDF_MIME_TYPE = "application/pdf"
LOCAL_UPLOAD_PREVIEW_WARNING = (
    "ไฟล์นี้เป็นลิงก์ชั่วคราวจากระบบเดิม ยังไม่สามารถแสดงในเว็บได้ "
    "ต้องอัปโหลดใหม่ไปยัง Google Drive"
)


def _cache_data(ttl: int):
    if st is not None and hasattr(st, "cache_data"):
        return st.cache_data(ttl=ttl, show_spinner=False)

    def decorator(func):
        return func

    return decorator


def is_google_drive_url(value: str | None) -> bool:
    text = str(value or "").strip().lower()
    return "drive.google.com" in text


def extract_drive_file_id(value: str | None) -> str | None:
    """
    Extract a Google Drive file ID from common Drive URLs or a raw file ID.
    """
    text = str(value or "").strip()
    if not text or is_local_upload_url(text):
        return None

    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", text):
        return text

    if not is_google_drive_url(text):
        return None

    file_path_match = re.search(r"/file/d/([^/?#]+)", text)
    if file_path_match:
        return file_path_match.group(1)

    parsed = urlparse(text)
    query = parse_qs(parsed.query)
    file_ids = query.get("id", [])
    if file_ids and file_ids[0]:
        return file_ids[0]

    return None


def get_drive_file_metadata(file_id: str) -> dict:
    service = get_drive_service()
    return service.files().get(
        fileId=file_id,
        fields="id,name,mimeType,size,webViewLink",
        supportsAllDrives=True,
    ).execute()


def download_drive_file_bytes(file_id: str) -> tuple[bytes, dict]:
    metadata = get_drive_file_metadata(file_id)
    data = service_download_bytes(file_id)
    return data, metadata


def service_download_bytes(file_id: str) -> bytes:
    service = get_drive_service()
    return service.files().get_media(fileId=file_id, supportsAllDrives=True).execute()


@_cache_data(ttl=600)
def _cached_load_drive_file(file_id: str) -> tuple[bytes, dict]:
    return download_drive_file_bytes(file_id)


def load_drive_file_for_preview(url_or_file_id: str) -> dict:
    file_id = extract_drive_file_id(url_or_file_id)
    if not file_id:
        return {
            "ok": False,
            "file_id": "",
            "file_name": "",
            "mime_type": "",
            "bytes": None,
            "error": "missing or invalid Google Drive file ID",
            "web_url": str(url_or_file_id or "").strip(),
        }

    try:
        data, metadata = _cached_load_drive_file(file_id)
        return {
            "ok": True,
            "file_id": file_id,
            "file_name": metadata.get("name", ""),
            "mime_type": metadata.get("mimeType", ""),
            "bytes": data,
            "error": None,
            "web_url": metadata.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view",
        }
    except Exception as exc:
        return {
            "ok": False,
            "file_id": file_id,
            "file_name": "",
            "mime_type": "",
            "bytes": None,
            "error": str(exc),
            "web_url": f"https://drive.google.com/file/d/{file_id}/view",
        }


def _link_button(label: str, url: str | None) -> None:
    if st is None:
        return
    text = str(url or "").strip()
    if text:
        st.link_button(label, text, use_container_width=True)


def _render_image(data: bytes, label: str) -> None:
    if st is None:
        return
    try:
        st.image(data, caption=label, use_container_width=True)
    except TypeError:  # pragma: no cover - older Streamlit compatibility
        st.image(data, caption=label, use_column_width=True)


def render_drive_image_preview(url_or_file_id: str | None, label: str) -> None:
    if st is None:
        return

    text = str(url_or_file_id or "").strip()
    if not text:
        st.caption("ไม่มีไฟล์")
        return

    if is_local_upload_url(text):
        st.warning(LOCAL_UPLOAD_PREVIEW_WARNING)
        return

    file_id = extract_drive_file_id(text)
    if not file_id:
        st.warning("ยังไม่รองรับลิงก์ไฟล์นี้")
        _link_button("เปิดไฟล์", text)
        return

    result = load_drive_file_for_preview(text)
    if not result["ok"]:
        st.warning("โหลดรูปจาก Google Drive ไม่สำเร็จ")
        _link_button("เปิดไฟล์ใน Google Drive", result.get("web_url"))
        with st.expander("รายละเอียดสำหรับผู้ดูแล"):
            st.code(result.get("error") or "")
        return

    mime_type = str(result.get("mime_type") or "").lower()
    file_name = str(result.get("file_name") or label)
    caption = f"{label}: {file_name}" if file_name else label

    if mime_type in IMAGE_MIME_TYPES or mime_type.startswith("image/"):
        _render_image(result["bytes"], caption)
        _link_button("เปิดใน Google Drive", result.get("web_url"))
        return

    if mime_type == PDF_MIME_TYPE:
        st.info("ไฟล์นี้เป็น PDF")
        _link_button("เปิดไฟล์ใน Google Drive", result.get("web_url"))
        st.download_button(
            "ดาวน์โหลดไฟล์",
            result["bytes"],
            file_name=file_name or "file.pdf",
            mime=mime_type,
            use_container_width=True,
        )
        return

    st.warning("ยังไม่รองรับการแสดงตัวอย่างไฟล์ชนิดนี้")
    _link_button("เปิดไฟล์ใน Google Drive", result.get("web_url"))
