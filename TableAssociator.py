import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class TableAssociator:
    @staticmethod
    def is_within(cell, table_cell, tolerance=5):
        x1, y1, x2, y2 = cell
        tx1, ty1, tx2, ty2 = table_cell
        return (
            (tx1 - tolerance <= x1 < tx2 + tolerance and tx1 - tolerance < x2 <= tx2 + tolerance) and
            (ty1 - tolerance <= y1 < ty2 + tolerance and ty1 - tolerance < y2 <= ty2 + tolerance)
        )

    def create_associated_cells(self, table_cells, cells_dict):
        associated_cells = {}
        for table_cell in table_cells:
            for cell_label, excel_cell in cells_dict.items():
                if self.is_within(excel_cell, table_cell):
                    if table_cell not in associated_cells:
                        associated_cells[table_cell] = []
                    associated_cells[table_cell].append(cell_label)
        for table_cell, associated in associated_cells.items():
            print(f"Ячейка таблицы {table_cell} ассоциирована с Excel-ячейками: {', '.join(associated)}")
        return associated_cells

    def associate_grid_and_cells(self, table_cells, cells_dict, image_path):
        associated_cells = {}
        result = cv2.imread(image_path)
        for table_cell in table_cells:
            for cell_label, excel_cell in cells_dict.items():
                if self.is_within(excel_cell, table_cell):
                    if table_cell not in associated_cells:
                        associated_cells[table_cell] = []
                    associated_cells[table_cell].append(cell_label)
        plt.figure(figsize=(12, 10))
        # plt.imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        i = 0
        for table_cell in table_cells:
            tx1, ty1, tx2, ty2 = table_cell
            table_rect = patches.Rectangle((tx1, ty1), tx2 - tx1, ty2 - ty1,
                                           linewidth=1, edgecolor='green', facecolor='none')
            plt.gca().add_patch(table_rect)
            plt.text(tx1 + 40, ty1 + 20, f"Table: {i}",
                     color='green', ha='center', va='center', fontsize=8)
            i += 1
        for cell_label, excel_cell in cells_dict.items():
            x1, y1, x2, y2 = excel_cell
            excel_rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1,
                                           linewidth=1, edgecolor='blue', facecolor='none')
            plt.gca().add_patch(excel_rect)
            plt.text((x1 + x2) / 2, (y1 + y2) / 2, cell_label,
                     color='blue', ha='center', va='center', fontsize=8)
        # plt.axis('on')
        # plt.title('Ассоциация Excel-ячейки и найденной ячейки таблицы')
        # plt.show()
        return associated_cells
