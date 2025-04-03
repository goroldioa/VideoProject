import cv2
import os
import time
import queue
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import keyboard
import logging
import platform
import numpy as np
import configparser

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('my_log.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.info('Программа запущена')

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 360

errors_queue =  queue.Queue(maxsize=0)

root = tk.Tk()
root.withdraw()

threads = []
lock = threading.Lock()
stop_event = threading.Event()

def error_handling(errors, stop_event):
    """
    Обрабатывает ошибки открытия камеры, уведомляя пользователя и предлагая варианты действий.
    """
    try:
        while not errors.empty() and not stop_event.is_set():
            index = errors.get()
            logger.error(f"Ошибка: Не удалось открыть камеру {index + 1}")
            should_continue = messagebox.askyesno("Ошибка камеры",
                                                f"Ошибка: Не удалось открыть камеру {index + 1}\nПродолжить выполнение программы?")
            if not should_continue:
                logger.info(f'Пользователь остановил программу из-за ошибки камеры {index + 1}')
                stop_event.set()

            else:
                logger.info(f'Пользователь продолжил программу несмотря на ошибку камеры {index + 1}')
                error_thread = threading.Thread(target=show_error, args=(index, stop_event,))
                threads.append(error_thread)
                error_thread.start()
    except Exception as e:
        logger.error(f'Непредвиденная ошибка в error_handling: {e}')


def create_error_image(text="ERROR", size=(200, 400), color=(0, 0, 255), thickness=2, font_scale=2):
    """
    Создает изображение с текстом об ошибке.
    """
    try:
        error_image = np.zeros((size[0], size[1], 3), dtype=np.uint8)
        text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        text_x = (size[1] - text_size[0]) // 2
        text_y = (size[0] + text_size[1]) // 2
        cv2.putText(error_image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
        return error_image
    except Exception as e:
        logger.error(f'Непредвиденная ошибка в create_error_image: {e}')
        return None

def show_error(index, stop_event):
    """
    Показывает изображение об ошибке в отдельном потоке.
    """
    try:
        error_image = create_error_image()
        while not stop_event.is_set():
            cv2.imshow(f"Camera {index + 1}", error_image)
            cv2.waitKey(1)
            position_window(f"Camera {index + 1}", index)

        cv2.destroyWindow(f"Camera {index + 1}")

    except Exception as e:
        logger.error(f'Непредвиденная ошибка в show_error: {e}')

def position_window(window_name, index, num_windows_per_row=2):
    """
    Размещает окно с заданным именем на экране в виде сетки.
    """
    try:
        x = (index % num_windows_per_row) * WINDOW_WIDTH
        y = (index // num_windows_per_row) * WINDOW_HEIGHT
        cv2.moveWindow(window_name, x, y)
    except Exception as e:
        logger.exception(f'Ошибка при позиционировании окна "{window_name}" с индексом {index}: {e}')

def capture_and_save(cap, folder_name, fps, index, start_count, stop_event):
    """
    Захватывает и сохраняет кадры с камеры в JPG-файлы, отображая видеопоток с подсчетом и отображением реального FPS, пока не получит сигнал остановки.
    """
    try:
        os.makedirs(folder_name, exist_ok=True)
        frame_count = 0
        start_time = time.perf_counter()
        while not stop_event.is_set():
            ret, frame = cap.read()

            filename = os.path.join(folder_name, f"{start_count} frame_{frame_count}.jpg")
            cv2.imwrite(filename, frame)
            frame_count += 1

            elapsed_time = time.perf_counter() - start_time
            if elapsed_time > 0:
                real_fps = frame_count // elapsed_time
            else:
                real_fps = 0

            cv2.putText(frame, str(int(real_fps)), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            cv2.imshow(f"Camera {index + 1}", frame)
            position_window(f"Camera {index + 1}", index)
            cv2.waitKey(1)
            time.sleep(max(0, 1/fps - (time.perf_counter() - start_time - frame_count/fps ) if fps>0 else 0))

        cap.release()
        cv2.destroyWindow(f"Camera {index + 1}")
    except Exception as e:
        logger.error(f'Непредвиденная ошибка в capture_and_save: {e}')

def connection(ip, fps, folder_name, width, height, index, start_count, timeout = 10):
    """
    Пытается подключиться к камере, обрабатывает успех/неудачу.
    """
    try:
        frames_received = False
        cap = None

        try:
            if platform.system() == 'Windows':
                cap = cv2.VideoCapture(ip, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(ip)

            if not cap or not cap.isOpened():
                 raise cv2.error("Failed to open video source")

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            start_time = time.time()
            while time.time() - start_time < timeout:
                if cap.grab():
                    frames_received = True
                    break
                else:
                    time.sleep(0.01)

            if not frames_received:
                with lock:
                    errors_queue.put(index)
            else:
                success_message = f"Успешное подключение к камере {index + 1}"
                logger.info(success_message)
                capture_and_save(cap, folder_name, fps, index, start_count, stop_event)

        except Exception as e:
            logger.error(f"Исключение при настройке соединения для камеры {index + 1}: {e}")
            if index is not None:
                 with lock:
                     errors_queue.put(index)

        finally:
            if cap is not None and not frames_received:
                cap.release()
    except Exception as e:
        logger.error(f'Непредвиденная ошибка в connection: {e}')

def getting_settings():
    """
    Загружает настройки из файла settings.ini или запрашивает их у пользователя.
    """
    config = configparser.ConfigParser()
    config_file = 'settings.ini'

    if os.path.exists(config_file):
        config.read(config_file)
        try:
            config.getint('General', 'fps')
            config.getint('General', 'width')
            config.getint('General', 'height')
            config.getint('USB', 'index')
            config.get('USB', 'folder')
            config.get('IPCamera1', 'address')
            config.get('IPCamera1', 'folder')
            config.get('IPCamera2', 'address')
            config.get('IPCamera2', 'folder')
            config.get('IPCamera3', 'address')
            config.get('IPCamera3', 'folder')

            change_settings = messagebox.askyesno("Настройки",
                                                  "Изменить текущие настройки?\n" +
                                                  "\n".join([f"{key}: {value}" for section in config.sections() for key, value in config.items(section)]))


        except (configparser.NoSectionError, configparser.NoOptionError):
            change_settings = True
    else:
        change_settings = True


    if change_settings:
        config['General'] = {}
        config['General']['fps'] = str(simpledialog.askinteger("FPS", "Введите количество кадров в секунду (1-60):", minvalue=1, maxvalue=60))
        config['General']['width'] = str(simpledialog.askinteger("Width", "Введите ширину кадра (320-2560):", minvalue=320, maxvalue=2560))
        config['General']['height'] = str(simpledialog.askinteger("Height", "Введите высоту кадра (200-2048):", minvalue=200, maxvalue=2048))

        config['USB'] = {}
        config['USB']['index'] = str(simpledialog.askinteger("USB Index", "Введите индекс USB камеры:"))
        config['USB']['folder'] = filedialog.askdirectory(title="Выберите папку для USB-камеры")

        for i in range(1, 4):
            section = f'IPCamera{i}'
            config[section] = {}
            config[section]['address'] = simpledialog.askstring(f'IP {i}', 'Введите адрес IP камеры в формате:\n "rtsp://user1:pass1@192.168.1.101/"')
            config[section]['folder'] = filedialog.askdirectory(title=f"Выберите папку для {i} IP-камеры")

        with open(config_file, 'w') as f:
            config.write(f)

    user_fps = config.getint('General', 'fps')
    user_width = config.getint('General', 'width')
    user_height = config.getint('General', 'height')
    user_usb_index = config.getint('USB', 'index')
    usb_folder = config.get('USB', 'folder')
    ip_camera_addresses = [config.get(f'IPCamera{i}', 'address') for i in range(1, 4)]
    ip_camera_folders = [config.get(f'IPCamera{i}', 'folder') for i in range(1, 4)]

    return user_fps, user_width, user_height, user_usb_index, usb_folder, ip_camera_addresses, ip_camera_folders

def start_counter():
    """
    Считывает счетчик из файла start_count.txt
    """
    try:
        try:
            with open('start_count.txt', 'r') as f:
                start_count = int(f.read())
            with open('start_count.txt', 'w') as f:
                f.write(str(start_count + 1))
        except FileNotFoundError:
            with open('start_count.txt', 'w') as f:
                f.write('1')
            start_count = 1
        return start_count
    except Exception as e:
        logger.error(f'Непредвиденная ошибка в start_counter: {e}')

def main():
    try:
        start_count = start_counter()

        user_fps, user_width, user_height, user_usb_index, usb_folder, ip_camera_addresses, ip_camera_folders = getting_settings()

        for ip_data in range(len(ip_camera_addresses)):
            try:
                ip_thread = threading.Thread(target=connection, args=(ip_camera_addresses[ip_data], user_fps, ip_camera_folders[ip_data], user_width, user_height, ip_data, start_count))
                threads.append(ip_thread)
                ip_thread.start()

            except Exception as e:
                logger.error(str(e))

        try:
            usb_index = 3
            usb_thread = threading.Thread(target=connection, args=(user_usb_index, user_fps, usb_folder, user_width, user_height, usb_index, start_count))
            threads.append(usb_thread)
            time.sleep(10)
            usb_thread.start()
        except Exception as e:
            logger.error(str(e))

        try:
            while True:
                time.sleep(0.1)
                error_handling(errors_queue, stop_event)

                if keyboard.is_pressed('ctrl') and keyboard.is_pressed('c'):
                    logger.info('Программа завершена нажатием клавиш.')
                    stop_event.set()
                    break

                if stop_event.is_set():
                    logger.info('Программа завершена')
                    break

        except Exception as e:
            logger.error(str(e))
            logger.info("Программа завершена из-за ошибки.")

        finally:
            for thread in threads:
                thread.join()
    except Exception as e:
        logger.error(f'Непредвиденная ошибка в main: {e}')

if __name__ == "__main__":
    main()
