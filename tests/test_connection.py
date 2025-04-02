import pytest
import cv2
import platform
import time
import queue
import threading
from unittest.mock import MagicMock, call

import Video

@pytest.fixture(autouse=True)
def reset_globals(mocker):
    """Сбрасывает очередь и мокирует лок перед каждым тестом."""
    while not Video.errors_queue.empty():
        try:
            Video.errors_queue.get_nowait()
        except queue.Empty:
            break
    mock_lock_instance = MagicMock()
    mock_lock_instance.__enter__ = MagicMock(return_value=mock_lock_instance)
    mock_lock_instance.__exit__ = MagicMock(return_value=None)
    mocker.patch('Video.lock', new=mock_lock_instance)
    yield mock_lock_instance

@pytest.mark.parametrize("system_platform, use_cap_dshow", [
    ('Windows', True),
    ('Linux', False),
    ('Darwin', False),
])
def test_connection_success(mocker, reset_globals, system_platform, use_cap_dshow):
    """Тест: Успешное подключение и захват кадра."""
    mock_platform = mocker.patch('Video.platform.system', return_value=system_platform)
    mock_time = mocker.patch('Video.time.time')
    mock_sleep = mocker.patch('Video.time.sleep')

    mock_logger_info = mocker.patch('Video.logger.info')
    mock_logger_error = mocker.patch('Video.logger.error')
    mock_capture_save = mocker.patch('Video.capture_and_save')
    mock_errors_put = mocker.patch('Video.errors_queue.put')
    mock_lock = reset_globals

    mock_cap = MagicMock(spec=cv2.VideoCapture)
    mock_cap.isOpened.return_value = True
    mock_cap.grab.return_value = True
    mock_videocapture = mocker.patch('Video.cv2.VideoCapture', return_value=mock_cap)

    start_timestamp = 1000.0
    mock_time.return_value = start_timestamp

    test_ip = 0
    test_fps = 10
    test_folder = "test_folder"
    test_width = 1920
    test_height = 1080
    test_index = 0
    test_start_count = 5
    test_timeout = 5

    expected_log_msg = f"Успешное подключение к камере {test_index + 1}"

    print(f"\nDEBUG: --- Starting test_connection_success ({system_platform}) ---")

    Video.connection(test_ip, test_fps, test_folder, test_width, test_height, test_index, test_start_count, test_timeout)
    print("DEBUG: --- Finished connection call ---")

    mock_platform.assert_called_once()
    if use_cap_dshow:
        mock_videocapture.assert_called_once_with(test_ip, cv2.CAP_DSHOW)
    else:
        mock_videocapture.assert_called_once_with(test_ip)

    mock_cap.isOpened.assert_called_once()

    expected_set_calls = [
        call(cv2.CAP_PROP_BUFFERSIZE, 1),
        call(cv2.CAP_PROP_FRAME_WIDTH, test_width),
        call(cv2.CAP_PROP_FRAME_HEIGHT, test_height),
    ]
    mock_cap.set.assert_has_calls(expected_set_calls, any_order=True)

    assert mock_time.call_count >= 2

    mock_cap.grab.assert_called_once()

    mock_logger_info.assert_called_once_with(expected_log_msg)
    mock_capture_save.assert_called_once_with(mock_cap, test_folder, test_fps, test_index, test_start_count)

    mock_errors_put.assert_not_called()
    mock_cap.release.assert_not_called()
    enter_call = call.__enter__()
    assert enter_call not in mock_lock.mock_calls
    mock_logger_error.assert_not_called()

@pytest.mark.parametrize("system_platform", ['Windows', 'Linux'])
def test_connection_failure_timeout(mocker, reset_globals, system_platform):
    """Тест: Неудачный захват кадра (таймаут)."""
    mocker.patch('platform.system', return_value=system_platform)
    start_timestamp = 1000.0
    timeout_val = 5
    time_sequence = [start_timestamp, start_timestamp + 1, start_timestamp + timeout_val + 1]
    mock_time = mocker.patch('Video.time.time', side_effect=time_sequence)
    mock_sleep = mocker.patch('Video.time.sleep')

    mock_logger_info = mocker.patch('Video.logger.info')
    mock_logger_error = mocker.patch('Video.logger.error')
    mock_capture_save = mocker.patch('Video.capture_and_save')
    mock_errors_put = mocker.patch('Video.errors_queue.put')
    mock_lock = reset_globals

    mock_cap = MagicMock(spec=cv2.VideoCapture)
    mock_cap.isOpened.return_value = True
    mock_cap.grab.return_value = False
    mock_videocapture = mocker.patch('Video.cv2.VideoCapture', return_value=mock_cap)

    test_ip = "rtsp://fail"
    test_index = 1
    test_fps, test_folder, test_width, test_height, test_start_count = 0, "", 0, 0, 0

    print(f"\nDEBUG: --- Starting test_connection_failure_timeout ({system_platform}) ---")

    Video.connection(test_ip, test_fps, test_folder, test_width, test_height, test_index, test_start_count, timeout_val)
    print("DEBUG: --- Finished connection call ---")

    mock_videocapture.assert_called_once()
    mock_cap.isOpened.assert_called_once()
    mock_cap.set.assert_called()

    assert mock_time.call_count >= 3

    mock_cap.grab.assert_called()
    mock_sleep.assert_called()

    mock_lock.__enter__.assert_called_once()
    mock_errors_put.assert_called_once_with(test_index)
    mock_lock.__exit__.assert_called_once()
    mock_cap.release.assert_called_once()

    mock_logger_info.assert_not_called()
    mock_capture_save.assert_not_called()
    mock_logger_error.assert_not_called()


def test_connection_failure_videocapture_open(mocker, reset_globals):
    """Тест: VideoCapture не смог открыть источник."""
    mocker.patch('platform.system', return_value='Windows')
    mock_time = mocker.patch('Video.time.time')
    mock_sleep = mocker.patch('Video.time.sleep')
    mock_logger_info = mocker.patch('Video.logger.info')
    mock_logger_error = mocker.patch('Video.logger.error')
    mock_capture_save = mocker.patch('Video.capture_and_save')
    mock_errors_put = mocker.patch('Video.errors_queue.put')
    mock_lock = reset_globals

    mock_cap = MagicMock(spec=cv2.VideoCapture)
    mock_cap.isOpened.return_value = False
    mock_cap.release = MagicMock()
    mock_videocapture = mocker.patch('Video.cv2.VideoCapture', return_value=mock_cap)

    test_ip = "bad_ip"
    test_index = 99
    test_timeout = 3
    test_fps, test_folder, test_width, test_height, test_start_count = 0, "", 0, 0, 0

    print("\nDEBUG: --- Starting test_connection_failure_videocapture_open ---")

    Video.connection(test_ip, test_fps, test_folder, test_width, test_height, test_index, test_start_count, test_timeout)
    print("DEBUG: --- Finished connection call ---")

    mock_videocapture.assert_called_once()
    mock_cap.isOpened.assert_called_once()
    mock_cap.set.assert_not_called()
    mock_cap.grab.assert_not_called()

    mock_logger_error.assert_called_once()
    mock_lock.__enter__.assert_called_once()
    mock_errors_put.assert_called_once_with(test_index)
    mock_lock.__exit__.assert_called_once()

    mock_cap.release.assert_called_once()


    mock_logger_info.assert_not_called()
    mock_capture_save.assert_not_called()
