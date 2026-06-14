# NACC Parking Request System
สำหรับบันทึกและติดตามคำขอที่จอดรถของสำนักงาน ป.ป.ช.

## Google Drive file storage

Production uploads should use Google Drive, not local `uploads/...` paths.

Required setup:

1. Enable Google Drive API and Google Sheets API for the Google Cloud project used by the service account.
2. Put upload folders in a Google Shared Drive, or use OAuth/domain-wide delegation. A plain My Drive folder shared with a service account can be readable but still fail uploads because service accounts do not have Drive storage quota.
3. Share the Google Sheet and the target Drive folder with the service account email.
4. Configure Streamlit Secrets:

```toml
[app]
storage_backend = "gsheets"
file_storage_backend = "google_drive"

[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit"

[connections.gdrive]
root_folder_id = "<GOOGLE_DRIVE_ROOT_FOLDER_ID>"
share_uploaded_files = false

[connections.gdrive.folders]
book_files = "<BOOK_FILES_FOLDER_ID>"
guard_submissions = "<GUARD_SUBMISSIONS_FOLDER_ID>"
generated_pdfs = "<GENERATED_PDFS_FOLDER_ID>"
other = "<OTHER_FOLDER_ID>"
```

Folder-specific IDs are recommended. If only `root_folder_id` is configured, the app will create or reuse direct child folders named `book_files`, `guard_submissions`, `generated_pdfs`, and `other`.

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
- Storage quota exceeded: move the folder into a Google Shared Drive, or implement OAuth/domain-wide delegation for uploads.
- File not found: verify the stored Drive URL/file ID and folder permissions.
- Local upload path: re-upload the file so Google Sheets stores a Drive URL.
- Unsupported file type: image previews support PNG, JPEG, JPG, and WebP; PDFs show a Drive link/download instead of inline image preview.
