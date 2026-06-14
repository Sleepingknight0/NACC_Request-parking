# Bugfix Report

## Summary
Google Drive storage and in-app Drive image preview are implemented. Production now detects the current Drive configuration before writing rows: both provided upload folders are readable, but still located in normal My Drive, so service-account upload is blocked with a clear Thai message and no partial request/submission row is written.

## Bugs Found
| Bug | Root cause | Fix summary | Verification |
|---|---|---|---|
| Uploads used local `uploads/...` paths | Storage module only had local filesystem upload | Added Google Drive backend with metadata return shape used by Sheets | Unit tests and production Settings show `google_drive` backend |
| Drive folders were readable but not upload-ready | Normal My Drive folders shared to a service account can be read, but service accounts cannot create owned files there | Added folder preflight using `driveId` and `canAddChildren`; Settings now shows `location` and `upload_ready` | Production Settings shows both folders as `My Drive` and `ยังไม่พร้อม` |
| Upload failure message was too generic | Drive API exceptions were collapsed into one message | Added error mapping for quota, permissions, missing folders, API disabled, and My Drive folder config | Production officer upload shows the exact Shared Drive fix |
| Streamlit Cloud kept stale imported storage code | Page scripts reloaded while `modules.storage` stayed cached in the running process | Reloaded `modules.storage` before importing storage functions on upload/settings pages | Production changed from quota API error to My Drive preflight error |
| Uploaded file objects could be skipped | Streamlit `UploadedFile` truthiness was used instead of `is not None` | Updated upload guards for book files and extra photos | Regression tests |
| Reviewers could only open Drive links manually | UI did not download Drive bytes for previews | Added `modules/drive_preview.py` and embedded image preview UI | Parser tests and page smoke checks |
| Legacy local file links looked durable | Old `uploads/...` values were rendered as links | Added local-path warning and Settings audit count | Production Settings local-file audit renders safely |

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
- `tests/test_drive_preview.py`
- `tests/test_storage.py`
- `tests/test_upload_pages.py`
- `TEST_REPORT.md`
- `BUGFIX_REPORT.md`

## Automated Verification
- `python -m pytest -q`: 67 passed
- Previous compile smoke check passed: `python -X utf8 -m compileall app.py streamlit_app.py modules pages tests`

## Production Verification
- Date/time: 2026-06-14 22:52 +07
- Commit tested: `3a921ee`
- Production app loaded to the role selector with no raw traceback.
- Admin PIN `1234` entered admin mode.
- Settings showed service account: `nacc-parking-streamlit@nacc-parking-streamlit.iam.gserviceaccount.com`.
- Drive read check passed for both configured folders.
- Drive readiness check showed:
  - `book_files`: `location = My Drive`, `upload_ready = ยังไม่พร้อม`
  - `guard_submissions`: `location = My Drive`, `upload_ready = ยังไม่พร้อม`
- Drive write check was blocked before upload with:
  - `โฟลเดอร์ Google Drive ปลายทางยังอยู่ใน My Drive service account อัปโหลดไฟล์บน production ไม่ได้เพราะไม่มีพื้นที่เก็บไฟล์ กรุณาสร้างหรือย้ายโฟลเดอร์ไป Google Shared Drive แล้วตั้งค่า folder ID ใหม่`
- Officer book-file upload showed the same preflight message.
- Google Sheets search for `QA-PROD-DRIVE-ERR-20260614-VERIFY`: `matched_row_count = 0`, confirming no partial request row was written.

## Production Blocker And Fix Plan
The current folder IDs still have no Shared Drive `driveId`; they are normal My Drive folders. Sharing a My Drive folder with the service account is not enough for uploads.

Fix plan:
1. Create or move the upload folders into a Google Shared Drive.
2. Grant `nacc-parking-streamlit@nacc-parking-streamlit.iam.gserviceaccount.com` Contributor or Content manager access.
3. Update Streamlit Secrets with the new Shared Drive folder IDs, or provide the new folder links so the defaults can be changed.
4. Rerun Settings Drive connection and upload checks.
5. Rerun officer book upload, guard near/far upload, admin photo preview, request detail preview, and QA cleanup.
