from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tmp" / "notebooks" / "extracted"
OUT.mkdir(parents=True, exist_ok=True)

NOTEBOOKS = [
    "Week1.ipynb",
    "Week2.ipynb",
    "Week3.ipynb",
    "Week4CalvinBakerSubmission.ipynb",
    "Week5-concealed-answer.ipynb",
    "Week6.ipynb",
    "Week7.ipynb",
    "Week8.ipynb",
    "Week9CalvinBakerSubmission.ipynb",
    "Week10.ipynb",
    "Week11.ipynb",
    "Week12.ipynb",
    "Week12CalvinBakerSubmission.ipynb",
]


def clean_text(value: object) -> str:
    if isinstance(value, list):
        value = "".join(str(part) for part in value)
    text = str(value)
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    return text.rstrip()


def extract_output(output: dict, image_dir: Path, image_index: int) -> tuple[str, int]:
    lines: list[str] = []
    output_type = output.get("output_type")
    if output_type == "stream":
        lines.append(clean_text(output.get("text", "")))
    elif output_type == "error":
        lines.append(
            f"ERROR {output.get('ename', '')}: {output.get('evalue', '')}\n"
            + "\n".join(output.get("traceback", []))
        )
    else:
        data = output.get("data", {})
        for mime in ("text/plain", "text/markdown", "text/html"):
            if mime in data:
                text = clean_text(data[mime])
                if mime == "text/html":
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text)
                lines.append(f"[{mime}]\n{text}")
        for mime, suffix in (("image/png", "png"), ("image/jpeg", "jpg")):
            if mime in data:
                payload = data[mime]
                if isinstance(payload, list):
                    payload = "".join(payload)
                image_dir.mkdir(parents=True, exist_ok=True)
                image_path = image_dir / f"figure-{image_index:03d}.{suffix}"
                image_path.write_bytes(base64.b64decode(payload))
                lines.append(f"[{mime}] {image_path.relative_to(ROOT)}")
                image_index += 1
    return "\n".join(line for line in lines if line), image_index


manifest: list[dict[str, object]] = []
for notebook_name in NOTEBOOKS:
    source = ROOT / notebook_name
    if not source.exists():
        continue

    nb = nbformat.read(source, as_version=4)
    output_path = OUT / f"{source.stem}.txt"
    image_dir = OUT / source.stem
    report_lines = [
        f"# {notebook_name}",
        f"Cells: {len(nb.cells)}",
        "",
    ]
    image_index = 1
    code_cells = 0
    markdown_cells = 0
    output_cells = 0
    errors = 0

    for idx, cell in enumerate(nb.cells, 1):
        source_text = clean_text(cell.get("source", ""))
        if cell.cell_type == "markdown":
            markdown_cells += 1
            report_lines.extend([f"\n## CELL {idx} MARKDOWN", source_text])
        elif cell.cell_type == "code":
            code_cells += 1
            report_lines.extend(
                [
                    f"\n## CELL {idx} CODE execution_count={cell.get('execution_count')}",
                    source_text,
                ]
            )
            outputs = cell.get("outputs", [])
            if outputs:
                output_cells += 1
                report_lines.append("\n### OUTPUT")
            for output in outputs:
                if output.get("output_type") == "error":
                    errors += 1
                extracted, image_index = extract_output(output, image_dir, image_index)
                if extracted:
                    report_lines.append(extracted)
        else:
            report_lines.extend(
                [f"\n## CELL {idx} {cell.cell_type.upper()}", source_text]
            )

    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    manifest.append(
        {
            "file": notebook_name,
            "cells": len(nb.cells),
            "markdown_cells": markdown_cells,
            "code_cells": code_cells,
            "code_cells_with_outputs": output_cells,
            "embedded_images": image_index - 1,
            "errors": errors,
            "text_export": str(output_path.relative_to(ROOT)),
        }
    )

(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
