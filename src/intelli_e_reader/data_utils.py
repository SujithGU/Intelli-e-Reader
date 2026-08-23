"""
Raw -> processed data pipeline, replacing the equivalent one-off scripts
under src/intelli_e_reader/data_pipeline/. Run it directly to regenerate
every data/processed/ file:

    python -m intelli_e_reader.data_utils
"""
import ast
import json

import pandas as pd

from config import Config


def save_processed(df: pd.DataFrame, name: str) -> None:
    """Save a processed DataFrame as parquet under data/processed/."""
    path = f"{Config.PROCESSED_DATA_FOLDER}/{name}.parquet"
    df.to_parquet(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


def build_family1_word_cefr() -> pd.DataFrame:
    """Word CEFR difficulty: merge the English Profile scrape (cleaned) with
    the teacher survey ratings, English Profile winning on overlap."""
    scraped = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/english_profile_cleaned.csv").assign(source="english_profile")
    teachers = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/teacher_survey_cefr_ratings.csv").assign(source="teacher_survey")
    teachers = teachers.rename(columns={"cefr_level_avg": "cefr_int", "cefr_level": "cefr"})

    df = pd.concat([scraped, teachers], ignore_index=True)
    # pandas silently reads the literal "NA" pos value as a real NaN by default,
    # which would break every (word, pos) join downstream -- restore it as an
    # ordinary, matchable category instead.
    df["pos"] = df["pos"].fillna("NA")
    df = df.drop_duplicates(subset=["word", "pos"], keep="first")
    return df


def build_family2_synonyms(family1_word_cefr: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synonyms: combine the synonym-scraper and thesaurus-scraper sources,
    then validate each candidate against Family 1's CEFR ratings -- mirrors
    reader/custom_reader.py's generate_synonyms/get_seperated_synonyms,
    which looks up every candidate's own CEFR level (keyed on the *original*
    word's part of speech) and silently drops candidates with no rating.

    Returns (word_synonyms, candidates_with_cefr):
      - word_synonyms: Family 1 (word, pos, cefr, ...) with each word's raw
        candidate list attached (unfiltered -- includes candidates with no
        CEFR rating). This is the combined word_cefr + synonyms table --
        Family 1 on its own isn't saved separately since this is a strict
        superset of it (same (word, pos) grain, same columns plus
        synonym_list).
      - candidates_with_cefr: one row per (original_word, candidate) pair,
        inner-joined so only candidates that themselves have a CEFR rating
        survive -- this is what the live app actually ends up using. Kept
        as a separate table since it's a different grain (one row per
        candidate, not per word) -- merging it into word_synonyms would mean
        repeating every word-level column once per candidate.
    """
    with open(f"{Config.RAW_DATA_FOLDER}/pos_acronym_map.json") as f:
        acronym_map = json.load(f)
    full_pos_map = {v: k for k, v in acronym_map.items()}

    synonyms = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/synonyms_scrape.csv").rename(
        columns={"Word": "word", "Synonyms": "synonym_list"})
    thesaurus = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/thesaurus_scrape.csv").rename(
        columns={"Word": "word", "Synonyms": "synonym_list"})
    synonyms["synonym_list"] = synonyms["synonym_list"].apply(ast.literal_eval)
    thesaurus["synonym_list"] = thesaurus["synonym_list"].apply(ast.literal_eval)
    thesaurus[["word", "pos"]] = thesaurus["word"].str.rsplit("_", n=1, expand=True)
    thesaurus["pos"] = thesaurus["pos"].map(full_pos_map)

    combined = pd.merge(synonyms, thesaurus, on="word", how="outer", suffixes=("_syn", "_thes"))

    def combine_lists(row):
        a = row["synonym_list_syn"] if isinstance(row["synonym_list_syn"], list) else []
        b = row["synonym_list_thes"] if isinstance(row["synonym_list_thes"], list) else []
        return a + b

    combined["synonym_list"] = combined.apply(combine_lists, axis=1)

    word_synonyms = family1_word_cefr.merge(
        combined[["word", "pos", "synonym_list"]], on=["word", "pos"], how="left")
    # A handful of (word, pos) pairs have duplicate rows in the raw thesaurus
    # source, which the merge above would otherwise carry through as exact
    # duplicate rows here.
    word_synonyms = word_synonyms.drop_duplicates(subset=["word", "pos"], keep="first")

    candidates = (word_synonyms[["word", "pos", "synonym_list"]]
                  .explode("synonym_list")
                  .dropna(subset=["synonym_list"])
                  .rename(columns={"word": "original_word", "synonym_list": "candidate"}))

    candidates_with_cefr = candidates.merge(
        family1_word_cefr[["word", "pos", "cefr"]].rename(columns={"word": "candidate"}),
        on=["candidate", "pos"], how="inner")

    return word_synonyms, candidates_with_cefr


def build_family3_vocabulary() -> pd.DataFrame:
    """Full English vocabulary + POS tags. The processed file already
    exists (src/intelli_e_reader/data_pipeline/create_word_dataset.py's
    output) -- this loads and verifies it against the raw word list rather
    than re-deriving it (re-tagging ~370k words one at a time is slow, and
    nothing upstream has changed)."""
    vocabulary = (pd.read_json(f"{Config.RAW_DATA_FOLDER}/all_english_words.json", typ="series")
                  .index.to_series(name="eng_words").reset_index(drop=True))
    # "nan" and "null" are real words in this vocabulary -- also on pandas'
    # default missing-value sentinel list, same trap as Family 1's "NA" pos.
    tagged = pd.read_csv(f"{Config.PROCESSED_DATA_FOLDER}/all_english_words_tagged.csv",
                         keep_default_na=False, na_values=[""])

    assert set(vocabulary) == set(tagged["eng_words"]), \
        "all_english_words.json and all_english_words_tagged.csv have diverged"
    return tagged


def build_all() -> None:
    # family1_word_cefr is computed but not saved on its own -- see
    # build_family2_synonyms' docstring.
    family1_word_cefr = build_family1_word_cefr()

    family2_word_synonyms, family2_candidates_with_cefr = build_family2_synonyms(family1_word_cefr)
    save_processed(family2_word_synonyms, "family2_word_synonyms")
    save_processed(family2_candidates_with_cefr, "family2_synonym_candidates_with_cefr")

    family3_vocabulary = build_family3_vocabulary()
    save_processed(family3_vocabulary, "family3_vocabulary")


if __name__ == "__main__":
    build_all()
