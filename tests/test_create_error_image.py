import pytest
import numpy as np
import cv2
from unittest.mock import ANY
from Video import create_error_image

EXPECTED_HEIGHT = 200
EXPECTED_WIDTH = 400
EXPECTED_CHANNELS = 3
EXPECTED_DTYPE = np.uint8
EXPECTED_SHAPE = (EXPECTED_HEIGHT, EXPECTED_WIDTH, EXPECTED_CHANNELS)
BLACK_COLOR_BGR = [0, 0, 0]
RED_COLOR_BGR = [0, 0, 255]

def test_return_type():
    """Проверяет, что функция возвращает numpy массив."""
    result = create_error_image()
    assert isinstance(result, np.ndarray)

def test_image_dimensions():
    """Проверяет правильность размеров (shape) изображения."""
    result = create_error_image()
    assert result.shape == EXPECTED_SHAPE

def test_image_dtype():
    """Проверяет тип данных пикселей (должен быть uint8)."""
    result = create_error_image()
    assert result.dtype == EXPECTED_DTYPE

def test_background_is_black():
    """Проверяет, что фон (угловые пиксели) черный."""
    result = create_error_image()
    assert np.array_equal(result[0, 0], BLACK_COLOR_BGR)
    assert np.array_equal(result[0, EXPECTED_WIDTH - 1], BLACK_COLOR_BGR)
    assert np.array_equal(result[EXPECTED_HEIGHT - 1, 0], BLACK_COLOR_BGR)
    assert np.array_equal(result[EXPECTED_HEIGHT - 1, EXPECTED_WIDTH - 1], BLACK_COLOR_BGR)

def test_text_presence_and_color():
    """Проверяет, что на изображении присутствуют красные пиксели текста."""
    result = create_error_image()

    assert np.any(result != BLACK_COLOR_BGR)

    non_black_mask = np.any(result != BLACK_COLOR_BGR, axis=2)

    assert np.any(non_black_mask)

    non_black_pixels = result[non_black_mask]

    found_pure_red = np.any(np.all(non_black_pixels == RED_COLOR_BGR, axis=1))
    assert found_pure_red, "На изображении не найдены пиксели чистого красного цвета [0, 0, 255]"

    assert np.max(result[:, :, 2]) == 255
    red_max_mask = result[:, :, 2] == 255
    assert np.all(result[red_max_mask, 0] == 0)
    assert np.all(result[red_max_mask, 1] == 0)

def test_create_error_image_calls_putText_once(mocker):
    """Проверяет, что cv2.putText вызывался ровно один раз"""
    mock_putText = mocker.patch('Video.cv2.putText')
    create_error_image()
    mock_putText.assert_called_once()




