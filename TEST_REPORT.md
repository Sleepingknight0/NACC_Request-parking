# Production QA Report

## Environment
- App URL: https://naccrequest-parking-ubxjmebrnxefxib6jt64su.streamlit.app/
- Google Sheet: https://docs.google.com/spreadsheets/d/1yZ5JEGP7S8VU7OPQqtvcPkHj3FC_guWbLZhAxpV1psg/edit
- Date/time: 2026-06-14 22:05 +07:00
- Commit SHA tested in production: `bac5a85`
- Tester: Codex browser automation and Google Sheets/Drive connector

## QA book numbers used
- `QA-PROD-DRIVE-FAIL-20260614-000001` - earlier missing-folder-config test; final status `cancelled`
- `QA-PROD-DRIVE-FAIL-20260614-000002` - earlier missing-folder-config test; final status `cancelled`
- `QA-PROD-DRIVE-PREVIEW-20260614-213904` - upload attempt before explicit `is not None` fix; final status `cancelled`
- `QA-PROD-DRIVE-PREVIEW-20260614-214341` - Drive write failure after fix; no request row created
- `QA-PROD-DRIVE-ERR-20260614-220405` - upload-form error-message test; no request row created

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
| Provided Drive folders resolved | Pass | Both folder IDs resolve to Google Drive folders |
| Folder config visible in app | Pass | `book_files` and `guard_submissions` show `ตั้งค่าแล้ว` |
| Service account read access | Pass | Settings Drive connection check reads both folders |
| Service account write access | Fail / blocked | Google Drive API returns `storageQuotaExceeded`: service accounts cannot upload into normal My Drive storage |
| Book upload stores Drive URL | Blocked | Upload reaches Drive backend, then fails before writing request row |
| Guard near/far upload stores Drive URLs | Blocked | Cannot test until Drive write access is fixed |
| No local `uploads/...` path written for Drive attempts | Pass | Drive write failure did not write a local path or partial request row |
| Upload-form error message | Pass | Officer form now shows the exact Shared Drive/OAuth fix instead of only a generic upload error |

## Photo preview
| Test | Result | Notes |
|---|---|---|
| Drive URL parser tests | Pass | `/file/d`, `open?id`, `uc?id`, raw ID, local-path rejection covered |
| Request detail preview UI | Pass local/static | Page compiles and renders through helper; production has no new Drive photo rows to preview |
| Admin submitted-job preview UI | Pass local/static | Admin home imports and renders preview helper; production has no new Drive photo rows to preview |
| Local legacy upload handling | Pass | Existing `uploads/...` records show warning path in Settings |

## Database checks
| Check | Result | Notes |
|---|---|---|
| QA rows cleaned up | Pass | Active QA rows returned to 0 after cleanup |
| Cleanup audit | Pass | `cancel_request` audit exists for QA cleanup |
| Failed Drive write safety | Pass | `QA-PROD-DRIVE-PREVIEW-20260614-214341` was not written after Drive upload failed |
| Attachments with Drive URLs | Blocked | No production Drive uploads possible until write access is fixed |

## Automated checks
| Check | Result | Notes |
|---|---|---|
| Unit tests | Pass | `python -m pytest -q`: 65 passed |
| Compile check | Pass | `python -X utf8 -m compileall app.py streamlit_app.py modules pages tests` |
| Production Drive read check | Pass | Both folders readable by service account |
| Production Drive write check | Fail / blocked | Exact error: `Service Accounts do not have storage quota` |

## Bugs found and fixed
- Added the provided production Drive folder IDs as defaults for `book_files` and `guard_submissions`, with secrets/env override support.
- Added admin-only Drive write diagnostic and service-account email display.
- Fixed upload call guards to use `is not None`; uploaded objects are no longer skipped by truthiness checks.
- Added regression tests for the upload guard behavior.
- Mapped Google Drive quota/permission errors to actionable Thai messages for officer/admin UI.

## Remaining issues
- Production Drive upload/preview QA is blocked because the provided folders are normal My Drive folders. Service-account uploads require a Google Shared Drive, OAuth delegation, or another backend with writable storage quota.

Fix plan:
1. Move `Data base หนังสือผู้ขอที่จอด` and `Data base รปภส่งงาน` into a Google Shared Drive, or create equivalent folders in a Shared Drive.
2. Grant `nacc-parking-streamlit@nacc-parking-streamlit.iam.gserviceaccount.com` Contributor/Content manager access.
3. Keep the same folder IDs if possible, or provide the new Shared Drive folder IDs.
4. Rerun Settings `ตรวจสิทธิ์อัปโหลด Google Drive`; it must pass before upload QA can pass.
5. Rerun officer book upload, guard near/far upload, admin in-app preview, request detail preview, and QA cleanup.
