# Intelli-e-Reader

Intelli-e-Reader takes a PDF and rewrites it to be easier to read for an English learner, without dumbing down the story. It finds words that are above a target reading level and swaps them for simpler synonyms — but only when a synonym can be found that doesn't change what the sentence actually means. Upload a book, get back the same book with hard words highlighted; click a highlighted word to see the original and the alternatives that were considered.

Difficulty is measured against **CEFR** (the Common European Framework of Reference for Languages), the same A1–C2 scale used in language teaching. This project collapses it to three buckets — **A** (easy), **B** (medium), **C** (hard) — and only ever simplifies *toward* A.

This started as a 2021 student project ([`Report/`](Report/) and [`notebook/Intelli_eReader.ipynb`](notebook/Intelli_eReader.ipynb) are the original writeup and prototype); this repo is a restructured, working version of it.

## Architecture

Two halves: a frontend you interact with, and a backend that does the actual language processing.

```
reader-ui/ (Angular)  --upload PDF-->  app.py (Flask)  -->  src/intelli_e_reader/reader/
     |                                                              |
     +-- highlighted book, click a word for details  <--------------+
                                                                      |
                                                        data/processed/ (word CEFR
                                                        ratings + synonym candidates)
```

- **[`reader-ui/`](reader-ui/)** — the Angular frontend. Upload a PDF, read the simplified result rendered like a book, click a highlighted word to see what it originally was and what other candidates were considered.
- **[`app.py`](app.py)** — the Flask API the frontend talks to. Takes the uploaded PDF, hands it to the pipeline below, returns the simplified text as JSON.
- **[`src/intelli_e_reader/reader/`](src/intelli_e_reader/reader/)** — the actual NLP pipeline:
  - `custom_reader.py` — orchestrates everything: extracts text from the PDF ([PyMuPDF](https://pymupdf.readthedocs.io/)), tags each word's part of speech ([NLTK](https://www.nltk.org/)), and for every word rated above CEFR level A, looks for a simpler replacement.
  - `cefr.py` — looks up a word's CEFR rating from a pre-built table (see **Data** below).
  - `syn_retriever.py` — finds candidate synonyms for a word from two independently-scraped sources.
  - `semantic_check.py` — scores how well each candidate preserves the original sentence's meaning, using a sentence-embedding model ([`sentence-transformers`](https://www.sbert.net/)) — so a replacement is only used if it's both simpler *and* still makes sense in context.

There's also a second, **separate and experimental** piece that is *not* part of the live pipeline above: [`src/intelli_e_reader/cefr_model/`](src/intelli_e_reader/cefr_model/) trains ML models (a Random Forest and a small neural network) to *predict* a word's CEFR level from its usage-frequency trend over time, as an alternative to the fixed lookup table. It was never wired into `reader/` — that always uses the lookup table — and its own dependencies haven't been verified on a modern Python yet (`pip install -e ".[training]"` if you want to try). In principle: `train.py` trains the Random Forest and neural network models and saves them under `models/cefr_prediction/`; `test.py` loads them to predict a given word/part-of-speech's CEFR level.

## Setup

**Prerequisites**: Python 3.11+ (tested on 3.12 and 3.14) and [`uv`](https://docs.astral.sh/uv/); Node.js if you also want the frontend (Angular 11 here — old enough that a modern Node can misbehave with its build tooling; Node 14 is what this was actually verified against).

### Backend

```
uv sync                                        # installs everything pinned in pyproject.toml
uv run python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng'); nltk.download('stopwords')"
uv run python -m intelli_e_reader.data_utils   # builds data/processed/ from data/raw/ (see Data below)
uv run python app.py                           # starts the API on http://localhost:5001
```

(No `uv`? `pip install -e .` installs the same pinned dependencies from `pyproject.toml`, then drop the `uv run` prefix from the rest.)

Check it's up:
```
curl http://localhost:5001/
```

### Frontend

```
cd reader-ui
npm install
npm start          # or: ng serve
```
Open `http://localhost:4200`. It's already pointed at `http://localhost:5001` (see `reader-ui/src/environments/environment.ts`) — no config needed if you're running both locally.

Try it end-to-end by uploading `data/pdf/Treasure Island.pdf` (already in the repo) through the UI.

## Data

**`data/raw/`** — the original collected sources: two independent word-difficulty ratings (a scrape of the English Profile website, and a small teacher survey), two independently-scraped synonym sources, and a general ~370,000-word English vocabulary list. These are committed to the repo — they can't be easily reconstructed if the original scrapers or sources ever go away.

**`data/processed/`** — tables *derived* from `data/raw/`, built by [`src/intelli_e_reader/data_utils.py`](src/intelli_e_reader/data_utils.py). Most of these are **not committed** — they're cheap to regenerate, so they're left out of the repo rather than carried around as build output. Before running the app for the first time (or after pulling changes to `data/raw/`), run:

```
python -m intelli_e_reader.data_utils
```

This builds:
- `family2_word_synonyms.parquet` — one row per (word, part of speech): its CEFR rating plus its combined candidate synonyms. This is what `reader/cefr.py` and the live pipeline actually depend on.
- `family2_synonym_candidates_with_cefr.parquet` — candidate synonyms that themselves have a CEFR rating (not used by the live app; useful for analysis).
- `family3_vocabulary.parquet` — the full vocabulary with part-of-speech tags (feeds `cefr_model/`, not the live app).

Two further processed files *are* committed, since regenerating them is slow or depends on an external service: `all_english_words_tagged.csv` (re-tagging ~370,000 words) and `master_cefr_with_ngram.csv` (re-scraping Google's Ngram viewer for usage-frequency trends, via `src/intelli_e_reader/data_pipeline/generate_ngram_data_for_cefr_master.py` and `google_ngram_parser.py`). Both only feed the experimental `cefr_model/`, not the live app.

**[`notebook/Dataset-EDA.ipynb`](notebook/Dataset-EDA.ipynb)** is where this raw-to-processed logic was worked out and explored before being finalized into `data_utils.py` — it's for exploration only and doesn't save anything itself.
