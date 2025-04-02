import pytest
import numpy as np
from unittest.mock import ANY

import Video

@pytest.fixture(autouse=True)
def reset_running_flag():
    """Сбрасывает флаг running перед/после каждого теста для изоляции."""
    original_running = Video.running
    yield
    Video.running = original_running

def test_show_error_calls_functions_in_loop_once(mocker):
    """
    Проверяет, что все необходимые функции вызываются один раз внутри цикла,
    когда running=True изначально.
    """
    test_index = 1
    expected_window_name = f"Camera {test_index + 1}"
    dummy_error_image = np.zeros((5, 5, 3), dtype=np.uint8)

    mock_create_img = mocker.patch('Video.create_error_image', return_value=dummy_error_image)
    mock_imshow = mocker.patch('Video.cv2.imshow')
    mock_waitkey = mocker.patch('Video.cv2.waitKey')
    mock_position = mocker.patch('Video.position_window')

    call_count = 0
    def waitkey_side_effect(delay):
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            Video.running = False
        return -1

    mock_waitkey.side_effect = waitkey_side_effect

    Video.running = True

    Video.show_error(test_index)

    mock_create_img.assert_called_once()

    mock_imshow.assert_called_once_with(expected_window_name, dummy_error_image)
    call_args, _ = mock_imshow.call_args
    assert call_args[0] == expected_window_name
    np.testing.assert_array_equal(call_args[1], dummy_error_image)

    mock_waitkey.assert_called_once_with(1) # Проверяем вызов с аргументом 1
    mock_position.assert_called_once_with(expected_window_name, test_index)

def test_show_error_does_not_enter_loop_if_running_false(mocker):
    """
    Проверяет, что функции внутри цикла не вызываются, если running изначально False.
    """
    test_index = 0
    dummy_error_image = np.zeros((5, 5, 3), dtype=np.uint8)

    mock_create_img = mocker.patch('Video.create_error_image', return_value=dummy_error_image)
    mock_imshow = mocker.patch('Video.cv2.imshow')
    mock_waitkey = mocker.patch('Video.cv2.waitKey')
    mock_position = mocker.patch('Video.position_window')

    Video.running = False


    Video.show_error(test_index)


    mock_create_img.assert_called_once()

    mock_imshow.assert_not_called()
    mock_waitkey.assert_not_called()
    mock_position.assert_not_called()
