from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
PAGE_DIR = ROOT / "tmp/report/rendered_pages"
OUTPUT = ROOT / "tmp/report/rendered_pages_contact_sheet.png"

pages = sorted(PAGE_DIR.glob("page-*.png"))
thumb_width = 285
thumb_height = 369
label_height = 28
gap = 18
columns = 3
rows = (len(pages) + columns - 1) // columns
sheet = Image.new(
    "RGB",
    (
        columns * thumb_width + (columns + 1) * gap,
        rows * (thumb_height + label_height) + (rows + 1) * gap,
    ),
    "white",
)
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=16)

for index, path in enumerate(pages):
    page = Image.open(path).convert("RGB")
    page.thumbnail((thumb_width, thumb_height))
    column = index % columns
    row = index // columns
    x = gap + column * (thumb_width + gap)
    y = gap + row * (thumb_height + label_height + gap)
    sheet.paste(page, (x, y))
    draw.text((x, y + thumb_height + 4), f"Page {index + 1}", fill="#111111", font=font)

sheet.save(OUTPUT)
print(OUTPUT)
