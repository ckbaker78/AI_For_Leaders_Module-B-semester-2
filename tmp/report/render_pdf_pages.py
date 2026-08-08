from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "CalvinBaker_DX699O2_Final_Project_Module_B_QA.pdf"
OUT = ROOT / "tmp/report/rendered_pages"
OUT.mkdir(parents=True, exist_ok=True)

document = fitz.open(PDF)
matrix = fitz.Matrix(1.55, 1.55)
for index, page in enumerate(document):
    image = page.get_pixmap(matrix=matrix, alpha=False)
    image.save(OUT / f"page-{index + 1:02d}.png")
print(f"Rendered {len(document)} pages to {OUT}")
