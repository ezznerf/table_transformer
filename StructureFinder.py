import warnings

import matplotlib.colors as mcolors
import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import TableTransformerForObjectDetection, DetrImageProcessor


class StructureFinder:
    COLORS = [
        [0.000, 0.447, 0.741],
        [0.850, 0.325, 0.098],
        [0.929, 0.694, 0.125],
        [0.494, 0.184, 0.556],
        [0.466, 0.674, 0.188],
        [0.301, 0.745, 0.933]
    ]

    def __init__(self, model_name: str = "microsoft/table-transformer-structure-recognition"):
        warnings.simplefilter("ignore")
        self.model = TableTransformerForObjectDetection.from_pretrained(model_name)
        self.image_processor = DetrImageProcessor.from_pretrained(model_name)

    def detect(self, image_path: str, resize_factor: float = 0.5, threshold: float = 0.97):
        try:
            image = Image.open(image_path).convert("RGB")
            original_size = image.size

            processed_image = image.resize((int(original_size[0] * resize_factor),
                                            (int(original_size[1] * resize_factor))))

            inputs = self.image_processor(images=processed_image, return_tensors="pt")

            with torch.no_grad():
                outputs = self.model(**inputs)

            target_sizes = torch.tensor([original_size[::-1]])
            results = self.image_processor.post_process_object_detection(
                outputs,
                threshold=threshold,
                target_sizes=target_sizes
            )[0]

            return {
                'scores': results['scores'],
                'labels': results['labels'],
                'boxes': results['boxes'],
                'image': image
            }

        except Exception as e:
            print(f"Ошибка: {str(e)}")
            return None

    def visualize_detections(self, detection_result, output_path: str = "result.jpg"):
        """Визуализация"""
        image = detection_result['image'].copy()
        draw = ImageDraw.Draw(image)

        pil_colors = [
            tuple(int(255 * ch) for ch in mcolors.to_rgb(color))
            for color in self.COLORS
        ]
        try:
            font = ImageFont.truetype("arialbd.ttf", 18)
        except:
            font = ImageFont.load_default()

        for idx, (score, label, box) in enumerate(zip(
            detection_result['scores'],
            detection_result['labels'],
            detection_result['boxes']
        )):
            color = pil_colors[idx % len(pil_colors)]
            box = [coord.item() for coord in box]

            draw.rectangle(box, outline=color, width=4)

            text = f"{self.model.config.id2label[label.item()]}: {score.item():0.2f}"

            text_bbox = draw.textbbox((box[0], box[1]), text, font=font)

            draw.rectangle(
                [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
                fill=(255, 255, 0, 128))

            draw.text((box[0], box[1]), text, fill="black", font=font)

            image.save(output_path)
        return image


if __name__ == "__main__":
    detector = StructureFinder()
    result = detector.detect("images/output.jpg", resize_factor=0.8, threshold=0.97)

    if result:
        final_image = detector.visualize_detections(result, "final_output.jpg")
        final_image.show()
