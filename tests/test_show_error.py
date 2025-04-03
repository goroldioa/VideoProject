import pytest
import threading
from unittest.mock import MagicMock, call, ANY

from Video import show_error


@pytest.fixture
def mock_cv2(mocker):
    """Мокает все необходимые функции cv2."""
    mock = MagicMock()
    mocker.patch('Video.cv2', mock)
    return mock

@pytest.fixture
def mock_position_window(mocker):
    """Мокает функцию position_window."""
    return mocker.patch('Video.position_window')

@pytest.fixture
def mock_create_error_image(mocker):
    """Мокает функцию create_error_image."""
    mock_image = MagicMock(name="MockErrorImage")
    mock_func = mocker.patch('Video.create_error_image', return_value=mock_image)
    mock_func.mock_image = mock_image
    return mock_func


def test_show_error_displays_image_in_loop_and_stops(
    mock_cv2, mock_position_window, mock_create_error_image
):
    """
    Тестирует, что функция вызывает create_error_image один раз,
    затем входит в цикл отображения, позиционирования и ожидания,
    и останавливается, когда установлен stop_event.
    """
    index = 0
    stop_event = threading.Event()
    num_loops_before_stop = 3

    call_count = 0
    def waitKey_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        print(f"waitKey mock called {call_count} times")
        if call_count >= num_loops_before_stop:
            print("Setting stop_event")
            stop_event.set()
        return 1

    mock_cv2.waitKey.side_effect = waitKey_side_effect

    show_error(index, stop_event)

    mock_create_error_image.assert_called_once_with()
    mock_error_image = mock_create_error_image.mock_image

    assert mock_cv2.imshow.call_count == num_loops_before_stop
    assert mock_cv2.waitKey.call_count == num_loops_before_stop
    assert mock_position_window.call_count == num_loops_before_stop

    expected_window_name = f"Camera {index + 1}"
    expected_imshow_calls = [call(expected_window_name, mock_error_image)] * num_loops_before_stop
    expected_waitKey_calls = [call(1)] * num_loops_before_stop
    expected_position_calls = [call(expected_window_name, index)] * num_loops_before_stop

    mock_cv2.imshow.assert_has_calls(expected_imshow_calls)
    mock_cv2.waitKey.assert_has_calls(expected_waitKey_calls)
    mock_position_window.assert_has_calls(expected_position_calls)


def test_show_error_stops_immediately_if_event_set(
    mock_cv2, mock_position_window, mock_create_error_image
):
    """
    Тестирует, что если stop_event установлен ДО вызова функции,
    цикл отображения не выполняется.
    """
    index = 1
    stop_event = threading.Event()
    stop_event.set()

    show_error(index, stop_event)

    mock_create_error_image.assert_called_once_with()

    mock_cv2.imshow.assert_not_called()
    mock_cv2.waitKey.assert_not_called()
    mock_position_window.assert_not_called()
