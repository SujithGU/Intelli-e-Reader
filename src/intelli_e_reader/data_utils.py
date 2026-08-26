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
    the teacher survey ratings, English Profile winning on overlap -- it's
    Cambridge's English Vocabulary Profile (corpus of real graded exam
    scripts), a more authoritative source than a 3-teacher survey.

    Reads teacher_survey_avg_scores.csv (raw per-word averages across the
    teachers, e.g. 1.667) rather than the older teacher_survey_cefr_ratings.csv
    (pre-rounded to a whole 1-6 level by a since-lost script, and missing
    ~2,200 words this file has). English Profile still wins on any (word,
    pos) both sources cover, so the rounding scheme below only actually
    determines the label for words English Profile doesn't rate at all.
    Rounding is pandas' default round-half-to-even (e.g. 2.5 -> 2, 3.5 -> 4),
    not round-half-up -- noted since CEFR bucket boundaries fall exactly on
    .5 for a 1-6 scale.
    """
    scraped = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/english_profile_cleaned.csv").assign(source="english_profile")

    teachers = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/teacher_survey_avg_scores.csv").rename(
        columns={"Word": "word", "PoS": "pos", "Teachers Avg": "cefr_int"})
    teachers = teachers.dropna(subset=["cefr_int"])
    teachers["word"] = teachers["word"].str.lower().str.strip()
    teachers = teachers.drop_duplicates(subset=["word", "pos"], keep="first")
    teachers["cefr_int"] = teachers["cefr_int"].round().astype(int)
    teachers["cefr"] = teachers["cefr_int"].map({1: "A", 2: "A", 3: "B", 4: "B", 5: "C", 6: "C"})
    teachers = teachers.assign(source="teacher_survey")

    df = pd.concat([scraped, teachers], ignore_index=True)
    # pandas silently reads the literal "NA" pos value as a real NaN by default,
    # which would break every (word, pos) join downstream -- restore it as an
    # ordinary, matchable category instead.
    df["pos"] = df["pos"].fillna("NA")
    df = df.drop_duplicates(subset=["word", "pos"], keep="first")
    return df


def build_efllex_cefr() -> pd.DataFrame:
    """Load EFLLex (UCLouvain's CEFRLex project -- normalized word frequency
    across ~40 graded readers + a handful of ESL coursebooks, not a large
    general corpus) and derive a per-word CEFR label the same way as
    Dataset-EDA.ipynb: whichever level-band has the highest frequency share
    for that word. EFLLex's source texts top out at C1 -- it has no C2
    label at all, so cefr_int here is always 1-5, never 6."""
    ptb_to_universal = {
        "NN": "NOUN", "JJ": "ADJ", "VB": "VERB", "RB": "ADV",
        "CD": "NUM", "IN": "ADP", "UH": "EXC", "PRP": "PRON",
        "PRP$": "PRON", "DT": "DET", "RP": "PART", "MD": "VERB",
        "PR": "PRON", "CC": "CONJ", "WP": "PRON", "WP$": "PRON",
        "WRB": "ADV", "PDT": "DET", "WDT": "DET", "TO": "ADP",
        "EX": "PRON", "FW": "X", "XX": "X", "RH": "X",
    }
    efllex = pd.read_csv(f"{Config.RAW_DATA_FOLDER}/EFLLex.tsv", sep="\t")
    drop_cols = ["word", "tag", "total_freq@total", "nb_doc@total", "face2face@total"]
    level_cols = efllex.columns.difference(drop_cols)
    cefr_label = efllex[level_cols].idxmax(axis=1).str.rsplit("@").str[-1].str.strip()

    efllex = efllex[["word", "tag", "total_freq@total"]].rename(
        columns={"tag": "pos", "total_freq@total": "total_freq"})
    efllex["pos"] = efllex["pos"].str.strip().replace(ptb_to_universal)

    ordinal_map = {"a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6}
    bucket_map = {1: "A", 2: "A", 3: "B", 4: "B", 5: "C", 6: "C"}
    efllex["cefr_int"] = cefr_label.map(ordinal_map)
    efllex["cefr"] = efllex["cefr_int"].map(bucket_map)
    efllex["source"] = "efllex"
    return efllex


def extend_family1_with_efllex(family1_word_cefr: pd.DataFrame, efllex_cefr: pd.DataFrame) -> pd.DataFrame:
    """Additive-only vocabulary expansion: appends (word, pos) pairs EFLLex
    covers that English Profile / the teacher survey don't rate at all.
    Never overrides an existing family1 rating -- English Profile stays GT
    wherever it has an opinion (see build_family1_word_cefr's docstring).
    Appended rows have no synonym_list (Family 2's synonym sources were
    never scraped for these words) and a real total_freq where family1's
    original rows don't have one at all."""
    known = family1_word_cefr[["word", "pos"]]
    efllex_only = efllex_cefr.merge(known, on=["word", "pos"], how="left", indicator=True)
    efllex_only = efllex_only[efllex_only["_merge"] == "left_only"].drop(columns="_merge")

    return pd.concat([family1_word_cefr, efllex_only], ignore_index=True)


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
    # Additive-only vocabulary expansion from EFLLex -- see
    # extend_family1_with_efllex's docstring. English Profile/teacher-survey
    # ratings are never overridden, only supplemented for words neither of
    # them rates at all.
    family1_word_cefr = extend_family1_with_efllex(family1_word_cefr, build_efllex_cefr())

    family2_word_synonyms, family2_candidates_with_cefr = build_family2_synonyms(family1_word_cefr)
    save_processed(family2_word_synonyms, "family2_word_synonyms")
    save_processed(family2_candidates_with_cefr, "family2_synonym_candidates_with_cefr")

    family3_vocabulary = build_family3_vocabulary()
    save_processed(family3_vocabulary, "family3_vocabulary")


if __name__ == "__main__":
    build_all()
