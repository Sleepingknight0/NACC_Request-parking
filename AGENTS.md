# AGENTS.md — NACC Parking Request System

> Brief สำหรับ Codex CLI / AI coding agent  
> Project: ระบบรวบรวมและติดตามคำขอที่จอดรถ สำนักงาน ป.ป.ช.  
> Stack target: Python + Streamlit + Google Sheets + Google Drive/Cloud Storage  
> UI direction: Clean, minimal, formal, black/white special theme inspired by official-government tone, not purple-first.

---

## 0. Executive Summary

สร้าง Streamlit Web App สำหรับบันทึก ติดตาม และปิดงานคำขอที่จอดรถจากหนังสือของสำนักต่าง ๆ ภายในสำนักงาน ป.ป.ช.

ระบบต้องรองรับ:

1. บันทึกข้อมูลหนังสือขอที่จอดรถ
2. เลือกวันที่ขอที่จอดได้หลายวัน และรองรับงานข้ามเดือน
3. ระบุจำนวนรถ และระบุทะเบียนรถได้หลายคันถ้ามี
4. แนบไฟล์หนังสือ เช่น PDF / รูปภาพ
5. บันทึกข้อมูลลง Google Sheets แบบเป็นระเบียบ
6. เก็บไฟล์จริงไว้ใน Google Drive หรือ Cloud Storage แล้วเก็บ URL ใน Google Sheets
7. มี Dashboard แสดงงานตามวัน เดือน สถานะ และงานค้าง
8. มีหน้าสำหรับ รปภ. ดูงาน ดาวน์โหลด PDF ป้าย และส่งงานพร้อมรูปภาพ
9. การยกเลิกข้อมูลต้องไม่ลบ row จริง ให้เปลี่ยน status เป็น cancelled และเก็บ audit log
10. เตรียมโครงข้อมูลให้ LINE Bot/LINE integration อ่านได้ในอนาคต

Important rule:

> Do not build this as a single flat Sheet1 table. Use multiple worksheets as pseudo-relational tables.

---

## 1. Existing Prototype Context

มี prototype เดิมเป็น Streamlit single-page app ที่ทำได้แล้ว:

- เชื่อม Google Sheets ผ่าน `streamlit_gsheets.GSheetsConnection`
- มีฟอร์มบันทึกข้อมูลพื้นฐาน
- มี dropdown สำนัก
- มี dropdown จุดจอด
- มี dynamic input ถ้าเลือก `อื่นๆ (ระบุเพิ่มเติม)`
- ตรวจเลขหนังสือซ้ำ
- บันทึกข้อมูลลง `Sheet1`
- มี undo ล่าสุดโดยลบ row ออกจาก Google Sheets
- แสดงรายการที่รับเรื่องวันนี้

Prototype เดิมใช้ schema:

```text
วันที่รับเรื่อง
สำนัก
เลขหนังสือ
วันที่จอด
เวลาที่จอด
จำนวนรถ
อาคารที่จอด
```

ให้ถือ prototype นี้เป็น proof of concept เท่านั้น ห้ามยึดเป็น data model หลักของระบบจริง

เหตุผล:

- รองรับวันที่จอดได้แค่วันเดียว
- รองรับทะเบียนไม่ได้
- รองรับแนบไฟล์ไม่ได้
- ไม่มีสถานะงาน
- ไม่มีงาน รปภ.
- ไม่มี PDF generator
- ไม่มี audit log
- Undo เป็นการลบข้อมูลจริง ซึ่งไม่เหมาะกับงานเอกสาร
- ใช้เลขหนังสือเป็น unique key แข็งเกินไป
- ถ้าหนังสือหนึ่งฉบับขอหลายวันหรือข้ามเดือนจะเริ่มพัง

---

## 2. Product Goal

ระบบนี้ต้องทำให้ workflow งานจริงง่ายขึ้น:

```text
เจ้าหน้าที่รับหนังสือ
→ บันทึกข้อมูลใน Streamlit
→ เลือกวันที่จอดหลายวัน
→ แนบไฟล์หนังสือ
→ ระบุจำนวนรถ/ทะเบียน
→ ระบบสร้าง task ให้ รปภ. ตามวันที่
→ Dashboard แสดงงานค้าง/เสร็จ/ยกเลิก
→ รปภ. เปิดหน้างาน
→ ดาวน์โหลด PDF ป้ายจอดรถ
→ แปะป้าย/กรวย
→ ถ่ายรูปใกล้และไกล
→ ส่งงานพร้อมรูป
→ ระบบเปลี่ยนสถานะและบันทึกเวลาส่งงาน
```

---

## 3. Target Tech Stack

### Required

- Python 3.11+
- Streamlit
- pandas
- streamlit-gsheets
- gspread หรือ Google Sheets API client ถ้าจำเป็น
- Google Sheets เป็น database ระยะ MVP
- Google Drive หรือ Google Cloud Storage สำหรับเก็บไฟล์
- PDF generator: แนะนำ `reportlab` หรือ `fpdf2`
- Pillow ถ้าต้องสร้าง/แปลงรูปภาพประกอบ PDF

### Optional Later

- LINE Messaging API
- FastAPI / Cloud Function สำหรับ LINE webhook
- PostgreSQL / Supabase ถ้า Google Sheets เริ่มไม่พอ

---

## 4. Non-Negotiable Engineering Rules

1. ห้ามลบข้อมูลจริงเมื่อกดยกเลิก
   - ให้เปลี่ยน `status = cancelled`
   - เก็บ `cancelled_at`, `cancelled_by`, `cancelled_reason`
   - เขียน `Audit_Log`

2. ห้ามใช้สีในตารางเป็นข้อมูลหลัก
   - สีเป็น UI effect จากค่า `status` เท่านั้น

3. ห้ามเก็บไฟล์รูป/PDF ลงใน cell ของ Google Sheets
   - ให้ upload ไป storage
   - เก็บ URL ใน Google Sheets

4. ห้ามใช้ `เลขหนังสือ` เป็น primary key หลักเพียงตัวเดียว
   - ต้องมี `request_id`

5. งานข้ามเดือนต้องจัดการด้วย table `Request_Dates`
   - ไม่แยกหนังสือเป็นหลายฉบับ
   - หนังสือหนึ่งฉบับเป็น parent request
   - วันที่จอดแต่ละวันเป็น child row

6. ทุก action สำคัญต้องมี audit log
   - create request
   - update request
   - cancel request
   - cancel date
   - submit guard task
   - mark done
   - upload/delete/replace attachment

7. `st.session_state` ใช้ได้เฉพาะ state ชั่วคราวใน UI
   - ห้ามใช้เป็น database จริง

8. ทุก ID ต้อง deterministic enough และ unique
   - เช่น `REQ-2026-000001`, `DATE-...`, `TASK-...`

9. ถ้า Google Sheets ถูกใช้เป็นฐานข้อมูล ให้ลดการ rewrite ทั้ง sheet เท่าที่ทำได้
   - การ append ใหม่ควร append
   - การ update เฉพาะ row ควร update เฉพาะ row ถ้า library ทำได้
   - ถ้าจำเป็นต้อง rewrite sheet ต้องระวัง concurrent users

---

## 5. Repository Structure

ให้ refactor เป็นโครงสร้างประมาณนี้:

```text
parking_app/
  app.py
  requirements.txt
  README.md
  AGENTS.md

  .streamlit/
    secrets.toml.example
    config.toml

  pages/
    01_แดชบอร์ด.py
    02_บันทึกหนังสือ.py
    03_รายการหนังสือ.py
    04_รายละเอียดหนังสือ.py
    05_งาน_รปภ.py
    06_ส่งงาน_รปภ.py
    07_รายงานรายเดือน.py
    08_ตั้งค่า.py

  modules/
    __init__.py
    constants.py
    db.py
    sheets.py
    storage.py
    pdf_generator.py
    validators.py
    auth.py
    ui.py
    line_ready.py
    audit.py
    ids.py
    dates.py

  assets/
    logo_placeholder.png
    fonts/
      .gitkeep

  tests/
    test_dates.py
    test_validators.py
    test_pdf_logic.py
```

ถ้าอยากเริ่มง่ายกว่า ให้ทำ modules หลักก่อน:

```text
modules/constants.py
modules/sheets.py
modules/ids.py
modules/dates.py
modules/pdf_generator.py
modules/ui.py
```

---

## 6. Configuration and Secrets

ห้าม hardcode secrets ใน source code

ใช้ `.streamlit/secrets.toml` สำหรับ local/dev และ Streamlit Cloud secrets สำหรับ production

ตัวอย่าง `.streamlit/secrets.toml.example`:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/xxxx/edit#gid=0"

[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxx"
private_key = "-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n"
client_email = "xxx@xxx.iam.gserviceaccount.com"
client_id = "xxx"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "xxx"

[app]
app_name = "ระบบขอที่จอดรถ ป.ป.ช."
environment = "development"

[line]
channel_access_token = ""
channel_secret = ""
```

ถ้าใช้ Google Drive upload ให้เพิ่ม scope/credential ตามที่ implementation ต้องใช้

---

## 7. Google Sheets Database Design

ใช้ Google Sheets ไฟล์เดียว แต่มีหลาย worksheet

### 7.1 Worksheet: `Requests`

หนังสือ 1 ฉบับ = 1 row

| Column | Type | Required | Description |
|---|---:|---:|---|
| request_id | string | yes | Primary key เช่น `REQ-2026-000001` |
| book_no | string | yes | เลขหนังสือ |
| book_date | date | optional | วันที่ลงในหนังสือ |
| received_date | date | yes | วันที่รับเรื่อง |
| source_agency | string | yes | สำนัก/หน่วยงานที่ขอ |
| car_count | int | yes | จำนวนรถที่ขอ |
| parking_location | string | yes | อาคาร/จุดจอดหลัก |
| note | string | optional | หมายเหตุ |
| status | enum | yes | draft/pending/active/done/cancelled |
| has_vehicle_plates | bool | yes | มีทะเบียนหรือไม่ |
| book_file_url | string | optional | URL ไฟล์หนังสือหลัก |
| created_by | string | optional | ผู้สร้าง |
| created_at | datetime | yes | วันเวลาสร้าง |
| updated_at | datetime | yes | วันเวลาแก้ไขล่าสุด |
| cancelled_at | datetime | optional | วันเวลายกเลิก |
| cancelled_by | string | optional | ผู้ยกเลิก |
| cancelled_reason | string | optional | เหตุผลยกเลิก |

Status values:

```text
draft
pending
active
done
cancelled
```

### 7.2 Worksheet: `Request_Dates`

วันที่จอด 1 วัน = 1 row

| Column | Type | Required | Description |
|---|---:|---:|---|
| request_date_id | string | yes | Primary key |
| request_id | string | yes | FK to Requests |
| parking_date | date | yes | วันที่ขอจอด |
| parking_time | time | optional | เวลาที่เข้าจอด ถ้ามี |
| month_key | string | yes | `YYYY-MM` ใช้ filter รายเดือน |
| status | enum | yes | pending/active/done/cancelled |
| created_at | datetime | yes | วันเวลาสร้าง |
| cancelled_at | datetime | optional | วันเวลายกเลิกวันที่นี้ |
| cancelled_reason | string | optional | เหตุผลยกเลิกวันที่นี้ |

ตัวอย่างข้ามเดือน:

```text
request_id = REQ-2026-000001
book_no = ปช 0001/1234
parking dates = 2026-06-30, 2026-07-01, 2026-07-02
```

Rows:

```text
DATE-2026-000001 | REQ-2026-000001 | 2026-06-30 | 2026-06 | pending
DATE-2026-000002 | REQ-2026-000001 | 2026-07-01 | 2026-07 | pending
DATE-2026-000003 | REQ-2026-000001 | 2026-07-02 | 2026-07 | pending
```

### 7.3 Worksheet: `Vehicles`

ทะเบียน 1 รายการ = 1 row

| Column | Type | Required | Description |
|---|---:|---:|---|
| vehicle_id | string | yes | Primary key |
| request_id | string | yes | FK to Requests |
| plate_no | string | yes | เลขทะเบียน |
| vehicle_note | string | optional | หมายเหตุ |
| status | enum | yes | active/cancelled |
| created_at | datetime | yes | วันเวลาสร้าง |
| cancelled_at | datetime | optional | วันเวลายกเลิกทะเบียน |
| cancelled_reason | string | optional | เหตุผลยกเลิกทะเบียน |

ถ้า request ไม่มีทะเบียน ไม่ต้องสร้าง row ใน worksheet นี้

### 7.4 Worksheet: `Guard_Tasks`

งาน รปภ. 1 งาน = 1 row

โดยปกติ task ควรถูกสร้างจาก `Request_Dates` 1 วัน = 1 task

| Column | Type | Required | Description |
|---|---:|---:|---|
| task_id | string | yes | Primary key |
| request_id | string | yes | FK to Requests |
| request_date_id | string | yes | FK to Request_Dates |
| parking_date | date | yes | วันที่ต้องปฏิบัติงาน |
| parking_location | string | yes | จุดจอด |
| status | enum | yes | pending/in_progress/submitted/done/cancelled |
| assigned_to | string | optional | ผู้รับผิดชอบ/ทีม |
| submitted_at | datetime | optional | เวลาที่ รปภ. ส่งงาน |
| completed_at | datetime | optional | เวลาปิดงาน |
| created_at | datetime | yes | วันเวลาสร้าง |
| updated_at | datetime | yes | วันเวลาแก้ไข |

Status values:

```text
pending
in_progress
submitted
done
cancelled
```

### 7.5 Worksheet: `Guard_Submissions`

การส่งงานของ รปภ. 1 ครั้ง = 1 row

| Column | Type | Required | Description |
|---|---:|---:|---|
| submission_id | string | yes | Primary key |
| task_id | string | yes | FK to Guard_Tasks |
| request_id | string | yes | FK to Requests |
| near_photo_url | string | yes | รูปใกล้ เห็นกรวย/กระดาษชัด |
| far_photo_url | string | yes | รูปไกล เห็นบริเวณ/สถานที่ |
| extra_photo_url | string | optional | รูปเสริม ถ้ามี |
| note | string | optional | รายละเอียดเพิ่มเติม |
| submitted_by | string | optional | ผู้ส่งงาน |
| submitted_at | datetime | yes | วันเวลาส่งงาน |
| is_final | bool | yes | ส่งเป็น final หรือ draft |

### 7.6 Worksheet: `Attachments`

เก็บไฟล์แนบทุกประเภท

| Column | Type | Required | Description |
|---|---:|---:|---|
| attachment_id | string | yes | Primary key |
| request_id | string | optional | FK to Requests |
| task_id | string | optional | FK to Guard_Tasks |
| file_type | enum | yes | book/guard_photo/pdf_form/other |
| file_name | string | yes | ชื่อไฟล์ |
| file_url | string | yes | URL ไฟล์ |
| mime_type | string | optional | MIME type |
| uploaded_by | string | optional | ผู้อัปโหลด |
| uploaded_at | datetime | yes | เวลา upload |
| status | enum | yes | active/deleted/replaced |

### 7.7 Worksheet: `Audit_Log`

ทุก action สำคัญต้องลง log

| Column | Type | Required | Description |
|---|---:|---:|---|
| log_id | string | yes | Primary key |
| action | string | yes | create/update/cancel/submit/upload/etc. |
| target_table | string | yes | table ที่ถูกกระทำ |
| target_id | string | yes | id ของ row |
| old_value | string/json | optional | ค่าเดิม |
| new_value | string/json | optional | ค่าใหม่ |
| user | string | optional | ผู้กระทำ |
| created_at | datetime | yes | วันเวลา |

---

## 8. ID Conventions

Implement helper functions in `modules/ids.py`.

Example output:

```text
REQ-2026-000001
DATE-2026-000001
VEH-2026-000001
TASK-2026-000001
SUB-2026-000001
ATT-2026-000001
LOG-2026-000001
```

MVP option:

- Generate ID from timestamp + random suffix to avoid expensive sheet scan.

Example:

```python
def make_id(prefix: str) -> str:
    # Example: REQ-20260613-153012-A7K3
    ...
```

Better option later:

- Read max running number by prefix/year from a settings worksheet or database sequence.

---

## 9. Date Handling Rules

Implement in `modules/dates.py`.

Required helpers:

```python
def to_iso_date(value) -> str:
    """Return YYYY-MM-DD."""


def to_month_key(date_value) -> str:
    """Return YYYY-MM."""


def expand_date_range(start_date, end_date, include_weekends=True) -> list[str]:
    """Return list of ISO dates."""


def parse_multiline_dates(text: str) -> list[str]:
    """Parse dates from textarea, one date per line, return unique sorted ISO dates."""
```

UI should support at least one of these date selection modes:

1. Single day
2. Date range
3. Manual multiline dates

Recommended MVP UI:

```text
เลือกวิธีระบุวันที่:
[วันที่เดียว] [ช่วงวันที่] [ระบุหลายวันเอง]
```

For cross-month jobs:

- Store all parking dates in `Request_Dates`
- Compute `month_key` per row
- Dashboard filters by `month_key`
- Do not duplicate parent request

---

## 10. Main Workflows

### 10.1 Create Request Workflow

Page: `02_บันทึกหนังสือ.py`

Steps:

1. User fills request form
2. Validate required fields
3. Check duplicate `book_no` in non-cancelled `Requests`
4. Generate `request_id`
5. Upload book file if provided
6. Create row in `Requests`
7. Expand selected parking dates
8. Create rows in `Request_Dates`
9. If vehicle plates provided, create rows in `Vehicles`
10. Create one `Guard_Tasks` row per `Request_Dates` row
11. Write `Audit_Log`
12. Show success message with link/button to request detail

Duplicate rule:

- If same `book_no` exists and status is not cancelled, block create.
- If same `book_no` exists but cancelled, show warning and let admin decide later. MVP can block entirely for safety.

### 10.2 Update Request Workflow

Page: `04_รายละเอียดหนังสือ.py`

Allow editing:

- source_agency
- car_count
- parking_location
- note
- book_file_url replacement
- vehicle plates
- parking dates only if guard task is not already done

If editing dates:

- New dates create new `Request_Dates` + `Guard_Tasks`
- Removed dates should be marked `cancelled`, not deleted

### 10.3 Cancel Request Workflow

Do not delete rows.

When cancelling entire request:

1. Ask confirmation
2. Require cancellation reason
3. Set `Requests.status = cancelled`
4. Set related `Request_Dates.status = cancelled`
5. Set related `Guard_Tasks.status = cancelled`
6. Optionally set related active `Vehicles.status = cancelled`
7. Write audit log
8. UI shows cancelled row in dark gray/near black style

### 10.4 Cancel One Date Workflow

When cancelling only one parking date:

1. Set selected `Request_Dates.status = cancelled`
2. Set related `Guard_Tasks.status = cancelled`
3. Keep parent request active if other dates remain active
4. Write audit log

### 10.5 Cancel One Vehicle Plate Workflow

1. Set `Vehicles.status = cancelled`
2. Keep request active
3. Regenerated PDF should exclude cancelled plates
4. Write audit log

### 10.6 Guard Task Submission Workflow

Page: `06_ส่งงาน_รปภ.py`

Steps:

1. Guard opens task detail
2. UI shows instructions:
   - Upload at least 2 photos
   - Photo 1: close-up, clear cone/paper
   - Photo 2: wide shot, visible parking/location context
3. Guard uploads near photo
4. Guard uploads far photo
5. Guard may upload extra photo
6. Guard may add optional note
7. Confirm modal/checkbox before submit
8. Upload photos to storage
9. Create row in `Guard_Submissions`
10. Set `Guard_Tasks.status = submitted` or `done` depending MVP policy
11. Set `submitted_at`
12. If all tasks for request are done/submitted, optionally update parent request to `done`
13. Write audit log

MVP policy:

- Use `submitted` after guard sends photo
- Admin/officer can mark `done` after review

Simpler MVP policy if no review:

- Set `done` immediately after guard submits

Pick one and implement consistently. Recommended: `submitted` first, `done` after review.

---

## 11. PDF Generation Rules

Module: `modules/pdf_generator.py`

Purpose:

- Generate printable parking signs/forms from request data
- Provide `st.download_button` for PDF download

### 11.1 If no vehicle plates

Generate 1-page PDF.

Content:

```text
(สำนัก...)
จำนวน 3 คัน
```

Design:

- Agency text: small/top, centered
- Main text: very large, centered
- Optional footer: location/date/book_no smaller

### 11.2 If vehicle plates exist

Generate one page per active vehicle plate.

Example for 3 plates:

Page 1:

```text
(สำนัก...)
TEST1
```

Page 2:

```text
(สำนัก...)
TEST2
```

Page 3:

```text
(สำนัก...)
TEST3
```

Design:

- Agency text: small/top, centered
- Plate number: very large, centered
- Optional footer: location/date/book_no

### 11.3 PDF Function Interface

Implement roughly:

```python
def build_parking_pdf(
    agency: str,
    car_count: int,
    plates: list[str],
    parking_location: str,
    parking_date: str | None = None,
    book_no: str | None = None,
) -> bytes:
    """Return PDF bytes."""
```

The function should return bytes so Streamlit can use:

```python
st.download_button(
    label="ดาวน์โหลด PDF",
    data=pdf_bytes,
    file_name="parking_sign_REQ-2026-000001.pdf",
    mime="application/pdf",
)
```

---

## 12. Pages and UI Requirements

### 12.1 `app.py`

Purpose:

- App bootstrap
- Set page config
- Load global CSS
- Render navigation if using Streamlit's native multipage

Required:

```python
st.set_page_config(
    page_title="ระบบขอที่จอดรถ ป.ป.ช.",
    page_icon="📝",
    layout="wide",
)
```

Use `modules/ui.py` for shared CSS/components.

### 12.2 Page: Dashboard

File: `pages/01_แดชบอร์ด.py`

Must show:

- Month selector
- Summary cards:
  - หนังสือทั้งหมด
  - วันที่ขอจอดทั้งหมด
  - จำนวนรถรวม
  - งานค้าง
  - งานส่งแล้ว
  - งานเสร็จ
  - งานยกเลิก
- Today tasks
- Pending guard tasks
- Recently submitted tasks
- Filter by:
  - month
  - source agency
  - parking location
  - status
- Clean table with status badges

### 12.3 Page: New Request

File: `pages/02_บันทึกหนังสือ.py`

Form sections:

1. ข้อมูลหนังสือ
   - เลขหนังสือ
   - วันที่หนังสือ
   - วันที่รับเรื่อง
   - สำนัก
   - แนบไฟล์หนังสือ

2. รายละเอียดที่จอด
   - จำนวนรถ
   - จุดจอด
   - อื่นๆ ระบุเพิ่มเติม
   - วันที่จอดแบบหลายวัน
   - เวลาที่จอด ถ้ามี

3. ทะเบียนรถ
   - มีทะเบียนหรือไม่
   - จำนวนทะเบียน/เพิ่มทะเบียน
   - plate inputs

4. หมายเหตุ

5. Save button

Validation:

- book_no required
- received_date required
- source agency required
- car_count >= 1
- parking location required
- at least one parking date
- if selected location is other, other location required
- if has plates, at least one plate required unless user confirms partial/unknown plates

### 12.4 Page: Request List

File: `pages/03_รายการหนังสือ.py`

Features:

- Search by book_no, request_id, agency, plate_no
- Filter by status
- Filter by month
- Filter by date range
- Filter by parking location
- Click/open request detail
- Show cancelled rows in dark muted style

### 12.5 Page: Request Detail

File: `pages/04_รายละเอียดหนังสือ.py`

Show:

- request summary
- book file link
- parking dates list
- vehicle plates list
- guard tasks list
- submission photos links
- status history/audit excerpt

Actions:

- Edit request
- Cancel request
- Cancel selected date
- Cancel selected plate
- Download PDF for selected date/task
- Mark task done after review

### 12.6 Page: Guard Tasks

File: `pages/05_งาน_รปภ.py`

Audience: รปภ.

Must be very simple.

Default sections:

```text
งานวันนี้
งานพรุ่งนี้
งานค้าง
งานส่งแล้วรอตรวจ
```

Each task card/table row:

- date
- agency
- location
- car count
- status
- button: ดูรายละเอียด
- button: ดาวน์โหลด PDF
- button: ส่งงาน

### 12.7 Page: Guard Submit

File: `pages/06_ส่งงาน_รปภ.py`

Show task details:

- agency
- book_no
- location
- date
- car count
- plates if any
- book file link
- PDF download

Submission form:

- Instruction text
- near photo uploader required
- far photo uploader required
- extra photo uploader optional
- note optional
- confirmation checkbox:
  - `ยืนยันว่าภาพถ่ายถูกต้องและต้องการส่งงานนี้`
- submit button

After submit:

- upload files to storage
- write `Guard_Submissions`
- update task status
- show success

### 12.8 Page: Monthly Report

File: `pages/07_รายงานรายเดือน.py`

Features:

- select month
- show grouped data by date
- show summary by agency
- show summary by parking location
- export CSV/XLSX if possible

### 12.9 Page: Settings

File: `pages/08_ตั้งค่า.py`

MVP:

- show constants
- maybe edit parking locations later
- show data health checks:
  - missing request links
  - orphan guard tasks
  - cancelled requests with active tasks

---

## 13. UI/UX Direction

The user wants clean minimal UI. Official organization normally uses white/purple, but this special system should use black/white.

### 13.1 Visual Style

Keywords:

```text
clean
minimal
formal
government-grade
calm
white/black
high readability
low decoration
compact but not cramped
```

Use:

- White background
- Black / near-black text
- Light gray dividers
- Soft gray cards
- Minimal borders
- No heavy gradients
- No colorful UI except status badges
- Use purple only as an optional tiny accent if necessary, but default theme is black/white

### 13.2 Color Tokens

Use design tokens in `modules/ui.py` or CSS:

```text
--bg: #FFFFFF
--surface: #F7F7F7
--surface-2: #F1F1F1
--text: #111111
--muted: #666666
--border: #E5E5E5
--black: #000000
--status-pending-bg: #FFF7D6
--status-pending-text: #6B5600
--status-progress-bg: #EAF2FF
--status-progress-text: #124B8A
--status-submitted-bg: #F0EAFE
--status-submitted-text: #4B267A
--status-done-bg: #E9F7EF
--status-done-text: #146C2E
--status-cancelled-bg: #1F1F1F
--status-cancelled-text: #F2F2F2
```

Even in black/white theme, status colors are allowed because they improve operational readability.

### 13.3 Typography

- Prefer system fonts first
- Thai readability important
- CSS font-family:

```css
font-family: "Noto Sans Thai", "Sarabun", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Do not bundle external fonts unless user provides them.

### 13.4 Layout

- Use wide layout
- Keep forms in cards/sections
- Two-column layout for data entry
- Dashboard cards at top
- Tables below with filters
- Guard page must be mobile-friendly and readable

### 13.5 Component Style

Use shared helper functions:

```python
def render_page_title(title: str, subtitle: str | None = None): ...
def status_badge(status: str) -> str: ...
def metric_card(label: str, value: str, caption: str | None = None): ...
def section_card(title: str): ...
```

### 13.6 Suggested CSS Injection

Implement in `modules/ui.py`:

```python
import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #FFFFFF;
            --surface: #F7F7F7;
            --surface-2: #F1F1F1;
            --text: #111111;
            --muted: #666666;
            --border: #E5E5E5;
            --black: #000000;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: "Noto Sans Thai", "Sarabun", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: -0.02em;
        }

        section[data-testid="stSidebar"] {
            background: #FAFAFA;
            border-right: 1px solid var(--border);
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 16px;
            border-radius: 14px;
        }

        .nacc-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .nacc-muted {
            color: var(--muted);
            font-size: 0.92rem;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            border: 1px solid transparent;
        }

        .status-pending {
            background: #FFF7D6;
            color: #6B5600;
        }

        .status-in_progress {
            background: #EAF2FF;
            color: #124B8A;
        }

        .status-submitted {
            background: #F0EAFE;
            color: #4B267A;
        }

        .status-done {
            background: #E9F7EF;
            color: #146C2E;
        }

        .status-cancelled {
            background: #1F1F1F;
            color: #F2F2F2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
```

---

## 14. Constants

Implement in `modules/constants.py`.

### 14.1 NACC Departments

```python
NACC_DEPARTMENTS = [
    "สำนักกิจการคณะกรรมการ ป.ป.ช.",
    "สำนักการประชุม",
    "สำนักบริหารงานกลาง",
    "สำนักตรวจสอบภายใน",
    "สำนักตรวจราชการ",
    "สำนักสืบสวนและกิจการพิเศษ",
    "สำนักไต่สวนคดีพิเศษ",
    "กลุ่มที่ปรึกษาสำนักงาน ป.ป.ช.",
    "สำนักพัฒนาวิชาการด้านการศึกษาและกระบวนการมีส่วนร่วมต้านทุจริต",
    "สำนักประเมินคุณธรรม ความโปร่งใส และส่งเสริมธรรมาภิบาล",
    "สำนักมาตรการป้องกันการทุจริต",
    "สำนักป้องกันการขัดกันแห่งผลประโยชน์และกำกับจริยธรรมภาครัฐ",
    "สำนักพัฒนาระบบตรวจสอบทรัพย์สิน",
    "สำนักตรวจสอบทรัพย์สินภาคการเมือง",
    "สำนักตรวจสอบทรัพย์สินภาครัฐและรัฐวิสาหกิจ ๑",
    "สำนักตรวจสอบทรัพย์สินภาครัฐและรัฐวิสาหกิจ ๒",
    "สำนักตรวจสอบทรัพย์สินภาครัฐและรัฐวิสาหกิจ ๓",
    "สำนักตรวจสอบทรัพย์สินภาครัฐและรัฐวิสาหกิจ ๔",
    "สำนักตรวจสอบทรัพย์สินภาครัฐและรัฐวิสาหกิจ ๕",
    "สำนักตรวจสอบทรัพย์สินภาครัฐและรัฐวิสาหกิจ ๖",
    "สำนักไต่สวนการทุจริตคดีการเมืองการปกครอง ๑",
    "สำนักไต่สวนการทุจริตคดีการเมืองการปกครอง ๒",
    "สำนักไต่สวนการทุจริตคดีการเมืองการปกครอง ๓",
    "สำนักไต่สวนการทุจริตคดีเศรษฐกิจ ๑",
    "สำนักไต่สวนการทุจริตคดีเศรษฐกิจ ๒",
    "สำนักไต่สวนการทุจริตคดีเศรษฐกิจ ๓",
    "สำนักไต่สวนการทุจริตคดีของหน่วยงานที่ขึ้นตรงต่อนายกรัฐมนตรี",
    "สำนักไต่สวนการทุจริตคดีความมั่นคงของรัฐ",
    "สำนักไต่สวนการทุจริตคดีความมั่นคงด้านทรัพยากรธรรมชาติและสิ่งแวดล้อม",
    "สำนักกฎหมาย",
    "สำนักพัฒนาระบบกฎหมาย",
    "สำนักพันธกรณีและความร่วมมือระหว่างประเทศ",
    "สำนักคดี ๑",
    "สำนักคดี ๒",
    "สำนักคดี ๓",
    "สำนักยุทธศาสตร์ด้านการป้องกันและปราบปรามการทุจริต",
    "สำนักวิเคราะห์แผนและงบประมาณ",
    "สำนักบริหารงานคลัง",
    "สำนักบริหารทรัพย์สิน",
    "สำนักสื่อสารองค์กร",
    "สำนักบริหารทรัพยากรบุคคล",
    "สถาบันการป้องกันและปราบปรามการทุจริตแห่งชาติ สัญญา ธรรมศักดิ์",
    "สำนักวิจัยและบริการวิชาการด้านการป้องกันและปราบปรามการทุจริต",
    "สำนักเทคโนโลยีสารสนเทศ",
    "สำนักนวัตกรรม เทคโนโลยี และภูมิสารสนเทศ",
]
```

### 14.2 Parking Locations

```python
PARKING_LOCATIONS = [
    "ข้างอาคาร 1 ฝั่งกองสลาก",
    "หน้าอาคาร 3",
    "หน้าอาคาร 2",
    "บริเวณอาคารสถาบันฯ",
    "หน้าอาคาร 4",
    "ชั้นใต้ดินอาคาร 4",
    "อาคาร 4",
    "อาคาร 7",
    "อาคาร 8",
    "อื่นๆ (ระบุเพิ่มเติม)",
]
```

### 14.3 Status Labels

```python
REQUEST_STATUS_LABELS = {
    "draft": "ร่าง",
    "pending": "รอดำเนินการ",
    "active": "ใช้งานอยู่",
    "done": "เสร็จสิ้น",
    "cancelled": "ยกเลิก",
}

GUARD_TASK_STATUS_LABELS = {
    "pending": "ยังไม่ได้ทำ",
    "in_progress": "กำลังดำเนินการ",
    "submitted": "ส่งงานแล้ว",
    "done": "เสร็จสิ้น",
    "cancelled": "ยกเลิก",
}
```

---

## 15. Data Access Layer

Module: `modules/sheets.py`

Do not scatter `conn.read()` and `conn.update()` across all pages. Centralize data access.

Required functions:

```python
def get_connection(): ...


def read_sheet(worksheet: str, ttl: int = 0) -> pd.DataFrame: ...


def write_sheet(worksheet: str, df: pd.DataFrame) -> None: ...


def append_rows(worksheet: str, rows: list[dict]) -> None: ...


def update_row_by_id(worksheet: str, id_col: str, id_value: str, updates: dict) -> None: ...


def get_request_by_id(request_id: str) -> dict | None: ...


def get_request_by_book_no(book_no: str) -> dict | None: ...


def list_request_dates(request_id: str) -> pd.DataFrame: ...


def list_vehicles(request_id: str, active_only: bool = True) -> pd.DataFrame: ...


def list_guard_tasks(request_id: str | None = None) -> pd.DataFrame: ...
```

If `streamlit_gsheets` does not support efficient append/update by row, MVP can read/write whole worksheet but keep all write operations centralized for future replacement.

---

## 16. Storage Layer

Module: `modules/storage.py`

MVP fallback:

- If Google Drive upload is not ready, save file metadata only and show warning.
- But production should upload files to Google Drive/Cloud Storage.

Required function shape:

```python
def upload_file(file, folder: str, prefix: str) -> dict:
    """
    Return:
    {
      "file_name": str,
      "file_url": str,
      "mime_type": str,
      "storage_key": str | None,
    }
    """
```

File categories:

```text
book_files/
guard_submissions/
generated_pdfs/
other/
```

---

## 17. LINE-Ready Data Design

Do not fully build LINE Bot in MVP unless requested.

But prepare data and helper functions so LINE can query:

- งานวันนี้
- งานค้าง
- ค้นหาเลขหนังสือ
- ค้นหาทะเบียน
- งานตามอาคาร

Module: `modules/line_ready.py`

Suggested functions:

```python
def get_today_tasks_for_line() -> list[dict]: ...
def get_pending_tasks_for_line() -> list[dict]: ...
def search_task_for_line(query: str) -> list[dict]: ...
def format_task_line_message(tasks: list[dict]) -> str: ...
```

Example LINE message:

```text
งานที่จอดรถวันนี้

1. สำนักบริหารงานกลาง
   อาคาร: หน้าอาคาร 3
   จำนวน: 3 คัน
   สถานะ: ยังไม่ได้ทำ

2. สำนักเทคโนโลยีสารสนเทศ
   อาคาร: อาคาร 4
   จำนวน: 1 คัน
   สถานะ: ส่งงานแล้ว
```

---

## 18. Validation Rules

Module: `modules/validators.py`

Required validators:

```python
def validate_book_no(book_no: str) -> tuple[bool, str | None]: ...
def validate_car_count(count: int) -> tuple[bool, str | None]: ...
def validate_parking_dates(dates: list[str]) -> tuple[bool, str | None]: ...
def validate_location(selected_loc: str, other_loc: str | None) -> tuple[bool, str | None]: ...
def validate_plates(plates: list[str], car_count: int) -> tuple[bool, str | None]: ...
def validate_guard_submission(near_photo, far_photo) -> tuple[bool, str | None]: ...
```

Rules:

- `book_no` cannot be empty
- `car_count >= 1`
- At least one parking date is required
- If selected `อื่นๆ`, other location cannot be empty
- Plate numbers should be stripped and normalized
- Duplicate plate numbers inside the same request should warn/block
- Guard submission must have near photo and far photo

---

## 19. Required Acceptance Criteria

### 19.1 Create Request

- User can create a new request with one or many parking dates
- System generates `request_id`
- System writes parent row to `Requests`
- System writes parking dates to `Request_Dates`
- System writes guard tasks to `Guard_Tasks`
- System writes vehicles if provided
- Duplicate active `book_no` is blocked
- Success message appears

### 19.2 Cross-Month Handling

Given one request with dates:

```text
2026-06-30
2026-07-01
2026-07-02
```

Then:

- `Requests` has 1 row
- `Request_Dates` has 3 rows
- `Guard_Tasks` has 3 rows
- Dashboard for June shows 2026-06-30
- Dashboard for July shows 2026-07-01 and 2026-07-02

### 19.3 Cancel Request

- User can cancel a request only after confirming
- Reason is required
- No row is deleted
- Related dates/tasks are marked cancelled
- Cancelled rows display dark gray/black badge
- Audit log is written

### 19.4 Guard Submission

- Guard sees pending task
- Guard can download PDF
- Guard must upload near and far photos
- Guard may add note
- Confirmation is required before submit
- Submission row is created
- Task status changes
- Timestamp is saved

### 19.5 PDF

- If request has no plates, generated PDF has 1 page with agency and car count
- If request has 3 active plates, generated PDF has 3 pages
- Cancelled plates are excluded
- PDF can be downloaded from Streamlit

### 19.6 Dashboard

- Month filter works
- Pending/done/cancelled counts are correct
- Today's tasks are visible
- Pending guard tasks are visible
- Cancelled tasks are visibly muted/dark

---

## 20. Suggested Build Phases for Codex CLI

### Phase 0: Refactor Skeleton

Tasks:

1. Create repository structure
2. Move constants out of main app
3. Add `modules/ui.py`
4. Add `modules/dates.py`
5. Add `modules/ids.py`
6. Add `modules/sheets.py`
7. Keep current form working if possible

### Phase 1: New Data Model

Tasks:

1. Replace flat `Sheet1` schema with multi-worksheet schema
2. Add initialization/check function that verifies required worksheets/columns
3. Add create request workflow
4. Add duplicate book_no check
5. Add request_id generation
6. Add date expansion
7. Add vehicle plate handling
8. Add guard task generation

### Phase 2: Dashboard and List

Tasks:

1. Build dashboard page
2. Build request list page
3. Implement filters
4. Add status badges
5. Add month_key filtering

### Phase 3: Detail, Cancel, and Audit

Tasks:

1. Build request detail page
2. Add cancel request
3. Add cancel date
4. Add cancel plate
5. Add audit logging

### Phase 4: Guard Workflow

Tasks:

1. Build guard task page
2. Build guard submit page
3. Add file upload placeholder/storage layer
4. Add submission records
5. Update task status

### Phase 5: PDF Generator

Tasks:

1. Add `pdf_generator.py`
2. Implement PDF bytes generation
3. Add download buttons on guard page/detail page
4. Add Thai text support if available
5. Fallback gracefully if Thai font unavailable

### Phase 6: Storage and LINE-ready

Tasks:

1. Implement Google Drive/Cloud Storage upload
2. Save attachment metadata
3. Add LINE-ready query helpers
4. Document future LINE Bot integration

---

## 21. Testing Strategy

At minimum, test pure functions:

- date range expansion
- month_key generation
- multiline date parsing
- plate validation
- status transition logic
- PDF page count logic

Manual scenario tests:

1. Create request, one day, no plate
2. Create request, multiple days, no plate
3. Create request, cross-month, no plate
4. Create request, 3 plates
5. Generate PDF with 3 plates
6. Cancel one plate and regenerate PDF
7. Cancel one date only
8. Cancel entire request
9. Submit guard task with two photos
10. Dashboard month filter

---

## 22. Streamlit-Specific Implementation Notes

1. Use `st.form()` for create request to avoid partial rerun confusion
2. Use `st.session_state` for dynamic plate input count
3. Use `st.cache_data` carefully for reads, but set ttl short or zero for operational pages
4. Avoid caching writes
5. Use `st.rerun()` after successful create/update/cancel if needed
6. Avoid local persistent file storage on Streamlit Cloud
7. Use `st.download_button` for PDF bytes
8. Keep guard pages mobile-friendly

---

## 23. Minimal Requirements File

Suggested `requirements.txt`:

```text
streamlit>=1.35
pandas>=2.0
streamlit-gsheets>=0.0.4
gspread>=6.0
google-auth>=2.0
reportlab>=4.0
Pillow>=10.0
python-dateutil>=2.8
```

Adjust versions based on actual environment.

---

## 24. Important UX Copy

### Guard Submit Instruction

```text
กรุณาอัปโหลดรูปอย่างน้อย 2 รูปก่อนส่งงาน

1. รูปใกล้: เห็นกรวยและกระดาษที่แปะชัดเจน
2. รูปไกล: เห็นตำแหน่งสถานที่วางกรวยโดยรวม

สามารถเพิ่มรายละเอียดเพิ่มเติมได้ หากมีข้อมูลที่ต้องแจ้งเจ้าหน้าที่
```

### Cancel Confirmation

```text
การยกเลิกจะไม่ลบข้อมูลออกจากระบบ แต่จะเปลี่ยนสถานะเป็น “ยกเลิก” และบันทึกประวัติไว้
กรุณาระบุเหตุผลก่อนยืนยัน
```

### Duplicate Book Number

```text
ไม่สามารถบันทึกได้ เลขหนังสือนี้มีอยู่ในระบบแล้ว
กรุณาตรวจสอบรายการเดิมก่อนสร้างคำขอใหม่
```

---

## 25. Open Questions / Decisions Needed

If implementation must proceed without asking user, use these defaults:

1. Review flow after guard submits:
   - Default: guard submission sets task to `submitted`; officer later marks `done`

2. Storage:
   - Default: prepare interface for Google Drive upload
   - If credentials unavailable, implement local/mock storage warning for dev only

3. Authentication:
   - Default MVP: simple role selector/password gate for internal testing
   - Production: use Google/Microsoft authentication

4. LINE:
   - Default MVP: do not build full bot yet
   - Build helper functions and make data LINE-readable

5. Date selection:
   - Default MVP: support single date, date range, and multiline manual dates

6. Official logo/assets:
   - Do not scrape official assets automatically
   - Use placeholder unless user provides approved logo/image

---

## 26. Definition of Done for MVP

MVP is done when:

- User can create requests with multiple dates
- Data is stored in multi-worksheet Google Sheets structure
- Cross-month requests display correctly by month
- User can add vehicle plates
- User can cancel without deleting rows
- Dashboard shows basic counts and pending tasks
- Guard can see tasks and submit two required photos
- PDF signs can be generated/downloaded
- UI is clean, minimal, black/white, and usable on desktop/tablet/mobile
- Core business actions write audit logs

---

## 27. Final Implementation Priority

Build in this order:

```text
1. Data schema and helper modules
2. Create request page
3. Multi-date and cross-month support
4. Vehicle plates
5. Guard task generation
6. Dashboard
7. Request detail/cancel/audit
8. Guard task page
9. Guard submission page
10. PDF generator
11. File storage integration
12. LINE-ready helpers
```

Do not start with visual polish before the data model is correct. The system will be hard to fix later if the schema is wrong.

