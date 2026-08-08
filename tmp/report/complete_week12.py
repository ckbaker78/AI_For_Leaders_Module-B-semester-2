from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Week12.ipynb"
OUTPUT = ROOT / "Week12CalvinBakerSubmission.ipynb"

notebook = nbformat.read(SOURCE, as_version=4)

answer = nbformat.v4.new_markdown_cell(
    """### Comparison of the two presentations

**Separate panels.** The separate-panel version keeps the two weeks visually distinct, so each week's shape is easy to inspect and overlapping lines cannot hide one another. Its main disadvantage is that the viewer must move back and forth between panels to compare the same day. The original version also labels only the final axes, which makes the shared day scale less immediate.

**Overlaid lines.** The shared-axis version makes day-by-day gaps, crossovers, and the overall change between weeks much easier to compare because both series use the same scale. Its disadvantages are that the lines can overlap, the plot needs direct labels or a legend, and color alone should not carry the distinction.

**Recommendation.** Use the overlaid version for this question, but add weekday labels, direct series labels, a shared scale, and restrained color. Those changes make the comparison fast without adding clutter."""
)

# Insert the written response immediately after the two comparison graphs.
notebook.cells.insert(7, answer)

storytelling_code = """# Chapter 8 recreation: direct labels, restrained color, and an action-oriented title
# Source data: Knaflic, Storytelling with Data, official Chapter 8 workbook.
years = np.arange(2019, 2026)
prices = {
    "Product A": [395, 420, 425, 390, 300, 270, 260],
    "Product B": [360, 400, 410, 375, 290, 260, 250],
    "Product C": [np.nan, np.nan, 100, 180, 198, 240, 180],
    "Product D": [np.nan, np.nan, np.nan, 160, 260, 220, 215],
    "Product E": [np.nan, np.nan, np.nan, np.nan, np.nan, 98, 210],
}

fig, ax = plt.subplots(figsize=(11, 6))
line_colors = ["#4A5568", "#667085", "#98A2B3", "#B0B7C3", "#C5CAD3"]
label_positions = {
    "Product A": 270,
    "Product B": 250,
    "Product C": 180,
    "Product D": 225,
    "Product E": 205,
}

for (label, values), color in zip(prices.items(), line_colors):
    values = np.asarray(values, dtype=float)
    ax.plot(years, values, color=color, linewidth=2.2)
    ax.scatter(years[-1], values[-1], s=55, color="#D95F02", zorder=3)
    label_y = label_positions[label]
    ax.plot(
        [years[-1] + 0.02, years[-1] + 0.09],
        [values[-1], label_y],
        color="#98A2B3",
        linewidth=0.9,
    )
    ax.text(
        years[-1] + 0.10,
        label_y,
        f"{label}: ${values[-1]:.0f}",
        va="center",
        fontsize=11,
        color="#344054",
    )

average_2025 = np.mean([values[-1] for values in prices.values()])
ax.axhline(average_2025, color="#D95F02", linewidth=1.4, linestyle="--")
ax.text(
    2019.05,
    average_2025 + 8,
    f"2025 average: ${average_2025:.0f}",
    color="#A23B00",
    fontsize=11,
    weight="bold",
)

ax.set_title(
    "Retail prices converged to an average of $223 by 2025",
    loc="left",
    fontsize=18,
    weight="bold",
    pad=18,
)
ax.text(
    0,
    1.01,
    "Later entrants launched below Products A and B, while the older products declined from their peaks",
    transform=ax.transAxes,
    fontsize=11,
    color="#667085",
)
ax.set_xlim(2019, 2026.05)
ax.set_ylim(50, 460)
ax.set_xticks(years)
ax.set_ylabel("Retail price ($)")
ax.grid(axis="y", color="#E4E7EC", linewidth=0.8)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.text(
    0,
    -0.14,
    "Source: Knaflic, Cole. Storytelling with Data, Chapter 8 workbook (Wiley, 2015; refreshed 2025).",
    transform=ax.transAxes,
    fontsize=9,
    color="#667085",
)
plt.tight_layout()
plt.show()
"""

notebook.cells[-1] = nbformat.v4.new_code_cell(storytelling_code)

# Execute the submission copy so the grader sees the completed output without
# needing to re-run the notebook.
client = NotebookClient(
    notebook,
    timeout=180,
    kernel_name="python3",
    resources={"metadata": {"path": str(ROOT)}},
)
client.execute()
nbformat.write(notebook, OUTPUT)
print(OUTPUT)
