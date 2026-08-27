"""Shared plumbing for the CEFR-prediction models: MLflow setup, the
train/test split used by every model tier (so results are comparable
across tiers), a common evaluation function, and class-weight computation
for the CEFR class imbalance (~4:1 largest:smallest, see README.md's
"final word->CEFR dataset" section).

Feature engineering and model architectures live with each tier in
notebook/CEFR-Model-Training.ipynb, not here.
"""
import mlflow
import numpy as np
import pandas as pd
import torch
from nltk.corpus import wordnet as wn
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from torch.utils.data import TensorDataset

from config import Config


def set_up_mlflow(experiment_name: str = "cefr-prediction"):
    """Local, file-free SQLite backend -- self-contained, no server needed,
    works for anyone who clones the repo. View results with:
        cd <repo root> && .venv/bin/mlflow ui --backend-store-uri sqlite:///mlflow.db
    """
    mlflow.set_tracking_uri(f"sqlite:///{Config.PROJECT_ROOT_FOLDER}/mlflow.db")
    mlflow.set_experiment(experiment_name)


def make_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    """Stratified by cefr_int, so every level -- including the thin A1/C2
    buckets -- is represented in both train and test, not just the common
    ones."""
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state, stratify=df["cefr_int"]
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def class_weights(train_df: pd.DataFrame) -> dict[int, float]:
    """Inverse-frequency weights per cefr_int (1-6), for whichever model's
    class_weight/loss-weighting mechanism -- sklearn's class_weight=,
    PyTorch's CrossEntropyLoss(weight=...), etc."""
    counts = train_df["cefr_int"].value_counts()
    total = len(train_df)
    n_classes = counts.index.nunique()
    return {cls: total / (n_classes * count) for cls, count in counts.items()}


def evaluate_predictions(y_true, y_pred, log_to_mlflow: bool = True) -> dict:
    """Common metric set for every model tier: accuracy + macro F1 (treats
    CEFR as categorical) and MAE on cefr_int (treats it as ordinal -- an
    off-by-one error costs less than an off-by-four, which plain accuracy
    can't distinguish -- ties back to the off-by-one analysis from the
    EFLLex cross-check earlier)."""
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro"),
        "mae_ordinal": mean_absolute_error(y_true, y_pred),
    }
    if log_to_mlflow:
        mlflow.log_metrics(metrics)
    return metrics


_NUMERIC_FEATURE_COLS = [
    "total_freq", "convs_freq", "phonem_count", "letter_count",
    "syllable_count", "aoa_kup_lem", "concreteness_score",
]
_CATEGORICAL_FEATURE_COLS = ["pos", "etymology_flag"]
_LATINATE_SUFFIXES = ("ity", "ify", "ation", "ative", "ic", "inal")


def build_features(df: pd.DataFrame, encoder: OneHotEncoder = None, imputer: SimpleImputer = None):
    """Tier 1's feature pipeline: AoA, concreteness, WordNet polysemy, a
    suffix-based etymology flag, log-frequency, POS. Fit/transform-safe --
    pass no encoder/imputer to fit fresh ones on df (training), or pass
    already-fitted ones to reuse them via .transform() only (test/inference),
    so test-set statistics never leak into training.

    df needs 'word', 'pos', and 'total_freq' columns at minimum; anything
    else ('cefr'/'cefr_int'/'source'/etc.) passes through untouched.

    Returns (features_df, fitted_encoder, fitted_imputer).
    """
    df = df.copy()
    fitting = encoder is None  # both encoder and imputer are fit together, or not at all

    aoa_df = pd.read_excel(
        f"{Config.FEATURES_FOLDER}/AoA_51715_words.xlsx",
        usecols=["Word", "Freq_pm", "Nphon", "Nletters", "Nsyll", "AoA_Kup_lem", "Perc_known_lem"],
    )
    aoa_df = aoa_df[aoa_df["Perc_known_lem"] > 0.75].drop(columns="Perc_known_lem")
    aoa_df = aoa_df.rename(columns={
        "Word": "word", "Freq_pm": "convs_freq", "Nphon": "phonem_count",
        "Nletters": "letter_count", "Nsyll": "syllable_count", "AoA_Kup_lem": "aoa_kup_lem",
    })
    df = df.merge(aoa_df, on="word", how="left")

    concreteness_df = pd.read_excel(
        f"{Config.FEATURES_FOLDER}/Concreteness_ratings_Brysbaert_et_al_BRM.xlsx",
        usecols=["Word", "Percent_known", "Conc.M"],
    )
    concreteness_df = concreteness_df[concreteness_df["Percent_known"] > 0.75].drop(columns="Percent_known")
    concreteness_df = concreteness_df.rename(columns={"Word": "word", "Conc.M": "concreteness_score"})
    df = df.merge(concreteness_df, on="word", how="left")

    df["polysem_count"] = df["word"].apply(lambda w: len(wn.synsets(w)))
    df["etymology_flag"] = df["word"].apply(
        lambda w: "LATINATE" if w.endswith(_LATINATE_SUFFIXES) else "ANGLO_SAXON"
    )

    df["total_freq"] = np.log1p(df["total_freq"])
    df["convs_freq"] = np.log1p(df["convs_freq"])

    if fitting:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        encoded_array = encoder.fit_transform(df[_CATEGORICAL_FEATURE_COLS])
        imputer = SimpleImputer(strategy="median", add_indicator=True)
        imputed_array = imputer.fit_transform(df[_NUMERIC_FEATURE_COLS])
    else:
        encoded_array = encoder.transform(df[_CATEGORICAL_FEATURE_COLS])
        imputed_array = imputer.transform(df[_NUMERIC_FEATURE_COLS])

    encoded_df = pd.DataFrame(
        encoded_array, columns=encoder.get_feature_names_out(_CATEGORICAL_FEATURE_COLS),
        dtype=int, index=df.index,
    )
    imputed_df = pd.DataFrame(
        imputed_array, columns=imputer.get_feature_names_out(_NUMERIC_FEATURE_COLS), index=df.index,
    )

    df = pd.concat([
        df.drop(columns=_CATEGORICAL_FEATURE_COLS + _NUMERIC_FEATURE_COLS),
        encoded_df,
        imputed_df,
    ], axis=1)

    return df, encoder, imputer


class EarlyStopping:
    """Generic training bookkeeping, not tied to a specific model/tier. Call
    .step(val_loss, model) after each epoch's validation pass; it keeps a
    copy of the weights from whichever epoch had the best (lowest) val_loss
    so far, and sets .should_stop once `patience` epochs have passed with no
    improvement. `val_loss` doesn't have to be a literal loss -- pass in
    `-metric` for any "higher is better" metric to early-stop on that
    instead."""

    def __init__(self, patience: int = 10, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float("inf")
        self.best_epoch = None
        self.best_state = None
        self.counter = 0
        self.should_stop = False

    def step(self, val_loss: float, model, epoch: int | None = None):
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.best_epoch = epoch
            self.best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True

    def restore_best(self, model):
        """Loads the best-seen weights back into model, in place."""
        if self.best_state is not None:
            model.load_state_dict(self.best_state)


def embed_words(words, model_name: str = "roberta-base-nli-stsb-mean-tokens", device: str = None) -> dict:
    """Batch-encodes every unique word in `words` with a pretrained
    sentence-transformers model -- defaults to the model
    reader/semantic_check.py already uses live.

    Returns {word: embedding_vector}, a lookup by word rather than a bare
    array -- so it can be .map()'d back onto a dataframe regardless of row
    order or duplicates. Safe to compute once over the full vocabulary
    before splitting train/test: it's a fixed, pretrained, deterministic
    function of spelling, not fit on the data, so there's no leakage risk.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, device=device)
    unique_words = sorted(set(words))
    embeddings = model.encode(unique_words, show_progress_bar=True)
    return dict(zip(unique_words, embeddings))


def tokenize_dataset(
    df: pd.DataFrame, tokenizer, text_col: str = "word", label_col: str = "cefr_int", max_length: int = 16
) -> TensorDataset:
    """Tokenizes text_col with the given HuggingFace tokenizer and packages
    it into a TensorDataset alongside 0-indexed labels. Batches from the
    resulting DataLoader yield (input_ids, attention_mask, labels).

    Labels are shifted -1 here (cefr_int is 1-6, CrossEntropyLoss wants
    0-5), so callers don't each have to remember to do it.

    Called separately on train_df/test_df, same as build_features, for
    symmetry -- a pretrained tokenizer has no train-set statistics to leak,
    so it would technically be safe to call once on the full vocabulary,
    but keeping both call sites the same shape avoids surprises later.

    max_length=16 is generous headroom for single words after subword
    tokenization -- raise it if text_col ever holds something longer.
    """
    encoded = tokenizer(
        df[text_col].tolist(),
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    labels = torch.tensor(df[label_col].to_numpy() - 1, dtype=torch.long)
    return TensorDataset(encoded["input_ids"], encoded["attention_mask"], labels)
