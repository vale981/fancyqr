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

print("SVG Paths near x=140, y=41:")
for path in root.findall('.//svg:path', ns):
    d = path.attrib.get('d', '')
    stroke = path.attrib.get('stroke', '')
    if stroke == '':
        x0, y0, x1, y1 = get_bbox(d)
        if 130 <= x0 <= 150 and 40 <= y0 <= 50:
            print(f"w={x1-x0}, h={y1-y0}, pos=({x0}, {y0})")
