import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QProgressBar, QStackedWidget, QDialog, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer

BUTTON_STYLE = """
QPushButton {
    background-color: #007BFF;
    color: white;
    border-radius: 10px;
    padding: 10px 20px;
    font-family: 'Arial';
    font-size: 16px;
}
QPushButton:hover {
    background-color: #0056b3;
}
"""


class StartScreen(QWidget):
    """Начальный экран."""

    def __init__(self, switch_callback):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Конвертер Таблиц")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        start_button = QPushButton("Начать работу")
        start_button.setFont(QFont("Arial", 16))
        start_button.setStyleSheet(BUTTON_STYLE)
        start_button.clicked.connect(switch_callback)
        layout.addWidget(start_button)

        self.setLayout(layout)


class CropConfirmationDialog(QDialog):
    """
    Окно подтверждения обрезки.
    """

    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Подтверждение обрезки")
        self.selected = False
        self.resize(500, 500)
        layout = QVBoxLayout()

        scaled_pixmap = pixmap.scaled(525, 525, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label = QLabel()
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        question_label = QLabel("Правильно ли обрезалось фото?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setFont(QFont("Arial", 14))
        layout.addWidget(question_label)

        # Кнопки "Да" и "Нет"
        button_layout = QHBoxLayout()
        yes_button = QPushButton("Да")
        yes_button.setStyleSheet(BUTTON_STYLE)
        no_button = QPushButton("Нет")
        no_button.setStyleSheet(BUTTON_STYLE)
        yes_button.clicked.connect(self.accepted)
        no_button.clicked.connect(self.rejected)
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def accepted(self):
        self.selected = True
        self.accept()

    def rejected(self):
        self.selected = False
        self.reject()


class ProcessingWindow(QDialog):
    """
    Окно обработки.
    """

    def __init__(self, pixmap, finish_callback):
        super().__init__()
        self.setWindowTitle("Обработка таблицы")
        self.finish_callback = finish_callback
        self.resize(800, 600)
        layout = QVBoxLayout()

        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Кнопка возврата, изначально скрыта
        self.return_button = QPushButton("Вернуться на главный экран")
        self.return_button.setStyleSheet(BUTTON_STYLE)
        self.return_button.setVisible(False)
        self.return_button.clicked.connect(self.on_return)
        layout.addWidget(self.return_button)

        self.setLayout(layout)

        # загрузка
        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)

    def update_progress(self):
        self.progress += (100 / 7000) * 100
        if self.progress >= 100:
            self.progress_bar.setValue(100)
            self.timer.stop()
            self.processing_finished()
        else:
            self.progress_bar.setValue(int(self.progress))

    def processing_finished(self):
        QMessageBox.information(self, "Завершено", "Таблица успешно обработана и перенесена в Excel!")
        self.return_button.setVisible(True)

    def on_return(self):
        self.finish_callback()
        self.accept()


class MainWorkScreen(QWidget):
    """
    Основной экран выбора фото.
    """

    def __init__(self, processing_callback):
        super().__init__()
        self.setAcceptDrops(True)
        self.processing_callback = processing_callback
        self.layout = QVBoxLayout(self)

        self.upload_button = QPushButton("Загрузить фото таблицы")
        self.upload_button.setStyleSheet(BUTTON_STYLE)
        self.upload_button.clicked.connect(self.load_image)
        self.layout.addWidget(self.upload_button)

        self.image_label = QLabel("Перетащите фото сюда или нажмите кнопку")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #aaa; font-family: Arial; font-size: 16px;")
        self.layout.addWidget(self.image_label)

    def load_image(self):
        """Открывает диалог выбора файла и загружает изображение."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото таблицы", "",
            "Images (*.png *.jpg *.jpeg *.bmp)", options=options
        )
        if fileName:
            self.display_image(fileName)

    def display_image(self, file_path):
        """Отображает изображение и запускает детектирование таблицы."""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            return
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.detect_table(pixmap)

    def detect_table(self, pixmap):
        """
       детектирования таблицы.
        """
        print("Вызов функции детектирования таблицы.")

        self.show_crop_confirmation(pixmap)

    def show_crop_confirmation(self, pixmap):
        dialog = CropConfirmationDialog(pixmap)
        result = dialog.exec_()
        if dialog.selected:
            # Если пользователь подтверждает, запускаем окно обработки
            self.processing_callback(pixmap)
            # Очищаем текущее изображение
            self.image_label.clear()
            self.image_label.setText("Перетащите фото сюда или нажмите кнопку")
        else:
            QMessageBox.information(self, "Отмена", "Пожалуйста, загрузите другое фото.")

    # Добавляем поддержку drag & drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.display_image(file_path)


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертер Таблиц")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Стартовый экран
        self.start_screen = StartScreen(self.switch_to_main)
        self.stack.addWidget(self.start_screen)

        # Экран выбора фото
        self.main_work_screen = MainWorkScreen(self.open_processing_window)
        self.stack.addWidget(self.main_work_screen)

    def switch_to_main(self):
        """Переход от стартового экрана к рабочему."""
        self.stack.setCurrentWidget(self.main_work_screen)

    def open_processing_window(self, pixmap):
        """
        Создаёт и показывает окно обработки.
        После завершения обработки пользователь вернется на стартовый экран.
        """
        processing_win = ProcessingWindow(pixmap, self.return_to_start)
        processing_win.exec_()

    def return_to_start(self):
        """Возврат на стартовый экран."""
        self.stack.setCurrentWidget(self.start_screen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(BUTTON_STYLE)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
