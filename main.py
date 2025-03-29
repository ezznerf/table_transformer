import sys
import cv2
import numpy as np
import tempfile
from StructureFinder import StructureFinder
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime
from TableProcessor import TableProcessor
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QProgressBar, QStackedWidget,
    QDialog, QHBoxLayout, QLineEdit, QFormLayout
)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QTimer

from Cropper import Cropper

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


def qpixmap_to_cv(qpixmap):
    qimage = qpixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())
    arr = np.array(ptr).reshape(height, width, 4)
    cv_img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv_img


def pil2pixmap(im):
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    data = im.tobytes("raw", "RGBA")
    qimage = QImage(data, im.width, im.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimage)


class StartScreen(QWidget):
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


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки программы")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        self.padding_x_edit = QLineEdit()
        self.padding_y_edit = QLineEdit()
        self.scale_edit = QLineEdit()

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet(BUTTON_STYLE)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setStyleSheet(BUTTON_STYLE)

        form_layout = QFormLayout()
        form_layout.addRow("Горизонтальный отступ (padding_x):", self.padding_x_edit)
        form_layout.addRow("Вертикальный отступ (padding_y):", self.padding_y_edit)
        form_layout.addRow("Масштаб изображения:", self.scale_edit)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_settings(self):
        try:
            return {
                'padding_x': int(self.padding_x_edit.text()),
                'padding_y': int(self.padding_y_edit.text()),
                'scale_factor': float(self.scale_edit.text())
            }
        except:
            return None


class CropConfirmationDialog(QDialog):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Подтверждение обрезки")
        self.selected = False
        self.resize(500, 500)
        layout = QVBoxLayout()
        scaled_pixmap = pixmap.scaled(int(pixmap.width()), int(pixmap.height()),
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.image_label = QLabel()
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        question_label = QLabel("Правильно ли обрезалось фото?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setFont(QFont("Arial", 14))
        layout.addWidget(question_label)
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
    def __init__(self, image_path, excel_path, finish_callback, scale_factor):
        super().__init__()
        self.setWindowTitle("Обработка таблицы")
        self.finish_callback = finish_callback
        self.image_path = image_path
        self.excel_path = excel_path
        self.scale_factor = scale_factor
        self.resize(800, 600)

        layout = QVBoxLayout()

        self.image_label = QLabel()
        pixmap = QPixmap(image_path)

        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * self.scale_factor),
            int(pixmap.height() * self.scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.return_button = QPushButton("Вернуться на главный экран")
        self.return_button.setStyleSheet(BUTTON_STYLE)
        self.return_button.setVisible(False)
        self.return_button.clicked.connect(self.on_return)
        layout.addWidget(self.return_button)

        self.setLayout(layout)

        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)

        QTimer.singleShot(500, self.process_image)

    def update_progress(self):
        if self.progress < 100:
            self.progress += 100 / 40
            self.progress_bar.setValue(int(self.progress))
        else:
            self.timer.stop()

    def process_image(self):
        detector = StructureFinder()
        result = detector.detect(self.image_path, resize_factor=1, threshold=0.97)

        if result:
            processed_image = detector.visualize_detections(result, "images/processed_output.jpg")
            self.update_image("images/processed_output.jpg")

            table_processor = TableProcessor(self.image_path, self.excel_path, lang='rus')
            try:
                table_processor.process()
                QTimer.singleShot(4100, self.processing_finished)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка обработки: {str(e)}")
                self.close()

    def update_image(self, image_path):
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * self.scale_factor),
            int(pixmap.height() * self.scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def processing_finished(self):
        QMessageBox.information(self, "Завершено",
                                f"Таблица успешно обработана!\nExcel-файл сохранён:\n{self.excel_path}")
        self.return_button.setVisible(True)

    def on_return(self):
        self.finish_callback()
        self.accept()


class MainWorkScreen(QWidget):
    def __init__(self, processing_callback):
        super().__init__()
        self.setAcceptDrops(True)
        self.processing_callback = processing_callback
        self.settings = {
            'padding_x': 0,
            'padding_y': 0,
            'scale_factor': 0.9
        }

        self.layout = QVBoxLayout(self)

        # Кнопка настроек
        self.settings_button = QPushButton("Настройки")
        self.settings_button.setStyleSheet(BUTTON_STYLE)
        self.settings_button.clicked.connect(self.show_settings)
        self.layout.addWidget(self.settings_button)

        self.upload_button = QPushButton("Загрузить фото таблицы")
        self.upload_button.setStyleSheet(BUTTON_STYLE)
        self.upload_button.clicked.connect(self.load_image)
        self.layout.addWidget(self.upload_button)

        self.image_label = QLabel("Перетащите фото сюда или нажмите кнопку")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #aaa; font-family: Arial; font-size: 16px;")
        self.layout.addWidget(self.image_label)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.padding_x_edit.setText(str(self.settings['padding_x']))
        dialog.padding_y_edit.setText(str(self.settings['padding_y']))
        dialog.scale_edit.setText(str(self.settings['scale_factor']))

        if dialog.exec_():
            new_settings = dialog.get_settings()
            if new_settings:
                self.settings.update(new_settings)
            else:
                QMessageBox.warning(self, "Ошибка", "Некорректные значения настроек")

    def load_image(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото таблицы", "",
            "Images (*.png *.jpg *.jpeg *.bmp)", options=options
        )
        if fileName:
            self.display_image(fileName)

    def display_image(self, file_path):
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            return
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.detect_table(pixmap)

    def detect_table(self, pixmap):
        try:
            cv_image = qpixmap_to_cv(pixmap)
            cropper = Cropper(cv_image)

            temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            temp_path = temp_file.name
            temp_file.close()

            cropped_file_path = cropper.extract_and_save_table(
                temp_path,
                padding_x=self.settings['padding_x'],
                padding_y=self.settings['padding_y']
            )

            if cropped_file_path:
                cropped_pixmap = QPixmap(cropped_file_path)
                self.show_crop_confirmation(cropped_pixmap, cropped_file_path)
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось извлечь таблицу.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def show_crop_confirmation(self, pixmap, image_path):
        dialog = CropConfirmationDialog(pixmap)
        result = dialog.exec_()

        if dialog.selected:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"table_{timestamp}.xlsx"
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить Excel файл", default_name, "Excel Files (*.xlsx)"
            )

            if save_path:
                if not save_path.endswith('.xlsx'):
                    save_path += '.xlsx'
                self.processing_callback(image_path, save_path)
            else:
                QMessageBox.information(self, "Отмена", "Сохранение отменено")
                return

            self.image_label.clear()
            self.image_label.setText("Перетащите фото сюда или нажмите кнопку")
        else:
            QMessageBox.information(self, "Отмена", "Пожалуйста, загрузите другое фото.")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.display_image(file_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертер Таблиц")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.start_screen = StartScreen(self.switch_to_main)
        self.stack.addWidget(self.start_screen)
        self.main_work_screen = MainWorkScreen(self.open_processing_window)
        self.stack.addWidget(self.main_work_screen)

    def switch_to_main(self):
        self.stack.setCurrentWidget(self.main_work_screen)

    def open_processing_window(self, image_path, excel_path):
        scale = self.main_work_screen.settings['scale_factor']
        processing_win = ProcessingWindow(image_path, excel_path, self.return_to_start, scale)
        processing_win.exec_()

    def return_to_start(self):
        self.stack.setCurrentWidget(self.start_screen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(BUTTON_STYLE)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
