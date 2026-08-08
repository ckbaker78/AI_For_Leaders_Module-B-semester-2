from __future__ import annotations

import json
from pathlib import Path

import fitz
from docx import Document
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT / "CalvinBaker_DX699O2_Final_Project_Module_B.docx"
PDF = (
    ROOT
    / "tmp/report/rendered/CalvinBaker_DX699O2_Final_Project_Module_B_QA_final.pdf"
)
WEEK12 = ROOT / "Week12CalvinBakerSubmission.ipynb"
VALIDATION = ROOT / "tmp/report/figures/validation.json"

required_labels = [
    "1. Problem statement/description",
    "2. Exploratory data analysis",
    "a. Multivariate analysis",
    "b. Random forest analysis",
    "c. Relationship to analysis from Week 1-7",
    "3. Data conclusions",
    "4. Proposal",
    "5. Teamwork",
    "6. Citations/bibliography",
    "7. AI Appendix",
    "8. Weekly graphs and homework assignments",
]

document = Document(DOCX)
document_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
pdf = fitz.open(PDF)
page_texts = [page.get_text() for page in pdf]
pdf_text = "\n".join(page_texts)
notebook = json.loads(WEEK12.read_text())
model_validation = json.loads(VALIDATION.read_text())

notebook_errors = []
for cell_index, cell in enumerate(notebook["cells"], 1):
    if cell.get("cell_type") != "code":
        continue
    for output in cell.get("outputs", []):
        if output.get("output_type") == "error":
            notebook_errors.append(
                {
                    "cell": cell_index,
                    "ename": output.get("ename"),
                    "evalue": output.get("evalue"),
                }
            )

section = document.sections[0]
normal_style = document.styles["Normal"]
checks = {
    "docx_exists": DOCX.exists(),
    "docx_size_bytes": DOCX.stat().st_size,
    "required_labels_present": {
        label: label in document_text for label in required_labels
    },
    "one_inch_margins": all(
        value == Inches(1)
        for value in (
            section.top_margin,
            section.bottom_margin,
            section.left_margin,
            section.right_margin,
        )
    ),
    "normal_style": {
        "font": normal_style.font.name,
        "size_pt": normal_style.font.size.pt if normal_style.font.size else None,
        "double_spacing": normal_style.paragraph_format.line_spacing == 2,
    },
    "embedded_images": len(document.inline_shapes),
    "numbered_figure_captions": {
        f"Figure {index}.": f"Figure {index}." in pdf_text
        for index in range(1, 7)
    },
    "body_table_caption_present": "Table 1." in document_text,
    "pdf_pages_total": len(pdf),
    "body_pages_before_appendix": next(
        index for index, text in enumerate(page_texts, 1) if "Appendices" in text
    )
    - 1,
    "appendix_starts_on_page": next(
        index for index, text in enumerate(page_texts, 1) if "Appendices" in text
    ),
    "placeholder_tokens_found": any(
        token in document_text.lower()
        for token in ("[placeholder", "[insert", "tbd", "todo")
    ),
    "week12": {
        "cells": len(notebook["cells"]),
        "executed_final_cell": notebook["cells"][-1].get("execution_count") is not None,
        "final_cell_outputs": len(notebook["cells"][-1].get("outputs", [])),
        "errors": notebook_errors,
    },
    "validated_auc": {
        key: round(value["test_roc_auc"], 3)
        for key, value in model_validation["validated_model_refits"].items()
    },
}

checks["all_required_labels_present"] = all(
    checks["required_labels_present"].values()
)
checks["all_figure_captions_present"] = all(
    checks["numbered_figure_captions"].values()
)
checks["overall_pass"] = all(
    [
        checks["all_required_labels_present"],
        checks["one_inch_margins"],
        checks["normal_style"]["font"] == "Times New Roman",
        checks["normal_style"]["size_pt"] == 12,
        checks["normal_style"]["double_spacing"],
        checks["embedded_images"] == 6,
        checks["all_figure_captions_present"],
        checks["body_table_caption_present"],
        checks["body_pages_before_appendix"] == 10,
        checks["appendix_starts_on_page"] == 11,
        not checks["placeholder_tokens_found"],
        checks["week12"]["executed_final_cell"],
        not checks["week12"]["errors"],
    ]
)

output = ROOT / "tmp/report/final_qa.json"
output.write_text(json.dumps(checks, indent=2))
print(json.dumps(checks, indent=2))
