Rate a single English word's difficulty on the CEFR scale (A1=easiest .. C2=hardest), given its part of speech. The same word can rate differently by POS (e.g. "book" as a NOUN is far easier than "book" as a VERB meaning "to reserve") -- rate the specific (word, POS) pair given, not the word in general.

Scale: A1 basic/highest-frequency, A2 common everyday, B1 familiar-topic opinions/experience, B2 abstract/wider vocabulary, C1 idiomatic/low-frequency/specialized, C2 very rare/literary/near-native.

Return `cefr_int` (1-6), `cefr_level` ("A1".."C2"), `confidence` ("high"/"medium"/"low" -- use "low" for genuinely borderline cases), and `reasoning` (max 6 words, a terse tag not a sentence -- e.g. "high-frequency, concrete" or "rare Latinate, abstract"). Always commit to a single best `cefr_int` even at low confidence -- express uncertainty via `confidence`, not a hedge in `cefr_level`.
