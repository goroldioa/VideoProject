import pytest
from unittest import mock
from unittest.mock import Mock
import tkinter as tk
from tkinter import ttk
import Video

@pytest.fixture
def setup_tkinter():
    root = tk.Tk()  # Создаем корневое окно Tkinter
    root.withdraw()  # Скрываем его, так как мы тестируем только диалог
    yield root
    root.destroy()  # Удаляем корневое окно после тестов


def test_ask_multiple_choice_question_select_some(setup_tkinter):
    def test_ask_multiple_choice_question_select_some(setup_tkinter):
        choices = ["Option 1", "Option 2", "Option 3"]
        vars = [mock.Mock(), mock.Mock(), mock.Mock()]
        vars[0].get.return_value = True
        vars[2].get.return_value = True

        with mock.patch('tkinter.Toplevel') as MockToplevel:
            mock_window = MockToplevel.return_value
            mock_window.wait_window = Mock()

            mock_ok_button = mock.Mock()
            mock_ok_button.invoke = mock.Mock()

            with mock.patch('your_module.tk.BooleanVar', side_effect=vars), \
                    mock.patch('your_module.ttk.Checkbutton', return_value=mock.Mock()), \
                    mock.patch('your_module.ttk.Button', return_value=mock_ok_button):  # Мокаем кнопки

                selected_choices = Video.ask_multiple_choice_question("Choose options:", choices)
                mock_ok_button.invoke.assert_called_once()  # Проверка, что кнопка была нажата

            assert selected_choices == ["Option 1", "Option 3"]

        assert selected_choices == ["Option 1", "Option 3"]

def test_ask_multiple_choice_question_select_none(setup_tkinter):
    choices = ["Option 1", "Option 2", "Option 3"]

    with mock.patch('tkinter.Toplevel') as MockToplevel:
        mock_window = MockToplevel.return_value
        mock_window.wait_window = Mock()

        # Имитация снятия выбора
        selected_var = mock.Mock()
        selected_var.get = Mock(return_value=False)  # Все чекбоксы не выбраны

        # Создание чекбоксов с использованием моков
        mock_checkbutton_1 = mock.Mock()
        mock_checkbutton_1.variable = selected_var
        mock_checkbutton_2 = mock.Mock()
        mock_checkbutton_2.variable = selected_var
        mock_checkbutton_3 = mock.Mock()
        mock_checkbutton_3.variable = selected_var

        # Имитация добавления чекбоксов в окно
        mock_window.children = {
            'checkbutton1': mock_checkbutton_1,
            'checkbutton2': mock_checkbutton_2,
            'checkbutton3': mock_checkbutton_3,
        }

        selected_choices = Video.ask_multiple_choice_question("Choose options:", choices)

        assert selected_choices is None

def test_ask_multiple_choice_question_cancel(setup_tkinter):
    choices = ["Option 1", "Option 2", "Option 3"]

    with mock.patch('tkinter.Toplevel') as MockToplevel:
        mock_window = MockToplevel.return_value
        mock_window.wait_window = Mock()

        # Имитация нажатия кнопки "Cancel"
        selected_choices = Video.ask_multiple_choice_question("Choose options:", choices)
        # Проверяем, что ничего не выбрано
        assert selected_choices is None
