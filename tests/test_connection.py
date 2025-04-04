import pytest
import platform
import time
import threading
import queue
from unittest.mock import MagicMock, call, ANY, patch

from Video import connection


class MockVideoCapture:
    def __init__(self, is_opened=True, grab_returns=True, set_raises=None, grab_raises=None):
        self._is_opened = is_opened
        self._grab_returns = grab_returns
        self._set_raises = set_raises
        self._grab_raises = grab_raises
        self.set_mock = MagicMock()
        self.grab_mock = MagicMock(side_effect=self._grab_side_effect)
        self.release_mock = MagicMock()

    def isOpened(self):
        print(f"Вызван мок isOpened, возвращает {self._is_opened}")
        return self._is_opened

    def set(self, prop, value):
        print(f"Вызван мок set с параметрами: {prop}, {value}")
        if self._set_raises:
            print("Мок set вызывает исключение")
            raise self._set_raises
        self.set_mock(prop, value)

    def _grab_side_effect(self):
        print("Вызван мок _grab_side_effect")
        if self._grab_raises:
            print("Мок grab вызывает исключение")
            raise self._grab_raises
        if isinstance(self._grab_returns, list):
            if self._grab_returns:
                return self._grab_returns.pop(0)
            else:
                return False
        print(f"Мок grab возвращает {self._grab_returns}")
        return self._grab_returns

    def grab(self):
        return self.grab_mock()

    def release(self):
        print("Вызван мок release")
        self.release_mock()


@pytest.fixture
def mock_cv2_connection(mocker):
    """Мокает cv2 специально для функции connection."""
    mock_cv2 = MagicMock()
    mock_cap_instance = MockVideoCapture()
    mock_cv2.VideoCapture.return_value = mock_cap_instance
    mock_cv2.CAP_DSHOW = 'mock_cap_dshow'
    mock_cv2.CAP_PROP_BUFFERSIZE = 1
    mock_cv2.CAP_PROP_FRAME_WIDTH = 2
    mock_cv2.CAP_PROP_FRAME_HEIGHT = 3
    mock_cv2.error = Exception
    mocker.patch('Video.cv2', mock_cv2)
    return {'cv2': mock_cv2, 'VideoCapture': mock_cv2.VideoCapture, 'instance': mock_cap_instance}

@pytest.fixture
def mock_platform_system(mocker):
    """Мокает platform.system."""
    return mocker.patch('Video.platform.system')

@pytest.fixture
def mock_time_connection(mocker):
    """Мокает time.time и time.sleep для функции connection."""
    mock_time_func = mocker.patch('Video.time.time')
    mock_sleep_func = mocker.patch('Video.time.sleep')
    return {'time': mock_time_func, 'sleep': mock_sleep_func}

@pytest.fixture
def mock_logger(mocker):
    """Мокает объект logger, предполагаемый в модуле Video."""
    mock = mocker.patch('Video.logger', MagicMock())
    return mock

@pytest.fixture
def mock_errors_queue(mocker):
    """Мокает объект errors_queue, предполагаемый в модуле Video."""
    mock_queue = MagicMock(spec=queue.Queue)
    mocker.patch('Video.errors_queue', mock_queue)
    return mock_queue

@pytest.fixture
def mock_lock(mocker):
    """Мокает объект lock с использованием autospec для поддержки 'with'."""
    mock = mocker.patch('Video.lock', autospec=True)
    return mock

@pytest.fixture
def mock_capture_and_save(mocker):
    """Мокает функцию capture_and_save."""
    return mocker.patch('Video.capture_and_save')

@pytest.fixture
def mock_stop_event(mocker):
    """Мокает объект stop_event (нужен для вызова capture_and_save)."""
    return MagicMock(spec=threading.Event, name="MockStopEvent")

IP = "rtsp://test"
FPS = 30
FOLDER = "/tmp/test_vid"
WIDTH = 640
HEIGHT = 480
INDEX = 0
START_COUNT = 100
TIMEOUT = 5


def test_connection_success_windows(
    mock_cv2_connection, mock_platform_system, mock_time_connection,
    mock_logger, mock_errors_queue, mock_lock, mock_capture_and_save, mock_stop_event
):
    """Тестирует успешное подключение в Windows."""
    mock_platform_system.return_value = 'Windows'
    mock_time_connection['time'].side_effect = [100.0, 100.1]
    mock_cv2_instance = mock_cv2_connection['instance']
    mock_cv2_instance._is_opened = True
    mock_cv2_instance._grab_returns = True

    connection(IP, FPS, FOLDER, WIDTH, HEIGHT, INDEX, START_COUNT, timeout=TIMEOUT)

    mock_platform_system.assert_called_once()
    mock_cv2_connection['VideoCapture'].assert_called_once_with(IP, mock_cv2_connection['cv2'].CAP_DSHOW)
    mock_cv2_instance.set_mock.assert_has_calls([
        call(mock_cv2_connection['cv2'].CAP_PROP_BUFFERSIZE, 1),
        call(mock_cv2_connection['cv2'].CAP_PROP_FRAME_WIDTH, WIDTH),
        call(mock_cv2_connection['cv2'].CAP_PROP_FRAME_HEIGHT, HEIGHT),
    ], any_order=True)
    mock_cv2_instance.grab_mock.assert_called_once()
    mock_time_connection['sleep'].assert_not_called()
    mock_logger.info.assert_called_once_with(f"Успешное подключение к камере {INDEX + 1}")
    mock_capture_and_save.assert_called_once_with(
        mock_cv2_instance, FOLDER, FPS, INDEX, START_COUNT, ANY
    )
    mock_errors_queue.put.assert_not_called()
    mock_cv2_instance.release_mock.assert_not_called()

def test_connection_success_linux(
    mock_cv2_connection, mock_platform_system, mock_time_connection,
    mock_logger, mock_errors_queue, mock_lock, mock_capture_and_save, mock_stop_event
):
    """Тестирует успешное подключение не в Windows (например, Linux)."""
    mock_platform_system.return_value = 'Linux'
    mock_time_connection['time'].side_effect = [200.0, 200.1]
    mock_cv2_instance = mock_cv2_connection['instance']
    mock_cv2_instance._is_opened = True
    mock_cv2_instance._grab_returns = True

    connection(IP, FPS, FOLDER, WIDTH, HEIGHT, INDEX, START_COUNT, timeout=TIMEOUT)

    mock_platform_system.assert_called_once()
    mock_cv2_connection['VideoCapture'].assert_called_once_with(IP)
    mock_cv2_instance.grab_mock.assert_called_once()
    mock_logger.info.assert_called_once_with(f"Успешное подключение к камере {INDEX + 1}")
    mock_capture_and_save.assert_called_once()
    mock_errors_queue.put.assert_not_called()
    mock_cv2_instance.release_mock.assert_not_called()

def test_connection_fail_open(
    mock_cv2_connection, mock_platform_system, mock_time_connection,
    mock_logger, mock_errors_queue, mock_lock, mock_capture_and_save
):
    """Тестирует неудачу, когда VideoCapture не удается открыть."""
    mock_platform_system.return_value = 'Linux'
    mock_cv2_instance = mock_cv2_connection['instance']
    mock_cv2_instance._is_opened = False

    connection(IP, FPS, FOLDER, WIDTH, HEIGHT, INDEX, START_COUNT, timeout=TIMEOUT)

    mock_cv2_connection['VideoCapture'].assert_called_once_with(IP)
    mock_logger.error.assert_called_once()
    log_message = mock_logger.error.call_args[0][0]
    assert f"Исключение при настройке соединения для камеры {INDEX + 1}: " in log_message

    mock_lock.__enter__.assert_called_once()
    mock_errors_queue.put.assert_called_once_with(INDEX)
    mock_lock.__exit__.assert_called_once()

    mock_capture_and_save.assert_not_called()
    mock_cv2_instance.release_mock.assert_called_once()


def test_connection_fail_timeout(
    mock_cv2_connection, mock_platform_system, mock_time_connection,
    mock_logger, mock_errors_queue, mock_lock, mock_capture_and_save
):
    """Тестирует неудачу из-за таймаута grab()."""
    mock_platform_system.return_value = 'Linux'
    start_t = 300.0
    timeout_t = start_t + TIMEOUT
    mock_time_connection['time'].side_effect = [
        start_t,
        start_t + 1,
        start_t + 2,
        timeout_t + 1
    ]
    mock_cv2_instance = mock_cv2_connection['instance']
    mock_cv2_instance._is_opened = True
    mock_cv2_instance._grab_returns = False

    connection(IP, FPS, FOLDER, WIDTH, HEIGHT, INDEX, START_COUNT, timeout=TIMEOUT)

    mock_cv2_connection['VideoCapture'].assert_called_once_with(IP)
    assert mock_cv2_instance.grab_mock.call_count > 1
    assert mock_time_connection['sleep'].call_count > 0

    mock_lock.__enter__.assert_called_once()
    mock_errors_queue.put.assert_called_once_with(INDEX)
    mock_lock.__exit__.assert_called_once()

    mock_logger.error.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_capture_and_save.assert_not_called()

    mock_cv2_instance.release_mock.assert_called_once()

def test_connection_fail_exception_in_setup(
    mock_cv2_connection, mock_platform_system, mock_time_connection,
    mock_logger, mock_errors_queue, mock_lock, mock_capture_and_save
):
    """Тестирует неудачу из-за исключения во время настройки (например, cap.set)."""
    mock_platform_system.return_value = 'Linux'
    mock_cv2_instance = mock_cv2_connection['instance']
    mock_cv2_instance._is_opened = True
    setup_exception = ValueError("Фейковая ошибка cv2 set")
    mock_cv2_instance.set = MagicMock(side_effect=setup_exception)

    connection(IP, FPS, FOLDER, WIDTH, HEIGHT, INDEX, START_COUNT, timeout=TIMEOUT)

    mock_cv2_connection['VideoCapture'].assert_called_once_with(IP)

    mock_cv2_instance.set.assert_called()

    mock_logger.error.assert_called_once()
    log_message = mock_logger.error.call_args[0][0]
    assert str(setup_exception) in log_message
    assert f"Исключение при настройке соединения для камеры {INDEX + 1}: {str(setup_exception)}" in log_message

    mock_lock.__enter__.assert_called_once()
    mock_errors_queue.put.assert_called_once_with(INDEX)
    mock_lock.__exit__.assert_called_once()

    mock_capture_and_save.assert_not_called()
    mock_cv2_instance.grab_mock.assert_not_called()

    mock_cv2_instance.release_mock.assert_called_once()



def test_connection_fail_exception_in_grab(
    mock_cv2_connection, mock_platform_system, mock_time_connection,
    mock_logger, mock_errors_queue, mock_lock, mock_capture_and_save
):
    """Тестирует неудачу из-за исключения во время цикла grab()."""
    mock_platform_system.return_value = 'Linux'
    mock_time_connection['time'].side_effect = [400.0, 400.1]
    mock_cv2_instance = mock_cv2_connection['instance']
    mock_cv2_instance._is_opened = True
    grab_exception = RuntimeError("Фейковая аппаратная ошибка grab")
    mock_cv2_instance._grab_raises = grab_exception

    connection(IP, FPS, FOLDER, WIDTH, HEIGHT, INDEX, START_COUNT, timeout=TIMEOUT)

    mock_cv2_connection['VideoCapture'].assert_called_once_with(IP)
    mock_cv2_instance.grab_mock.assert_called_once()

    mock_logger.error.assert_called_once()
    log_message = mock_logger.error.call_args[0][0]
    assert str(grab_exception) in log_message
    assert f"Исключение при настройке соединения для камеры {INDEX + 1}: {str(grab_exception)}" in log_message

    mock_lock.__enter__.assert_called_once()
    mock_errors_queue.put.assert_called_once_with(INDEX)
    mock_lock.__exit__.assert_called_once()

    mock_capture_and_save.assert_not_called()

    mock_cv2_instance.release_mock.assert_called_once()
