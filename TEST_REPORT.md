# Production QA Report

## Environment
- App URL: https://naccrequest-parking-ubxjmebrnxefxib6jt64su.streamlit.app/
- Google Sheet: https://docs.google.com/spreadsheets/d/1yZ5JEGP7S8VU7OPQqtvcPkHj3FC_guWbLZhAxpV1psg/edit
- Date/time: 2026-06-14 22:52 +07
- Commit SHA: `3a921ee`
- Tester: Codex browser automation plus Google Drive/Sheets connector

## QA book numbers used
- `QA-PROD-DRIVE-FAIL-20260614-000001` - earlier Drive-config test, final status `cancelled`
- `QA-PROD-DRIVE-FAIL-20260614-000002` - earlier Drive-config test, final status `cancelled`
- `QA-PROD-DRIVE-PREVIEW-20260614-213904` - earlier upload/preview test, final status `cancelled`
- `QA-PROD-DRIVE-PREVIEW-20260614-214341` - Drive write failure test, no request row created
- `QA-PROD-DRIVE-ERR-20260614-220405` - earlier upload error-message test, no request row created
- `QA-PROD-DRIVE-ERR-20260614-VERIFY` - latest officer upload preflight test, no request row created

## Role tests
| Test | Result | Notes |
|---|---|---|
| Fresh production load | Pass | Role selector rendered with no traceback |
| Officer role selection | Pass | Entered officer home and opened `บันทึกหนังสือใหม่` through in-app navigation |
| Admin PIN `1234` | Pass | Entered admin mode |
| Admin Settings access | Pass | Settings rendered and diagnostics ran |
| Direct page URL without role | Pass | Direct new-request URL returned role selector/unauthorized state instead of exposing the page |

## Officer flow
| Test | Result | Notes |
|---|---|---|
| New request page opens from officer home | Pass | Form rendered with dynamic sections |
| Book-file upload when Drive folder is not ready | Pass / blocked safely | Shows My Drive preflight message and does not write a request row |
| Failed upload write safety | Pass | Sheets search for `QA-PROD-DRIVE-ERR-20260614-VERIFY` returned `matched_row_count=0` |
| Successful book upload | Blocked by Drive config | Requires Shared Drive folder IDs |

## Guard flow
| Test | Result | Notes |
|---|---|---|
| Guard work package UI | Previously passed | Existing package rendered without technical IDs in normal card |
| Guard near/far photo upload | Blocked by Drive config | Same storage backend/folder readiness blocker as book upload |
| Guard submitted-photo preview | Blocked by Drive config | Needs successful Drive photo rows first |

## Admin flow
| Test | Result | Notes |
|---|---|---|
| Settings Drive backend visible | Pass | `file_storage_backend = google_drive` |
| Service account shown | Pass | `nacc-parking-streamlit@nacc-parking-streamlit.iam.gserviceaccount.com` |
| Drive read check | Pass | Both configured folders are readable |
| Drive folder readiness | Fail / config blocked | Both folders show `location = My Drive`, `upload_ready = ยังไม่พร้อม` |
| Drive write check | Pass / blocked safely | App blocks before writing and shows Shared Drive remediation |
| Admin photo review | Blocked by Drive config | Needs successful guard photo upload |

## Database checks
| Check | Result | Notes |
|---|---|---|
| Failed upload did not create request | Pass | `QA-PROD-DRIVE-ERR-20260614-VERIFY` not found in `คำขอ` |
| Failed upload did not create local path | Pass | Upload was blocked before local fallback; backend remains `google_drive` |
| Existing QA cleanup | Pass | Earlier active QA rows were cancelled, not deleted |

## Visual checks
| Check | Result | Notes |
|---|---|---|
| Role selector | Pass | Thai role cards visible and readable |
| Settings diagnostics | Pass | `location` and `upload_ready` columns visible |
| Upload error | Pass | User-facing Thai message appears on officer form |

## Bugs found and fixed
- Added Drive folder readiness validation before upload.
- Added Settings `location/upload_ready` diagnostics.
- Fixed Streamlit Cloud stale `modules.storage` imports on upload/settings pages.
- Verified failed Drive upload no longer reaches Google API quota write and no longer creates partial Sheets rows.
- Added OAuth Google Drive upload mode for normal My Drive folders. Local verification passed, but production upload still requires OAuth secrets to be configured.

## Remaining issues
Production file upload cannot pass until either OAuth Drive secrets are configured or the upload folders are moved to Google Shared Drive. Current provided folder IDs are normal My Drive folders.

Fix plan:
1. Create a Google OAuth client and refresh token for the Drive owner account.
2. Add `[connections.gdrive].auth_mode = "oauth"` and `[connections.gdrive.oauth]` secrets in Streamlit.
3. Keep the existing My Drive folder IDs or replace them with the intended folders.
4. Rerun full production QA for officer upload, guard photo upload, admin preview, request detail preview, and cleanup.
