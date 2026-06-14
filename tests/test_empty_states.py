from modules import home


def test_guard_empty_home_message_is_specific():
    assert home.GUARD_EMPTY_HOME_MESSAGE == "ยังไม่มีงาน รปภ."

