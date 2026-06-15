# Bugfix Report

## Summary
Google Drive storage and in-app Drive image preview are production-verified. The app now uploads book files and guard near/far photos to Google Drive through OAuth, writes Drive URLs and attachment metadata to Google Sheets, and lets admins/officers preview submitted images inside Streamlit without opening Drive manually.

## Bugs Found
| Bug | Root cause | Fix summary | Verification |
|---|---|---|---|
| Uploads used local `uploads/...` paths | Storage module only had local filesystem upload | Added Google Drive backend with the same `upload_file(...)` return contract | Unit tests and production upload verification |
| Service-account upload could not write to normal My Drive folders | Service accounts have no personal My Drive storage quota | Added OAuth Drive credential mode and refresh-token helper | Production Drive write check passed after OAuth secrets were configured |
| OAuth upload failed with `invalid_scope` | The app reused Sheets-related scopes for OAuth Drive refresh | Split OAuth Drive scope to `https://www.googleapis.com/auth/drive` only | Production Settings Drive write check uploaded and trashed a test file |
| Google Drive errors were too generic | Drive API exceptions were collapsed into one message | Added clearer Drive configuration/error handling | Earlier failure paths showed friendly Thai errors without partial request rows |
| Uploaded file objects could be skipped | Streamlit `UploadedFile` truthiness was used instead of `is not None` | Updated upload guards for book files and optional extra photos | Regression tests |
| Reviewers could only open Drive links manually | UI did not fetch private Drive image bytes | Added `modules/drive_preview.py` and embedded preview UI | Production admin home and detail page rendered two image elements from Drive bytes |
| Legacy local file links looked durable | Old `uploads/...` values could be rendered as normal links | Added local-path warning and Settings audit count | Existing behavior verified during QA |
| Request detail displayed raw guard status codes | Detail metric used internal package status directly | Mapped the metric through `GUARD_TASK_STATUS_LABELS` | Automated tests passed; ready for deploy |

## Files Changed
- `README.md`
- `modules/storage.py`
- `modules/drive_preview.py`
- `modules/home.py`
- `modules/ui.py`
- `pages/02_บันทึกหนังสือ.py`
- `pages/04_รายละเอียดหนังสือ.py`
- `pages/06_ส่งงาน_รปภ.py`
- `pages/08_ตั้งค่า.py`
- `requirements.txt`
- `scripts/generate_drive_oauth_refresh_token.py`
- `tests/test_drive_preview.py`
- `tests/test_storage.py`
- `tests/test_upload_pages.py`
- `TEST_REPORT.md`
- `BUGFIX_REPORT.md`

## Automated Verification
- `python -m pytest -q`: 71 passed

## Production Verification
- Date/time: 2026-06-15 02:21 +07
- Commit tested: `572c486` for OAuth Drive upload and preview
- Production app loaded to role selector with no raw traceback.
- Admin PIN `1234` entered admin mode.
- Settings Drive connection check passed.
- Settings Drive write check passed: test file uploaded, then trashed.
- Officer created `QA-PROD-OAUTHPDF-20260615-020402` with a book PDF uploaded to Drive.
- Requests sheet stored a Drive URL in `book_file_url`.
- Attachments sheet stored the book metadata row.
- Guard accepted the package, submitted near/far PNG photos, and saw `ส่งงานแล้ว รอเจ้าหน้าที่ตรวจ`.
- Guard_Submissions sheet stored near/far Drive URLs.
- Attachments sheet stored two `guard_photo` rows with `image/png`.
- Admin home showed the submitted package in `งานรอยืนยัน`.
- Admin home rendered two visible `img` elements for near/far photos using app-served media URLs.
- Admin confirmed the package done; Guard_Tasks status became `เสร็จสิ้น`.
- Request detail rendered submitted photo previews inside Streamlit.
- Partial QA rows `QA-PROD-OAUTH-20260615-020000` and `QA-PROD-OAUTHFILE-20260615-020146` were cancelled through admin UI with note `ข้อมูลทดสอบ production QA`.

## Security Note
OAuth and service-account credentials were pasted into chat during setup. Rotate the OAuth client secret, refresh token, and service-account private key after this verification round. Do not commit secrets.
