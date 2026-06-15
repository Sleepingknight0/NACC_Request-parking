# NACC Parking Request System
สำหรับบันทึกและติดตามคำขอที่จอดรถของสำนักงาน ป.ป.ช.

## Google Drive file storage

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
