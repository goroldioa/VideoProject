import os
import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, call, ANY, PropertyMock
from Video import capture_and_save as func_to_test
import Video
@pytest.fixture
def reset_running_flag():
    """Сбрасывает флаг running перед/после каждого теста для изоляции."""
    original_running = Video.running
    yield
    Video.running = original_running

@pytest.fixture
def mock_dependencies(mocker):
    """Фикстура для моканья всех внешних зависимостей."""
    mocks = {
        'makedirs': mocker.patch('Video.os.makedirs'),
        'imwrite': mocker.patch('Video.cv2.imwrite'),
        'imshow': mocker.patch('Video.cv2.imshow'),
        'putText': mocker.patch('Video.cv2.putText'),
        'waitKey': mocker.patch('Video.cv2.waitKey', return_value=-1),
        'destroyWindow': mocker.patch('Video.cv2.destroyWindow'),
        'perf_counter': mocker.patch('Video.time.perf_counter'),
        'sleep': mocker.patch('Video.time.sleep'),
        'position_window': mocker.patch('Video.position_window'),
    }
    return mocks

@pytest.fixture
def mock_cap(mocker):
    """Фикстура для создания мок-объекта видеозахвата."""
    cap = MagicMock()
    cap.release = MagicMock()

    fake_frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    fake_frame2 = np.ones((100, 100, 3), dtype=np.uint8)

    cap.read.side_effect = [
        (True, fake_frame1),
        (True, fake_frame2),
        (False, None)
    ]
    return cap, fake_frame1, fake_frame2

def test_capture_and_save_creates_directory(mock_dependencies, mock_cap, tmp_path):
    """Тест: Проверяет, что директория создается."""
    mock_capture, _, _ = mock_cap
    test_folder = tmp_path / "frames"
    folder_name = str(test_folder)
    start_count = 0

    mock_dependencies['perf_counter'].side_effect = [10.0, 10.1, 10.2, 10.3]
    call_count = 0
    def waitkey_side_effect(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            Video.running = False
        return -1

    mock_dependencies['waitKey'].side_effect = waitkey_side_effect

    Video.running = True

    func_to_test(mock_capture, folder_name, 30, 0, start_count)

    mock_dependencies['makedirs'].assert_called_once_with(folder_name, exist_ok=True)

def test_capture_and_save_saves_frames_correctly(mock_dependencies, mock_cap, tmp_path):
    """Тест: Проверяет правильность сохранения кадров."""
    mock_capture, frame1, frame2 = mock_cap
    test_folder = tmp_path / "saved_frames"
    folder_name = str(test_folder)
    fps = 10
    index = 1
    start_count = 100

    mock_dependencies['perf_counter'].side_effect = [t / 10.0 for t in range(100, 105)]

    call_count = 0

    def waitkey_side_effect(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            Video.running = False
        return -1

    mock_dependencies['waitKey'].side_effect = waitkey_side_effect

    Video.running = True

    func_to_test(mock_capture, folder_name, fps, index, start_count)

    expected_filename1 = os.path.join(folder_name, f"{start_count}_frame_0.jpg")
    expected_filename2 = os.path.join(folder_name, f"{start_count}_frame_1.jpg")

    expected_calls = [
        call(expected_filename1, frame1),
        call(expected_filename2, frame2)
    ]
    assert mock_dependencies['imwrite'].call_count == 1

def test_capture_and_save_displays_frames_and_info(mock_dependencies, mock_cap, tmp_path):
    """Тест: Проверяет вызовы функций отображения."""
    mock_capture, frame1, frame2 = mock_cap
    test_folder = tmp_path / "display_test"
    folder_name = str(test_folder)
    fps = 20
    index = 0
    start_count = 0

    mock_dependencies['perf_counter'].side_effect = [5.0, 5.05, 5.10, 5.15]

    call_count = 0

    def waitkey_side_effect(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            Video.running = False
        return -1

    mock_dependencies['waitKey'].side_effect = waitkey_side_effect

    Video.running = True

    func_to_test(mock_capture, folder_name, fps, index, start_count)

    assert mock_dependencies['imshow'].call_count == 1
    assert mock_dependencies['putText'].call_count == 1
    assert mock_dependencies['waitKey'].call_count == 1
    assert mock_dependencies['position_window'].call_count == 1

    expected_win_name = f"Camera {index + 1}"
    mock_dependencies['imshow'].assert_any_call(expected_win_name, frame1)
    mock_dependencies['imshow'].assert_any_call(expected_win_name, ANY)

    mock_dependencies['putText'].assert_any_call(
        frame1,
        ANY,
        (50, 50),
        ANY,
        1,
        (0, 0, 255),
        2
    )

def test_capture_and_save_cleans_up_correctly(mock_dependencies, mock_cap, tmp_path):
    """Тест: Проверяет вызов cap.release() и destroyWindow()."""
    mock_capture, _, _ = mock_cap
    test_folder = tmp_path / "cleanup_test"
    folder_name = str(test_folder)
    index = 2

    mock_dependencies['perf_counter'].side_effect = [1.0, 1.1, 1.2, 1.3]

    call_count = 0

    def waitkey_side_effect(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            Video.running = False
        return -1

    mock_dependencies['waitKey'].side_effect = waitkey_side_effect

    Video.running = True

    func_to_test(mock_capture, folder_name, 30, index, 0)

    mock_capture.release.assert_called_once()

    if mock_dependencies['imshow'].call_count > 0:
         mock_dependencies['destroyWindow'].assert_called_once_with(f"Camera {index + 1}")
    else:
         mock_dependencies['destroyWindow'].assert_not_called()

def test_capture_and_save_handles_zero_fps(mock_dependencies, mock_cap, tmp_path):
    """Тест: Проверяет поведение при fps=0 (без задержки)."""
    mock_capture, _, _ = mock_cap
    test_folder = tmp_path / "zerofps_test"
    folder_name = str(test_folder)
    fps = 0
    index = 0
    start_count = 10

    mock_dependencies['perf_counter'].side_effect = [100.0, 100.1, 100.2, 100.3]
    call_count = 0

    def waitkey_side_effect(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            Video.running = False
        return -1

    mock_dependencies['waitKey'].side_effect = waitkey_side_effect

    Video.running = True

    func_to_test(mock_capture, folder_name, fps, index, start_count)

    assert mock_dependencies['sleep'].call_count == 1
    mock_dependencies['sleep'].assert_has_calls([call(0)])

    mock_dependencies['makedirs'].assert_called_once()
    assert mock_dependencies['imwrite'].call_count == 1
    mock_capture.release.assert_called_once()
    if mock_dependencies['imshow'].call_count > 0:
        mock_dependencies['destroyWindow'].assert_called_once()
