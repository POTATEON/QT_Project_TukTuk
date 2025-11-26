from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QListWidgetItem, QMessageBox, QDialog, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, \
    QHBoxLayout, QListWidget, QMenu

from .base_page import BasePage
from simple_api_client import SimpleTheatreClient  # Добавлен импорт


class PerfPage(BasePage):
    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("ui/perf_page.ui", parent)
        self.client = SimpleTheatreClient()  # Добавлен клиент API
        self.setup_export()
        self.current_performance = None
        self.current_role = None
        self.current_application = None
        self.current_user = None
        self.user_name = None
        self.init_db()
        self.setupUi()
        self.load_data()

        # self.applyBtn.setEnabled(True)

    def setupUi(self):
        """Настройка UI после загрузки .ui файла"""
        try:
            # Устанавливаем режим выделения
            self.performancesList.setSelectionMode(
                QListWidget.SelectionMode.SingleSelection)
            self.rolesList.setSelectionMode(
                QListWidget.SelectionMode.SingleSelection)
            self.applicationsList.setSelectionMode(
                QListWidget.SelectionMode.SingleSelection)

            # Включаем контекстное меню
            self.performancesList.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            self.rolesList.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            self.applicationsList.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)

            self.performancesList.customContextMenuRequested.connect(
                self.show_list_context_menu)
            self.rolesList.customContextMenuRequested.connect(
                self.show_list_context_menu)
            self.applicationsList.customContextMenuRequested.connect(
                self.show_list_context_menu)

            # Подключаем сигналы
            self.connect_signals()

            # Обновляем видимость кнопок по роли
            self.update_ui_for_role()
        except Exception as e:
            print(f"Ошибка в setup_ui: {e}")

    def show_list_context_menu(self, position):
        """Показ контекстного меню для списков"""
        sender = self.sender()
        menu = QMenu(self)

        clear_selection_action = menu.addAction("Снять выделение")
        action = menu.exec(sender.mapToGlobal(position))

        if action == clear_selection_action:
            sender.clearSelection()
            sender.setCurrentRow(-1)

            # Обновляем состояние в зависимости от того, какой список
            if sender == self.performancesList:
                self.current_performance = None  # ДОБАВЛЕНО
                self.on_performance_selected(-1)
            elif sender == self.rolesList:
                self.current_role = None  # ДОБАВЛЕНО
                self.on_role_selected(-1)
            elif sender == self.applicationsList:
                self.current_application = None  # ДОБАВЛЕНО
                self.on_application_selected(-1)

    def connect_signals(self):
        """Подключение сигналов к слотам"""
        try:
            self.performancesList.currentRowChanged.connect(
                self.on_performance_selected)
            self.rolesList.currentRowChanged.connect(self.on_role_selected)
            self.applicationsList.currentRowChanged.connect(
                self.on_application_selected)
            self.deletePerformanceBtn.clicked.connect(self.delete_performance)
            self.deleteRoleBtn.clicked.connect(self.delete_role)
            self.addPerformanceBtn.clicked.connect(
                self.show_add_performance_dialog)
            self.addRoleBtn.clicked.connect(self.show_add_role_dialog)
            self.applyBtn.clicked.connect(self.apply_for_role)

            self.approveBtn.clicked.connect(self.approve_application)
            self.rejectBtn.clicked.connect(self.reject_application)
        except Exception as e:
            print(f"Ошибка в connect_signals: {e}")

    def init_db(self):
        """Инициализация базы данных - теперь через API"""
        # Получаем текущего пользователя через API
        user_data = self.client.get_current_user()
        print(user_data, "для perf.page")
        if user_data:
            self.current_user = user_data['role']
            self.user_name = user_data['username']

    def load_data(self):
        """Загрузка всех данных через API"""
        self.load_performances()
        self.load_applications()

    def load_performances(self):
        """Загрузка списка спектаклей через API"""
        self.performancesList.clear()
        performances = self.client.get_performances()

        for perf in performances:
            perf_id = perf['id']
            title = perf['title']
            date = perf['performance_date']
            item = QListWidgetItem(f"{title}\n{date}")
            item.setData(Qt.ItemDataRole.UserRole, perf_id)
            self.performancesList.addItem(item)

    def load_roles(self, performance_id):
        """Загрузка ролей для спектакля через API"""
        self.rolesList.clear()
        roles = self.client.get_roles(performance_id)

        for role in roles:
            role_id = role['id']
            name = role['role_name']
            desc = role['description']
            status = role['status']
            user = role['assigned_user']

            icon = "" if status == 'assigned' else "⏳" if status == 'open' else "❌"
            text = f"{name}\n"
            if user:
                text += f"\nБудет играть - {user}"
            if desc:
                text += f"\n{desc}\n"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, role_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, status)
            self.rolesList.addItem(item)

    def load_cover_image(self):
        """Загрузка обложки спектакля"""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QPixmap

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите обложку",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            pixmap = QPixmap(file_path)
            # Масштабируем изображение до разумных размеров
            pixmap = pixmap.scaled(
                272,
                100,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            return pixmap
        else:
            print("segwe")
            return None

    def load_applications(self):
        """Загрузка заявок через API"""
        self.applicationsList.clear()
        applications = self.client.get_applications()

        for app in applications:
            app_id = app['id']
            role = app['role_name']
            perf = app['title']

            if self.current_user == "organizer":
                user = app['username']
                date = app['applied_at']
                item = QListWidgetItem(f"{role}\n{perf}\n{user}\n{date}")
            else:
                status = app['status']
                date = app['applied_at']
                status_text = "Ожидает" if status == 'pending' else "Одобрена" if status == 'approved' else "Отклонена"
                item = QListWidgetItem(f"{role}\n{perf}\n{status_text}\n{date}")

            item.setData(Qt.ItemDataRole.UserRole, app_id)
            self.applicationsList.addItem(item)

    def on_performance_selected(self, row):
        if row == -1:
            return

        item = self.performancesList.item(row)
        perf_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_performance = perf_id

        # Загрузка деталей через API
        performance_data = self.client.get_performance(perf_id)
        if performance_data:
            title = performance_data['title']
            desc = performance_data['description']
            date = performance_data['performance_date']
            cover_image = performance_data.get('cover_image')

            self.detailsTitle.setText(title)
            self.performanceDate.setText(f"{date}")
            self.performanceDescription.setText(f"{desc or 'Нет описания'}")

            if hasattr(self, 'coverLabel') and cover_image:
                # Конвертируем base64 обратно в QPixmap
                from PyQt6.QtGui import QPixmap
                from PyQt6.QtCore import QByteArray
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray.fromBase64(cover_image.encode()))
                pixmap = pixmap.scaled(
                    272,
                    100,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                self.coverLabel.setPixmap(pixmap)
                self.coverLabel.setVisible(True)
            else:
                self.coverLabel.setVisible(False)

        self.load_roles(perf_id)

    def on_role_selected(self, row):
        if row == -1:
            return

        item = self.rolesList.item(row)
        self.current_role = item.data(Qt.ItemDataRole.UserRole)

    def on_application_selected(self, row):
        if row == -1 or self.current_user != "organizer":
            self.approveBtn.setEnabled(False)
            self.rejectBtn.setEnabled(False)
            return

        self.approveBtn.setEnabled(True)
        self.rejectBtn.setEnabled(True)
        self.current_application = self.applicationsList.item(
            row).data(Qt.ItemDataRole.UserRole)

    def apply_for_role(self):
        """Подача заявки на роль через API"""
        if not self.current_role:
            return

        success = self.client.apply_for_role(self.current_role)
        if success:
            QMessageBox.information(self, "Успех", "Заявка подана!")
            self.load_applications()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось подать заявку")

    def approve_application(self):
        """Одобрение заявки через API"""
        if not self.current_application:
            return

        # Получаем информацию о заявке, чтобы узнать username заявителя
        applications = self.client.get_applications()
        current_app = next((app for app in applications if app['id'] == self.current_application), None)

        if not current_app:
            QMessageBox.warning(self, "Ошибка", "Заявка не найдена")
            return

        # Получаем username заявителя из заявки
        applicant_username = current_app.get('username')  # для организатора
        if not applicant_username:
            # Если username нет в данных, используем поле из заявки
            applicant_username = current_app.get('user') or current_app.get('applicant')

        if not applicant_username:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить заявителя")
            return

        # Передаем username заявителя в метод approve
        success = self.client.approve_application(self.current_application, applicant_username)
        if success:
            QMessageBox.information(self, "Успех", "Заявка одобрена!")
            self.load_roles(self.current_performance)
            self.load_applications()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось одобрить заявку")

    def reject_application(self):
        """Отклонение заявки через API"""
        if not self.current_application:
            return

        success = self.client.reject_application(self.current_application)
        if success:
            QMessageBox.information(self, "Успех", "Заявка отклонена")
            self.load_applications()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось отклонить заявку")

    def show_add_performance_dialog(self):
        dialog = AddDialog("спектакль", self.add_performance)
        if dialog.exec():
            self.load_performances()

    def show_add_role_dialog(self):
        if not self.current_performance:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите спектакль")
            return

        dialog = AddDialog("роль", self.add_role)
        if dialog.exec():
            self.load_roles(self.current_performance)

    def add_performance(self, title, description, date):
        """Добавление спектакля с обложкой через API"""
        cover_pixmap = self.load_cover_image()
        cover_data = None

        if cover_pixmap and not cover_pixmap.isNull():
            # Конвертируем QPixmap в байты для API
            from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            cover_pixmap.save(buffer, "PNG")
            cover_data = byte_array.data()

        success = self.client.create_performance(title, description, date, cover_data)
        if not success:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить спектакль")

    def delete_performance(self):
        """Удаление выбранного спектакля с обработкой предупреждений"""
        if not self.current_performance:
            QMessageBox.warning(
                self, "Ошибка", "Сначала выберите спектакль для удаления")
            return

        # Получаем информацию о спектакле для подтверждения
        performance_data = self.client.get_performance(self.current_performance)
        if not performance_data:
            QMessageBox.warning(self, "Ошибка", "Спектакль не найден")
            return

        perf_title = performance_data['title']

        # Проверяем есть ли назначенные роли через API
        roles = self.client.get_roles(self.current_performance)
        assigned_roles = sum(1 for role in roles if role.get('assigned_user'))

        # Формируем текст подтверждения
        confirmation_text = f"Вы уверены, что хотите удалить спектакль '{perf_title}'?"
        if assigned_roles > 0:
            confirmation_text += f"\n⚠️ ВНИМАНИЕ: {assigned_roles} роль(ей) уже назначена пользователям!"

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            confirmation_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.client.delete_performance(self.current_performance)

            if result.get('success'):
                # Показываем дополнительное предупреждение если были назначенные роли
                if result.get('warning'):
                    QMessageBox.warning(self, "Внимание", result['warning'])
                else:
                    QMessageBox.information(self, "Успех", result['message'])

                # Сбрасываем текущий выбор
                self.current_performance = None
                self.current_role = None
                self.current_application = None

                # Обновляем интерфейс
                self.load_performances()
                self.rolesList.clear()
                self.applicationsList.clear()
                self.detailsTitle.setText("Выберите спектакль")
                self.performanceDate.setText("")
                self.performanceDescription.setText("")

                # Очищаем обложку
                if hasattr(self, 'coverLabel'):
                    self.coverLabel.setPixmap(QPixmap())
                    self.coverLabel.setText("Нет обложки")
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить спектакль: {result.get('error', 'Unknown error')}")

    def add_role(self, title, description, date=None):
        """Добавление роли через API"""
        success = self.client.create_role(self.current_performance, title, description)
        if not success:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить роль")

    def delete_role(self):
        """Удаление выбранной роли с обработкой предупреждений"""
        if not self.current_role:
            QMessageBox.warning(
                self, "Ошибка", "Сначала выберите роль для удаления")
            return

        # Получаем информацию о роли для подтверждения
        roles = self.client.get_roles(self.current_performance)
        role_info = next((role for role in roles if role['id'] == self.current_role), None)

        if not role_info:
            QMessageBox.warning(self, "Ошибка", "Роль не найдена")
            return

        role_name = role_info['role_name']
        assigned_user = role_info['assigned_user']

        # Формируем текст подтверждения
        confirmation_text = f"Вы уверены, что хотите удалить роль '{role_name}'?"
        if assigned_user:
            confirmation_text += f"\n⚠️ ВНИМАНИЕ: Роль назначена пользователю: {assigned_user}"

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            confirmation_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.client.delete_role(self.current_role)

            if result.get('success'):
                # Показываем дополнительное предупреждение если роль была назначена
                if result.get('warning'):
                    QMessageBox.warning(self, "Внимание", result['warning'])
                else:
                    QMessageBox.information(self, "Успех", result['message'])

                # Сбрасываем текущий выбор
                self.current_role = None

                # Обновляем интерфейс
                self.load_roles(self.current_performance)
                self.load_applications()
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось удалить роль: {result.get('error', 'Unknown error')}")
    
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
        """Данные для экспорта спектаклей"""
        data = []
        for row in range(self.performancesList.count()):
            item = self.performancesList.item(row)
            if item:
                # Предполагаем, что текст в формате "Название (Дата)"
                text = item.text()
                parts = text.split(' (')
                title = parts[0]
                date = parts[1].replace(')', '') if len(parts) > 1 else ""
                
                data.append({
                    "title": title,
                    "date": date,
                    "roles_count": "0"  # Можно добавить подсчет ролей
                })
        return data

    def set_user_role(self, role):
        """Установка роли пользователя"""
        self.current_user = role
        self.update_ui_for_role()

    def update_ui_for_role(self):
        """Обновление UI по роли пользователя"""
        is_organizer = self.current_user == "organizer"
        self.addPerformanceBtn.setVisible(is_organizer)
        self.addRoleBtn.setVisible(is_organizer)
        self.deletePerformanceBtn.setVisible(is_organizer)
        self.deleteRoleBtn.setVisible(is_organizer)
        self.approveBtn.setVisible(is_organizer)
        self.rejectBtn.setVisible(is_organizer)

    def on_page_show(self):
        self.load_data()

    def closeEvent(self, event):
        if hasattr(self, 'conn'):
            self.conn.close()
        super().closeEvent(event)


class AddDialog(QDialog):
    """Универсальный диалог добавления"""

    def __init__(self, item_type, add_callback):
        super().__init__()
        self.add_callback = add_callback
        self.item_type = item_type
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Добавить {self.item_type}")
        self.setFixedSize(300, 300)
        self.setStyleSheet(
            "background-color: rgba(113, 37, 37, 1); color: #fdefc8; font-family: 'Martian Mono';")

        layout = QVBoxLayout(self)

        # Поля ввода
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(f"Название")
        self.title_input.setStyleSheet(
            "background-color: rgba(50, 15, 15, 1); border: 2px solid #8B4513; border-radius: 10px; padding: 8px; color: #fdefc8;")
        layout.addWidget(self.title_input)

        if self.item_type == "спектакль":
            from PyQt6.QtWidgets import QLabel, QDateEdit
            from PyQt6.QtCore import QDate

            date_label = QLabel("Дата спектакля:")
            date_label.setStyleSheet("color: #fdefc8;")
            layout.addWidget(date_label)

            self.date_input = QDateEdit()
            self.date_input.setDate(QDate.currentDate().addDays(30))
            self.date_input.setCalendarPopup(True)
            self.date_input.setStyleSheet(
                "background-color: rgba(50, 15, 15, 1); border: 2px solid #8B4513; border-radius: 10px; padding: 8px; color: #fdefc8;")
            layout.addWidget(self.date_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(f"Описание")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(
            "background-color: rgba(50, 15, 15, 1); border: 2px solid #8B4513; border-radius: 10px; padding: 8px; color: #fdefc8;")
        layout.addWidget(self.desc_input)

        # Кнопки
        btn_layout = QHBoxLayout()  # ДОБАВЛЕНО: использование QHBoxLayout
        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet(
            "background-color: #2E8B57; color: #fdefc8; border: none; border-radius: 15px; padding: 8px 15px;")
        add_btn.clicked.connect(self.add_item)
        btn_layout.addWidget(add_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(
            "background-color: #8B4513; color: #fdefc8; border: none; border-radius: 15px; padding: 8px 15px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def add_item(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(
                self, "Ошибка", f"Введите название для объекта {
                    self.item_type}")
            return

        date = None
        if self.item_type == "спектакль" and hasattr(self, 'date_input'):
            date = self.date_input.date().toString("yyyy-dd-MM")

        self.add_callback(title, self.desc_input.toPlainText().strip(), date)
        self.accept()
