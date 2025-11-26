import sys
import os
import sqlite3
import traceback
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_api_client import SimpleTheatreClient

# Глобальная переменная для хранения окон
app_windows = {}


def main():
    app = QApplication(sys.argv)

    # Проверяем есть ли сохраненный пользователь
    settings = QSettings("TheatreApp", "TEAC_Auth")
    saved_username = settings.value("username", "")
    print(f"Сохраненный пользователь: {saved_username}")

    if saved_username:
        # Проверяем существует ли пользователь через API
        try:
            client = SimpleTheatreClient()
            user_data = client.get_current_user()
            print(user_data)
            if user_data and user_data['username'] == saved_username:
                # Автоматически открываем главное окно
                from main_window import MainWindow
                app_windows['main'] = MainWindow()
                app_windows['main'].setWindowTitle("«TEAC»")
                app_windows['main'].setWindowIcon(QIcon("icon.png"))

                # Устанавливаем пользователя в главном окне
                if hasattr(app_windows['main'], 'set_current_user'):
                    app_windows['main'].set_current_user(saved_username)

                app_windows['main'].show()
                print("Главное окно открыто")
            else:
                # Пользователь удален из БД, показываем окно авторизации
                print("Пользователь не найден через API")
                settings.remove("username")  # очищаем настройки
                show_auth_window()

        except Exception as e:
            # Если ошибка, показываем окно авторизации
            print(f"Ошибка API: {e}")
            traceback.print_exc()
            show_auth_window()
    else:
        # Нет сохраненного пользователя, показываем окно авторизации
        print("Нет сохраненного пользователя")
        show_auth_window()

        # Запуск главного цикла
    result = app.exec()
    sys.exit(result)


def show_auth_window():
    """Показать окно авторизации"""
    from auth_window import SimpleAuth
    print("Создание окна авторизации")
    try:
        app_windows['auth'] = SimpleAuth()
        app_windows['auth'].setWindowTitle("«TEAC»")
        app_windows['auth'].setWindowIcon(QIcon("icon.png"))
        app_windows['auth'].show()
        print("Окно авторизации показано")
    except Exception as e:
        print(f"Ошибка создания окна авторизации: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
