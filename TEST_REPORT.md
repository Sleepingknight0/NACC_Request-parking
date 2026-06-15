# Production QA Report

## Environment
- App URL: https://naccrequest-parking-ubxjmebrnxefxib6jt64su.streamlit.app/
- Google Sheet: https://docs.google.com/spreadsheets/d/1yZ5JEGP7S8VU7OPQqtvcPkHj3FC_guWbLZhAxpV1psg/edit
- Date/time: 2026-06-15 02:21 +07
- Commit SHA: `572c486` production-tested for OAuth Drive upload and preview; latest local patch verified by tests before final commit
- Tester: Codex browser automation plus Google Drive/Sheets connector

## QA book numbers used
- `QA-PROD-OAUTH-20260615-020000` - created during upload attachment automation attempt, final status `cancelled`, note `ข้อมูลทดสอบ production QA`
- `QA-PROD-OAUTHFILE-20260615-020146` - created during upload attachment automation attempt, final status `cancelled`, note `ข้อมูลทดสอบ production QA`
- `QA-PROD-OAUTHPDF-20260615-020402` - full Drive upload, guard photo submit, admin preview, and confirm flow, final status `done`

## Role tests
| Test | Result | Notes |
|---|---|---|
| Fresh production load | Pass | Role selector rendered with no traceback |
| Guard role | Pass | Guard submit page and package flow accessible only after role selection |
| Officer role | Pass | Officer request creation worked with book-file upload |
| Admin PIN `1234` | Pass | Entered admin home and Settings |
| Change user | Pass | Returned to role selector before switching roles |
| Unauthorized direct detail URL without role | Pass | Showed `หน้านี้ไม่เปิดให้บทบาทของคุณใช้งาน` and role selector |

## Officer flow
| Test | Result | Notes |
|---|---|---|
| Create request with book PDF | Pass | `QA-PROD-OAUTHPDF-20260615-020402` saved successfully |
| Requests row | Pass | One row created with Drive `book_file_url` |
| Attachments row for book file | Pass | `file_type=book`, MIME `application/pdf`, Drive URL stored |
| No local upload path for production upload | Pass | Stored URL is `https://drive.google.com/file/d/...` |
| Search/list by book number | Pass | Admin list showed book number as card title and opened detail |

## Guard flow
| Test | Result | Notes |
|---|---|---|
| One request equals one guard package | Pass | Guard/admin UI showed one card for the request |
| Accept job | Pass | Package moved from pending to in progress; audit wrote `accept_guard_package` once |
| PDF download button | Pass | Download button rendered for the package |
| Submit validation | Pass | Submit page required near photo, far photo, and confirmation |
| Submit near/far photos | Pass | Success message `ส่งงานแล้ว รอเจ้าหน้าที่ตรวจ` appeared |
| Guard_Submissions row | Pass | One row created with near/far Drive URLs |
| Attachments rows for guard photos | Pass | Two `guard_photo` rows created with Drive URLs and `image/png` MIME type |

## Admin flow
| Test | Result | Notes |
|---|---|---|
| Settings Drive backend | Pass | `auth_mode=oauth` and OAuth configured |
| Drive connection check | Pass | Folder metadata read succeeded |
| Drive write check | Pass | Test upload and trash cleanup succeeded |
| Submitted job review card | Pass | Admin home showed `งานรอยืนยัน` for the QA package |
| In-app photo preview | Pass | Admin home rendered two visible `img` elements from Drive bytes |
| Confirm done | Pass | Button showed success; pending review count moved from 1 to 0 |
| Detail photo gallery | Pass | Request detail rendered two visible image previews |
| QA cleanup | Pass | Two partial QA requests were cancelled through admin UI, not deleted |

## Database checks
| Check | Result | Notes |
|---|---|---|
| Requests book URL | Pass | `QA-PROD-OAUTHPDF-20260615-020402` has a Drive file URL |
| Guard_Submissions URLs | Pass | near/far fields are Drive file URLs |
| Attachments metadata | Pass | Book plus near/far metadata rows exist |
| Guard task final status | Pass | Task row status is `เสร็จสิ้น`, with `completed_at` set |
| Audit log | Pass | `create_request`, `accept_guard_package`, `submit_guard_task`, and `mark_done` logged |
| QA cleanup statuses | Pass | Partial QA rows are `ยกเลิก` with reason `ข้อมูลทดสอบ production QA` |

## Visual checks
| Check | Result | Notes |
|---|---|---|
| Role selector | Pass | Only guard/officer public choices plus hidden admin expander |
| Admin review images | Pass | Images render inside Streamlit, not only as Drive links |
| Request detail images | Pass | Submitted photos render inside the detail page |
| Local-path handling | Pass | Existing local paths remain warning-only behavior from earlier implementation |
| Status label in detail metric | Fixed locally | Raw `pending/done/cancelled` metric changed to Thai status label |

## Bugs found and fixed
- Fixed OAuth Drive scope mismatch that caused token refresh/upload failures.
- Verified Google Drive uploads use OAuth owner storage for normal My Drive folders.
- Verified Drive URLs are written to Sheets and Attachments instead of `uploads/...`.
- Verified Drive image preview downloads bytes through the app and renders with `st.image`.
- Fixed request detail metric to show Thai guard status labels instead of raw internal status values.

## Remaining issues
- None known for the tested Drive upload and preview flow.

## Security note
OAuth and service-account credentials were pasted into chat during setup. Rotate the OAuth client secret, refresh token, and service-account key after production verification.
