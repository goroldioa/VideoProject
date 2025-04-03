import pytest
import threading
import time
import keyboard
from unittest.mock import patch, MagicMock
from Video import main, getting_settings, connection, error_handling, start_counter


@pytest.fixture
def mock_settings():
    with patch('Video.getting_settings') as mock_get:
        mock_get.return_value = (30, 640, 480, 0, "usb_folder", ["rtsp://127.0.0.1:8554/test"], ["ip_folder"])
        yield mock_get


@pytest.fixture
def mock_connection():
    with patch('Video.connection') as mock_conn:
        yield mock_conn

@pytest.fixture
def mock_sleep():
    with patch('Video.time.sleep') as mock_time_sleep:
        yield mock_time_sleep

@pytest.fixture
def mock_error_handling():
    with patch('Video.error_handling') as mock_err:
        yield mock_err

@pytest.fixture
def mock_start_counter():
    with patch('Video.start_counter') as mock_start:
        mock_start.return_value = 0
        yield mock_start

@pytest.fixture
def mock_threads():
    threads = []
    yield threads
    for thread in threads:
        thread.join()

@pytest.fixture
def mock_stop_event():
    stop_event = threading.Event()
    yield stop_event

@pytest.fixture
def mock_errors_queue():
    errors_queue = MagicMock()
    yield errors_queue

@pytest.fixture
def mock_keyboard():
    with patch('Video.keyboard') as mock_key:
        yield mock_key




def test_main_ip_camera(mock_settings, mock_connection, mock_error_handling, mock_start_counter, mock_threads, mock_stop_event, mock_errors_queue, mock_keyboard, mock_sleep):
    mock_keyboard.is_pressed.return_value = True
    main()

    mock_connection.assert_called_with(0, 30, 'usb_folder', 640, 480, 3, 0)
    mock_error_handling.assert_called()


def test_main_usb_camera(mock_settings, mock_connection, mock_error_handling, mock_start_counter, mock_threads, mock_stop_event, mock_errors_queue, mock_keyboard, mock_sleep):
    mock_settings.return_value = (30, 640, 480, 0, "usb_folder", [], [])
    mock_keyboard.is_pressed.return_value = True
    main()
    mock_connection.assert_called_with(0, 30, "usb_folder", 640, 480, 3, 0)




def test_main_keyboard_interrupt(mock_settings, mock_connection, mock_error_handling, mock_start_counter, mock_threads, mock_stop_event, mock_errors_queue, mock_keyboard, mock_sleep):

    mock_keyboard.is_pressed.side_effect = [False, True]
    main()
    assert not mock_stop_event.is_set()



