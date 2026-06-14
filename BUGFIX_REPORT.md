# Bugfix Report

## Summary
Google Drive-backed storage and in-app Drive image preview are implemented and deployed. The provided production folders are configured and readable, but real upload QA is blocked by Google Drive service-account storage quota rules for normal My Drive folders.

## Bugs Found
| Bug | Root cause | Fix summary | Verification |
|---|---|---|---|
| Uploaded files were saved to local `uploads/...` paths | `modules/storage.py` only had a local filesystem implementation | Added Google Drive backend, service-account upload, configurable sharing, and compatible metadata return shape | Unit tests; production Settings shows `google_drive` backend |
| Production had no Drive folder config | No folder IDs were configured in app/secrets | Added provided folder IDs as defaults for `book_files` and `guard_submissions`, while preserving env/secrets override | Production Settings shows both folders configured |
| Drive diagnostics only checked read access | Settings could not prove uploads would work | Added service-account email display and write-access health check | Production write test exposed exact API blocker |
| Valid uploaded files could be skipped | Page code used truthiness checks (`if book_file`) instead of explicit `is not None` | Updated book and extra-photo upload guards | Regression tests in `tests/test_upload_pages.py` |
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
- `tests/test_upload_pages.py`
- `TEST_REPORT.md`
- `BUGFIX_REPORT.md`

## Automated Verification
- `python -m pytest -q`: 63 passed
- `python -X utf8 -m compileall app.py streamlit_app.py modules pages tests`: passed
- Local Streamlit smoke test: role selector, admin login, Settings storage-health section loaded without runtime error

## Production Verification
- Production app loaded to role selector with no raw traceback.
- Admin PIN `1234` entered admin mode.
- Settings page showed:
  - `file_storage_backend = google_drive`
  - `book_files = ตั้งค่าแล้ว`
  - `guard_submissions = ตั้งค่าแล้ว`
  - service account email
  - local upload audit counts
- Drive read check passed for:
  - `Data base หนังสือผู้ขอที่จอด`
  - `Data base รปภส่งงาน`
- Drive write check failed with Google API error:
  - `Service Accounts do not have storage quota`
  - `reason: storageQuotaExceeded`
- QA rows created during production testing were cancelled with audit.

## Production Blocker
The provided folders appear to be normal My Drive folders. Service accounts can read shared My Drive folders but cannot upload files there because service accounts have no Drive storage quota.

Required fix:
- Move or recreate both upload folders in a Google Shared Drive, or switch the app to OAuth/domain-wide delegation.
- Grant `nacc-parking-streamlit@nacc-parking-streamlit.iam.gserviceaccount.com` write access.
- Rerun production Drive write check, officer upload, guard photo upload, admin preview, and request detail preview.
