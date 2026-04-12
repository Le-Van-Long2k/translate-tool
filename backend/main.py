from ocr_engine.paddle_ocr_engine import PaddleOCREngine
import cv2

ocr_engine = PaddleOCREngine()

image = cv2.imread("/home/test/translate-tool/backend/test2/1.jpg")
images = []
images.append(image)

ocr_results = ocr_engine.recognize(images)
