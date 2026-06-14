# Production QA Report

## Environment
- App URL: https://naccrequest-parking-ubxjmebrnxefxib6jt64su.streamlit.app/
- Google Sheet: https://docs.google.com/spreadsheets/d/1yZ5JEGP7S8VU7OPQqtvcPkHj3FC_guWbLZhAxpV1psg/edit
- Date/time: 2026-06-14 21:24 +07:00
- Commit SHA tested in production: `7bc7084`
- Tester: Codex browser automation and Google Sheets connector

## QA book numbers used
- `QA-PROD-DRIVE-FAIL-20260614-000001` - production upload attempt while Drive folder config was missing; final status `cancelled`
- `QA-PROD-DRIVE-FAIL-20260614-000002` - repeated production upload attempt while Drive folder config was missing; final status `cancelled`

## Role tests
| Test | Result | Notes |
|---|---|---|
| Fresh production load | Pass | App loaded inside Streamlit Cloud frame and showed role selector |
| Admin PIN `1234` | Pass | Entered admin mode |
| Admin Settings access | Pass | Settings rendered without traceback |

## Drive storage
| Test | Result | Notes |
|---|---|---|
| Deployment picked up Drive code | Pass | Settings shows `file_storage_backend = google_drive` |
| Drive folder config visible | Pass | Settings shows root and per-folder configuration status |
| Drive connection readiness | Blocked | Production has no `connections.gdrive.root_folder_id` or folder IDs configured |
| Book upload stores Drive URL | Blocked | Cannot complete until Drive folder IDs are configured in Streamlit Secrets |
| Guard near/far upload stores Drive URLs | Blocked | Cannot complete until Drive folder IDs are configured in Streamlit Secrets |
| No local `uploads/...` path written for Drive attempts | Pass | QA rows had blank `book_file_url`, not local paths |

## Photo preview
| Test | Result | Notes |
|---|---|---|
| Drive URL parser tests | Pass | `/file/d`, `open?id`, `uc?id`, raw ID, local-path rejection covered |
| Request detail preview UI | Pass local/static | Page compiles and renders through helper; production has no Drive photo rows to preview |
| Admin submitted-job preview UI | Pass local/static | Admin home imports and renders preview helper; production has no Drive photo rows to preview |
| Local legacy upload handling | Pass | Existing `uploads/...` records show warning path in Settings |

## Database checks
| Check | Result | Notes |
|---|---|---|
| QA rows cleaned up | Pass | Both `QA-PROD-DRIVE-FAIL-*` rows are `ยกเลิก` |
| Cleanup audit | Pass | `cancel_request` audit exists for QA cleanup |
| Attachments with Drive URLs | Blocked | No production Drive uploads possible until folder IDs are configured |

## Automated checks
| Check | Result | Notes |
|---|---|---|
| Unit tests | Pass | `python -m pytest -q`: 60 passed |
| Compile check | Pass | `python -X utf8 -m compileall app.py streamlit_app.py modules pages tests` |
| Local Streamlit smoke | Pass | Admin Settings showed storage-health section with local backend |

## Bugs found and fixed
- Local upload storage was the only backend; `modules/storage.py` now supports Google Drive with service-account upload.
- Uploaded-file metadata did not include backend/file ID fields; return dict now includes `storage_backend` and `drive_file_id`.
- File names were not traceable enough; book/guard upload prefixes now include book number where available.
- Reviewers only saw Drive links or photo-present flags; admin home and request detail now render Drive image bytes in-app.
- Local `uploads/...` links could look permanent; UI now warns and avoids treating them as durable links.
- Admin Settings had no Drive health section; it now reports backend, folder config, connection test, and local upload counts.

## Remaining issues
- Production Drive upload/preview QA is blocked by missing Streamlit Secrets for Google Drive folders.

Fix plan:
1. Create/share the Drive root folder with the Google service account used by the app.
2. Add `[connections.gdrive] root_folder_id` and recommended `[connections.gdrive.folders]` IDs in Streamlit Secrets.
3. Keep `share_uploaded_files = false` unless anyone-with-link access is explicitly approved.
4. Rerun officer book upload, guard near/far upload, admin in-app preview, and Drive link permission tests.
