from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi
from PyQt6.QtCore import pyqtSignal


class BasePage(QWidget):
    page_closed = pyqtSignal()

    def __init__(self, ui_file, parent=None):
        super().__init__(parent)
        loadUi(ui_file, self)
        self.setup_ui()

    def setup_ui(self):
        """Инициализация UI - переопределить в дочерних классах"""
        pass

    def showEvent(self, event):
        """Вызывается при показе страницы"""
        self.on_page_show()
        super().showEvent(event)

    def hideEvent(self, event):
        """Вызывается при скрытии страницы"""
        self.on_page_hide()
        super().hideEvent(event)

    def on_page_show(self):
        """Действия при открытии страницы"""
        pass

    def on_page_hide(self):
        """Действия при закрытии страницы"""
        pass
