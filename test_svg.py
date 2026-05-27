import xml.etree.ElementTree as ET
tree = ET.parse('image.svg')
root = tree.getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}
paths = root.findall('.//svg:path', ns)
print(f"Total paths: {len(paths)}")
