import cv2
import re
import pytesseract


class ImageTextExtractor:
    def __init__(self, image_path, lang='rus'):
        self.image = cv2.imread(image_path)
        self.lang = lang

    def extract_text_from_image(self, coordinates):
        x1, y1, x2, y2 = coordinates
        cropped_image = self.image[y1:y2, x1:x2]
        custom_config = r'--psm 6'
        text = pytesseract.image_to_string(cropped_image, config=custom_config, lang=self.lang)
        return text.strip()

    def create_text_to_cells(self, associated_cells):
        text_to_cells = {}
        for coordinates, excel_labels in associated_cells.items():
            extracted_text = self.extract_text_from_image(coordinates)
            text_to_cells[extracted_text] = excel_labels
        for text, excel_labels in text_to_cells.items():
            print(f"Text '{text}' is associated with cells: {', '.join(excel_labels)}")
        print(text_to_cells)
        return text_to_cells

    @staticmethod
    def extract_row_number(cell):
        return int(re.sub("[^0-9]", "", cell))

    @staticmethod
    def extract_column_letter(cell):
        return ''.join(re.findall('[A-Za-z]+', cell))
