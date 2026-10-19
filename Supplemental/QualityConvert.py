# Imports
from PIL import Image
import sys

# Garbo script for quality conversion
try:
    image = sys.argv[1]
    quality = int(sys.argv[2])
    output = f"{quality}conv-{image}"
    with Image.open(image) as img:
        img.save(output, quality=quality)

# Catch all because whatever
except Exception as e:
    print(f"[-] Error occurred: {e}")
    print("usage: python QualityConvert.py <image> <quality> <optional out file name>")

# EOF
