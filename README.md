# NACC Parking Request System

A Streamlit workflow for recording, tracking, and completing official parking requests for the Office of the National Anti-Corruption Commission.

The system follows each request from the incoming official letter through vehicle scheduling, security execution, photo evidence, reporting, and PDF generation.

## Overview

The application supports Google Sheets as the operational data store and Google Drive as the production file store. A CSV and local-file mode is available for development without cloud credentials.

The user interface is localized for Thai operational staff. This documentation is maintained in English.

## Workflow

1. Record the official letter and request details.
2. Add parking dates, vehicles, locations, and supporting files.
3. Track the request through its operational status.
4. Package the approved work for the security team.
5. Upload completion evidence from the field.
6. Review monthly activity and generate PDF summaries.

## Application pages

| Order | Page purpose                                      |
| ----: | ------------------------------------------------- |
|     1 | Dashboard and current status overview             |
|     2 | New official-letter and request entry             |
|     3 | Searchable request list                           |
|     4 | Request details, dates, vehicles, and attachments |
|     5 | Security team job queue                           |
|     6 | Security completion and photo submission          |
|     7 | Monthly reporting                                 |
|     8 | Application settings                              |

The entry point renders the home screen. The `pages/` directory contains the eight localized Streamlit pages.

## Data model

The storage layer uses six logical tables or worksheets:

- `Requests`
- `Request_Dates`
- `Vehicles`
- `Guard_Tasks`
- `Attachments`
- `Audit_Log`

Local development represents the same entities as CSV files under `data/`.

### Status values

| Entity       | Allowed values                                             |
| ------------ | ---------------------------------------------------------- |
| Request      | `draft`, `pending`, `active`, `done`, `cancelled`          |
| Request date | `pending`, `active`, `done`, `cancelled`                   |
| Vehicle      | `active`, `cancelled`                                      |
| Guard task   | `pending`, `in_progress`, `submitted`, `done`, `cancelled` |
| Attachment   | `active`, `deleted`, `replaced`                            |

Status codes are stored in English. Localized labels are defined in `modules/constants.py` and rendered by the interface.

## Requirements

- Python 3.11.
- Google Sheets API access for the production data backend.
- Google Drive API access for production file storage.
- A service account for Sheets.
- A Shared Drive service account or an OAuth-enabled user account for Drive uploads.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Update `.streamlit/secrets.toml` for the intended backend, then start the application:

```bash
streamlit run streamlit_app.py
```

`app.py` is an equivalent entry-point alias.

## Local development without Google

Leave `storage_backend` unset or set it to `csv`. The application writes entity data under `data/` and uploaded files under `uploads/`.

This mode requires no Google credentials and is the quickest way to review the interface and workflow.

These environment variables override the matching application settings:

```text
PARKING_APP_STORAGE_BACKEND
PARKING_APP_FILE_STORAGE_BACKEND
```

## Google backend configuration

Use `gsheets` for records and `google_drive` for durable production uploads:

```toml
[app]
storage_backend = "gsheets"
file_storage_backend = "google_drive"

[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit"

[connections.gdrive]
auth_mode = "oauth"
root_folder_id = "<ROOT_FOLDER_ID>"
share_uploaded_files = false

[connections.gdrive.folders]
book_files = "<BOOK_FILES_FOLDER_ID>"
guard_submissions = "<GUARD_SUBMISSIONS_FOLDER_ID>"
generated_pdfs = "<GENERATED_PDFS_FOLDER_ID>"
other = "<OTHER_FOLDER_ID>"

[connections.gdrive.oauth]
client_id = "<OAUTH_CLIENT_ID>"
client_secret = "<OAUTH_CLIENT_SECRET>"
refresh_token = "<OAUTH_REFRESH_TOKEN>"
token_uri = "https://oauth2.googleapis.com/token"
```

Use folder-specific IDs when possible. If only `root_folder_id` is set, the application creates or reuses direct child folders for each supported file category.

Keep `share_uploaded_files` set to `false` unless uploaded files must be available to anyone with the link.

### My Drive uploads with OAuth

Service accounts do not have normal My Drive storage quota. Use OAuth when the target folders belong to a standard Google account.

1. Enable the Google Drive and Google Sheets APIs.
2. Configure an OAuth consent screen and add the Drive owner as a test user when required.
3. Create a desktop or web OAuth client.
4. Generate a refresh token with the `https://www.googleapis.com/auth/drive` scope.
5. Store the client ID, client secret, and refresh token under `[connections.gdrive.oauth]`.
6. Set `auth_mode` to `oauth`.

The helper script can generate the refresh token:

```powershell
python scripts\generate_drive_oauth_refresh_token.py `
  --client-id "<OAUTH_CLIENT_ID>" `
  --client-secret "<OAUTH_CLIENT_SECRET>"
```

Add `http://localhost:8765/oauth2callback` to the OAuth client when Google requires an authorized redirect URI.

## Drive preview behavior

The application stores Drive URLs in the data backend and downloads private image bytes through the configured credentials for inline previews.

PNG, JPEG, JPG, and WebP images can be previewed. PDF files are presented as links or downloads.

Common failures include missing folder permissions, a disabled Drive API, service-account storage limits, an invalid refresh token, or a stale file ID.

## Testing

Run the complete automated suite from the repository root:

```bash
pytest
```

The tests cover authentication, date logic, validation, status transitions, security workflows, storage, Google Drive previews, PDF logic, empty states, and upload pages.

## Repository structure

```text
.
|-- streamlit_app.py            # Primary Streamlit entry point
|-- app.py                      # Equivalent entry-point alias
|-- modules/                    # Domain, storage, authentication, and UI modules
|-- pages/                      # Eight localized application pages
|-- scripts/                    # OAuth setup utility
|-- tests/                      # Pytest suite
|-- data/                       # Local CSV backend
|-- uploads/                    # Local upload backend
|-- assets/fonts/               # Fonts used for generated PDFs
|-- .streamlit/                 # Streamlit settings and secret template
|-- BUGFIX_REPORT.md            # Recorded defects and resolutions
`-- TEST_REPORT.md              # Test execution record
```

## Security and data handling

- Never commit `.streamlit/secrets.toml`, service account keys, OAuth secrets, or refresh tokens.
- Treat local CSV files and uploads as potentially sensitive operational records.
- Review `data/` and `uploads/` before every push.
- Keep Drive files private unless the operational process requires link sharing.
- Grant the minimum Google permissions required by the application.
- Rotate credentials immediately if a secret is exposed.

## GitHub Codespaces

The development container installs the Python dependencies and starts Streamlit on port `8501`.

Add `.streamlit/secrets.toml` inside the Codespace for Google-backed operation. Leave the storage backend in CSV mode for a credential-free review.

## Related documentation

- [`BUGFIX_REPORT.md`](BUGFIX_REPORT.md) records resolved defects.
- [`TEST_REPORT.md`](TEST_REPORT.md) records test results.

## License

Released under the [MIT License](LICENSE).
