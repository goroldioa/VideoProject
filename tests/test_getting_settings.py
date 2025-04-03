import pytest
import configparser
import os
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox

from Video import getting_settings

@pytest.fixture
def temp_config_file(tmp_path):
    config_file = tmp_path / "settings.ini"
    return str(config_file)


@pytest.fixture
def mock_tk_root():
    root = tk.Tk()
    root.withdraw()
    return root

def test_no_config_file(monkeypatch, temp_config_file, mock_tk_root):
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)

    inputs = ["30", "640", "480", "0", "/tmp/usb", "rtsp://user:pass@1.1.1.1/", "/tmp/ip1", "rtsp://user:pass@2.2.2.2/", "/tmp/ip2", "rtsp://user:pass@3.3.3.3/", "/tmp/ip3"]
    monkeypatch.setattr('builtins.input', lambda _: inputs.pop(0))
    monkeypatch.setattr('tkinter.simpledialog.askinteger', lambda *args, **kwargs: int(inputs.pop(0)))
    monkeypatch.setattr('tkinter.simpledialog.askstring', lambda *args, **kwargs: inputs.pop(0))
    monkeypatch.setattr('tkinter.filedialog.askdirectory', lambda *args, **kwargs: inputs.pop(0))


    fps, width, height, usb_index, usb_folder, ip_addresses, ip_folders = getting_settings()

    assert fps == 30
    assert width == 640
    assert height == 480
    assert usb_index == 0
    assert usb_folder == "/tmp/usb"
    assert ip_addresses == ["rtsp://user:pass@1.1.1.1/", "rtsp://user:pass@2.2.2.2/", "rtsp://user:pass@3.3.3.3/"]
    assert ip_folders == ["/tmp/ip1", "/tmp/ip2", "/tmp/ip3"]

def test_config_file_exists_change(monkeypatch, temp_config_file, mock_tk_root):
    config = configparser.ConfigParser()
    config['General'] = {'fps': '25', 'width': '1280', 'height': '720'}
    config['USB'] = {'index': '1', 'folder': '/tmp/old_usb'}
    config['IPCamera1'] = {'address': 'rtsp://old', 'folder': '/tmp/old_ip1'}
    config['IPCamera2'] = {'address': 'rtsp://old2', 'folder': '/tmp/old_ip2'}
    config['IPCamera3'] = {'address': 'rtsp://old3', 'folder': '/tmp/old_ip3'}
    with open(temp_config_file, 'w') as f:
        config.write(f)


    inputs = ["30", "640", "480", "0", "/tmp/usb", "rtsp://user:pass@1.1.1.1/", "/tmp/ip1", "rtsp://user:pass@2.2.2.2/", "/tmp/ip2", "rtsp://user:pass@3.3.3.3/", "/tmp/ip3", "yes"] # Добавили 'yes'
    monkeypatch.setattr('builtins.input', lambda _: inputs.pop(0) if inputs else None)
    monkeypatch.setattr('tkinter.simpledialog.askinteger', lambda *args, **kwargs: int(inputs.pop(0)) if inputs else None)
    monkeypatch.setattr('tkinter.simpledialog.askstring', lambda *args, **kwargs: inputs.pop(0) if inputs else None)
    monkeypatch.setattr('tkinter.filedialog.askdirectory', lambda *args, **kwargs: inputs.pop(0) if inputs else None)
    monkeypatch.setattr('tkinter.messagebox.askyesno', lambda *args, **kwargs: True if inputs.pop() == "yes" else False)


    fps, width, height, usb_index, usb_folder, ip_addresses, ip_folders = getting_settings()

    assert fps == 30
    assert width == 640
    assert height == 480
    assert usb_index == 0
    assert usb_folder == "/tmp/usb"
    assert ip_addresses == ["rtsp://user:pass@1.1.1.1/", "rtsp://user:pass@2.2.2.2/", "rtsp://user:pass@3.3.3.3/"]
    assert ip_folders == ["/tmp/ip1", "/tmp/ip2", "/tmp/ip3"]


def test_config_file_exists_no_change(monkeypatch, temp_config_file, mock_tk_root):
    config = configparser.ConfigParser()
    config['General'] = {'fps': '25', 'width': '1280', 'height': '720'}
    config['USB'] = {'index': '1', 'folder': '/tmp/old_usb'}
    config['IPCamera1'] = {'address': 'rtsp://old', 'folder': '/tmp/old_ip1'}
    config['IPCamera2'] = {'address': 'rtsp://old2', 'folder': '/tmp/old_ip2'}
    config['IPCamera3'] = {'address': 'rtsp://old3', 'folder': '/tmp/old_ip3'}
    with open(temp_config_file, 'w') as f:
        config.write(f)

    inputs = ["30", "640", "480", "0", "/tmp/usb", "rtsp://user:pass@1.1.1.1/", "/tmp/ip1", "rtsp://user:pass@2.2.2.2/",
              "/tmp/ip2", "rtsp://user:pass@3.3.3.3/", "/tmp/ip3", "no"]

    monkeypatch.setattr('builtins.input', lambda _: inputs.pop(0) if inputs else None)
    monkeypatch.setattr('tkinter.simpledialog.askinteger',
                        lambda *args, **kwargs: int(inputs.pop(0)) if inputs else None)
    monkeypatch.setattr('tkinter.simpledialog.askstring', lambda *args, **kwargs: inputs.pop(0) if inputs else None)
    monkeypatch.setattr('tkinter.filedialog.askdirectory', lambda *args, **kwargs: inputs.pop(0) if inputs else None)
    monkeypatch.setattr('tkinter.messagebox.askyesno', lambda *args, **kwargs: True if inputs.pop() == "yes" else False)

    fps, width, height, usb_index, usb_folder, ip_addresses, ip_folders = getting_settings()

    assert fps == 30
    assert width == 640
    assert height == 480
    assert usb_index == 0
    assert usb_folder == "/tmp/usb"
    assert ip_addresses == ["rtsp://user:pass@1.1.1.1/", "rtsp://user:pass@2.2.2.2/", "rtsp://user:pass@3.3.3.3/"]
    assert ip_folders == ["/tmp/ip1", "/tmp/ip2", "/tmp/ip3"]
