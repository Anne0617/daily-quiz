import sys, zipfile, os
from xml.etree import ElementTree as ET

# Get file path from command line
path = sys.argv[1]
print(f'Reading: {path}')
print(f'File exists: {os.path.exists(path)}')

# Try reading with zipfile
with zipfile.ZipFile(path) as z:
    slides = sorted([f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
    print(f'Total slides: {len(slides)}')
    print('='*80)
    for i, slide_name in enumerate(slides):
        print(f'\n=== Slide {i+1} ===')
        xml_content = z.read(slide_name)
        root = ET.fromstring(xml_content)
        ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
              'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
              'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
        
        texts = []
        for t_elem in root.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
            if t_elem.text and t_elem.text.strip():
                texts.append(t_elem.text.strip())
        
        for t in texts:
            print(t)
        print('===')
