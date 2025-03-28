import cv2
import matplotlib.pyplot as plt


class TableDetector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError("Изображение не найдено или указан некорректный путь.")
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.blur = cv2.GaussianBlur(self.gray, (3, 3), 0)
        self.thresh = cv2.threshold(
            self.blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]

    @staticmethod
    def excel_cell_name(row, col):
        col_name = ""
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            col_name = chr(65 + remainder) + col_name
        return f"{col_name}{row}"

    def detect_horizontal_lines(self):
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        horizontal_mask = cv2.morphologyEx(
            self.thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1
        )
        contours, _ = cv2.findContours(
            horizontal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        horizontal_lines = [cv2.boundingRect(cnt) for cnt in contours]
        horizontal_lines = [(x, y, x + w, y + h) for x, y, w, h in horizontal_lines if w > 10]
        return sorted(horizontal_lines, key=lambda x: x[1])

    def detect_vertical_lines(self):
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
        vertical_mask = cv2.morphologyEx(
            self.thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1
        )
        contours, _ = cv2.findContours(
            vertical_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        vertical_lines = [cv2.boundingRect(cnt) for cnt in contours]
        vertical_lines = [(x, y, x + w, y + h) for x, y, w, h in vertical_lines if h > 10]
        return sorted(vertical_lines, key=lambda x: x[0])

    def detect_grid(self):
        horizontal_lines = self.detect_horizontal_lines()
        vertical_lines = self.detect_vertical_lines()

        # Фильтруем горизонтальные линии: оставляем те, что пересекаются с вертикальными
        filtered_horizontal = []
        for h_line in horizontal_lines:
            x1, y1, x2, y2 = h_line
            for v_line in vertical_lines:
                vx1, vy1, vx2, vy2 = v_line
                if not (x2 < vx1 or x1 > vx2) and not (y1 > vy2 or y2 < vy1):
                    filtered_horizontal.append(h_line)
                    break

        full_width = self.image.shape[1]
        stretched_horizontal = [(0, y1, full_width, y1) for (_, y1, _, y2) in filtered_horizontal]
        full_height = self.image.shape[0]
        stretched_vertical = [(x1, 0, x1, full_height) for (x1, _, x2, _) in vertical_lines]

        stretched_horizontal = sorted(stretched_horizontal, key=lambda x: x[1])
        stretched_vertical = sorted(stretched_vertical, key=lambda x: x[0])

        print("Горизонтальные линии:", stretched_horizontal)
        print("Вертикальные линии:", stretched_vertical)

        min_width_cell = 10
        min_height_cell = 10
        rows_dict = {}

        for i in range(len(stretched_horizontal) - 1):
            row_start_y = stretched_horizontal[i][1]
            row_end_y = stretched_horizontal[i + 1][1]
            for j in range(len(stretched_vertical) - 1):
                cell_start_x = stretched_vertical[j][0]
                cell_end_x = stretched_vertical[j + 1][0]
                if (cell_end_x - cell_start_x >= min_width_cell) and (row_end_y - row_start_y >= min_height_cell):
                    cell = (cell_start_x, row_start_y, cell_end_x, row_end_y)
                    row_index = (row_start_y + row_end_y) // 2
                    if row_index not in rows_dict:
                        rows_dict[row_index] = []
                    rows_dict[row_index].append(cell)

        sorted_rows = sorted(rows_dict.items(), key=lambda x: x[0])
        sorted_cells_per_row = [cells for _, cells in sorted_rows]
        print("Ячейки, распределённые по строкам:", sorted_cells_per_row)

        # Визуализация (по желанию)
        plt.figure(figsize=(20, 20))
        result = self.image.copy()
        # plt.imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        for line in stretched_horizontal:
            plt.plot([line[0], line[2]], [line[1], line[1]], color='green', linewidth=2)
        for line in stretched_vertical:
            plt.plot([line[0], line[0]], [line[1], line[3]], color='red', linewidth=2)
        cells_dict = {}
        for row_idx, row in enumerate(sorted_cells_per_row):
            for col_idx, cell in enumerate(row):
                x1, y1, x2, y2 = cell
                plt.plot([x1, x2], [y1, y2], color='blue', linewidth=1)
                cell_label = self.excel_cell_name(row_idx + 1, col_idx + 1)
                plt.text((x1 + x2) / 2, (y1 + y2) / 2, cell_label,
                         color='black', ha='center', va='center', fontsize=8)
                cells_dict[cell_label] = (x1, y1, x2, y2)
        plt.axis('on')
        # plt.show()
        print("Словарь ячеек:", cells_dict)
        return cells_dict

    def detect_table_structure(self):
        # Реализация аналогична предыдущей функции detect_table_structure
        # Здесь можно добавить рекурсивное определение вложенных ячеек
        # Для краткости приведём упрощённую версию без рекурсии
        rows = self._detect_horizontal_lines_structure(self.thresh)
        all_cells = []
        for row_start, row_end in rows:
            cells = self._detect_vertical_lines_in_row(self.thresh, row_start, row_end)
            all_cells.extend(cells)
            for cell in cells:
                print(f'Ячейка: {cell}')
                x1, y1, x2, y2 = cell
                cell_image = self.image[y1:y2, x1:x2]
                plt.figure(figsize=(5, 5))
                # plt.imshow(cv2.cvtColor(cell_image, cv2.COLOR_BGR2RGB))
                # plt.axis('off')
                # plt.show()
        # Визуализация итоговой сетки
        output_image = self.image.copy()
        for (x1, y1, x2, y2) in all_cells:
            cv2.rectangle(output_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.line(output_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        plt.figure(figsize=(12, 8))
        # plt.imshow(cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB))
        plt.axis('on')
        # plt.show()
        return all_cells

    def _detect_horizontal_lines_structure(self, thresh):
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        horizontal_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
        contours, _ = cv2.findContours(horizontal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        horizontal_lines = [cv2.boundingRect(cnt) for cnt in contours]
        horizontal_lines = [(x, y, x + w, y + h) for x, y, w, h in horizontal_lines if w > 10]
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        vertical_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
        contours_ver, _ = cv2.findContours(vertical_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        vertical_lines = [cv2.boundingRect(cnt) for cnt in contours_ver]
        vertical_lines = [(x, y, x + w, y + h) for x, y, w, h in vertical_lines if h > 10]
        filtered_horizontal = []
        for h_line in horizontal_lines:
            x1, y1, x2, y2 = h_line
            for v_line in vertical_lines:
                vx1, vy1, vx2, vy2 = v_line
                if not (x2 < vx1 or x1 > vx2) and not (y1 > vy2 or y2 < vy1):
                    filtered_horizontal.append(h_line)
                    break
        filtered_horizontal = sorted(filtered_horizontal, key=lambda x: x[1])
        rows = [
            (int(filtered_horizontal[i][1]), int(filtered_horizontal[i + 1][1]))
            for i in range(len(filtered_horizontal) - 1)
        ]
        return rows

    def _detect_vertical_lines_in_row(self, thresh, row_start, row_end):
        row_image = thresh[row_start:row_end, :]
        if row_image.size == 0:
            return []
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
        detect_vertical = cv2.morphologyEx(row_image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        cnts, _ = cv2.findContours(detect_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        lines = sorted([cv2.boundingRect(c)[0] for c in cnts])
        cells = [(lines[i], row_start, lines[i + 1], row_end) for i in range(len(lines) - 1)]
        return cells
