import pytest
import os

from Video import start_counter

def test_start_counter_file_not_found(tmp_path, monkeypatch):
    """
    Тест: Файл 'start_count.txt' не существует.
    Ожидание: Функция возвращает 1, создает файл и записывает в него '1'.
    """
    monkeypatch.chdir(tmp_path)
    expected_file = tmp_path / "start_count.txt"

    result = start_counter()

    assert result == 1, "Функция должна вернуть 1, если файла нет"
    assert expected_file.exists(), "Файл 'start_count.txt' должен быть создан"
    assert expected_file.read_text() == "1", "В созданном файле должно быть значение '1'"

def test_start_counter_file_exists_with_value(tmp_path, monkeypatch):
    """
    Тест: Файл 'start_count.txt' существует с начальным значением.
    Ожидание: Функция возвращает начальное значение, а в файле оказывается инкрементированное.
    """
    monkeypatch.chdir(tmp_path)
    initial_value = 5
    expected_file = tmp_path / "start_count.txt"
    expected_file.write_text(str(initial_value))

    result = start_counter()

    assert result == initial_value, f"Функция должна вернуть исходное значение {initial_value}"
    assert expected_file.read_text() == str(initial_value + 1), f"В файле должно быть инкрементированное значение {initial_value + 1}"

def test_start_counter_multiple_calls(tmp_path, monkeypatch):
    """
    Тест: Последовательные вызовы функции должны корректно инкрементировать счетчик.
    """
    monkeypatch.chdir(tmp_path)
    expected_file = tmp_path / "start_count.txt"

    result1 = start_counter()
    assert result1 == 1
    assert expected_file.read_text() == "1"

    result2 = start_counter()
    assert result2 == 1
    assert expected_file.read_text() == "2"

    result3 = start_counter()
    assert result3 == 2
    assert expected_file.read_text() == "3"

