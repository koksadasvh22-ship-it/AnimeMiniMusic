import os
from PIL import Image, ImageDraw

size = 500
base_vinyl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(base_vinyl)

# Czarny winyl wypełniający całe pole
draw.ellipse([0, 0, size, size], fill="#111111")
center = size // 2

# Wyraziste rowki płyty
for r in range(70, 240, 16):
  draw.ellipse(
      [center - r, center - r, center + r, center + r],
      outline="#222222",
      width=3,
  )

# Szukamy pliku z anime
filename = None
for f in ["anime.png", "anime.jpg", "anime.jpeg", "character.png"]:
  if os.path.exists(f):
    filename = f
    break

if filename:
  print(f"Znaleziono grafikę: '{filename}'")
  label_img = Image.open(filename).convert("RGBA")
else:
  print("Nie znaleziono pliku anime! Używam awaryjnego koloru.")
  label_img = Image.new("RGBA", (350, 350), "#1DB954")

# POWIĘKSZAMY ETYKIETĘ: Teraz zajmuje aż 340 pikseli (czyli większość płyty)
label_size = 340
label_img = label_img.resize(
    (label_size, label_size), Image.Resampling.LANCZOS
)

mask = Image.new("L", (label_size, label_size), 0)
mask_draw = ImageDraw.Draw(mask)
mask_draw.ellipse([0, 0, label_size, label_size], fill=255)

circular_label = Image.new("RGBA", (label_size, label_size), (0, 0, 0, 0))
circular_label.paste(label_img, (0, 0), mask)

# Środkowa dziurka na oś adaptera
hole_r = 20
hole_mask = Image.new("L", (label_size, label_size), 255)
hole_draw = ImageDraw.Draw(hole_mask)
hole_draw.ellipse(
    [
        label_size // 2 - hole_r,
        label_size // 2 - hole_r,
        label_size // 2 + hole_r,
        label_size // 2 + hole_r,
    ],
    fill=0,
)
circular_label.putalpha(
    Image.composite(
        circular_label.split()[3],
        Image.new("L", (label_size, label_size), 0),
        hole_mask,
    )
)

label_pos = (center - label_size // 2, center - label_size // 2)
base_vinyl.paste(circular_label, label_pos, circular_label)

# Generowanie klatek animacji
frames = []
num_frames = 30
for i in range(num_frames):
  angle = i * (360 / num_frames)
  rotated = base_vinyl.rotate(angle, resample=Image.Resampling.BICUBIC)
  frame_resized = rotated.resize((76, 76), Image.Resampling.LANCZOS)
  frames.append(frame_resized)

frames[0].save(
    "vinyl.gif",
    save_all=True,
    append_images=frames[1:],
    optimize=False,
    duration=40,
    loop=0,
)
print("Sukces! Wygenerowano nowy, wyraźny vinyl.gif z dużym anime!")