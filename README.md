# ระบบขอที่จอดรถ ป.ป.ช. — NACC Parking Request System

Streamlit app for recording and tracking parking requests for the Office of the National Anti-Corruption Commission (สำนักงาน ป.ป.ช.). A request starts from an official letter (หนังสือ), gains vehicles and parking dates, becomes a job for the security team (รปภ.), and ends with a submitted photo record and a generated PDF summary.

Data lives in Google Sheets and uploaded files in Google Drive, so the whole system runs on Streamlit Community Cloud with no server to maintain. A local CSV mode is available for development.

## Pages

The app is a Streamlit multipage app; the entry point renders the home screen and `pages/` provides the rest.

| Page | Purpose |
|------|---------|
| `01_แดชบอร์ด` | Dashboard — current status overview |
| `02_บันทึกหนังสือ` | Record a new letter and its request details |
| `03_รายการหนังสือ` | Browse and filter letters |
| `04_รายละเอียดหนังสือ` | Letter detail — vehicles, dates, attachments |
| `05_งาน_รปภ` | Security team job queue |
| `06_ส่งงาน_รปภ` | Security team submission with photo upload |
| `07_รายงานรายเดือน` | Monthly report |
| `08_ตั้งค่า` | Settings |

## Data model

Worksheets (or CSV files under `data/` in local mode): `Requests`, `Request_Dates`, `Vehicles`, `Guard_Tasks`, `Attachments`, `Audit_Log`.

Statuses are fixed sets defined in `modules/constants.py`:

| Entity | Statuses |
|--------|----------|
| Request | `draft` · `pending` · `active` · `done` · `cancelled` |
| Request date | `pending` · `active` · `done` · `cancelled` |
| Vehicle | `active` · `cancelled` |
| Guard task | `pending` · `in_progress` · `submitted` · `done` · `cancelled` |
| Attachment | `active` · `deleted` · `replaced` |

Codes are stored in the sheet; Thai labels are rendered in the UI.

## Requirements

- Python **3.11** (the version pinned in `.devcontainer/devcontainer.json`)
- A Google Cloud project with the **Google Sheets API** and **Google Drive API** enabled
- A service account for Sheets, and a Drive account (service account on a Shared Drive, or OAuth for My Drive)

## Run in GitHub Codespaces

The fastest way to get a running instance. Open the repo in a Codespace and the devcontainer installs `requirements.txt` and starts Streamlit on port 8501 automatically, with a preview tab opening on its own.

You still need to add `.streamlit/secrets.toml` inside the Codespace before the Google backends will work — or leave the storage backend unset to run against the CSV files in `data/`.

## Setup

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Fill in `.streamlit/secrets.toml` — see [Configuration](#configuration) below. Then:

```bash
streamlit run streamlit_app.py
```

### Local development without Google

Leave `[app].storage_backend` unset (it defaults to `csv`) and the app reads and writes the CSV files in `data/`, with uploads going to `uploads/`. This needs no Google credentials, and is the fastest way to click through the app.

Environment variables override secrets, which is handy for local runs:

- `PARKING_APP_STORAGE_BACKEND`
- `PARKING_APP_FILE_STORAGE_BACKEND`

## Tests

```bash
pytest
```

Covers auth, date logic, validators, status transitions, guard workflow and packaging, sheet titles, storage, Drive preview, PDF logic, and upload pages.

## Layout

```text
streamlit_app.py    # entry point (app.py is an equivalent alias)
modules/
  auth.py           # login and role checks
  db.py             # data access over the active storage backend
  sheets.py         # Google Sheets connection and worksheet I/O
  storage.py        # backend selection, Drive config, file uploads
  drive_preview.py  # render private Drive files inside Streamlit
  guard_packages.py # security team job packaging
  pdf_generator.py  # ReportLab PDF output
  dates.py          # parking date handling
  validators.py     # input validation
  locks.py          # concurrent edit guards
  audit.py          # audit log writes
  constants.py      # statuses, labels, departments, locations
  ids.py            # ID generation
  ui.py             # shared UI components
  home.py           # home screen
  line_ready.py     # LINE notification payloads
pages/              # eight Thai-language Streamlit pages
data/               # CSV store for local mode
uploads/            # local upload fallback
assets/fonts/       # Thai fonts for PDF generation
scripts/            # generate_drive_oauth_refresh_token.py
tests/              # pytest suite
```

## Configuration

### Google Drive file storage

Production uploads should use Google Drive, not local `uploads/...` paths.

Required setup:

1. Enable Google Drive API and Google Sheets API for the Google Cloud project used by the service account.
2. For a normal Gmail/My Drive folder, use OAuth upload. Service-account upload only works reliably with Google Shared Drive, because service accounts do not have My Drive storage quota.
3. Share the Google Sheet and the target Drive folder with the service account email.
4. Configure Streamlit Secrets:

```toml
[app]
storage_backend = "gsheets"
file_storage_backend = "google_drive"

[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit"

[connections.gdrive]
auth_mode = "oauth"
root_folder_id = "<GOOGLE_DRIVE_ROOT_FOLDER_ID>"
share_uploaded_files = false

[connections.gdrive.folders]
book_files = "<BOOK_FILES_FOLDER_ID>"
guard_submissions = "<GUARD_SUBMISSIONS_FOLDER_ID>"
generated_pdfs = "<GENERATED_PDFS_FOLDER_ID>"
other = "<OTHER_FOLDER_ID>"

[connections.gdrive.oauth]
client_id = "<GOOGLE_OAUTH_CLIENT_ID>"
client_secret = "<GOOGLE_OAUTH_CLIENT_SECRET>"
refresh_token = "<GOOGLE_OAUTH_REFRESH_TOKEN>"
token_uri = "https://oauth2.googleapis.com/token"
```

Folder-specific IDs are recommended. If only `root_folder_id` is configured, the app will create or reuse direct child folders named `book_files`, `guard_submissions`, `generated_pdfs`, and `other`.

### OAuth setup for My Drive uploads

Use this when the Google Drive account does not have Shared Drive.

1. Google Cloud Console > APIs & Services > OAuth consent screen.
2. Create or configure the OAuth app. Add the Google account that owns the Drive folders as a test user if the app is in testing mode.
3. APIs & Services > Credentials > Create credentials > OAuth client ID.
4. Choose a desktop app or web app client and copy `client_id` and `client_secret`.
5. Generate a refresh token for the Drive owner account with Drive scope:
   `https://www.googleapis.com/auth/drive`
   You can use the helper script:
   ```powershell
   python scripts/generate_drive_oauth_refresh_token.py `
     --client-id "GOOGLE_OAUTH_CLIENT_ID" `
     --client-secret "GOOGLE_OAUTH_CLIENT_SECRET"
   ```
   If Google says the redirect URI is invalid, add this authorized redirect URI to the OAuth client:
   `http://localhost:8765/oauth2callback`
6. Put `client_id`, `client_secret`, and `refresh_token` in Streamlit Secrets under `[connections.gdrive.oauth]`.
7. Set `[connections.gdrive].auth_mode = "oauth"`.

With OAuth, uploaded files are created in the Drive owner's My Drive account, so normal My Drive folders can be used. Google Sheets can still use the service account.

The current production defaults are:

- `book_files`: `Data base หนังสือผู้ขอที่จอด`
- `guard_submissions`: `Data base รปภส่งงาน`

Streamlit Secrets or environment variables override these defaults.

`share_uploaded_files = false` keeps uploaded files private and relies on Drive folder permissions. Set it to `true` only if files should be opened by anyone with the link.

## Drive preview behavior

Guard-submitted photos are stored as Drive URLs in Google Sheets and previewed inside Streamlit by downloading bytes through the service account. This means private Drive files can still render in the app when the service account has access.

If users need to open Drive links directly, the Drive folder or file permissions must allow those users. Existing `uploads/...` rows are temporary legacy paths and should be re-uploaded or migrated to Drive; the app shows a warning instead of rendering them as durable links.

Troubleshooting:

- Permission denied: share the Drive folder with the service account and confirm Drive API is enabled.
- Storage quota exceeded with `auth_mode = service_account`: move the folder into a Google Shared Drive or switch to `auth_mode = "oauth"`.
- OAuth upload fails: confirm the refresh token belongs to the account that can write to the target Drive folders and that Google Drive API is enabled.
- File not found: verify the stored Drive URL/file ID and folder permissions.
- Local upload path: re-upload the file so Google Sheets stores a Drive URL.
- Unsupported file type: image previews support PNG, JPEG, JPG, and WebP; PDFs show a Drive link/download instead of inline image preview.

## Security notes

- `.streamlit/secrets.toml` holds a service account private key and an OAuth refresh token — it is gitignored and must never be committed.
- `data/` and `uploads/` may contain real request records and photos when the local backend has been used. Check before pushing.

## Related docs

- `BUGFIX_REPORT.md` — recorded defects and their fixes
- `TEST_REPORT.md` — test run results

## License

MIT — see [LICENSE](LICENSE).
