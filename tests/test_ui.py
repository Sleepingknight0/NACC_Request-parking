from modules.ui import safe_download_filename


def test_safe_download_filename_removes_path_separators():
    assert safe_download_filename("parking_sign", "ปช 0001/1234", "pdf") == "parking_sign_ปช_0001_1234.pdf"
    assert safe_download_filename("parking_sign", "QA\\PROD:*?", "pdf") == "parking_sign_QA_PROD.pdf"

