from PyQt6 import QtWidgets
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtWidgets import (QCalendarWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QMessageBox,
                             QLabel, QFrame)

from simple_api_client import SimpleTheatreClient  # Добавлен импорт

from .base_page import BasePage


class CalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lessons_data = {}
        self.setMouseTracking(True)

    def set_lessons_data(self, lessons_data):
        """Устанавливает данные о занятиях"""
        self.lessons_data = lessons_data
        self.updateCells()

    def paintCell(self, painter, rect, date):
        """Переопределяем отрисовку ячеек календаря"""
        super().paintCell(painter, rect, date)

        date_str = date.toString("dd-MM-yyyy")
        if date_str in self.lessons_data:
            # Рисуем индикатор занятий
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Красный кружок с количеством занятий
            lessons_count = len(self.lessons_data[date_str])
            painter.setBrush(QBrush(QColor(255, 0, 0, 200)))
            painter.setPen(QPen(QColor(255, 255, 255)))

            circle_radius = 6
            circle_x = rect.right() - circle_radius - 3
            circle_y = rect.top() + circle_radius + 3

            # Рисуем кружок
            painter.drawEllipse(
                circle_x - circle_radius,
                circle_y - circle_radius,
                circle_radius * 2,
                circle_radius * 2)

            # Рисуем количество занятий
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 6, QFont.Weight.Bold))
            painter.drawText(circle_x - 4, circle_y + 2, str(lessons_count))


class LessonPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self.setFrameStyle(QFrame.Shape.Box)
        # self.setLineWidth(2)
        self.current_lesson_index = 0
        self.current_lessons = []
        self.current_date = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setStyleSheet("""
                    QFrame {
                        background-color: rgba(64, 20, 20, 1);
                        border-radius: 15px;
                        padding: 5px;
                        min-width: 365px;
                        border: none;
                    }
                    QFrame::window {
                        border-radius: 15px;
                    }
                    """)
        # Заголовок с навигацией
        header_layout = QHBoxLayout()

        self.nav_label = QLabel()
        self.nav_label.setStyleSheet(
            "font-family: 'Martian Mono Condensed'; font-size: 11px; color:#fdefc8;")
        header_layout.addWidget(self.nav_label)

        header_layout.addStretch()

        # Кнопка закрытия
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)

        layout.addLayout(header_layout)

        # Навигация между занятиями
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Пред.")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                font-family: "Martian Mono Condensed";
                font-size: 10px;
                color:#fdefc8;
                border-radius: 15px;
                background-color: rgba(113, 37, 37, 1);
                padding: 10px;
            }

            QPushButton:hover {
                    background-color: rgba(120, 41, 41, 1);
             }
            QPushButton:pressed {
                    background-color: rgba(85, 29, 29, 1);
                }
        """)
        self.prev_btn.clicked.connect(self.show_previous_lesson)
        nav_layout.addWidget(self.prev_btn)

        nav_layout.addStretch()

        self.next_btn = QPushButton("След. ▶")
        self.next_btn.setStyleSheet("""
            QPushButton {
                font-family: "Martian Mono Condensed";
                font-size: 10px;
                color:#fdefc8;
                border-radius: 15px;
                background-color: rgba(113, 37, 37, 1);
                padding: 10px;
            }

            QPushButton:hover {
                    background-color: rgba(120, 41, 41, 1);
             }
            QPushButton:pressed {
                    background-color: rgba(85, 29, 29, 1);
                }
        """)
        self.next_btn.clicked.connect(self.show_next_lesson)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        # Заголовок занятия
        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "font-family: 'Martian Mono Condensed'; font-size: 13px; color: #fdefc8; margin: 5px 0;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Детали занятия
        self.details_label = QLabel()
        self.details_label.setStyleSheet(
            "font-size: 11px; color: #fdefc8; font-family: 'Martian Mono Condensed';")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)

        # Кнопка удаления
        self.delete_btn = QPushButton("Удалить занятие")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                font-family: "Martian Mono Condensed";
                font-size: 10px;
                color:#fdefc8;
                border-radius: 15px;
                background-color: rgba(113, 37, 37, 1);
                padding: 10px;
            }

            QPushButton:hover {
                    background-color: rgba(120, 41, 41, 1);
             }
            QPushButton:pressed {
                    background-color: rgba(85, 29, 29, 1);
                }
        """)
        self.delete_btn.clicked.connect(self.delete_current_lesson)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    def show_lessons(self, lessons, date, pos):
        """Показывает занятия для выбранной даты"""
        if not lessons:
            self.hide()
            return

        self.current_lessons = lessons
        self.current_date = date
        self.current_lesson_index = 0

        self.update_navigation()
        self.show_lesson_at_index()
        self.move(pos)
        self.show()
        self.adjustSize()

    def show_lesson_at_index(self):
        """Показывает занятие по текущему индексу"""
        if not self.current_lessons:
            return

        lesson_data = self.current_lessons[self.current_lesson_index]
        lesson_id, title, description, time, location, date = lesson_data

        # Обновляем заголовок
        self.title_label.setText(f"🎭 {title}")

        # Обновляем детали
        details = []
        if time:
            details.append(f"⏰ <b>Время:</b> {time}")
        if location:
            details.append(f"📍 <b>Место:</b> {location}")
        if description:
            details.append(f"📝 <b>Описание:</b> {description}")

        if not details:
            details.append("ℹ️ <i>Нет дополнительной информации</i>")

        self.details_label.setText("<br>".join(details))

        # Сохраняем ID текущего занятия для удаления
        self.current_lesson_id = lesson_id

    def update_navigation(self):
        """Обновляет состояние кнопок навигации"""
        total_lessons = len(self.current_lessons)

        # Обновляем label навигации
        self.nav_label.setText(
            f"{self.current_lesson_index + 1}/{total_lessons}")

        # Обновляем кнопки
        self.prev_btn.setEnabled(self.current_lesson_index > 0)
        self.next_btn.setEnabled(self.current_lesson_index < total_lessons - 1)

    def show_previous_lesson(self):
        """Показывает предыдущее занятие"""
        if self.current_lesson_index > 0:
            self.current_lesson_index -= 1
            self.update_navigation()
            self.show_lesson_at_index()
            self.adjustSize()

    def show_next_lesson(self):
        """Показывает следующее занятие"""
        if self.current_lesson_index < len(self.current_lessons) - 1:
            self.current_lesson_index += 1
            self.update_navigation()
            self.show_lesson_at_index()
            self.adjustSize()

    def delete_current_lesson(self):
        """Удаляет текущее занятие"""
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            "Вы уверены, что хотите удалить это занятие?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.parent(), 'delete_lesson_by_id'):
                self.parent().delete_lesson_by_id(self.current_lesson_id, self.current_date)


class ShedPage(BasePage):
    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("ui/shed_page.ui", parent)
        self.client = SimpleTheatreClient()  # Добавлен клиент API
        self.current_user = ""
        self.init_db()

        self.setup_calendar()
        self.popup = LessonPopup(self)
        self.add_btn.clicked.connect(self.add_lesson)
        self.load_lessons_data()
        is_organizer = self.current_user == "organizer"
        if not is_organizer:
            self.form_container.setVisible(is_organizer)
            self.calendarWidget.move(150, 0)

    def init_db(self):
        """Инициализация базы данных для занятий через API"""
        user_data = self.client.get_current_user()
        if user_data:
            self.current_user = user_data['role']
    def setup_calendar(self):
        """Настройка календаря"""

        # Заменяем стандартный календарь на наш кастомный
        old_calendar = self.calendarWidget
        self.calendarWidget = CalendarWidget(self)
        self.calendarWidget.setGeometry(old_calendar.geometry())
        self.calendarWidget.setStyleSheet(old_calendar.styleSheet())
        self.calendarWidget.setGridVisible(False)
        self.calendarWidget.setNavigationBarVisible(True)
        self.calendarWidget.setDateEditEnabled(True)
        self.calendarWidget.setVerticalHeaderFormat(
            QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        # Подключаем обработчики
        self.calendarWidget.clicked.connect(self.on_date_clicked)

        # Удаляем старый календарь
        old_calendar.deleteLater()

    def load_lessons_data(self):
        """Загружает данные о занятиях для календаря через API"""
        try:
            lessons = self.client.get_lessons()

            # Группируем занятия по датам
            lessons_by_date = {}
            for lesson in lessons:
                date = lesson['date']
                if date not in lessons_by_date:
                    lessons_by_date[date] = []
                lessons_by_date[date].append((
                    lesson['id'],
                    lesson['title'],
                    lesson['description'],
                    lesson['time'],
                    lesson['location'],
                    lesson['date']
                ))

            self.calendarWidget.set_lessons_data(lessons_by_date)

        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")

    def on_date_clicked(self, date):
        """Обработка клика по дате в календаре"""
        date_str = date.toString("dd-MM-yyyy")

        # Получаем занятия на эту дату через API
        lessons = self.client.get_lessons()
        date_lessons = [lesson for lesson in lessons if lesson['date'] == date_str]

        if date_lessons:
            # Конвертируем в нужный формат для попапа
            formatted_lessons = []
            for lesson in date_lessons:
                formatted_lessons.append((
                    lesson['id'],
                    lesson['title'],
                    lesson['description'],
                    lesson['time'],
                    lesson['location'],
                    lesson['date']
                ))

            # Показываем попап с занятиями рядом с календарем
            calendar_pos = self.calendarWidget.mapToGlobal(QPoint(0, 0))
            popup_pos = QPoint(calendar_pos.x(), calendar_pos.y() + 400)

            self.popup.show_lessons(formatted_lessons, date_str, popup_pos)

    def delete_lesson_by_id(self, lesson_id, date):
        """Удаляет занятие по ID через API"""
        try:
            success = self.client.delete_lesson(lesson_id)
            if success:
                # Обновление данных
                self.load_lessons_data()
                self.popup.hide()
                QMessageBox.information(self, "Успех", "Занятие удалено")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить занятие")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {e}")

    def add_lesson(self):
        """Добавление нового занятия через API"""
        title = self.title_input.toPlainText().strip()
        time = self.time_input.text().strip()
        selected_date = self.calendarWidget.selectedDate().toString("dd-MM-yyyy")

        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название занятия")
            return

        try:
            success = self.client.create_lesson(title, selected_date, time, "", "")
            if success:
                # Очистка формы
                self.title_input.clear()
                self.time_input.clear()

                # Обновление данных
                self.load_lessons_data()

                QMessageBox.information(
                    self, "Успех", f"Занятие '{title}' добавлено на {selected_date}!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить занятие")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")
