from PIL import Image

# Otwieramy wygenerowany obrazek i zapisujemy jako wielorozmiarową ikonę .ico
img = Image.open("icon.png")
img.save(
    "icon.ico",
    format="ICO",
    sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
)
print("Ikona została pomyślnie przekonwertowana!")