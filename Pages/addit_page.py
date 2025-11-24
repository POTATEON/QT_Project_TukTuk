import os
import sqlite3
import sys
from datetime import datetime

from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (QFileDialog,
                             QMessageBox, QAbstractItemView)

from .base_page import BasePage
from simple_api_client import SimpleTheatreClient

class AdditPage(BasePage):
    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("ui/addit_page.ui", parent)
        self.client = SimpleTheatreClient()  # Добавлен клиент API
        self.current_user = None
        self.setup_export()
        self.init_db()
        # Инициализация модели для списка файлов
        self.model = QStandardItemModel()
        self.listView.setModel(self.model)

        # Настройка списка файлов
        self.listView.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.listView.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)

        # Подключение сигналов кнопок
        self.shedButton_2.clicked.connect(self.add_file)
        self.shedButton_3.clicked.connect(self.delete_file)

        # Загрузка существующих файлов через API при запуске
        self.load_files_from_api()

        # Дополнительные настройки UI
        self.setup_ui_enhancements()

    def init_db(self):
        """Инициализация базы данных для занятий через API"""
        user_data = self.client.get_current_user()
        if user_data:
            self.current_user = user_data['role']

    def load_files_from_api(self):
        """Загрузка списка файлов через API"""
        try:
            files = self.client.get_additional_files()
            for file_data in files:
                file_name = file_data['file_name']
                file_path = file_data['file_path']
                file_size = file_data['file_size']
                file_extension = file_data['file_extension']

                # Проверяем, существует ли файл
                if os.path.exists(file_path):
                    item = QStandardItem(f"{file_name} ({file_size})")
                    item.setData(file_path, Qt.ItemDataRole.UserRole)
                    item.setToolTip(
                        f"Путь: {file_path}\nРазмер: {file_size}\nРасширение: {file_extension}")
                    self.model.appendRow(item)
                else:
                    # Файл не существует, удаляем через API
                    self.client.delete_additional_file(file_path)

        except Exception as e:
            print(f"Ошибка загрузки файлов: {e}")

    def setup_ui_enhancements(self):
        """Дополнительные улучшения интерфейса"""

        # Добавление контекстного меню для списка файлов
        self.listView.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.listView.customContextMenuRequested.connect(
            self.show_context_menu)

        # Двойной клик для открытия файла
        self.listView.doubleClicked.connect(self.open_file)
        print(self.current_user)
        print("segsegsegeges")

        if self.current_user != 'organizer':
            self.shedButton_2.hide()
            self.shedButton_3.hide()
        print("d")

    def add_file(self):
        """Добавление файла через диалог выбора"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            "Выберите файлы для добавления",
            "",
            "Все файлы (*);;Текстовые файлы (*.txt);;Изображения (*.png *.jpg *.jpeg);;Документы (*.pdf *.doc *.docx)"
        )

        if file_paths:
            for file_path in file_paths:
                self.add_file_to_list(file_path)
            # Сохраняем через API
            self.save_files_to_api()

    def save_files_to_api(self):
        """Сохранение всех файлов из списка через API"""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                file_size = self.get_file_size(file_path)
                file_extension = os.path.splitext(file_path)[1]
                last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                success = self.client.create_additional_file(
                    file_name, file_path, file_size, file_extension, last_modified.isoformat()
                )
                if not success:
                    print(f"Не удалось сохранить файл {file_name} через API")

    def add_file_to_list(self, file_path):
        """Добавление файла в список"""
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            file_size = self.get_file_size(file_path)
            file_extension = os.path.splitext(file_path)[1]

            # Проверка на дубликаты в модели
            for i in range(self.model.rowCount()):
                item = self.model.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == file_path:
                    return

            # Создание элемента с информацией о файле
            item = QStandardItem(f"{file_name} ({file_size})")
            item.setData(file_path, Qt.ItemDataRole.UserRole)  # Сохраняем полный путь
            item.setToolTip(f"Путь: {file_path}\nРазмер: {file_size}\nРасширение: {file_extension}")

            self.model.appendRow(item)

    def delete_file(self):
        """Удаление выбранного файла из списка через API"""
        selected_indexes = self.listView.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(
                self, "Внимание", "Пожалуйста, выберите файл для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить выбранный файл из списка?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for index in selected_indexes:
                file_path = self.model.itemFromIndex(
                    index).data(Qt.ItemDataRole.UserRole)
                # Удаляем через API
                success = self.client.delete_additional_file(file_path)
                if success:
                    # Удаляем из модели
                    self.model.removeRow(index.row())
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить файл через API")

    def open_file(self, index):
        """Открытие файла при двойном клике"""
        if index.isValid():
            file_path = self.model.itemFromIndex(
                index).data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                try:
                    if sys.platform == "win32":
                        os.startfile(file_path)
                    elif sys.platform == "darwin":  # macOS
                        os.system(f'open "{file_path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{file_path}"')
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Не удалось открыть файл: {
                            str(e)}")

    def show_context_menu(self, position):
        """Показ контекстного меню для списка файлов"""
        menu = QtWidgets.QMenu()

        open_action = menu.addAction("Открыть файл")
        if self.current_user == 'organizer':
            delete_action = menu.addAction("Удалить из списка")
            menu.addSeparator()
        else:
            delete_action = "None"

        info_action = menu.addAction("Информация о файле")

        action = menu.exec(self.listView.mapToGlobal(position))

        selected_index = self.listView.currentIndex()
        if not selected_index.isValid():
            return

        file_path = self.model.itemFromIndex(
            selected_index).data(Qt.ItemDataRole.UserRole)

        if action == open_action:
            self.open_file(selected_index)
        elif action == delete_action:
            self.delete_file()
        elif action == info_action:
            self.show_file_info(file_path)

    def show_file_info(self, file_path):
        """Показ информации о файле"""
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            file_size = self.get_file_size(file_path)
            file_extension = os.path.splitext(file_path)[1]
            created_time = os.path.getctime(file_path)
            modified_time = os.path.getmtime(file_path)

            created_str = datetime.fromtimestamp(
                created_time).strftime("%Y-%m-%d %H:%M:%S")
            modified_str = datetime.fromtimestamp(
                modified_time).strftime("%Y-%m-%d %H:%M:%S")

            info_text = f"""
            Информация о файле:

            Имя: {file_name}
            Размер: {file_size}
            Расширение: {file_extension}
            Путь: {file_path}
            Создан: {created_str}
            Изменен: {modified_str}
            """

            QMessageBox.information(self, "Информация о файле", info_text)

    def show_file_db_info(self, file_path):
        """Показ информации о файле из базы данных"""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT file_name, file_path, file_size, file_extension, created_date, last_modified
                FROM additional_files
                WHERE file_path = ?
            ''', (file_path,))

            file_data = cursor.fetchone()

            if file_data:
                file_name, file_path, file_size, file_extension, created_date, last_modified = file_data

                info_text = f"""
                Информация из базы данных:

                Имя: {file_name}
                Размер: {file_size}
                Расширение: {file_extension}
                Путь: {file_path}
                Добавлен в БД: {created_date}
                Последнее изменение: {last_modified}
                """

                QMessageBox.information(self, "Информация из БД", info_text)
            else:
                QMessageBox.warning(
                    self, "Внимание", "Файл не найден в базе данных")

        except sqlite3.Error as e:
            QMessageBox.critical(
                self, "Ошибка", f"Ошибка получения данных из БД: {e}")

    def get_file_size(self, file_path):
        """Получение размера файла в читаемом формате"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.1f} GB"
        except BaseException:
            return "Неизвестно"
        
    def setup_export(self):
        """Настройка экспорта"""
        self.exportButton.clicked.connect(self.export_to_csv)

    def export_to_csv(self):
        """Экспорт данных в CSV"""
        try:
            from datetime import datetime
            import csv
            
            # Получаем данные для экспорта
            data = self.get_export_data()
            if not data:
                QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
                return
                
            # Создаем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{self.__class__.__name__}_{timestamp}.csv"
            
            # Сохраняем в CSV
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                if data:
                    writer = csv.DictWriter(file, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    
            QMessageBox.information(self, "Успех", f"Данные экспортированы в {filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def get_export_data(self):
        """Данные для экспорта файлов"""
        data = []
        for row in range(self.filesTable.rowCount()):
            data.append({
                "file_name": self.filesTable.item(row, 0).text(),
                "file_size": self.filesTable.item(row, 1).text(),
                "file_type": self.filesTable.item(row, 2).text(),
                "uploaded_by": self.filesTable.item(row, 3).text()
            })
        return data