import cv2
import numpy as np
class Cropper:
    """
    Класс для извлечения таблицы с изображения.
    """

    def __init__(self, image_input):
        if isinstance(image_input, str):
            self.image = cv2.imread(image_input)
            if self.image is None:
                raise ValueError("Не удалось загрузить изображение по указанному пути.")
        elif isinstance(image_input, np.ndarray):
            self.image = image_input
        else:
            raise TypeError("image_input должен быть либо путем к файлу, либо numpy-массивом.")

    def extract_and_save_table(self, output_path, padding_x=10, padding_y=10):
        """
        Извлекает таблицу и сохраняет обрезанное изображение в output_path.
        :return: output_path, если успешно, иначе None.
        """
        try:
            cropped_image = self.extract_table(padding_x, padding_y)
            if cropped_image is not None:
                cv2.imwrite(output_path, cropped_image)
                return output_path
            return None
        except Exception as e:
            print(f"Ошибка при сохранении: {str(e)}")
            return None

    def extract_table(self, padding_x=0, padding_y=0):
        """
        Извлекает область таблицы с изображения.
        :return: numpy array с обрезанным изображением или None.
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray_inv = cv2.bitwise_not(gray)
        binary = cv2.adaptiveThreshold(
            gray_inv, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 15, -2
        )
        horizontal = self._get_lines(binary, axis="horizontal")
        vertical = self._get_lines(binary, axis="vertical")
        table_mask = cv2.add(horizontal, vertical)
        contours, _ = cv2.findContours(
            table_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        x, y, w, h = self._apply_padding(x, y, w, h, padding_x, padding_y)
        return self.image[y:y + h, x:x + w]

    def _get_lines(self, binary_img, axis):
        """Вспомогательный метод для выделения линий"""
        img = binary_img.copy()
        rows, cols = img.shape
        size = cols // 30 if axis == "horizontal" else rows // 30
        kernel_size = (size, 1) if axis == "horizontal" else (1, size)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        img = cv2.erode(img, kernel)
        img = cv2.dilate(img, kernel)
        return img

    def _apply_padding(self, x, y, w, h, padding_x, padding_y):
        """Вспомогательный метод для добавления разного отступа по горизонтали и вертикали"""
        new_x = max(0, x - padding_x)
        new_y = max(0, y - padding_y)
        new_w = min(self.image.shape[1] - new_x, w + 2 * padding_x)
        new_h = min(self.image.shape[0] - new_y, h + 2 * padding_y)
        return new_x, new_y, new_w, new_h
