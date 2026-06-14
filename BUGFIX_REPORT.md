# Bugfix Report

## Summary
Implemented Google Drive-backed upload storage and in-app Drive photo preview. The app no longer needs production uploads to be saved as local `uploads/...` paths. Production deployment picked up the code, but full upload/preview QA is blocked until Drive folder IDs are configured in Streamlit Secrets.

## Bugs Found
| Bug | Root cause | Fix summary | Verification |
|---|---|---|---|
| Uploaded files were saved to local `uploads/...` paths | `modules/storage.py` only had a local filesystem implementation | Added Google Drive backend, service-account upload, configurable sharing, and compatible metadata return shape | Unit tests; production Settings shows `google_drive` backend |
| Production could silently keep using local storage | File storage backend was not separate from app data backend | Added `file_storage_backend` selection and Drive default when app storage is Google Sheets | Settings and tests verify backend selection |
| Missing Drive config was not visible | No storage health UI existed | Added Settings section for backend, root/folder config, Drive connection check, and local-upload audit | Production Settings rendered storage section |
| Reviewers had to open Drive manually to inspect guard photos | UI rendered links/flags, not image bytes | Added `modules/drive_preview.py` to fetch Drive bytes by service account and render `st.image` previews | Parser tests and local compile/smoke checks |
| Drive URLs needed robust parsing | Stored URLs may use `/file/d`, `open?id`, `uc?id`, or raw IDs | Added parser with tests and local-path rejection | `tests/test_drive_preview.py` |
| Existing local upload paths looked like durable links | `safe_file_link()` treated non-empty URLs as normal links | Added local upload warning and Drive URL classifier | Existing production local rows counted/warned in Settings |
| Upload filenames were not traceable to business records | Call sites used generic prefixes or internal request IDs | Book uploads now use `book_{book_no}`; guard photos use `guard_{book_no}_{near|far|extra}` | Code review and unit tests for sanitization |

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
- `TEST_REPORT.md`
- `BUGFIX_REPORT.md`

## Automated Verification
- `python -m pytest -q`: 60 passed
- `python -X utf8 -m compileall app.py streamlit_app.py modules pages tests`: passed
- Local Streamlit smoke test: role selector, admin login, Settings storage-health section loaded without runtime error

## Production Verification
- Production app loaded to role selector with no raw traceback.
- Admin PIN `1234` entered admin mode.
- Settings page showed:
  - `file_storage_backend = google_drive`
  - root folder not configured
  - all Drive folder IDs not configured
  - local upload audit counts
- Two QA production rows created during upload attempts were cancelled through admin QA cleanup with audit.

## Production Blocker
Google Drive folder configuration is missing in Streamlit Secrets, so a real production Drive upload and in-app private-photo preview cannot be completed yet.

Required fix:
- Add `[connections.gdrive].root_folder_id`.
- Add folder IDs for `book_files`, `guard_submissions`, `generated_pdfs`, and `other`, or allow the app to create child folders under the root.
- Share the folder with the app service account.
- Rerun production QA for officer book upload, guard near/far photo upload, admin preview, request detail preview, and link permissions.
