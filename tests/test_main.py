import pytest
import threading
import time
from unittest.mock import patch, MagicMock, call, ANY


import Video


@pytest.fixture(autouse=True)
def reset_globals():
    Video.threads = []
    Video.running = True


    try:
        import queue
        Video.errors_queue = queue.Queue()
    except AttributeError:
         Video.errors_queue = MagicMock()


@patch('Video.logger')
@patch('Video.keyboard')
@patch('Video.error_handling')
@patch('Video.connection')
@patch('Video.getting_settings')
@patch('Video.start_counter')
@patch('threading.Thread')
@patch('time.sleep')
def test_main_happy_path(
    mock_sleep, mock_thread_class, mock_start_counter, mock_getting_settings,
    mock_connection, mock_error_handling, mock_keyboard, mock_logger
):
    """
    Тест нормального выполнения: запускаются IP и USB потоки,
    цикл выполняется несколько раз, затем имитируется Ctrl+C.
    """

    mock_start_counter.return_value = 100
    mock_getting_settings.return_value = (
        30, 1920, 1080, 0, '/usb/folder',
        ['rtsp://ip1', 'rtsp://ip2'],
        ['/ip1/folder', '/ip2/folder']
    )

    mock_ip_thread1_instance = MagicMock()
    mock_ip_thread2_instance = MagicMock()
    mock_usb_thread_instance = MagicMock()

    mock_thread_class.side_effect = [mock_ip_thread1_instance, mock_ip_thread2_instance, mock_usb_thread_instance]


    mock_keyboard.is_pressed.side_effect = [
        False, False,
        False, False,
        True, True
    ]

    Video.main()

    mock_start_counter.assert_called_once()
    mock_getting_settings.assert_called_once()

    expected_ip_calls = [
        call(target=mock_connection, args=('rtsp://ip1', 30, '/ip1/folder', 1920, 1080, 0, 100)),
        call(target=mock_connection, args=('rtsp://ip2', 30, '/ip2/folder', 1920, 1080, 1, 100)),
    ]

    expected_usb_call = call(target=mock_connection, args=(0, 30, '/usb/folder', 1920, 1080, 3, 100))

    assert mock_thread_class.call_count == 3
    mock_thread_class.assert_has_calls(expected_ip_calls + [expected_usb_call], any_order=False)

    mock_ip_thread1_instance.start.assert_called_once()
    mock_ip_thread2_instance.start.assert_called_once()

    mock_sleep.assert_any_call(10)
    mock_usb_thread_instance.start.assert_called_once()

    assert mock_error_handling.call_count == 5
    mock_error_handling.assert_called_with(Video.errors_queue)
    assert mock_sleep.call_count >= 3
    mock_sleep.assert_any_call(0.1)

    mock_logger.info.assert_any_call('Программа завершена нажатием клавиш.')

    mock_ip_thread1_instance.join.assert_called_once()
    mock_ip_thread2_instance.join.assert_called_once()
    mock_usb_thread_instance.join.assert_called_once()

    assert Video.running is False


@patch('Video.logger')
@patch('Video.keyboard')
@patch('Video.error_handling')
@patch('Video.connection')
@patch('Video.getting_settings')
@patch('Video.start_counter')
@patch('threading.Thread')
@patch('time.sleep')
def test_main_ip_thread_creation_exception(
    mock_sleep, mock_thread_class, mock_start_counter, mock_getting_settings,
    mock_connection, mock_error_handling, mock_keyboard, mock_logger
):
    """
    Тест: Ошибка при создании одного из IP потоков.
    Остальные потоки должны создаться и запуститься.
    """

    mock_start_counter.return_value = 100
    mock_getting_settings.return_value = (30, 1920, 1080, 0, '/usb/folder', ['ip1', 'ip2'], ['f1', 'f2'])

    mock_ip_thread1_instance = MagicMock()
    mock_usb_thread_instance = MagicMock()
    test_exception = Exception("IP Thread Error")
    mock_thread_class.side_effect = [mock_ip_thread1_instance, test_exception, mock_usb_thread_instance]

    mock_keyboard.is_pressed.side_effect = [True, True]

    Video.main()

    mock_start_counter.assert_called_once()
    mock_getting_settings.assert_called_once()

    assert mock_thread_class.call_count == 3
    mock_thread_class.assert_any_call(target=mock_connection, args=('ip1', 30, 'f1', 1920, 1080, 0, 100))
    mock_thread_class.assert_any_call(target=mock_connection, args=('ip2', 30, 'f2', 1920, 1080, 1, 100))
    mock_thread_class.assert_any_call(target=mock_connection, args=(0, 30, '/usb/folder', 1920, 1080, 3, 100))

    mock_ip_thread1_instance.start.assert_called_once()
    mock_usb_thread_instance.start.assert_called_once()

    mock_logger.error.assert_called_with(str(test_exception))



    mock_logger.info.assert_any_call('Программа завершена нажатием клавиш.')

    mock_ip_thread1_instance.join.assert_called_once()
    mock_usb_thread_instance.join.assert_called_once()


@patch('Video.logger')
@patch('Video.keyboard')
@patch('Video.error_handling')
@patch('Video.connection')
@patch('Video.getting_settings')
@patch('Video.start_counter')
@patch('threading.Thread')
@patch('time.sleep')
def test_main_usb_thread_creation_exception(
    mock_sleep, mock_thread_class, mock_start_counter, mock_getting_settings,
    mock_connection, mock_error_handling, mock_keyboard, mock_logger
):
    """
    Тест: Ошибка при создании USB потока.
    IP потоки должны создаться и запуститься.
    """

    mock_start_counter.return_value = 100
    mock_getting_settings.return_value = (30, 1920, 1080, 0, '/usb/folder', ['ip1'], ['f1'])

    mock_ip_thread1_instance = MagicMock()
    test_exception = Exception("USB Thread Error")

    mock_thread_class.side_effect = [mock_ip_thread1_instance, test_exception]

    mock_keyboard.is_pressed.side_effect = [True, True]

    Video.main()

    assert mock_thread_class.call_count == 2
    mock_thread_class.assert_any_call(target=mock_connection, args=('ip1', 30, 'f1', 1920, 1080, 0, 100))
    mock_thread_class.assert_any_call(target=mock_connection, args=(0, 30, '/usb/folder', 1920, 1080, 3, 100))

    mock_ip_thread1_instance.start.assert_called_once()
    mock_sleep.assert_called_with(0.1)

    mock_logger.error.assert_called_with(str(test_exception))

    mock_logger.info.assert_any_call('Программа завершена нажатием клавиш.')
    mock_ip_thread1_instance.join.assert_called_once()

@patch('Video.logger')
@patch('Video.keyboard')
@patch('Video.error_handling')
@patch('Video.connection')
@patch('Video.getting_settings')
@patch('Video.start_counter')
@patch('threading.Thread')
@patch('time.sleep')
def test_main_error_in_loop(
    mock_sleep, mock_thread_class, mock_start_counter, mock_getting_settings,
    mock_connection, mock_error_handling, mock_keyboard, mock_logger
):
    """
    Тест: Ошибка возникает внутри основного цикла while.
    """

    mock_start_counter.return_value = 100
    mock_getting_settings.return_value = (30, 1920, 1080, 0, '/usb/folder', ['ip1'], ['f1'])

    mock_ip_thread_instance = MagicMock()
    mock_usb_thread_instance = MagicMock()
    mock_thread_class.side_effect = [mock_ip_thread_instance, mock_usb_thread_instance]

    test_exception = RuntimeError("Error during handling")
    mock_error_handling.side_effect = test_exception

    mock_keyboard.is_pressed.return_value = False

    Video.main()


    assert mock_thread_class.call_count == 2
    mock_ip_thread_instance.start.assert_called_once()
    mock_usb_thread_instance.start.assert_called_once()

    mock_error_handling.assert_called_once()
    mock_logger.error.assert_called_with(str(test_exception))

    mock_logger.info.assert_called_once_with("Программа завершена из-за ошибки.")

    mock_ip_thread_instance.join.assert_called_once()
    mock_usb_thread_instance.join.assert_called_once()


