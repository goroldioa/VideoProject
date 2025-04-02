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
running = True

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

def error_handling(errors):
    if not errors.empty():
        index = errors.get()
        should_continue = messagebox.askyesno("Ошибка камеры",
                                              f"Ошибка: Не удалось открыть камеру {index + 1}\nПродолжить выполнение программы?")
        if not should_continue:
            global running
            running = False
        else:
            error_thread = threading.Thread(target=show_error, args=(index,))
            threads.append(error_thread)
            error_thread.start()
        logger.error(f"Ошибка: Не удалось открыть камеру {index + 1}")


def create_error_image():
    error_image = np.zeros((200, 400, 3), dtype=np.uint8)
    cv2.putText(error_image, "ERROR", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2, cv2.LINE_AA)
    return error_image

def show_error(index):
    error_image = create_error_image()
    while running:
        cv2.imshow(f"Camera {index + 1}", error_image)
        cv2.waitKey(1)
        position_window(f"Camera {index + 1}", index)

def position_window(window_name, index):
    x = (index % 2) * WINDOW_WIDTH
    y = (index // 2) * WINDOW_HEIGHT
    cv2.moveWindow(window_name, x, y)

def capture_and_save(cap, folder_name, fps, index, start_count):
    os.makedirs(folder_name, exist_ok=True)
    frame_count = 0
    start_time = time.perf_counter()
    while running:
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

def connection(ip, fps, folder_name, width, height, index, start_count, timeout = 10):
    """Пытается подключиться к камере, обрабатывает успех/неудачу."""
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
            capture_and_save(cap, folder_name, fps, index, start_count)

    except Exception as e:
        logger.error(f"Exception during connection setup for index {index}: {e}")
        if index is not None:
             with lock:
                 errors_queue.put(index)

    finally:
        if cap is not None and not frames_received:
            cap.release()

def getting_settings():
    settings = []
    if os.path.exists('settings.txt'):
        try:
            with open('settings.txt', 'r') as file:
                for line in file:
                    settings.append(line)
            change_settings = messagebox.askyesno("Настройки",
                                              f'Вы хотите изменить настройки? \n'
                                              f'Сейчас заданы: \n'
                                              f'FPS: {settings[0]}'
                                              f'Size: {settings[1][:-1]} x {settings[2]}'
                                              f'USB Index: {settings[3]}'
                                              f'Папка для USB камеры: {settings[4]}'
                                              f'IP 1: {settings[5]}'
                                              f'Папка для 1 IP камеры: {settings[6]}'
                                              f'IP 2: {settings[7]}'
                                              f'Папка для 2 IP камеры: {settings[8]}'
                                              f'IP 3: {settings[9]}'
                                              f'Папка для 3 IP камеры: {settings[10]}')
        except IndexError:
            change_settings = True
    else:
        change_settings = True

    if change_settings:
        with open('settings.txt', 'w') as f:
            user_fps = simpledialog.askinteger("FPS", "Введите количество кадров в секунду(1-60):")
            f.write(str(user_fps) + '\n')
            user_width = simpledialog.askinteger("WIDTH", "Введите ширину кадра(320-2560):")
            f.write(str(user_width) + '\n')
            user_height = simpledialog.askinteger("HEIGHT", "Введите высоту кадра(200-2048):")
            f.write(str(user_height) + '\n')
            user_usb_index = simpledialog.askinteger('USB INDEX', 'Введите индекс usb камеры:')
            f.write(str(user_usb_index) + '\n')
            usb_folder = filedialog.askdirectory(title="Выберите папку для USB-камеры")
            f.write(f'{str(usb_folder)} \n')
            ip_camera_addresses = []
            ip_camera_folders = []
            for i in range(1,4):
                user_ip= simpledialog.askstring(f'IP {i}', 'Введите ip камеры в формате: \n'
                                                         '"rtsp://user1:pass1@192.168.1.101/"')
                f.write(user_ip + '\n')
                ip_folder = filedialog.askdirectory(title=f"Выберите папку для {i} IP-камеры")
                f.write(f'{str(ip_folder)} \n')
                ip_camera_addresses.append(user_ip)
                ip_camera_folders.append(ip_folder)
    else:
        user_fps = int(settings[0][:-1])
        user_width = int(settings[1][:-1])
        user_height = int(settings[2][:-1])
        user_usb_index = int(settings[3][:-1])
        usb_folder = settings[4][:-1]
        ip_camera_addresses = [settings[5][:-1], settings[7][:-1], settings[9][:-1]]
        ip_camera_folders = [settings[6][:-2], settings[8][:-2], settings[10][:-2]]
    return user_fps, user_width, user_height, user_usb_index, usb_folder, ip_camera_addresses, ip_camera_folders

def start_counter():
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

def main():

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
        global running
        while running:
            time.sleep(0.1)
            error_handling(errors_queue)

            if keyboard.is_pressed('ctrl') and keyboard.is_pressed('c'):
                logger.info('Программа завершена нажатием клавиш.')
                running = False
                break

    except Exception as e:
        logger.error(str(e))
        logger.info("Программа завершена из-за ошибки.")

    finally:
        for thread in threads:
            thread.join()


if __name__ == "__main__":
    main()
