import cv2
import os
import time
import queue
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
import keyboard
import logging
import platform
import numpy as np
import configparser
from typing import List

logger = logging.getLogger(__name__) # Получаем логгер для текущего модуля
logger.setLevel(logging.DEBUG) # Устанавливаем уровень логирования на DEBUG, чтобы фиксировать все сообщения от этой важности и выше
file_handler = logging.FileHandler('my_log.log') # Создаем файловый обработчик, чтобы записывать логи в файл 'my_log.log'
file_handler.setLevel(logging.INFO) # Устанавливаем уровень логирования для обработчика на INFO, чтобы фиксировать сообщения от этой важности и выше
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') # Создаем формат для записи сообщений лога
file_handler.setFormatter(file_formatter) # Назначаем формат сообщений для обработчика
logger.addHandler(file_handler) # Добавляем обработчик в логгер
logger.info('Программа запущена') # Записываем информационное сообщение о запуске программы

# Размеры окна для отображения видео
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 360

errors_queue =  queue.Queue(maxsize=0) # Создаем очередь для хранения ошибок с неограниченным размером

root = tk.Tk() # Создаем главное окно Tkinter
root.withdraw() # Скрываем главное окно (withdraw)

threads = [] # Список для хранения потоков
lock = threading.Lock() # Создаем объект блокировки для управления доступом к общим ресурсам
stop_event = threading.Event() # Создаем событие для управления остановкой потоков

def error_handling(errors: queue, stop_event: threading.Event()) -> None:
    """
    Обрабатывает ошибки открытия камеры, уведомляя пользователя и предлагая варианты действий.

    :param errors: Очередь из индексов камер, вызвавших ошибку
    :param stop_event: Ивент-флаг для отслеживания работы программы
    """
    try:
        # Входим в цикл, пока в очереди есть ошибки и программа не остановлена
        while not errors.empty() and not stop_event.is_set():
            # Получаем индекс ошибки из очереди
            index = errors.get()
            # Логируем сообщение об ошибке
            logger.error(f"Ошибка: Не удалось открыть камеру {index + 1}")
            # Запрашиваем у пользователя, продолжать ли выполнение программы после ошибки
            should_continue = messagebox.askyesno("Ошибка камеры",
                                                  f"Ошибка: Не удалось открыть камеру {index + 1}\nПродолжить выполнение программы?")
            # Если пользователь не хочет продолжать, останавливаем программу
            if not should_continue:
                logger.info(f'Пользователь остановил программу из-за ошибки камеры {index + 1}')
                stop_event.set()
            else:
                # Если пользователь решил продолжить, логируем это событие
                logger.info(f'Пользователь продолжил программу несмотря на ошибку камеры {index + 1}')
                # Создаем новый поток для отображения ошибки
                error_thread = threading.Thread(target=show_error, args=(index, stop_event,))
                threads.append(error_thread)  # Добавляем поток в список потоков
                error_thread.start()  # Запускаем поток
    except Exception as e:
        # Логируем непредвиденные ошибки в блоке обработки ошибок
        logger.error(f'Непредвиденная ошибка в error_handling: {e}')


def create_error_image(text: str = "ERROR", size: List[int] = (200, 400), color: List[int] = (0, 0, 255), thickness: int = 2, font_scale: int = 2) -> np.array:
    """
    Создает изображение с текстом об ошибке.

    :param text: Текст, который будет на изображении (По умолчанию "ERROR")
    :param size: Размер изображения (По умолчанию (200, 400))
    :param color: Цвет надписи на изображении (По умолчанию (0, 0, 255))
    :param thickness: Толщина текста (По умолчанию 2)
    :param font_scale: Размер текста (По умолчанию 2)
    :return: Изображение с текстом на черном фоне
    """
    try:
        # Создаем черное изображение заданного размера
        error_image = np.zeros((size[0], size[1], 3), dtype=np.uint8)
        # Получаем размеры текста для правильного размещения на изображении
        text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        text_x = (size[1] - text_size[0]) // 2  # Вычисляем координаты X для центровки текста
        text_y = (size[0] + text_size[1]) // 2  # Вычисляем координаты Y для центровки текста
        # Размещаем текст на изображении
        cv2.putText(error_image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
        return error_image  # Возвращаем изображение
    except Exception as e:
        # Логируем непредвиденные ошибки в функции создания изображения с ошибкой
        logger.error(f'Непредвиденная ошибка в create_error_image: {e}')
        return None  # Возвращаем None в случае ошибки

def show_error(index: int, stop_event: threading.Event()) -> None:
    """
    Показывает изображение об ошибке в отдельном потоке.

    :param index: Индекс камеры
    :param stop_event: Ивент-флаг для отслеживания работы программы
    """
    try:
        # Создаем изображение с текстом об ошибке, вызывая функцию create_error_image
        error_image = create_error_image()

        # Запускаем цикл, который будет работать, пока флаг stop_event не установлен
        while not stop_event.is_set():
            # Отображаем изображение с ошибкой в новом окне с именем "Camera {index + 1}"
            cv2.imshow(f"Camera {index + 1}", error_image)
            # Ждем 1 миллисекунду для обработки событий окна
            cv2.waitKey(1)
            # Устанавливаем позицию окна с изображением об ошибке в соответствии с индексом камеры
            position_window(f"Camera {index + 1}", index)

        # Закрываем окно с изображением об ошибке, когда цикл завершается
        cv2.destroyWindow(f"Camera {index + 1}")

    except Exception as e:
        # Логируем непредвиденные ошибки, возникшие в процессе выполнения функции
        logger.error(f'Непредвиденная ошибка в show_error: {e}')


def position_window(window_name: str, index: int, num_windows_per_row: int = 2) -> None:
    """
    Размещает окно с заданным именем на экране в виде сетки.

    :param window_name: Название окна, которое позиционируется
    :param index: Индекс камеры, окно которой позиционируется
    :param num_windows_per_row: Кол-во окон в строке (По умолчанию 2)
    """
    try:
        # Вычисляем координату X для позиции окна на экране
        x = (index % num_windows_per_row) * WINDOW_WIDTH

        # Вычисляем координату Y для позиции окна на экране
        y = (index // num_windows_per_row) * WINDOW_HEIGHT

        # Перемещаем окно с заданным именем на рассчитанные координаты
        cv2.moveWindow(window_name, x, y)

    except Exception as e:
        # Логируем ошибку, если произошла проблема при позиционировании окна
        logger.exception(f'Ошибка при позиционировании окна "{window_name}" с индексом {index}: {e}')


def capture_and_save(cap: cv2.VideoCapture(), folder_name: str, fps: int, index: int, start_count: int, stop_event: threading.Event()) -> None:
    """
    Захватывает и сохраняет кадры с камеры в JPG-файлы, отображая видеопоток с подсчетом и отображением реального FPS, пока не получит сигнал остановки.

    :param cap: Камера, с которой захватывается изображение
    :param folder_name: Путь к папке, куда сохраняются кадры
    :param fps: Кол-во кадров в секунду для захвата кадров
    :param index: Индекс камеры, с которой захватывается изображение
    :param start_count: Номер итерации программы
    :param stop_event: Ивент-флаг для отслеживания работы программы
    """
    try:
        # Создаем папку для сохранения кадров, если она не существует
        os.makedirs(folder_name, exist_ok=True)

        frame_count = 0  # Счетчик кадров
        start_time = time.perf_counter()  # Запоминаем время начала захвата

        # Запускаем цикл, пока не получен сигнал остановки
        while not stop_event.is_set():
            ret, frame = cap.read()  # Захватываем кадр с камеры

            # Формируем имя файла для сохранения кадра
            filename = os.path.join(folder_name, f"{start_count} frame_{frame_count}.jpg")
            cv2.imwrite(filename, frame)  # Сохраняем кадр в файл
            frame_count += 1  # Увеличиваем счетчик кадров

            # Вычисляем время, прошедшее с начала захвата
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > 0:
                # Вычисляем реальный FPS
                real_fps = frame_count // elapsed_time
            else:
                real_fps = 0  # Если прошло ноль времени, FPS равен 0

            # Отображаем реальный FPS на кадре
            cv2.putText(frame, str(int(real_fps)), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow(f"Camera {index + 1}", frame)  # Показываем кадр в окне
            position_window(f"Camera {index + 1}", index)  # Позиционируем окно на экране
            cv2.waitKey(1)  # Ждем одну миллисекунду для обработки событий окна

            # Рассчитываем время ожидания до следующего кадра, чтобы соблюсти нужный FPS
            time.sleep(max(0, 1 / fps - (time.perf_counter() - start_time - frame_count / fps) if fps > 0 else 0))

        cap.release()  # Освобождаем ресурсы камеры
    except Exception as e:
        # Логируем непредвиденные ошибки, возникшие в процессе выполнения функции
        logger.error(f'Непредвиденная ошибка в capture_and_save: {e}')


def connection(ip: str | int, fps: int, folder_name: str, width: int, height: int, index: int, start_count: int, timeout: int = 10) -> None:
    """
    Пытается подключиться к камере, обрабатывает успех/неудачу.

    :param ip: IP камеры для подключения
    :param fps: Кол-во кадров в секунду для захвата кадров
    :param folder_name: Путь к папке, куда сохраняются кадры
    :param width: Ширина кадра для захвата
    :param height: Высота кадра для захвата
    :param index: Индекс камеры, с которой захватывается изображение
    :param start_count: Номер итерации программы
    :param timeout: Время ожидания кадра с камеры
    """
    try:
        frames_received = False  # Флаг для отслеживания, были ли получены кадры
        cap = None  # Переменная для видеозахвата

        try:
            # Настраиваем видеозахват в зависимости от операционной системы
            if platform.system() == 'Windows':
                cap = cv2.VideoCapture(ip, cv2.CAP_DSHOW)  # Используем DSHOW для Windows
            else:
                cap = cv2.VideoCapture(ip)  # Используем общий видеозахват для других ОС

            # Настраиваем параметры захвата
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Устанавливаем размер буфера
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)  # Устанавливаем ширину кадра
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)  # Устанавливаем высоту кадра

            start_time = time.time()  # Запоминаем время начала попытки подключения

            # Цикл ожидания подключения к камере
            while time.time() - start_time < timeout:
                if cap.grab():  # Пытаемся захватить кадр
                    frames_received = True  # Успешный захват, обновляем флаг
                    break  # Выходим из цикла
                else:
                    time.sleep(0.01)  # Ждем 10 миллисекунд перед следующей попыткой

            if not frames_received:  # Если кадры не были получены
                with lock:
                    errors_queue.put(index)  # Добавляем индекс камеры в очередь ошибок
            else:
                success_message = f"Успешное подключение к камере {index + 1}"  # Сообщение об успешном подключении
                logger.info(success_message)  # Логируем сообщение
                capture_and_save(cap, folder_name, fps, index, start_count, stop_event)  # Запускаем захват и сохранение кадров

        except Exception as e:
            # Логируем ошибку, возникшую при настройке соединения
            logger.error(f"Исключение при настройке соединения для камеры {index + 1}: {e}")
            # Если индекс камеры известен, добавляем его в очередь ошибок
            if index is not None:
                with lock:
                    errors_queue.put(index)

        finally:
            # Освобождаем ресурсы видеозахвата, если кадры не были получены
            if cap is not None and not frames_received:
                cap.release()
    except Exception as e:
        # Логируем непредвиденные ошибки в функции
        logger.error(f'Непредвиденная ошибка в connection: {e}')


def ask_multiple_choice_question(question: str, choices: List[str]) -> List[str] | None:
    """
    Создает окно с вопросом и выбором нескольких вариантов ответа.

    :param question: Заголовок окна с вопросом
    :param choices: Список - варианты ответа на вопрос
    :return: Список - выбранные варианты ответа
    """
    try:
        # Создаем новое окно для вопроса
        top = tk.Toplevel()
        top.title("Вопрос")  # Устанавливаем заголовок окна

        # Создаем метку с заданным вопросом
        label = ttk.Label(top, text=question, wraplength=300)
        label.pack(pady=10)  # Добавляем отступы

        selected_choices = []  # Список для хранения выбранных вариантов
        vars = []  # Список для хранения переменных состояния чекбоксов

        # Создаем чекбоксы для каждого варианта ответа
        for choice in choices:
            var = tk.BooleanVar()  # Переменная, представляющая состояние чекбокса
            vars.append(var)  # Добавляем переменную в список
            checkbutton = ttk.Checkbutton(top, text=choice, variable=var)  # Создаем чекбокс
            checkbutton.pack(anchor="w", padx=20)  # Добавляем чекбокс в окно

        # Функция, вызываемая при нажатии кнопки "OK"
        def ok_button_clicked():
            for i, var in enumerate(vars):
                if var.get():  # Проверяем, выбран ли чекбокс
                    selected_choices.append(choices[i])  # Добавляем выбранный вариант в список
            top.destroy()  # Закрываем окно

        # Функция, вызываемая при нажатии кнопки "Отмена"
        def cancel_button_clicked():
            selected_choices.clear()  # Очищаем список выбранных вариантов
            top.destroy()  # Закрываем окно

        # Создаем кнопку "OK" и связываем её с функцией ок
        ok_button = ttk.Button(top, text="OK", command=ok_button_clicked)
        ok_button.pack(pady=10, side=tk.LEFT, padx=10)  # Добавляем кнопку в окно

        # Создаем кнопку "Отмена" и связываем её с функцией отмены
        cancel_button = ttk.Button(top, text="Отмена", command=cancel_button_clicked)
        cancel_button.pack(pady=10, side=tk.LEFT, padx=10)  # Добавляем кнопку в окно

        top.wait_window()  # Ожидаем закрытия окна

        # Возвращаем выбранные варианты (или None, если ничего не выбрано)
        return selected_choices if selected_choices else None

    except Exception as e:
        # Логируем ошибку, если произошла непредвиденная ошибка
        logger.error(f'Непредвиденная ошибка в ask_multiple_choice_question: {e}')


def getting_settings() -> tuple[int, int, int, int, str, list[str], list[str]] | None:
    """
    Загружает настройки из файла settings.ini или запрашивает их у пользователя.
    :return: Кортеж с настройками
    """
    try:
        # Импортируем модуль configparser для работы с файлами конфигурации
        config = configparser.ConfigParser()

        # Определяем имя файла конфигурации
        config_file = 'settings.ini'

        # Флаг, определяющий, нужно ли установить настройки
        set_the_settings = False

        # Проверяем существует ли файл конфигурации
        if os.path.exists(config_file):
            # Читаем содержимое файла конфигурации
            config.read(config_file)
            try:
                # Проверяем наличие и правильность настроек в секции 'General'
                config.getint('General', 'fps')
                config.getint('General', 'width')
                config.getint('General', 'height')

                # Проверяем наличие и правильность настроек в секции 'USB'
                config.getint('USB', 'index')
                config.get('USB', 'folder')

                # Проверяем наличие и правильность настроек для первой IP камеры
                config.get('IPCamera1', 'address')
                config.get('IPCamera1', 'folder')

                # Проверяем наличие и правильность настроек для второй IP камеры
                config.get('IPCamera2', 'address')
                config.get('IPCamera2', 'folder')

                # Проверяем наличие и правильность настроек для третьей IP камеры
                config.get('IPCamera3', 'address')
                config.get('IPCamera3', 'folder')

                # Спрашиваем пользователя, хочет ли он изменить текущие настройки
                change_settings = messagebox.askyesno(
                    "Настройки",
                    "Изменить текущие настройки?\n" +
                    "\n".join([f"{key}: {value}"
                               for section in config.sections()
                               for key, value in config.items(section)])
                )

            # Если возникают ошибки отсутствия секции или опции, устанавливаем флаг на установку настроек
            except (configparser.NoSectionError, configparser.NoOptionError):
                set_the_settings = True
        else:
            # Если файл конфигурации не существует, устанавливаем флаг на установку настроек
            set_the_settings = True
        # Проверяем, установлен ли флаг для настройки конфигурации
        if set_the_settings:
            # Устанавливаем значения в секции 'General'
            config['General'] = {}
            # Запрашиваем у пользователя ввод FPS с помощью диалога, с ограничениями значений от 1 до 60
            config['General']['fps'] = str(
                simpledialog.askinteger("FPS", "Введите количество кадров в секунду (1-60):", minvalue=1, maxvalue=60)
            )
            # Запрашиваем у пользователя ввод ширины кадра, с ограничениями значений от 320 до 2560
            config['General']['width'] = str(
                simpledialog.askinteger("Width", "Введите ширину кадра (320-2560):", minvalue=320, maxvalue=2560)
            )
            # Запрашиваем у пользователя ввод высоты кадра, с ограничениями значений от 200 до 2048
            config['General']['height'] = str(
                simpledialog.askinteger("Height", "Введите высоту кадра (200-2048):", minvalue=200, maxvalue=2048)
            )

            # Устанавливаем значения в секции 'USB'
            config['USB'] = {}
            # Запрашиваем у пользователя индекс USB камеры
            config['USB']['index'] = str(simpledialog.askinteger("USB Index", "Введите индекс USB камеры:"))
            # Запрашиваем у пользователя выбрать папку для USB-камера
            config['USB']['folder'] = filedialog.askdirectory(title="Выберите папку для USB-камеры")

            # Цикл для настройки данных для каждой из трех IP-камер
            for i in range(1, 4):
                section = f'IPCamera{i}'  # Формируем название секции для каждой камеры
                config[section] = {}  # Создаем секцию в конфигурации
                # Запрашиваем у пользователя адрес IP камеры в указанном формате
                config[section]['address'] = simpledialog.askstring(
                    f'IP {i}',
                    'Введите адрес IP камеры в формате:\n "rtsp://user1:pass1@192.168.1.101/"'
                )
                # Запрашиваем у пользователя выбрать папку для соответствующей IP-камеры
                config[section]['folder'] = filedialog.askdirectory(title=f"Выберите папку для {i} IP-камеры")

            # Сохраняем настройки в файл
            with open(config_file, 'w') as f:
                config.write(f)  # Записываем текущую конфигурацию в файл

        # Проверяем, нужно ли изменять настройки
        if change_settings:
            # Определяем список доступных для выбора настроек
            choices = [
                "FPS",
                "WIDTH",
                "HEIGHT",
                "USB_INDEX",
                "USB_FOLDER",
                "IP_ADDRESS_1",
                "IP_FOLDER_1",
                "IP_ADDRESS_2",
                "IP_FOLDER_2",
                "IP_ADDRESS_3",
                "IP_FOLDER_3"
            ]

            # Вызываем функцию для выбора одного или нескольких вариантов изменений
            selected = ask_multiple_choice_question("Выберите один или несколько вариантов:", choices)

            # Проверяем выборы пользователя и запрашиваем новые значения, если необходимо
            if "FPS" in selected:
                config['General']['fps'] = str(
                    simpledialog.askinteger("FPS", "Введите количество кадров в секунду (1-60):", minvalue=1,
                                            maxvalue=60)
                )
            if "WIDTH" in selected:
                config['General']['width'] = str(
                    simpledialog.askinteger("Width", "Введите ширину кадра (320-2560):", minvalue=320, maxvalue=2560)
                )
            if "HEIGHT" in selected:
                config['General']['height'] = str(
                    simpledialog.askinteger("Height", "Введите высоту кадра (200-2048):", minvalue=200, maxvalue=2048)
                )
            if "USB_INDEX" in selected:
                config['USB']['index'] = str(simpledialog.askinteger("USB Index", "Введите индекс USB камеры:"))
            if "USB_FOLDER" in selected:
                config['USB']['folder'] = filedialog.askdirectory(title="Выберите папку для USB-камеры")
            if "IP_ADDRESS_1" in selected:
                config['IPCamera1']['address'] = simpledialog.askstring(
                    f'IP 1',
                    'Введите адрес IP камеры в формате:\n "rtsp://user1:pass1@192.168.1.101/"'
                )
            if "IP_FOLDER_1" in selected:
                config['IPCamera1']['folder'] = filedialog.askdirectory(title=f"Выберите папку для 1 IP-камеры")
            if "IP_ADDRESS_2" in selected:
                config['IPCamera2']['address'] = simpledialog.askstring(
                    f'IP 2',
                    'Введите адрес IP камеры в формате:\n "rtsp://user1:pass1@192.168.1.101/"'
                )
            if "IP_FOLDER_2" in selected:
                config['IPCamera2']['folder'] = filedialog.askdirectory(title=f"Выберите папку для 2 IP-камеры")
            if "IP_ADDRESS_3" in selected:
                config['IPCamera3']['address'] = simpledialog.askstring(
                    f'IP 3',
                    'Введите адрес IP камеры в формате:\n "rtsp://user1:pass1@192.168.1.101/"'
                )
            if "IP_FOLDER_3" in selected:
                config['IPCamera3']['folder'] = filedialog.askdirectory(title=f"Выберите папку для 3 IP-камеры")

            # Сохраняем обновленные настройки в файл
            with open(config_file, 'w') as f:
                config.write(f)

        # Получаем значение настроек для пользователя после изменений или без них
        user_fps = config.getint('General', 'fps')
        user_width = config.getint('General', 'width')
        user_height = config.getint('General', 'height')
        user_usb_index = config.getint('USB', 'index')
        usb_folder = config.get('USB', 'folder')

        # Получаем адреса IP-камер и папки для каждой из них
        ip_camera_addresses = [config.get(f'IPCamera{i}', 'address') for i in range(1, 4)]
        ip_camera_folders = [config.get(f'IPCamera{i}', 'folder') for i in range(1, 4)]

        # Возвращаем полученные пользовательские настройки
        return user_fps, user_width, user_height, user_usb_index, usb_folder, ip_camera_addresses, ip_camera_folders

    except Exception as e:
        # Логируем ошибку, если произошла непредвиденная ошибка
        logger.error(f'Непредвиденная ошибка в getting_settings: {e}')
        return None

def start_counter() -> int | None:
    """
    Считывает счетчик из файла start_count.txt
    :return: Номер итерации
    """
    try:
        # Вложенный блок try для обработки ситуации, когда файл существует
        try:
            with open('start_count.txt', 'r') as f:
                start_count = int(f.read())  # Читаем текущее значение счетчика из файла и преобразуем в целое число

            # Открываем файл для записи, чтобы увеличить счетчик на 1
            with open('start_count.txt', 'w') as f:
                f.write(str(start_count + 1))  # Записываем новое значение счетчика (текущее + 1)

        except FileNotFoundError:
            # Обрабатываем случай, если файл не найден
            with open('start_count.txt', 'w') as f:
                f.write('1')  # Если файла нет, создаем его и записываем начальное значение 1
            start_count = 1  # Устанавливаем начальное значение счетчика в переменную

        return start_count  # Возвращаем текущее значение счетчика

    except Exception as e:
        # Логируем ошибку, если произошла непредвиденная ошибка
        logger.error(f'Непредвиденная ошибка в start_counter: {e}')


def main() -> None:
    """
    Главная функция
    """
    try:
        # Инициализируем счетчик, считывая его значение из файла
        start_count = start_counter()

        # Получаем настройки пользователя: FPS, размеры, индекс USB и папки для IP-камер
        user_fps, user_width, user_height, user_usb_index, usb_folder, ip_camera_addresses, ip_camera_folders = getting_settings()

        # Создаем и запускаем потоки для каждого IP-адреса камеры
        for ip_data in range(len(ip_camera_addresses)):
            try:
                # Создаем поток для соединения с IP-камерой
                ip_thread = threading.Thread(target=connection, args=(ip_camera_addresses[ip_data], user_fps, ip_camera_folders[ip_data], user_width, user_height, ip_data, start_count))
                threads.append(ip_thread)  # Добавляем поток в список потоков
                ip_thread.start()  # Запускаем поток

            except Exception as e:
                # Логируем ошибку, если произошла ошибка при создании потока
                logger.error(str(e))

        # Создаем и запускаем поток для USB-устройства
        try:
            usb_index = 3  # Индекс USB-устройства
            usb_thread = threading.Thread(target=connection, args=(user_usb_index, user_fps, usb_folder, user_width, user_height, usb_index, start_count))
            threads.append(usb_thread)  # Добавляем поток в список потоков
            time.sleep(10)  # Задержка перед запуском
            usb_thread.start()  # Запускаем поток для USB

        except Exception as e:
            # Логируем ошибку, если произошла ошибка при создании потока для USB
            logger.error(str(e))

        # Основной цикл для обработки ошибок и завершения программы
        try:
            while True:
                time.sleep(0.1)  # Небольшая задержка для снижения нагрузки на процессор
                error_handling(errors_queue, stop_event)  # Обработка ошибок из очереди

                # Проверка нажатия клавиш Ctrl+C для завершения программы
                if keyboard.is_pressed('ctrl') and keyboard.is_pressed('c'):
                    logger.info('Программа завершена нажатием клавиш.')  # Логируем сообщение о завершении
                    stop_event.set()  # Устанавливаем событие для завершения
                    break

                # Проверка события на остановку программы
                if stop_event.is_set():
                    logger.info('Программа завершена')  # Логируем сообщение о завершении
                    break

        except Exception as e:
            # Логируем ошибку, если произошла ошибка в основном цикле
            logger.error(str(e))
            logger.info("Программа завершена из-за ошибки.")

        finally:
            # Ожидаем завершения всех потоков перед выходом
            for thread in threads:
                thread.join()
            cv2.destroyAllWindows()  # Закрываем все окна OpenCV

    except Exception as e:
        # Логируем непредвиденные ошибки
        logger.error(f'Непредвиденная ошибка в main: {e}')


if __name__ == "__main__":
    main()
