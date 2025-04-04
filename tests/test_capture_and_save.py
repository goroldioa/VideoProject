import os
import time
import threading
import pytest
from unittest.mock import MagicMock, call, ANY

from Video import capture_and_save

class MockVideoCapture:
    def __init__(self, frames_to_produce=5):
        self._read_count = 0
        self._frames_to_produce = frames_to_produce
        self.isOpened_return = True
        self.read_side_effect = self._mock_read
        self.release_mock = MagicMock()

    def _mock_read(self):
        if self._read_count < self._frames_to_produce:
            fake_frame = object()
            self._read_count += 1
            print(f"Mock read called: {self._read_count}/{self._frames_to_produce}")
            return True, fake_frame
        else:
            print("Mock read returning False")
            return True, object()

    def read(self):
        if callable(self.read_side_effect):
            return self.read_side_effect()
        return True, object()

    def release(self):
        self.release_mock()

    def isOpened(self):
        return self.isOpened_return

@pytest.fixture
def mock_cv2(mocker):
    """Мокает все необходимые функции cv2."""
    mock = MagicMock()
    mocker.patch('Video.cv2', mock)
    mock.FONT_HERSHEY_SIMPLEX = 1
    return mock

@pytest.fixture
def mock_os(mocker):
    """Мокает функции os."""
    mock_makedirs = mocker.patch('Video.os.makedirs')
    mock_path_join = mocker.patch('Video.os.path.join', side_effect=os.path.join)
    return {'makedirs': mock_makedirs, 'path_join': mock_path_join}

@pytest.fixture
def mock_time(mocker):
    """Мокает функции time."""
    mock_sleep = mocker.patch('Video.time.sleep')
    mock_perf_counter = mocker.patch('Video.time.perf_counter', side_effect=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6])
    return {'sleep': mock_sleep, 'perf_counter': mock_perf_counter}

@pytest.fixture
def mock_position_window(mocker):
    """Мокает функцию position_window."""
    return mocker.patch('Video.position_window')

def test_capture_and_save_creates_dir_saves_frames_and_cleans_up(
    tmp_path, mock_cv2, mock_os, mock_time, mock_position_window
):
    """
    Тестирует основной сценарий: создание директории, сохранение нескольких кадров,
    вызов функций отображения и очистки.
    """
    num_frames_to_capture = 3
    folder_name = tmp_path / "test_output"
    fps = 30
    index = 0
    start_count = 100
    stop_event = threading.Event()

    mock_cap = MockVideoCapture(frames_to_produce=num_frames_to_capture + 1)

    frame_read_counter = 0
    original_read_side_effect = mock_cap.read_side_effect
    def read_and_stop(*args, **kwargs):
        nonlocal frame_read_counter
        ret, frame = original_read_side_effect()
        if ret:
            frame_read_counter += 1
            if frame_read_counter >= num_frames_to_capture:
                print(f"Setting stop event after {frame_read_counter} reads")
                stop_event.set()
        return ret, frame

    mock_cap.read_side_effect = read_and_stop
    capture_and_save(mock_cap, str(folder_name), fps, index, start_count, stop_event)

    mock_os['makedirs'].assert_called_once_with(str(folder_name), exist_ok=True)

    expected_calls = []
    for i in range(num_frames_to_capture):
        expected_filename = os.path.join(str(folder_name), f"{start_count} frame_{i}.jpg")
        expected_calls.append(call(expected_filename, ANY))

    assert mock_cv2.imwrite.call_count == num_frames_to_capture
    mock_cv2.imwrite.assert_has_calls(expected_calls, any_order=False)

    assert mock_cv2.putText.call_count == num_frames_to_capture
    assert mock_cv2.imshow.call_count == num_frames_to_capture
    assert mock_position_window.call_count == num_frames_to_capture
    assert mock_cv2.waitKey.call_count == num_frames_to_capture
    mock_cv2.imshow.assert_called_with(f"Camera {index + 1}", ANY)
    mock_position_window.assert_called_with(f"Camera {index + 1}", index)

    assert mock_time['sleep'].call_count == num_frames_to_capture
    assert mock_time['perf_counter'].call_count >= num_frames_to_capture * 2

    mock_cap.release_mock.assert_called_once()


def test_capture_and_save_stops_immediately_if_event_set(
    tmp_path, mock_cv2, mock_os, mock_time, mock_position_window
):
    """
    Тестирует случай, когда событие остановки установлено до начала цикла.
    """
    folder_name = tmp_path / "test_output_stop"
    fps = 30
    index = 1
    start_count = 200
    stop_event = threading.Event()
    stop_event.set()

    mock_cap = MockVideoCapture(frames_to_produce=5)

    capture_and_save(mock_cap, str(folder_name), fps, index, start_count, stop_event)

    mock_os['makedirs'].assert_called_once_with(str(folder_name), exist_ok=True)

    assert mock_cap._read_count == 0
    mock_cv2.imwrite.assert_not_called()
    mock_cv2.imshow.assert_not_called()
    mock_position_window.assert_not_called()
    mock_cv2.waitKey.assert_not_called()
    mock_time['sleep'].assert_not_called()

    mock_cap.release_mock.assert_called_once()


def test_capture_and_save_handles_zero_fps(
    tmp_path, mock_cv2, mock_os, mock_time, mock_position_window
):
    """
    Тестирует случай с fps = 0, чтобы убедиться в отсутствии деления на ноль
    и правильной логике time.sleep.
    """
    num_frames_to_capture = 2
    folder_name = tmp_path / "test_output_zero_fps"
    fps = 0
    index = 0
    start_count = 300
    stop_event = threading.Event()

    mock_cap = MockVideoCapture(frames_to_produce=num_frames_to_capture + 1)

    frame_read_counter = 0
    original_read_side_effect = mock_cap.read_side_effect
    def read_and_stop(*args, **kwargs):
        nonlocal frame_read_counter
        ret, frame = original_read_side_effect()
        if ret:
            frame_read_counter += 1
            if frame_read_counter >= num_frames_to_capture:
                stop_event.set()
        return ret, frame
    mock_cap.read_side_effect = read_and_stop

    capture_and_save(mock_cap, str(folder_name), fps, index, start_count, stop_event)

    assert mock_cv2.imwrite.call_count == num_frames_to_capture

    mock_time['sleep'].assert_has_calls([call(0)] * num_frames_to_capture)

    mock_cap.release_mock.assert_called_once()
