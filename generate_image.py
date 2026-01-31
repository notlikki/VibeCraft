from PIL import Image, ImageDraw
import random

# Create a new image with a white background
width, height = 256, 256
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Add some random colored rectangles to create edges/texture
for _ in range(20):
    x1 = random.randint(0, width)
    y1 = random.randint(0, height)
    x2 = random.randint(0, width)
    y2 = random.randint(0, height)
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    draw.rectangle([min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)], fill=color)

# Save the image
image.save('input.jpg')
print("Created input.jpg")
