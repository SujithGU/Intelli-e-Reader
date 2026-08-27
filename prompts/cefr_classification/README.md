# CEFR classification prompt

Prompt assets for the LLM baseline in the CEFR-prediction model comparison -- a few-shot LLM call (currently run against Gemini, see `notebook/GeminiBatch-Inference-Test.ipynb`) that rates a single (word, part of speech) pair on the CEFR scale, used as an independent comparison point against the lookup-table data and the trained models.

- **`system_prompt.md`** -- the task description, compact CEFR rubric, and output field definitions. Goes in the `system_instruction` field of the API request. Kept deliberately short: a modern LLM already knows the CEFR framework from its training data, so a long explanatory rubric mostly costs tokens without adding signal -- and a leaner prompt is also a more honest "baseline" (less in-context-tuned) than a heavily-engineered one.
- **`few_shot_examples.json`** -- 3 calibration examples, one each from the easy/medium/hard range (`you`/PRON at A1, `learn`/VERB at B1, `natural`/ADJ at C1), spanning different parts of speech. All picked from words where English Profile and EFLLex *independently agree* on the exact level, not hand-picked from intuition. Each includes a one-line `reasoning` matching the style the model should produce, and a `source_note` documenting why it was trusted as an anchor. Add more (e.g. 2 per level) if a run's outputs look poorly calibrated at a specific level -- token cost is the tradeoff.

## How these combine into an actual request

The few-shot examples are turned into alternating `user`/`model` turns (each `model` turn is the exact JSON the model should have produced for that example), followed by the real target word as a final `user` turn -- not stuffed into the system prompt as a block of text. This is what actually teaches the output style/format, not just the rubric.

Output is constrained with structured output (`response_mime_type="application/json"` + `response_schema=...` on Gemini; `output_config: {format: {...}}` on Claude) matching this shape, so responses don't need re-parsing/validation:

```json
{
  "cefr_int": 1,
  "cefr_level": "A1",
  "confidence": "high",
  "reasoning": "short sentence"
}
```

See `system_prompt.md` for field definitions.

## Cost note

Gemini's free-tier context-caching quota is 0 -- caching the fixed prefix isn't available without a paid tier, which is the actual reason this prompt is kept lean rather than a heavier few-shot version with caching layered on top.
