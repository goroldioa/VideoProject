import pytest
import cv2
import platform
from multiprocessing import Lock, Queue, Event
from unittest.mock import patch, MagicMock
from Video import connection # Импортируем тестируемую функцию


# Фикстуры для имитации внешних зависимостей
@pytest.fixture
def mock_cv2_videocapture():
    with patch('Video.cv2.VideoCapture') as mock:
        yield mock

@pytest.fixture
def mock_logger():
    with patch('Video.logger') as mock:
        yield mock

@pytest.fixture
def mock_capture_and_save():
    with patch('Video.capture_and_save') as mock:
        yield mock

@pytest.fixture
def lock_fixture():
    return Lock()

@pytest.fixture
def errors_queue_fixture():
    return Queue()

@pytest.fixture
def stop_event_fixture():
    return Event()

# Тесты
def test_connection_success_windows(mock_cv2_videocapture, mock_logger, mock_capture_and_save, lock_fixture, errors_queue_fixture, stop_event_fixture):
    with patch('Video.platform.system', return_value='Windows'):
        mock_cap = MagicMock()
        mock_cap.grab.return_value = True
        mock_cv2_videocapture.return_value = mock_cap

        connection('test_ip', 30, 'test_folder', 1920, 1080, 0, 1, lock=lock_fixture, errors_queue=errors_queue_fixture, stop_event=stop_event_fixture)

        mock_cv2_videocapture.assert_called_once_with('test_ip', cv2.CAP_DSHOW)
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        mock_logger.info.assert_called_once_with("Успешное подключение к камере 1")
        mock_capture_and_save.assert_called_once()
        assert errors_queue_fixture.empty()

def test_connection_success_linux(mock_cv2_videocapture, mock_logger, mock_capture_and_save, lock_fixture, errors_queue_fixture, stop_event_fixture):
    with patch('Video.platform.system', return_value='Linux'): # Или другая ОС, не Windows
        mock_cap = MagicMock()
        mock_cap.grab.return_value = True
        mock_cv2_videocapture.return_value = mock_cap

        connection('test_ip', 30, 'test_folder', 1920, 1080, 0, 1, lock=lock_fixture, errors_queue=errors_queue_fixture, stop_event=stop_event_fixture)

        mock_cv2_videocapture.assert_called_once_with('test_ip')
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        mock_logger.info.assert_called_once_with("Успешное подключение к камере 1")
        mock_capture_and_save.assert_called_once()
        assert errors_queue_fixture.empty()



def test_connection_failure(mock_cv2_videocapture, mock_logger, lock_fixture, errors_queue_fixture, stop_event_fixture):
    mock_cap = MagicMock()
    mock_cap.grab.return_value = False # Имитируем неудачный захват кадра
    mock_cv2_videocapture.return_value = mock_cap

    connection('test_ip', 30, 'test_folder', 1920, 1080, 0, 1, lock=lock_fixture, errors_queue=errors_queue_fixture, stop_event=stop_event_fixture)

    mock_logger.info.assert_not_called() # Проверяем, что сообщение об успехе не выводится
    assert not errors_queue_fixture.empty() # Проверяем, что индекс ошибки добавлен в очередь

def test_connection_exception(mock_cv2_videocapture, mock_logger, lock_fixture, errors_queue_fixture, stop_event_fixture):
    mock_cv2_videocapture.side_effect = Exception("Test exception")

    connection('test_ip', 30, 'test_folder', 1920, 1080, 0, 1, lock=lock_fixture, errors_queue=errors_queue_fixture, stop_event=stop_event_fixture)


    mock_logger.error.assert_called_once() # Проверяем вызов логгера с ошибкой
    assert not errors_queue_fixture.empty() # Проверяем, что индекс ошибки добавлен в очередь
