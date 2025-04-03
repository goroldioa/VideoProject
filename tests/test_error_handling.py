import pytest
import queue
import threading
import logging
from unittest.mock import Mock, patch

from Video import error_handling

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture
def errors_queue():
    return queue.Queue()


@pytest.fixture
def stop_event():
    return threading.Event()


@patch('Video.messagebox.askyesno')
@patch('Video.threading.Thread')
@patch('Video.show_error')
def test_error_handling_no_errors(mock_show_error, mock_thread, mock_askyesno, errors_queue, stop_event):
    """Тест: Очередь ошибок пуста."""
    error_handling(errors_queue, stop_event)
    mock_askyesno.assert_not_called()
    mock_thread.assert_not_called()
    mock_show_error.assert_not_called()


@patch('Video.messagebox.askyesno', return_value=True)
@patch('Video.threading.Thread')
@patch('Video.show_error')
def test_error_handling_continue(mock_show_error, mock_thread, mock_askyesno, errors_queue, stop_event):
    """Тест: Одна ошибка, пользователь продолжает."""
    errors_queue.put(0)
    error_handling(errors_queue, stop_event)
    mock_askyesno.assert_called_once_with("Ошибка камеры", "Ошибка: Не удалось открыть камеру 1\nПродолжить выполнение программы?")
    mock_thread.assert_called_once_with(target=mock_show_error, args=(0, stop_event,))
    mock_thread.return_value.start.assert_called_once()
    assert not stop_event.is_set()


@patch('Video.messagebox.askyesno', return_value=False)
@patch('Video.threading.Thread')
@patch('Video.show_error')
def test_error_handling_stop(mock_show_error, mock_thread, mock_askyesno, errors_queue, stop_event):
    """Тест: Одна ошибка, пользователь останавливает."""
    errors_queue.put(1)
    error_handling(errors_queue, stop_event)
    mock_askyesno.assert_called_once_with("Ошибка камеры", "Ошибка: Не удалось открыть камеру 2\nПродолжить выполнение программы?")
    mock_thread.assert_not_called()
    mock_show_error.assert_not_called()
    assert stop_event.is_set()


@patch('Video.messagebox.askyesno', side_effect=Exception("Test Exception"))
@patch('Video.threading.Thread')
@patch('Video.show_error')
def test_error_handling_exception(mock_show_error, mock_thread, mock_askyesno, errors_queue, stop_event, caplog):
    """Тест: Обработка исключения в messagebox.askyesno."""
    errors_queue.put(0)
    error_handling(errors_queue, stop_event)
    assert "Непредвиденная ошибка в error_handling: Test Exception" in caplog.text
    mock_thread.assert_not_called()
    mock_show_error.assert_not_called()
