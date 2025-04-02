import pytest
import cv2

from Video import position_window, WINDOW_WIDTH, WINDOW_HEIGHT

@pytest.mark.parametrize(
    "index, expected_x_offset, expected_y_offset",
    [
        (0, 0, 0),
        (1, 1, 0),
        (2, 0, 1),
        (3, 1, 1),
        (4, 0, 2),
        (5, 1, 2),
        pytest.param(10, 0, 5, id="large_index_10"),
    ]
)
def test_position_window_calculates_correctly_and_calls_moveWindow(
    mocker, index, expected_x_offset, expected_y_offset
):
    """
    Проверяет, что position_window правильно вычисляет координаты
    и вызывает cv2.moveWindow с этими координатами.
    """
    test_window_name = f"Test Window {index}"
    expected_x = expected_x_offset * WINDOW_WIDTH
    expected_y = expected_y_offset * WINDOW_HEIGHT

    mock_moveWindow = mocker.patch('Video.cv2.moveWindow')
    print(f"\nDEBUG: Testing index={index}, name='{test_window_name}', expecting ({expected_x}, {expected_y})")

    position_window(test_window_name, index)

    mock_moveWindow.assert_called_once()
    mock_moveWindow.assert_called_once_with(test_window_name, expected_x, expected_y)

def test_position_window_handles_different_names(mocker):
    """Проверяет, что имя окна правильно передается в moveWindow."""
    specific_window_name = "MySpecialCameraFeed"
    test_index = 1
    expected_x = (test_index % 2) * WINDOW_WIDTH
    expected_y = (test_index // 2) * WINDOW_HEIGHT

    mock_moveWindow = mocker.patch('Video.cv2.moveWindow')
    print(f"\nDEBUG: Testing specific name='{specific_window_name}', index={test_index}")

    position_window(specific_window_name, test_index)

    mock_moveWindow.assert_called_once_with(specific_window_name, expected_x, expected_y)
