import pytest
from unittest.mock import patch, mock_open, MagicMock
import configparser
from Video import getting_settings
import os
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
import tkinter.filedialog as filedialog


@pytest.fixture
def mock_config():
    config = configparser.ConfigParser()
    config['General'] = {
        'fps': '30',
        'width': '1920',
        'height': '1080'
    }
    config['USB'] = {
        'index': '0',
        'folder': '/path/to/usb/folder'
    }
    for i in range(1, 4):
        config[f'IPCamera{i}'] = {
            'address': f'rtsp://camera{i}',
            'folder': f'/path/to/ip{i}/folder'
        }
    return config


@pytest.fixture
def mock_file_exists():
    with patch('os.path.exists', return_value=True):
        yield


@pytest.fixture
def mock_messagebox_yes():
    with patch.object(messagebox, 'askyesno', return_value=False):
        yield


@pytest.fixture
def mock_filedialog():
    with patch.object(filedialog, 'askdirectory', side_effect=[
        '/path/to/usb/folder',
        '/path/to/ip1/folder',
        '/path/to/ip2/folder',
        '/path/to/ip3/folder'
    ]):
        yield


@pytest.fixture
def mock_simpledialog():
    with patch.object(simpledialog, 'askinteger', side_effect=[30, 1920, 1080, 0]), \
            patch.object(simpledialog, 'askstring', side_effect=[
                'rtsp://camera1',
                'rtsp://camera2',
                'rtsp://camera3'
            ]):
        yield


def test_getting_settings_with_existing_config(mock_config, mock_file_exists, mock_messagebox_yes):
    # Подготовка моков для чтения конфига
    with patch('configparser.ConfigParser') as mock_config_parser, \
            patch('builtins.open', mock_open()) as mock_file:
        # Настраиваем mock ConfigParser
        mock_config_instance = mock_config_parser.return_value
        mock_config_instance.sections.return_value = ['General', 'USB', 'IPCamera1', 'IPCamera2', 'IPCamera3']
        mock_config_instance.items.side_effect = [
            [('fps', '30'), ('width', '1920'), ('height', '1080')],
            [('index', '0'), ('folder', '/path/to/usb/folder')],
            [('address', 'rtsp://camera1'), ('folder', '/path/to/ip1/folder')],
            [('address', 'rtsp://camera2'), ('folder', '/path/to/ip2/folder')],
            [('address', 'rtsp://camera3'), ('folder', '/path/to/ip3/folder')]
        ]

        # Настройка getint и get
        def mock_getint(section, option):
            return int(mock_config[section][option])

        def mock_get(section, option):
            return mock_config[section][option]

        mock_config_instance.getint.side_effect = mock_getint
        mock_config_instance.get.side_effect = mock_get

        # Вызов тестируемой функции
        result = getting_settings()

        # Проверка результата
        assert result == (
            30,  # fps
            1920,  # width
            1080,  # height
            0,  # usb index
            '/path/to/usb/folder',  # usb folder
            ['rtsp://camera1', 'rtsp://camera2', 'rtsp://camera3'],  # ip addresses
            ['/path/to/ip1/folder', '/path/to/ip2/folder', '/path/to/ip3/folder']  # ip folders
        )


def test_getting_settings_with_missing_config(mock_config, mock_filedialog, mock_simpledialog):
    # Мок отсутствия файла конфига
    with patch('os.path.exists', return_value=False), \
            patch('configparser.ConfigParser') as mock_config_parser, \
            patch('builtins.open', mock_open()) as mock_file:

        # Настраиваем mock ConfigParser
        mock_config_instance = mock_config_parser.return_value
        mock_config_instance.sections.return_value = []

        # Настраиваем возвращаемые значения для getint и get
        def mock_getint(section, option):
            if section == 'General':
                if option == 'fps': return 30
                if option == 'width': return 1920
                if option == 'height': return 1080
            elif section == 'USB' and option == 'index':
                return 0
            raise configparser.NoOptionError(option, section)

        def mock_get(section, option):
            if section == 'USB' and option == 'folder':
                return '/path/to/usb/folder'
            if section.startswith('IPCamera'):
                if option == 'address':
                    return f'rtsp://camera{section[-1]}'
                if option == 'folder':
                    return f'/path/to/ip{section[-1]}/folder'
            raise configparser.NoOptionError(option, section)

        mock_config_instance.getint.side_effect = mock_getint
        mock_config_instance.get.side_effect = mock_get

        # Вызов тестируемой функции
        result = getting_settings()

        # Проверка результата
        assert result == (
            30,  # fps
            1920,  # width
            1080,  # height
            0,  # usb index
            '/path/to/usb/folder',  # usb folder
            ['rtsp://camera1', 'rtsp://camera2', 'rtsp://camera3'],  # ip addresses
            ['/path/to/ip1/folder', '/path/to/ip2/folder', '/path/to/ip3/folder']  # ip folders
        )

def test_getting_settings_with_error():
    # Мок возникновения исключения
    with patch('os.path.exists', side_effect=Exception("Test error")), \
            patch('Video.logger.error') as mock_logger:
        # Вызов тестируемой функции
        result = getting_settings()

        # Проверка результата
        assert result is None
        mock_logger.assert_called_once_with('Непредвиденная ошибка в getting_settings: Test error')