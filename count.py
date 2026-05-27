import xml.etree.ElementTree as ET

tree = ET.parse('image.svg')
root = tree.getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}

modules = 0
eyes = 0
for path in root.findall('.//svg:path', ns):
    fill = path.attrib.get('fill', '')
    stroke = path.attrib.get('stroke', '')
    if fill == 'none':
        eyes += 1
    elif stroke == '':
        modules += 1

print(f"SVG Modules rendered: {modules}")
print(f"SVG Eyes rendered: {eyes}")
