import xml.etree.ElementTree as ET
import re
import qrcode

tree = ET.parse('image.svg')
root = tree.getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}

def get_bbox(d):
    coords = re.findall(r'([0-9.]+),([0-9.]+)', d)
    if not coords: return 0,0,0,0
    xs = [float(x) for x,y in coords]
    ys = [float(y) for x,y in coords]
    return min(xs), min(ys), max(xs), max(ys)

found_cols_by_row = {}
for path in root.findall('.//svg:path', ns):
    stroke = path.attrib.get('stroke', '')
    if stroke == '':
        x0, y0, x1, y1 = get_bbox(d=path.attrib.get('d', ''))
        row = int(round((y0 - 1) / 10)) - 4  # y0 = (row+4)*10 + 1  ==> (y0-1)/10 - 4
        col = int(round(x0 / 10)) - 4        # x0 = (col+4)*10      ==> x0/10 - 4
        if row not in found_cols_by_row:
            found_cols_by_row[row] = set()
        found_cols_by_row[row].add(col)

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=100)
qr.add_data('Hello Michael')
qr.make()
mc = qr.modules_count

missing = []
for r in range(mc):
    for c in range(mc):
        is_eye = (r < 7 and c < 7) or (r < 7 and c >= mc - 7) or (r >= mc - 7 and c < 7)
        if qr.modules[r][c] and not is_eye:
            if c not in found_cols_by_row.get(r, set()):
                missing.append((r, c))

print(f"Missing modules: {missing}")
