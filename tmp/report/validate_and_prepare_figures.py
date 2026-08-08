from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tmp" / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#4C78A8"
ORANGE = "#D55E00"
ORANGE_LIGHT = "#E8A15F"
GRAY = "#AEB4BC"
DARK = "#263238"
MUTED = "#667085"
GRID = "#E6E8EB"

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 10,
        "axes.titleweight": "bold",
        "text.color": DARK,
        "axes.labelcolor": DARK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
    }
)


def clean_axis(ax, grid_axis: str = "x") -> None:
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.spines["bottom"].set_color("#CDD3D8")


def fit_model(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    dataset: str,
    n_estimators: int,
    max_depth: int,
    min_samples_leaf: int,
    max_features: str | float,
) -> dict[str, object]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        stratify=y,
        random_state=42,
    )
    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_leaf=min_samples_leaf,
                    max_features=max_features,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)
    probabilities = pipeline.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    scored = pd.DataFrame(
        {
            "actual": np.asarray(y_test),
            "score": probabilities,
        }
    )
    scored["risk_decile"] = pd.qcut(
        scored["score"].rank(method="first"),
        10,
        labels=range(1, 11),
    )
    deciles = (
        scored.groupby("risk_decile", observed=True)
        .agg(
            observed_rate=("actual", "mean"),
            average_score=("score", "mean"),
            records=("actual", "size"),
        )
        .reset_index()
    )
    feature_importance = pd.Series(
        pipeline.named_steps["model"].feature_importances_,
        index=X.columns,
    ).sort_values(ascending=False)
    return {
        "dataset": dataset,
        "rows": int(len(X)),
        "adverse_rate": float(y.mean()),
        "test_roc_auc": float(roc_auc_score(y_test, probabilities)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions)),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "importance": feature_importance,
        "deciles": deciles,
    }


# Validate the mortgage source and reproduce the final selected model.
mortgage_features = [
    "loan_amount",
    "property_value",
    "income",
    "LTV",
    "Credit_Score",
    "dtir1",
]
mortgage_raw = pd.read_csv(
    ROOT / "DATA" / "Loan_Default.csv",
    usecols=mortgage_features + ["Status", "rate_of_interest"],
).replace([np.inf, -np.inf], np.nan)
mortgage_complete = mortgage_raw.dropna(
    subset=mortgage_features + ["Status"]
).copy()
mortgage_result = fit_model(
    mortgage_complete[mortgage_features],
    mortgage_complete["Status"].astype(int),
    dataset="Mortgage Loan Default",
    n_estimators=208,
    max_depth=12,
    min_samples_leaf=13,
    max_features="sqrt",
)

# Validate the accepted-loan sample exactly as the Week 9-11 notebooks do.
lending_features = [
    "loan_amnt",
    "int_rate",
    "installment",
    "annual_inc",
    "dti",
    "fico_range_low",
    "open_acc",
    "revol_util",
    "total_acc",
]
accepted_path = (
    ROOT
    / "DATA"
    / "All Lending Club Loan Data"
    / "accepted_2007_to_2018q4.csv"
    / "accepted_2007_to_2018Q4.csv"
)
accepted_total_rows = 2_260_701
accepted_every = max(accepted_total_rows // 60_000, 1)
accepted = pd.read_csv(
    accepted_path,
    usecols=lending_features + ["loan_status"],
    skiprows=lambda row: row > 0 and row % accepted_every != 0,
    low_memory=False,
)
bad_statuses = {
    "Charged Off",
    "Default",
    "Late (31-120 days)",
    "Late (16-30 days)",
    "Does not meet the credit policy. Status:Charged Off",
}
accepted["bad_loan"] = accepted["loan_status"].isin(bad_statuses).astype(int)
lending_result = fit_model(
    accepted[lending_features].replace([np.inf, -np.inf], np.nan),
    accepted["bad_loan"],
    dataset="Accepted Lending Club",
    n_estimators=289,
    max_depth=8,
    min_samples_leaf=12,
    max_features=1.0,
)


# Figure 4: PCA comparison using the exact values printed in Week 9.
mortgage_pca = np.array([0.344, 0.184, 0.169, 0.166, 0.093, 0.044])
lending_pca = np.array([0.262, 0.205, 0.170, 0.114, 0.090, 0.076, 0.046, 0.031, 0.006])

fig, ax = plt.subplots(figsize=(10.5, 5.8))
for values, label, color, marker in [
    (mortgage_pca, "Mortgage loan-default data", BLUE, "o"),
    (lending_pca, "Accepted Lending Club data", ORANGE, "s"),
]:
    cumulative = np.cumsum(values)
    x = np.arange(1, len(values) + 1)
    ax.plot(
        x,
        cumulative,
        label=label,
        color=color,
        marker=marker,
        linewidth=2.2,
        markersize=6,
    )
    threshold = int(np.argmax(cumulative >= 0.80) + 1)
    ax.scatter(
        threshold,
        cumulative[threshold - 1],
        s=90,
        color=color,
        edgecolor="white",
        linewidth=1.2,
        zorder=4,
    )
    ax.annotate(
        f"{threshold} components: {cumulative[threshold - 1]:.1%}",
        (threshold, cumulative[threshold - 1]),
        xytext=(8, -18 if label.startswith("Mortgage") else 10),
        textcoords="offset points",
        color=color,
        fontsize=9,
        weight="bold",
    )
ax.axhline(0.80, color="#667085", linestyle="--", linewidth=1.2)
ax.text(8.9, 0.812, "80% retention target", ha="right", color=MUTED, fontsize=9)
fig.suptitle(
    "Cumulative Variance Explained by Principal Components",
    x=0.07,
    y=0.98,
    ha="left",
    fontsize=19,
    fontweight="bold",
)
fig.text(
    0.07,
    0.925,
    "Standardized numeric features; one or two components do not preserve enough structure",
    fontsize=9.5,
    color=MUTED,
)
ax.set_xlabel("Number of principal components retained")
ax.set_ylabel("Cumulative variance explained")
ax.set_xticks(range(1, 10))
ax.set_xlim(1, 9)
ax.set_ylim(0.20, 1.03)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
ax.legend(frameon=False, loc="lower right")
clean_axis(ax, grid_axis="y")
fig.tight_layout(rect=[0.03, 0.02, 1, 0.89])
fig.savefig(OUT / "figure-04-pca-comparison.png", dpi=220, bbox_inches="tight")
plt.close(fig)


# Figure 5: feature importance comparison from the validated refits.
fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.8))
for ax, result, title in [
    (axes[0], mortgage_result, "Mortgage loan-default model"),
    (axes[1], lending_result, "Accepted Lending Club model"),
]:
    importance = result["importance"]
    top_n = 6 if title.startswith("Mortgage") else 7
    ordered = importance.head(top_n).sort_values()
    colors = [ORANGE if name == importance.index[0] else GRAY for name in ordered.index]
    bars = ax.barh(ordered.index, ordered.values, color=colors)
    for bar, value in zip(bars, ordered.values):
        ax.text(
            value + ordered.max() * 0.018,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            fontsize=8.5,
            color=MUTED,
        )
    ax.set_title(title, loc="left", fontsize=12)
    ax.set_xlabel("Impurity-based importance")
    ax.set_xlim(0, ordered.max() * 1.18)
    clean_axis(ax)
fig.suptitle(
    "Random Forest Feature Importance by Dataset",
    x=0.07,
    ha="left",
    fontsize=15,
    fontweight="bold",
)
fig.text(
    0.07,
    0.92,
    "Importance indicates how often a feature improved model splits; it is not a causal effect",
    color=MUTED,
    fontsize=9.5,
)
fig.tight_layout(rect=[0.04, 0.02, 1, 0.90])
fig.savefig(OUT / "figure-05-feature-importance.png", dpi=220, bbox_inches="tight")
plt.close(fig)


# Figure 6: observed outcome rate by predicted-risk decile.
fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.8), sharey=False)
for ax, result, title, label in [
    (
        axes[0],
        mortgage_result,
        "Mortgage loan-default model",
        "Observed default rate",
    ),
    (
        axes[1],
        lending_result,
        "Accepted Lending Club model",
        "Observed bad-loan rate",
    ),
]:
    deciles = result["deciles"]
    x = deciles["risk_decile"].astype(int)
    rates = deciles["observed_rate"]
    colors = [GRAY] * 7 + [ORANGE_LIGHT, "#DF7A2B", ORANGE]
    bars = ax.bar(x, rates, color=colors, width=0.78)
    for bar, rate in zip(bars, rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate + rates.max() * 0.018,
            f"{rate:.0%}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=MUTED if rate < result["adverse_rate"] else "#9A3F00",
            weight="bold",
        )
    ax.axhline(
        result["adverse_rate"],
        color=BLUE,
        linestyle="--",
        linewidth=1.3,
    )
    ax.text(
        1,
        result["adverse_rate"] + rates.max() * 0.025,
        f"Portfolio average: {result['adverse_rate']:.1%}",
        color=BLUE,
        fontsize=8.8,
        weight="bold",
    )
    ax.set_title(title, loc="left", fontsize=12)
    ax.set_xlabel("Predicted-risk decile")
    ax.set_ylabel(label)
    ax.set_xticks(range(1, 11))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_ylim(0, rates.max() * 1.14)
    clean_axis(ax, grid_axis="y")
fig.suptitle(
    "Observed Adverse-Outcome Rate by Predicted-Risk Decile",
    x=0.07,
    ha="left",
    fontsize=15,
    fontweight="bold",
)
fig.text(
    0.07,
    0.92,
    "Held-out test sets; decile 1 is the lowest predicted risk and decile 10 is the highest",
    color=MUTED,
    fontsize=9.5,
)
fig.tight_layout(rect=[0.04, 0.02, 1, 0.90])
fig.savefig(OUT / "figure-06-risk-deciles.png", dpi=220, bbox_inches="tight")
plt.close(fig)


missingness_risk = {}
for column in ["property_value", "LTV", "rate_of_interest", "dtir1", "income"]:
    rates = (
        mortgage_raw.assign(is_missing=mortgage_raw[column].isna())
        .groupby("is_missing")["Status"]
        .agg(["mean", "size"])
    )
    missingness_risk[column] = {
        str(index): {"default_rate": float(row["mean"]), "rows": int(row["size"])}
        for index, row in rates.iterrows()
    }

validation = {
    "mortgage_source": {
        "rows": int(len(mortgage_raw)),
        "columns_in_source": 34,
        "overall_default_rate": float(mortgage_raw["Status"].mean()),
        "complete_case_rows": int(len(mortgage_complete)),
        "complete_case_default_rate": float(mortgage_complete["Status"].mean()),
        "missingness_outcome_check": missingness_risk,
    },
    "accepted_lending_club_source": {
        "source_rows": accepted_total_rows,
        "sample_rows": int(len(accepted)),
        "sample_bad_loan_rate": float(accepted["bad_loan"].mean()),
        "grade_counts_available": bool("loan_status" in accepted.columns),
    },
    "validated_model_refits": {
        "mortgage": {
            key: value
            for key, value in mortgage_result.items()
            if key not in {"importance", "deciles"}
        },
        "lending_club": {
            key: value
            for key, value in lending_result.items()
            if key not in {"importance", "deciles"}
        },
    },
}
(OUT / "validation.json").write_text(
    json.dumps(validation, indent=2),
    encoding="utf-8",
)
print(json.dumps(validation, indent=2))
