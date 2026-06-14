# Production QA Report

## Environment
- App URL: https://naccrequest-parking-ubxjmebrnxefxib6jt64su.streamlit.app/
- Google Sheet: https://docs.google.com/spreadsheets/d/1yZ5JEGP7S8VU7OPQqtvcPkHj3FC_guWbLZhAxpV1psg/edit
- Date/time: 2026-06-14 16:46 +07:00
- Commit SHA: `134cc76`
- Tester: Codex browser automation and Google Sheets connector

## QA book numbers used
- `QA-PROD-20260614-161146-A` - full one-day no-plate flow; final cleanup status `cancelled`
- `QA-PROD-20260614-161800-B` - multi-day flow; final cleanup status `cancelled`
- `QA-PROD-20260614-162019-C` - accidental no-plate QA artifact; final cleanup status `cancelled`
- `QA-PROD-20260614-162308-C2` - plate flow with TEST1/TEST2/TEST3; final cleanup status `cancelled`

## Role tests
| Test | Result | Notes |
|---|---|---|
| Fresh production load | Pass | Shows role selector, no dashboard, no traceback |
| Visible public role choices | Pass | Only รปภ. and เจ้าหน้าที่ are visible |
| Admin hidden behind expander | Pass | Expander label shown; PIN field hidden until opened |
| Admin PIN `1234` | Pass | Enters admin mode |
| Direct protected Settings path without role | Pass | Shows Thai unauthorized warning and role selector |
| Refresh/new session behavior | Pass | Refresh returned to role selection when session role was absent |

## Officer flow
| Test | Result | Notes |
|---|---|---|
| Create one-day request, no plate | Pass | 1 Requests row, 1 Request_Dates row, 1 Guard_Tasks row |
| Create multi-day request | Pass | 1 Requests row, 3 Request_Dates rows, 1 Guard_Tasks package |
| Create request with plates | Pass | TEST1, TEST2, TEST3 written as 3 vehicle rows |
| Duplicate book number | Pass | Save blocked with duplicate-book error |
| Search/detail | Pass | QA book numbers searchable; detail uses book number title and hides system IDs in normal UI |

## Guard flow
| Test | Result | Notes |
|---|---|---|
| Job availability for tomorrow | Pass | Job was open and could be accepted |
| Upcoming job 3 days out | Pass | Shown as upcoming with open date `2026-06-16` and not actionable |
| Accept job | Pass | Status moved to in progress once |
| Download PDF | Pass | Downloaded `parking_sign_QA-PROD-20260614-161146-A.pdf` |
| Submit without/with photos | Pass | Required near/far photos and confirmation; successful submit wrote 1 submission and 2 attachments |
| One package per request | Pass | Multi-day and plate requests showed one operational package each |

## Admin flow
| Test | Result | Notes |
|---|---|---|
| Admin home | Pass | Shows dashboard/report/settings/repair launchers and required status sections |
| Confirm submitted package | Pass | Submitted package moved to done before QA cleanup |
| QA cleanup | Pass | Batch cleanup completed; active QA rows now 0 |
| Settings schema/data health | Pass | Loads without runtime error; shows local upload warnings and data-health metrics |
| Orphan task visibility | Pass | Legacy orphan tasks no longer appear as operational cards |

## Database checks
| Check | Result | Notes |
|---|---|---|
| Requests | Pass | 4 QA rows, all `ยกเลิก`, reason `ข้อมูลทดสอบ production QA` |
| Request_Dates | Pass | 6 QA date rows, all `ยกเลิก`, month keys `2026-06` |
| Guard_Tasks | Pass | 4 QA package rows, all `ยกเลิก`; one package per request |
| Vehicles | Pass | TEST1/TEST2/TEST3 rows present and cancelled |
| Guard_Submissions | Pass | 1 submission row for the completed guard test |
| Attachments | Pass | 2 photo attachment rows with local `uploads/...` paths |
| Audit_Log | Partial | Cancellation audit rows exist for the latest cleanup; earlier audit rows were not recoverable after the pre-hardening cleanup failure |

## Visual checks
| Check | Result | Notes |
|---|---|---|
| Role selector layout | Pass | Clean launcher, no dense table |
| Admin home cards | Pass | No blank orphan cards after final deploy |
| Settings page | Pass | Tables are in expanders; local upload warning is visible |
| Mobile/card overflow | Pass | Smoke checked during local browser QA |
| Theme contrast | Pass | Light/dark theme smoke checks did not expose unreadable controls |

## Bugs found and fixed
- Role/session access hardening.
- Date and month normalization.
- Backend guard availability enforcement.
- One package per request for multi-day jobs.
- Idempotent accept, submit, mark done, cancel, and status transitions.
- Safe local upload link warnings.
- Batch QA cleanup instead of repeated per-row cancellation.
- Operational hiding of legacy orphan guard task rows.
- Strict read-before-write protection for Google Sheets writes.

## Remaining issues
- Six legacy orphan rows remain in `งาน รปภ.` with no parent request. They are no longer shown in guard/admin operational cards and are visible in Settings data health. Fix plan: add an admin repair action that marks orphan task rows as quarantined/cancelled with an audit entry, without deleting rows.
- Earlier `Audit_Log` rows were lost or not recoverable after the pre-hardening cleanup failure. Fix plan: the deployed strict-read storage fix prevents recurrence; for historical reconstruction, use Google Sheets revision history or add a one-time admin audit reconciliation tool that writes clearly labeled `audit_repair` entries instead of pretending to recreate original logs.

