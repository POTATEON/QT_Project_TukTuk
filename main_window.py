from os import path

from PIL.ImageQt import QPixmap
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtGui import QFontDatabase, QIcon, QPainter, QBrush
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QDialogButtonBox, QStyle
from PyQt6.uic import loadUi

from pages.home_page import HomePage
from pages.shed_page import ShedPage
from pages.perf_page import PerfPage
from pages.addit_page import AdditPage
from simple_api_client import SimpleTheatreClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_fonts()
        self.current_user = "b"
        loadUi("ui/main_window2.ui", self)
        self.client = SimpleTheatreClient()  # Добавлен клиент API
        self.partCheck.toggled.connect(self.is_part_check)
        self.avatarLabel.mousePressEvent = lambda event: self.change_avatar()
        self.logoutButton.clicked.connect(self.logout)
        self.setup_pages()
        self.setup_navigation()
        self.current_page = None
        self.update_part_check()

    def load_fonts(self) -> None:
        """
        Загружает шрифты из папки fonts в базу шрифтов приложения.

        Загружаемые шрифты:
            - MartianMono
            - Oranienbaum
        """

        font_names = ["MartianMono", "Oranienbaum"]

        for font_name in font_names:
            font_path = f"fonts/{font_name}.ttf"
            try:
                # Проверяем существование файла
                if not path.exists(font_path):
                    raise FileNotFoundError(
                        f"Файл шрифта не найден: {font_path}")

                font_id = QFontDatabase.addApplicationFont(font_path)

                if font_id == -1:
                    raise Exception(f"Путь: {font_path}\n\n"
                                    "Скорее всего шрифт повреждён")

            except Exception as e:
                QMessageBox.warning(
                    None,
                    "Ошибка загрузки шрифта",
                    f"Ошибка при загрузке шрифта {font_name}:\n{str(e)}"
                )

    def set_current_user(self, username):
        """Установка текущего пользователя и загрузка его данных"""
        self.current_user = username
        print("Начинаем поиск user_data")
        # Получаем данные пользователя через API
        user_data = self.client.get_current_user()
        print(user_data, "полученная user_data")
        if user_data:
            username = user_data['username']
            self.usernameLabel.setText(username)
            self.current_user = username
            # Загружаем аватар
            avatar_data = self.client.get_user_avatar(username)
            if avatar_data:
                self.set_avatar_image(avatar_data)
            else:
                self.set_default_avatar()
        else:
            self.usernameLabel.setText("кто здесь")

    def set_default_avatar(self):
        """Установка аватарки по умолчанию"""
        self.avatarLabel.setText("👤")

    def set_avatar_image(self, avatar_data):
        """Установка аватарки из данных БД"""
        try:
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(avatar_data)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    60,
                    60,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                rounded = QPixmap(pixmap.size())
                rounded.fill(Qt.GlobalColor.transparent)

                # Создаем круглую маску
                rounded = QPixmap(60, 60)
                rounded.fill(Qt.GlobalColor.transparent)

                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                # Создаем круглый клип
                painter.setBrush(Qt.GlobalColor.black)
                painter.drawEllipse(0, 0, 60, 60)

                # Устанавливаем композиционный режим для обрезки
                painter.setCompositionMode(
                    QPainter.CompositionMode.CompositionMode_SourceIn)

                # Рисуем изображение внутри круга
                painter.drawPixmap(0, 0, pixmap)
                painter.end()

                self.avatarLabel.setPixmap(rounded)
                self.avatarLabel.setText("")

            else:
                self.set_default_avatar()
        except BaseException:
            self.set_default_avatar()

    def logout(self):
        """Выход из аккаунта через API"""
        from PyQt6.QtCore import QSettings

        # Удаляем сохраненного пользователя
        settings = QSettings("TheatreApp", "TEAC_Auth")
        settings.remove("username")

        # Закрываем главное окно
        self.close()

        # Импортируем здесь, чтобы избежать циклической зависимости
        from auth_window import SimpleAuth
        auth_window = SimpleAuth()
        auth_window.setWindowTitle("«TEAC»")
        auth_window.setWindowIcon(QIcon("icon.png"))
        auth_window.show()

    def closeEvent(self, event):
        """Закрытие БД при выходе"""
        if hasattr(self, 'conn'):
            self.conn.close()
        event.accept()

    def setup_pages(self):
        """Инициализация всех страниц"""
        # Создаем страницы
        self.home_page = HomePage()
        self.shed_page = ShedPage()
        self.perf_page = PerfPage()
        self.addit_page = AdditPage()

        # Добавляем в stacked widget
        self.stackedWidget.addWidget(self.home_page)
        self.stackedWidget.addWidget(self.shed_page)
        self.stackedWidget.addWidget(self.perf_page)
        self.stackedWidget.addWidget(self.addit_page)

        # Сохраняем в словарь для быстрого доступа
        self.pages = {
            "home": self.home_page,
            "shed": self.shed_page,
            "perf": self.perf_page,
            "addit": self.addit_page
        }
        self.stackedWidget.setCurrentWidget(self.pages["home"])

    def setup_navigation(self):
        """Настройка навигации"""
        # Подключаем кнопки навигации в боковой панели
        self.shedButton.clicked.connect(lambda: self.switch_page("shed"))
        self.perfButton.clicked.connect(lambda: self.switch_page("perf"))
        self.additButton.clicked.connect(lambda: self.switch_page("addit"))

        self.buttons = {
            "shed": "Расписание",
            "perf": "Спектакли",
            "addit": "Дополнительные\nматериалы"
        }

    def setup_connections(self):
        """Подключение сигналов от страниц"""
        # Навигация с домашней страницы
        self.home_page.navigate_to.connect(self.switch_page)
        self.shed_page.navigate_to.connect(self.switch_page)
        self.perf_page.navigate_to.connect(self.switch_page)
        self.addit_page.navigate_to.connect(self.switch_page)

    def switch_page(self, page_name):
        """Переключение между страницами"""
        if page_name not in self.pages:
            return

        self.stackedWidget.setCurrentWidget(self.pages[page_name])
        self.current_page = page_name

        for name in self.pages:
            btn = getattr(self, f"{name}Button", None)
            if btn:
                btn.disconnect()
                if name == page_name and page_name != 'home':
                    btn.setText('На главную')
                    btn.clicked.connect(lambda: self.switch_page('home'))
                else:
                    btn.setText(self.buttons[name])
                    btn.clicked.connect(
                        lambda checked, n=name: self.switch_page(n))

    def update_part_check(self):
        """Обновление состояния чекбокса через API"""
        if not self.current_user:
            print("No current user for participation check")
            return

        print(f"Updating participation for user: {self.current_user}")

        is_part = self.client.get_participation(self.current_user)
        print(f"Participation result: {is_part}")

        if is_part is not None:
            self.partCheck.setChecked(is_part)
            print(f"Checkbox set to: {is_part}")
        else:
            print("Failed to get participation status")

    def is_part_check(self, checked):
        """Обновление статуса участия через API"""
        if not self.current_user:
            print("No current user for participation update")
            return

        print(f"Updating participation to: {checked} for user: {self.current_user}")
        success = self.client.update_participation(checked)

        if success:
            print("Participation updated successfully")
        else:
            print("Failed to update participation")
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить статус участия")

    def change_avatar(self):
        """Смена аватарки через API"""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import QBuffer, QByteArray, QIODevice

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аватарку",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Конвертируем в байты для API
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                pixmap.save(buffer, "PNG")
                avatar_data = byte_array.data()

                # Сохраняем через API
                success = self.client.update_avatar(avatar_data)
                if success:
                    self.set_avatar_image(avatar_data)
