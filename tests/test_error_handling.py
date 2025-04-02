import pytest
import queue
import threading
from unittest.mock import MagicMock, call

import Video

@pytest.fixture(autouse=True)
def setup_global_state():
    """Сбрасывает глобальное состояние перед каждым тестом."""
    Video.running = True
    Video.threads = []
    yield
    Video.threads = []
    Video.running = True

def test_error_handling_empty_queue_new(mocker):
    """
    Тест: Очередь ошибок пуста.
    Ожидание: Ничего не происходит.
    """
    errors_queue = queue.Queue()
    mock_msgbox = mocker.patch('Video.messagebox.askyesno')
    mock_logger = mocker.patch('Video.logger.error')
    mock_thread_class = mocker.patch('Video.threading.Thread')

    print("\nDEBUG: --- Starting test_error_handling_empty_queue_new ---")
    Video.error_handling(errors_queue)
    print("DEBUG: --- Finished error_handling call ---")

    assert errors_queue.empty()
    mock_msgbox.assert_not_called()
    mock_logger.assert_not_called()
    mock_thread_class.assert_not_called()
    assert Video.running is True
    assert len(Video.threads) == 0


def test_error_handling_user_stops_no_thread_new(mocker):
    """
    Тест: Ошибка есть, пользователь нажимает "Нет".
    Ожидание: running=False, ошибка логируется, ПОТОК НЕ СОЗДАЕТСЯ.
    """
    test_index = 0
    errors_queue = queue.Queue()
    errors_queue.put(test_index)

    mock_msgbox = mocker.patch('Video.messagebox.askyesno', return_value=False)
    mock_logger = mocker.patch('Video.logger.error')
    mock_thread_class = mocker.patch('Video.threading.Thread')

    expected_msgbox_title = "Ошибка камеры"
    expected_msgbox_text = f"Ошибка: Не удалось открыть камеру {test_index + 1}\nПродолжить выполнение программы?"
    expected_log_message = f"Ошибка: Не удалось открыть камеру {test_index + 1}"

    print("\nDEBUG: --- Starting test_error_handling_user_stops_no_thread_new ---")
    initial_threads_len = len(Video.threads)
    Video.running = True

    Video.error_handling(errors_queue)
    print("DEBUG: --- Finished error_handling call ---")

    assert errors_queue.empty()
    mock_msgbox.assert_called_once_with(expected_msgbox_title, expected_msgbox_text)
    mock_logger.assert_called_once_with(expected_log_message)
    assert Video.running is False
    mock_thread_class.assert_not_called()
    assert len(Video.threads) == initial_threads_len

def test_error_handling_user_continues_starts_thread_new(mocker):
    """
    Тест: Ошибка есть, пользователь нажимает "Да".
    Ожидание: running=True, ошибка логируется, ПОТОК СОЗДАЕТСЯ И ЗАПУСКАЕТСЯ.
    """
    test_index = 2
    errors_queue = queue.Queue()
    errors_queue.put(test_index)

    mock_msgbox = mocker.patch('Video.messagebox.askyesno', return_value=True)
    mock_logger = mocker.patch('Video.logger.error')

    mock_thread_instance = MagicMock(spec=threading.Thread)
    mock_thread_class = mocker.patch('Video.threading.Thread', return_value=mock_thread_instance)

    expected_msgbox_title = "Ошибка камеры"
    expected_msgbox_text = f"Ошибка: Не удалось открыть камеру {test_index + 1}\nПродолжить выполнение программы?"
    expected_log_message = f"Ошибка: Не удалось открыть камеру {test_index + 1}"

    print("\nDEBUG: --- Starting test_error_handling_user_continues_starts_thread_new ---")
    initial_threads_len = len(Video.threads)

    Video.error_handling(errors_queue)
    print("DEBUG: --- Finished error_handling call ---")

    assert errors_queue.empty()
    mock_msgbox.assert_called_once_with(expected_msgbox_title, expected_msgbox_text)
    mock_logger.assert_called_once_with(expected_log_message)
    assert Video.running is True
    mock_thread_class.assert_called_once_with(target=Video.show_error, args=(test_index,))
    assert len(Video.threads) == initial_threads_len + 1
    assert Video.threads[0] is mock_thread_instance
    mock_thread_instance.start.assert_called_once()
