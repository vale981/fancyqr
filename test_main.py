import qrcode
from qrcode.main import QRCode
import main

qr = QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=100)
qr.add_data("Hello Michael")

img_1 = qr.make_image(
    image_factory=main.StyledSvgImage,
    module_drawer=main.SvgHorizontalBarsDrawer(),
    eye_drawer=main.SvgCustomEyeDrawer(),
    color_mask=main.SolidFillColorMask(
        front_color=(255, 146, 50, 255), back_color=(255, 255, 255, 0)
    ),
)
img_1.save("image.svg")

import xml.etree.ElementTree as ET
import re

tree = ET.parse('image.svg')
root = tree.getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}

def get_bbox(d):
    coords = re.findall(r'([0-9.]+),([0-9.]+)', d)
    if not coords: return 0,0,0,0
    xs = [float(x) for x,y in coords]
    ys = [float(y) for x,y in coords]
    return min(xs), min(ys), max(xs), max(ys)

print("SVG Row 0 (y0 == 41.0 or y0 == 40.0):")
for path in root.findall('.//svg:path', ns):
    d = path.attrib.get('d', '')
    x0, y0, x1, y1 = get_bbox(d)
    if y0 == 41.0 or y0 == 40.0:
        print(f"w={x1-x0}, h={y1-y0}, pos=({x0}, {y0})")
