# Bugfix Report

## Summary
Production app, guard package, role access, date, cleanup, and write-safety bugs were fixed and deployed through commit `134cc76`.

## Bugs Found
| Bug | Root cause | Fix summary | Manual verification |
|---|---|---|---|
| Role could be inferred from URL/session state and protected pages were not always role-first | Role handling trusted query/navigation state too much | Restricted role source to session state, added protected-page warning before selector | Fresh production load shows only รปภ., เจ้าหน้าที่, and hidden admin PIN |
| Guard/officer/admin homes showed incomplete launcher sections | Home cards did not match role workflows | Added required sections and role-specific launcher cards | Production admin/guard/officer homes smoke-tested |
| Multi-day guard work could split or display incorrectly | Guard task display used task/date rows too directly | Guard package builder groups by request; one request creates one package/PDF/submission flow | QA multi-day request created 3 date rows and 1 guard package |
| Guard could accept/submit jobs before open date through backend paths | Availability was mostly UI-side | Backend now enforces open date = start date minus 1 day for accept and submit | Upcoming QA job showed disabled/not-open state; tests cover backend block |
| Done/submitted/cancelled guard packages allowed unsafe repeated operations | Status transitions were not fully idempotent | Added status checks and idempotent accept/submit/mark-done/cancel behavior | Double-click/idempotence covered by tests; production flow accepted/submitted/confirmed once |
| Date strings displayed with `00:00:00` and month filters could break | Datetime-like sheet strings were not normalized everywhere | Normalized ISO dates, month keys, Buddhist year inputs, and date ranges | Production sheet date/month rows verified as `YYYY-MM-DD` and `YYYY-MM` |
| Local upload paths rendered like durable links | UI did not distinguish `uploads/...` from real URLs | Added temporary-file warnings and Settings local upload checker | Production Settings shows 2 temporary guard photo links |
| Admin QA cleanup failed partway with a redacted Streamlit error | Settings loop cancelled each QA row by rereading/rewriting sheets repeatedly | Added batch `cancel_requests()` and wired QA cleanup to one idempotent write path | Production cleanup completed; active QA rows now 0 |
| Legacy orphan guard task rows appeared as blank operational cards | Package builder accepted rows with blank/missing parent request IDs | Operational package builder now skips blank or missing parent requests | Production admin home now shows no blank pending/upcoming cards |
| Append-style writes could overwrite a sheet after transient Google read failure | `read_sheet()` returned an empty dataframe on Google read errors, and `append_rows()` wrote over it | Added strict read mode for write paths; append/update/normalize/batch cancel stop before writing if reads fail | Regression test added; Settings still loads after deploy |

## Files Changed
- `modules/auth.py`
- `modules/dates.py`
- `modules/db.py`
- `modules/guard_packages.py`
- `modules/home.py`
- `modules/sheets.py`
- `modules/ui.py`
- `pages/02_บันทึกหนังสือ.py`
- `pages/03_รายการหนังสือ.py`
- `pages/04_รายละเอียดหนังสือ.py`
- `pages/05_งาน_รปภ.py`
- `pages/06_ส่งงาน_รปภ.py`
- `pages/08_ตั้งค่า.py`
- `tests/test_auth.py`
- `tests/test_dates.py`
- `tests/test_guard_packages.py`
- `tests/test_guard_workflow.py`
- `tests/test_pdf_logic.py`
- `tests/test_sheets.py`
- `tests/test_status_transitions.py`
- `tests/test_ui.py`
- `tests/test_validators.py`

## Automated Verification
- `python -m pytest -q`: 47 passed
- `python -X utf8 -m compileall app.py streamlit_app.py modules pages tests`: passed

## Production Verification
- Production app loaded cleanly with no redacted runtime error.
- Role selector showed รปภ. and เจ้าหน้าที่ only; admin remained hidden behind PIN `1234`.
- Officer created QA requests, duplicate book number was blocked, search/detail paths worked.
- Guard accepted an available job, downloaded one PDF sign, submitted near/far photos, and could not operate early/upcoming jobs.
- Admin confirmed submitted work, used QA cleanup, and verified cancelled QA rows in Google Sheets.
- README was not changed because setup and usage did not change.

