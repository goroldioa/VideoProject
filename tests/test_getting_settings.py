import pytest
import os
from unittest import mock

try:
    import tkinter
    import tkinter.messagebox
    import tkinter.simpledialog
    import tkinter.filedialog
except ImportError:
    tkinter = mock.MagicMock()
    tkinter.messagebox = mock.MagicMock()
    tkinter.simpledialog = mock.MagicMock()
    tkinter.filedialog = mock.MagicMock()

from Video import getting_settings

EXISTING_SETTINGS_CONTENT = """30
1280
720
0
/path/to/usb/folder
rtsp://user1:pass1@192.168.1.101/
/path/to/ip1/folder
rtsp://user2:pass2@192.168.1.102/
/path/to/ip2/folder
rtsp://user3:pass3@192.168.1.103/
/path/to/ip3/folder
"""


MOCK_USER_INPUT = {
    "fps": 25,
    "width": 640,
    "height": 480,
    "usb_index": 1,
    "usb_folder": "/new/usb/path",
    "ip1": "rtsp://new_user1:new_pass1@10.0.0.1/",
    "ip1_folder": "/new/ip1/path",
    "ip2": "rtsp://new_user2:new_pass2@10.0.0.2/",
    "ip2_folder": "/new/ip2/path",
    "ip3": "rtsp://new_user3:new_pass3@10.0.0.3/",
    "ip3_folder": "/new/ip3/path",
}

EXPECTED_NEW_SETTINGS = (
    MOCK_USER_INPUT["fps"],
    MOCK_USER_INPUT["width"],
    MOCK_USER_INPUT["height"],
    MOCK_USER_INPUT["usb_index"],
    MOCK_USER_INPUT["usb_folder"],
    [MOCK_USER_INPUT["ip1"], MOCK_USER_INPUT["ip2"], MOCK_USER_INPUT["ip3"]],
    [MOCK_USER_INPUT["ip1_folder"], MOCK_USER_INPUT["ip2_folder"], MOCK_USER_INPUT["ip3_folder"]]
)


@pytest.fixture
def mock_tkinter(mocker):
    """Фикстура для моканья всех tkinter диалогов."""
    mock_askyesno = mocker.patch('tkinter.messagebox.askyesno', return_value=False)
    mock_askinteger = mocker.patch('tkinter.simpledialog.askinteger')
    mock_askstring = mocker.patch('tkinter.simpledialog.askstring')
    mock_askdirectory = mocker.patch('tkinter.filedialog.askdirectory')
    return mock_askyesno, mock_askinteger, mock_askstring, mock_askdirectory

def test_settings_exist_and_user_declines_change(tmp_path, monkeypatch, mock_tkinter):
    """
    Тест: Файл settings.txt существует, пользователь НЕ хочет менять настройки.
    Ожидание: Функция должна прочитать настройки из файла и вернуть их. Файл не меняется.
    """
    mock_askyesno, _, _, _ = mock_tkinter
    mock_askyesno.return_value = False

    settings_file = tmp_path / "settings.txt"
    settings_file.write_text(EXISTING_SETTINGS_CONTENT, encoding='utf-8')
    initial_content = settings_file.read_text(encoding='utf-8')

    monkeypatch.chdir(tmp_path)

    result = getting_settings()
    mock_askyesno.assert_called_once()
    assert settings_file.read_text(encoding='utf-8') == initial_content

def test_settings_exist_and_user_accepts_change(tmp_path, monkeypatch, mock_tkinter):
    """
    Тест: Файл settings.txt существует, пользователь ХОЧЕТ менять настройки.
    Ожидание: Функция должна запросить новые настройки, перезаписать файл и вернуть новые настройки.
    """
    mock_askyesno, mock_askinteger, mock_askstring, mock_askdirectory = mock_tkinter

    mock_askyesno.return_value = True
    mock_askinteger.side_effect = [
        MOCK_USER_INPUT["fps"], MOCK_USER_INPUT["width"],
        MOCK_USER_INPUT["height"], MOCK_USER_INPUT["usb_index"]
    ]
    mock_askstring.side_effect = [
        MOCK_USER_INPUT["ip1"], MOCK_USER_INPUT["ip2"], MOCK_USER_INPUT["ip3"]
    ]
    mock_askdirectory.side_effect = [
        MOCK_USER_INPUT["usb_folder"], MOCK_USER_INPUT["ip1_folder"],
        MOCK_USER_INPUT["ip2_folder"], MOCK_USER_INPUT["ip3_folder"]
    ]

    settings_file = tmp_path / "settings.txt"
    settings_file.write_text(EXISTING_SETTINGS_CONTENT, encoding='utf-8')

    monkeypatch.chdir(tmp_path)

    result = getting_settings()

    assert result == EXPECTED_NEW_SETTINGS
    assert settings_file.exists()

    mock_askyesno.assert_called_once()
    assert mock_askinteger.call_count == 4
    assert mock_askstring.call_count == 3
    assert mock_askdirectory.call_count == 4


def test_settings_do_not_exist(tmp_path, monkeypatch, mock_tkinter):
    """
    Тест: Файл settings.txt НЕ существует.
    Ожидание: Функция должна запросить новые настройки, создать файл, записать их и вернуть новые настройки.
    """
    settings_file = tmp_path / "settings.txt"

    _, mock_askinteger, mock_askstring, mock_askdirectory = mock_tkinter

    mock_askinteger.side_effect = [
        MOCK_USER_INPUT["fps"], MOCK_USER_INPUT["width"],
        MOCK_USER_INPUT["height"], MOCK_USER_INPUT["usb_index"]
    ]
    mock_askstring.side_effect = [
        MOCK_USER_INPUT["ip1"], MOCK_USER_INPUT["ip2"], MOCK_USER_INPUT["ip3"]
    ]
    mock_askdirectory.side_effect = [
        MOCK_USER_INPUT["usb_folder"], MOCK_USER_INPUT["ip1_folder"],
        MOCK_USER_INPUT["ip2_folder"], MOCK_USER_INPUT["ip3_folder"]
    ]

    monkeypatch.chdir(tmp_path)

    result = getting_settings()

    assert result == EXPECTED_NEW_SETTINGS
    assert settings_file.exists()

    assert mock_askinteger.call_count == 4
    assert mock_askstring.call_count == 3
    assert mock_askdirectory.call_count == 4

def test_settings_exist_but_invalid_indexerror(tmp_path, monkeypatch, mock_tkinter):
    """
    Тест: Файл settings.txt существует, но неполный (вызовет IndexError).
    Ожидание: Функция должна запросить новые настройки, перезаписать файл и вернуть новые настройки.
    """
    mock_askyesno, mock_askinteger, mock_askstring, mock_askdirectory = mock_tkinter

    mock_askinteger.side_effect = [
        MOCK_USER_INPUT["fps"], MOCK_USER_INPUT["width"],
        MOCK_USER_INPUT["height"], MOCK_USER_INPUT["usb_index"]
    ]
    mock_askstring.side_effect = [
        MOCK_USER_INPUT["ip1"], MOCK_USER_INPUT["ip2"], MOCK_USER_INPUT["ip3"]
    ]
    mock_askdirectory.side_effect = [
        MOCK_USER_INPUT["usb_folder"], MOCK_USER_INPUT["ip1_folder"],
        MOCK_USER_INPUT["ip2_folder"], MOCK_USER_INPUT["ip3_folder"]
    ]

    settings_file = tmp_path / "settings.txt"
    settings_file.write_text("30\n1280\n", encoding='utf-8')

    monkeypatch.chdir(tmp_path)

    result = getting_settings()

    assert result == EXPECTED_NEW_SETTINGS
    assert settings_file.exists()

    mock_askyesno.assert_not_called()
    assert mock_askinteger.call_count == 4
    assert mock_askstring.call_count == 3
    assert mock_askdirectory.call_count == 4
