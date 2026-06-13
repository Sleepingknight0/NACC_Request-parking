# NACC Parking Request System

Streamlit MVP สำหรับบันทึกและติดตามคำขอที่จอดรถของสำนักงาน ป.ป.ช.

## Run Locally

```powershell
rtk python -m streamlit run app.py
```

ข้อมูลระหว่างพัฒนาจะถูกเก็บเป็น CSV ใน `data/` และไฟล์อัปโหลดจะอยู่ใน `uploads/`.
โครง `modules/sheets.py` ถูกแยกไว้เพื่อเปลี่ยนเป็น Google Sheets/Drive ภายหลังโดยไม่ต้องแก้ทุกหน้า UI.

## Test

```powershell
rtk python -m pytest -q
```
