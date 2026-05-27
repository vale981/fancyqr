import cv2
import sys

def decode_qr(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Could not read image: {image_path}")
        return
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)
    if bbox is not None:
        print(f"{image_path} decoded data: {data}")
    else:
        print(f"Could not detect QR code in {image_path}")

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        decode_qr(arg)
