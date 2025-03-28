from TableDetector import TableDetector
from TableAssociator import TableAssociator
from ImageTextExtractor import ImageTextExtractor
from ExcelHelper import ExcelHelper


class TableProcessor:
    def __init__(self, image_path, excel_filename, lang='rus'):
        self.image_path = image_path
        self.excel_filename = excel_filename
        self.lang = lang

    def process(self):
        detector = TableDetector(self.image_path)
        cells_dict = detector.detect_grid()
        all_cells = detector.detect_table_structure()

        associator = TableAssociator()
        associated_cells = associator.associate_grid_and_cells(all_cells, cells_dict, self.image_path)

        ExcelHelper.create_empty_excel_file(cells_dict)

        text_extractor = ImageTextExtractor(self.image_path, lang=self.lang)
        text_to_cells = text_extractor.create_text_to_cells(associated_cells)

        ExcelHelper.create_excel(self.excel_filename, text_to_cells)


if __name__ == '__main__':
    image_path = 'images/output.jpg'
    excel_filename = 'final.xlsx'
    processor = TableProcessor(image_path, excel_filename, lang='rus')
    processor.process()
