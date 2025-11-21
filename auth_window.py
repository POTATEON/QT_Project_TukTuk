from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.uic import loadUi
import sys
import os

# Добавляем путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_api_client import SimpleTheatreClient


class SimpleAuth(QWidget):
    WARNING_TEMPLATE = """
    <div style="color: #fdefc8; font-size: 14pt; font-family: Martian Mono;">
    «Не верю»
    </div>
    <div style="color: #fdefc8; font-size: 12pt; margin-top: 10px; text-align: right">
    Станиславский
    </div>
    <div style="color: #fdefc8; font-size: 10pt; margin-top: 5px; font-family: Martian Mono">
    {message}
    </div>
    """

    EMPTY_FIELDS_MESSAGE = "Заполните пустые поля"
    INVALID_CREDENTIALS_MESSAGE = "Неверный логин или пароль"
    EXISTANCE_CRISIS = "Пользователь уже существует"

    INFORMATION_TEMPLATE = """
            <div style="color: #fdefc8; font-size: 14pt; font-family: Martian Mono;">
            Здравствуй, {greet}!
            </div>
            <div style="color: #fdefc8; font-size: 10pt; margin-top: 10px; font-family: Martian Mono">
            {message}
            </div>
            """

    SUCCESS_LOG = "С возвращением!"
    SUCCESS_REG = "Будем знакомы!"

    def __init__(self):
        super().__init__()
        # Используем более надежные настройки
        self.settings = QSettings("TheatreApp", "TEAC_Auth")
        self.main_window = None
        self.client = SimpleTheatreClient()
        loadUi("ui/auth.ui", self)
        print("Инициализация окна авторизации")

        self.logButton.clicked.connect(self.login)
        self.regButton.clicked.connect(self.register)

        # Загружаем сохраненного пользователя при запуске
        self.load_saved_user()

    def load_saved_user(self):
        """Загрузка сохраненного пользователя"""
        print("Загрузка сохраненного пользователя")
        try:
            # Проверяем все доступные ключи в настройках
            all_keys = self.settings.allKeys()
            print(f"Все ключи в настройках: {all_keys}")

            saved_username = self.settings.value("username", "")
            print(f"Загружен пользователь: '{saved_username}'")
            print(f"Тип загруженного значения: {type(saved_username)}")

        except Exception as e:
            print(f"Ошибка загрузки пользователя: {e}")

        if saved_username and saved_username != "":
            self.user_input.setText(saved_username)
            if hasattr(self, 'remember_check'):
                self.remember_check.setChecked(True)
            self.pass_input.setFocus()
            print(f"Пользователь '{saved_username}' загружен в поле ввода")
        else:
            print("Сохраненный пользователь не найден")

    def save_user(self, username):
        """Сохранение пользователя в настройках"""
        print(f"Попытка сохранения пользователя: '{username}'")
        print(f"remember_check существует: {hasattr(self, 'remember_check')}")

        if hasattr(self, 'remember_check'):
            is_checked = self.remember_check.isChecked()
            print(f"Чекбокс 'Запомнить меня': {is_checked}")
        else:
            is_checked = True  # Если чекбокса нет, всегда сохраняем
            print("Чекбокс не найден, сохраняем по умолчанию")

        if is_checked:
            self.settings.setValue("username", username)
            # Принудительно синхронизируем настройки
            self.settings.sync()
            print(f"Пользователь '{username}' сохранен. Статус синхронизации: {self.settings.status()}")

            # Проверяем, что сохранилось
            saved_value = self.settings.value("username", "NOT_FOUND")
            print(f"Проверка сохранения: '{saved_value}'")
        else:
            self.settings.remove("username")
            self.settings.sync()
            print("Пользователь не сохранен (чекбокс снят)")

    def login(self):
        """Авторизация через API"""
        user = self.user_input.text()
        pwd = self.pass_input.text()

        if not user or not pwd:
            QMessageBox.warning(self, "Ошибка", self.WARNING_TEMPLATE.format(message=self.EMPTY_FIELDS_MESSAGE))
            return

        result = self.client.login(user, pwd)

        if result.get('success'):
            # Сохраняем пользователя
            self.save_user(user)
            print("сохранение прошло")

            QMessageBox.information(self, "Успех",
                                    self.INFORMATION_TEMPLATE.format(greet=user, message=self.SUCCESS_LOG))

            # Закрываем окно авторизации и открываем главное окно
            print("начало импорта")
            from main_window import MainWindow
            print("импортировали")
            self.main_window = MainWindow()
            print("экземпляр")
            self.main_window.setWindowTitle("«TEAC»")
            print("заголовок")
            self.main_window.setWindowIcon(QIcon("icon.png"))
            print("иконка")

            # Устанавливаем пользователя в главном окне
            if hasattr(self.main_window, 'set_current_user'):
                self.main_window.set_current_user(user)
            print("запуск окна")
            self.main_window.show()
            self.hide()
            print("Окно авторизации скрыто, главное окно открыто")

        else:
            error_message = result.get('error', self.INVALID_CREDENTIALS_MESSAGE)
            QMessageBox.warning(self, "Ошибка", self.WARNING_TEMPLATE.format(message=error_message))

    def register(self):
        """Регистрация через API"""
        user = self.user_input.text()
        pwd = self.pass_input.text()

        if not user or not pwd:
            QMessageBox.warning(self, "Ошибка", self.WARNING_TEMPLATE.format(message=self.EMPTY_FIELDS_MESSAGE))
            return

        success = self.client.register(user, pwd)

        if success:
            # Сохраняем пользователя после регистрации
            self.save_user(user)

            QMessageBox.information(self, "Успех",
                                    self.INFORMATION_TEMPLATE.format(greet=user, message=self.SUCCESS_REG))
        else:
            QMessageBox.warning(self, "Ошибка", self.WARNING_TEMPLATE.format(message=self.EXISTANCE_CRISIS))

    def closeEvent(self, event):
        """Закрытие при выходе"""
        event.accept()