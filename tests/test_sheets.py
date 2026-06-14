from modules.sheets import _normalize_private_key


def test_normalize_private_key_converts_escaped_newlines():
    raw_key = "-----BEGIN PRIVATE KEY-----\\nABC123\\n-----END PRIVATE KEY-----\\n"

    assert _normalize_private_key(raw_key) == (
        "-----BEGIN PRIVATE KEY-----\nABC123\n-----END PRIVATE KEY-----"
    )


def test_normalize_private_key_repairs_dot_after_pem_markers():
    raw_key = "-----BEGIN PRIVATE KEY-----.ABC123.-----END PRIVATE KEY-----"

    assert _normalize_private_key(raw_key) == (
        "-----BEGIN PRIVATE KEY-----\nABC123\n-----END PRIVATE KEY-----"
    )
