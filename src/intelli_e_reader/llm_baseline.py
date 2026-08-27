"""Gemini LLM baseline for CEFR-level prediction -- inference over the
word/POS vocabulary, as an independent comparison point against the
lookup-table data and the trained models. Prompt assets this builds
requests from live in prompts/cefr_classification/.

The Batch API (build_batch_request / write_batch_jsonl_files /
parse_batch_results below) is the primary path -- cheaper, and built to run
unattended over the full vocabulary. run_concurrent_inference is a
synchronous fallback for accounts without batch access: threaded calls with
retry-on-rate-limit and incremental, resumable disk writes.
"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from google.genai import types
from google.genai.errors import ClientError, ServerError

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "cefr_int": {"type": "INTEGER"},
        "cefr_level": {"type": "STRING", "enum": ["A1", "A2", "B1", "B2", "C1", "C2"]},
        "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
        "reasoning": {"type": "STRING"},
    },
    "required": ["cefr_int", "cefr_level", "confidence", "reasoning"],
}


def word_target_text(word: str, pos: str) -> str:
    return f'Word: "{word}"\nPart of speech: {pos}'


def load_prompt_assets(prompt_dir: Path):
    """Returns (system_prompt, few_shot, few_shot_contents) -- see
    prompts/cefr_classification/README.md for what these are."""
    system_prompt = (prompt_dir / "system_prompt.md").read_text()
    few_shot = json.loads((prompt_dir / "few_shot_examples.json").read_text())
    few_shot_contents = []
    for ex in few_shot:
        few_shot_contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=word_target_text(ex["word"], ex["pos"]))])
        )
        assistant_json = json.dumps({k: ex[k] for k in ("cefr_int", "cefr_level", "confidence", "reasoning")})
        few_shot_contents.append(types.Content(role="model", parts=[types.Part.from_text(text=assistant_json)]))
    return system_prompt, few_shot, few_shot_contents


def build_batch_request(word: str, pos: str, few_shot_contents, system_prompt: str) -> dict:
    """One JSONL line for the Gemini Batch API. `key` identifies the row so
    unordered results can be matched back to (word, pos); '|||' as the
    separator since some entries (EFLLex phrasal ones) already contain
    underscores.

    Wire shape traced from the installed SDK's own request-building code
    (_InlinedRequest_to_mldev / _GenerateContentConfig_to_mldev in
    google/genai/batches.py and models.py): systemInstruction is a sibling
    of contents, and the response format sits directly under
    generationConfig -- there's no top-level "config" wrapper for a
    hand-authored JSONL file, only for the SDK's Python-object submission
    path."""
    target = types.Content(role="user", parts=[types.Part.from_text(text=word_target_text(word, pos))])
    system_instruction = types.Content(role="user", parts=[types.Part.from_text(text=system_prompt)])
    request = {
        "contents": [c.model_dump(mode="json", exclude_none=True) for c in (few_shot_contents + [target])],
        "systemInstruction": system_instruction.model_dump(mode="json", exclude_none=True),
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    return {"key": f"{word}|||{pos}", "request": request}


def write_batch_jsonl_files(df, few_shot_contents, system_prompt, out_dir: Path, chunk_size: int = 3000):
    """df needs 'word' and 'pos' columns. Writes chunked JSONL files (well
    under the Batch API's 2GB/file limit even as one file -- chunked instead
    for manageable, resumable submission/monitoring). Returns the written
    file paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    rows = df[["word", "pos"]].to_dict("records")
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        path = out_dir / f"cefr_batch_{i // chunk_size:03d}.jsonl"
        with open(path, "w") as f:
            for row in chunk:
                line = build_batch_request(row["word"], row["pos"], few_shot_contents, system_prompt)
                f.write(json.dumps(line) + "\n")
        paths.append(path)
    return paths


def parse_batch_results(jsonl_bytes: bytes) -> list[dict]:
    """Parses the JSONL bytes returned by client.files.download() for a
    completed batch job into a list of {word, pos, ...prediction fields}."""
    records = []
    for line_number, line in enumerate(jsonl_bytes, 1):
        try:
            if not line.strip():
                continue
            row = json.loads(line)
            word, pos = row["key"].split("|||")
            record = {"word": word, "pos": pos}
            if "response" in row:
                text = row["response"]["candidates"][0]["content"]["parts"][0]["text"]
                record.update(json.loads(text))
            else:
                record["error"] = row.get("error")
            records.append(record)
        except Exception as e:
            print(f'Error in line {line_number}! error : {e}')
    return records
    


def generate_with_retry(client, model, contents, config, max_retries=5, base_delay=3.0):
    """Retry on transient 429 (rate limit) / 503 (overloaded) with exponential
    backoff. Doesn't retry other errors (e.g. 400s) -- those are real bugs."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except (ClientError, ServerError) as e:
            code = getattr(e, "code", None)
            if code not in (429, 503) or attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))


def run_concurrent_inference(client, model, targets, few_shot_contents, system_prompt, out_path, max_workers=6):
    """targets: list of (word, pos) tuples. Writes results incrementally as
    JSONL to out_path, one line per completed word -- safe to interrupt
    (Ctrl-C, kernel crash, restart) and re-run: already-completed rows are
    read back from out_path and skipped rather than re-requested and re-billed.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done_keys = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    done_keys.add((row["word"], row["pos"]))

    todo = [(w, p) for w, p in targets if (w, p) not in done_keys]
    print(f"{len(done_keys)} already done, {len(todo)} remaining")

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
    )

    def process_one(word, pos):
        target = types.Content(role="user", parts=[types.Part.from_text(text=word_target_text(word, pos))])
        response = generate_with_retry(client, model, few_shot_contents + [target], config)
        parsed = json.loads(response.text)
        parsed["word"] = word
        parsed["pos"] = pos
        return parsed

    write_lock = threading.Lock()
    n_done, n_failed = 0, 0
    with open(out_path, "a") as f, ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(process_one, w, p): (w, p) for w, p in todo}
        for future in as_completed(futures):
            w, p = futures[future]
            try:
                result = future.result()
                with write_lock:
                    f.write(json.dumps(result) + "\n")
                    f.flush()
                n_done += 1
            except Exception as e:
                n_failed += 1
                print(f"  failed {w}/{p}: {e}")
            if (n_done + n_failed) % 200 == 0:
                print(f"{n_done + n_failed}/{len(todo)} processed ({n_failed} failed)")

    print(f"done: {n_done} succeeded, {n_failed} failed, results in {out_path}")
