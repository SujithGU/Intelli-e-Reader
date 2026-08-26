import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score


def plot_pos_distribution(df:pd.Dataframe,x_axis='pos',normalise=True):
    plt.figure(figsize=(15,6))
    sns.histplot(df,x=x_axis,stat='percent' if normalise else 'count')
    plt.title('Distribution of POS')
    plt.show()


CEFR_ORDINAL = {"a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6}
CEFR_BUCKET = {1: "A", 2: "A", 3: "B", 4: "B", 5: "C", 6: "C"}


def compare_cefr_sources(df_a, df_b, name_a="Source A", name_b="Source B",
                          join_on=("word", "pos"), cefr_col="cefr"):
    """
    Cross-check two word->CEFR sources on their overlapping (word, pos) pairs:
    inner-joins them, computes raw + bucketed (A/B/C) agreement, Cohen's Kappa
    (unweighted + linear-weighted, both raw and bucketed), and plots the two
    summary panels (agreement rate, direction of disagreement).

    df_a, df_b: each needs `join_on` columns plus a `cefr_col` column with
    values in {a1,a2,b1,b2,c1,c2}.

    Returns (combined_df, stats) — combined_df has the joined rows plus all
    derived columns (ordinal ints, bucket letters, level_diff), stats is a
    dict of the printed/plotted numbers for reuse in a markdown writeup.
    """
    combined = df_a.merge(df_b, on=list(join_on), suffixes=("_a", "_b"))

    combined["cefr_a_int"] = combined[f"{cefr_col}_a"].map(CEFR_ORDINAL)
    combined["cefr_b_int"] = combined[f"{cefr_col}_b"].map(CEFR_ORDINAL)

    for side, col in (("df_a", "cefr_a_int"), ("df_b", "cefr_b_int")):
        if combined[col].isna().any():
            bad_values = sorted(set(combined.loc[combined[col].isna(), f"{cefr_col}_{col[5]}"].unique()))
            raise ValueError(
                f"{side}'s '{cefr_col}' column has values that aren't in "
                f"CEFR_ORDINAL {sorted(CEFR_ORDINAL)}: {bad_values}. "
                f"compare_cefr_sources() expects a1-c2 labels, not collapsed A/B/C buckets "
                f"or raw cefr_int (1-6) — map those first."
            )
    combined["level_diff"] = combined["cefr_a_int"] - combined["cefr_b_int"]

    combined["bucket_a"] = combined["cefr_a_int"].map(CEFR_BUCKET)
    combined["bucket_b"] = combined["cefr_b_int"].map(CEFR_BUCKET)

    exact_raw = (combined["level_diff"] == 0).mean()
    exact_bucketed = (combined["bucket_a"] == combined["bucket_b"]).mean()

    stats = {
        "n_overlap": len(combined),
        "exact_match_raw": exact_raw,
        "exact_match_bucketed": exact_bucketed,
        "kappa_raw_unweighted": cohen_kappa_score(combined["cefr_a_int"], combined["cefr_b_int"]),
        "kappa_raw_linear": cohen_kappa_score(combined["cefr_a_int"], combined["cefr_b_int"], weights="linear"),
        "kappa_bucketed": cohen_kappa_score(combined["bucket_a"], combined["bucket_b"]),
        "mean_level_diff": combined["level_diff"].mean(),
        "median_level_diff": combined["level_diff"].median(),
    }

    order = [f"{name_b} harder", "Agreement", f"{name_a} harder"]
    conditions = [
        combined["bucket_a"] > combined["bucket_b"],
        combined["bucket_a"] == combined["bucket_b"],
        combined["bucket_a"] < combined["bucket_b"],
    ]
    combined["bucket_agreement"] = np.select(conditions, order, default="")
    pct = combined["bucket_agreement"].value_counts(normalize=True).reindex(order).fillna(0) * 100

    _, axes = plt.subplots(1, 2, figsize=(14, 5))

    match_rates = pd.Series({"Raw levels (A1-C2)": exact_raw, "Bucketed (A/B/C)": exact_bucketed}) * 100
    match_rates.plot(kind="bar", ax=axes[0], color=["#d95f5f", "#5f9ed9"])
    axes[0].set_ylabel("% exact agreement")
    axes[0].set_title(f"Agreement rate\n(kappa={stats['kappa_raw_linear']:.2f} linear-weighted)")
    axes[0].set_xticklabels(match_rates.index, rotation=0)
    for i, v in enumerate(match_rates):
        axes[0].text(i, v + 1, f"{v:.1f}%", ha="center")

    pct.plot(kind="bar", ax=axes[1], color=["#d9a25f", "#5f9ed9", "#d95f5f"])
    axes[1].set_ylabel("% of overlapping words")
    axes[1].set_title("Direction of disagreement (bucketed)")
    axes[1].set_xticklabels(order, rotation=15)
    for i, v in enumerate(pct):
        axes[1].text(i, v + 1, f"{v:.1f}%", ha="center")

    plt.suptitle(f"{name_a} vs {name_b} (n={len(combined):,} overlapping words)")
    plt.tight_layout()
    plt.show()

    return combined, stats