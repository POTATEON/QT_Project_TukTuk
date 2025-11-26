from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem, QMessageBox

from .base_page import BasePage
from simple_api_client import SimpleTheatreClient  # Добавлен импорт


class HomePage(BasePage):
        navigate_to = pyqtSignal(str)

        def __init__(self, parent=None):
            super().__init__("ui/home_page.ui", parent)
            self.client = SimpleTheatreClient()  # Добавлен клиент API
            self.setup_displays()
            self.setup_export()

        def showEvent(self, event):
            self.setup_displays()
            super().showEvent(event)

        def setup_displays(self):
            # Получаем информацию о ближайшем занятии через API
            lessons = ""
            lessons = self.client.get_lessons()
            if lessons:
                # Берем первое занятие (предполагаем, что API возвращает отсортированный список)
                lesson = lessons[0]
                title = lesson['title']
                time = lesson['time']
                date = lesson['date']

                # Парсим дату
                day, month, year = date.split("-")
                months = [
                    "января", "февраля", "марта", "апреля", "мая", "июня",
                    "июля", "августа", "сентября", "октября", "ноября", "декабря"
                ]

                date_text = """
                <div align="center" style="line-height: 0.7;">
                    <span style="
                        font-size: 48pt;
                        font-weight: bold;
                        color: #fdefc8;
                        font-family: 'Martian Mono Condensed';
                    ">{day}</span><br>

                    <span style="
                        font-size: 12pt;
                        color: #fdefc8;
                        font-family: 'Martian Mono Condensed';
                    ">{month}</span><br>

                    <span style="
                        font-size: 16pt;
                        color: #fdefc8;
                        font-family: 'Martian Mono Condensed';
                    ">{time}</span><br>
                </div>
                """

                lesson_text = """
                <div style="
                    font-family: 'Oranienbaum';
                    font-size: 42pt;
                    color: #fdefc8;
                    text-align: left;
                    line-height: 1;
                ">
                    {title}<br>
                </div>
                """

                self.dateDisplay.setHtml(date_text.format(
                    day=day, month=months[int(month) - 1], time=time))
                self.lessonDisplay.setHtml(lesson_text.format(title=title))

            self.listWidget.clear()

            # Получаем организаторов через API
            organizers = self.client.get_organizers()
            for organizer in organizers:
                name = organizer['username']
                avatar_data = organizer.get('avatar')
                custom_item = CustomListItem(name, avatar_data)
                item = QListWidgetItem()
                item.setSizeHint(custom_item.sizeHint())
                self.listWidget.addItem(item)
                self.listWidget.setItemWidget(item, custom_item)

            try:
                participants = self.client.get_participants()
                self.participantsList.clear()
                
                for participant in participants:
                    item = f"{participant['username']}"
                    self.participantsList.addItem(item)
                        
            except Exception as e:
                print(f"Ошибка загрузки участников: {e}")

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
            return [{"participant": item.text().replace("👤 ", "")} 
                    for item in range(self.participantsList.count())]
        
class CustomListItem(QWidget):
    def __init__(self, name, avatar_data):
        super().__init__()

        layout = QHBoxLayout()

        # Создаем метку для отображения имени
        label = QLabel(name)
        label.setStyleSheet(
            "font-family: 'Martian Mono Condensed'; color: #fdefc8; font-size: 14px;")

        # Создаем метку для отображения аватара
        mate = QLabel()

        try:
            if avatar_data:
                from PyQt6.QtGui import QPixmap
                from PyQt6.QtCore import QByteArray

                pixmap = QPixmap()

                # Если avatar_data - это base64 строка
                if isinstance(avatar_data, str):
                    # Декодируем base64 строку в байты
                    avatar_bytes = QByteArray.fromBase64(avatar_data.encode())
                    success = pixmap.loadFromData(avatar_bytes)
                else:
                    # Если это уже байты
                    success = pixmap.loadFromData(avatar_data)

                if success and not pixmap.isNull():
                    # Масштабируем и делаем круглым
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

                    mate.setPixmap(rounded)
                    mate.setText("")
                else:
                    mate.setText("👤")  # Иконка вместо текста
            else:
                mate.setText("👤")  # Иконка если нет аватара

        except Exception as e:
            print(f"Error loading avatar for {name}: {e}")
            mate.setText("👤")  # Иконка при ошибке

        layout.addWidget(mate)
        layout.addWidget(label)
        layout.addStretch()

        self.setLayout(layout)
