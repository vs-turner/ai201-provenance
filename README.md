# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

A writer sends a piece of text. The service scores it with two signals, turns that into one number, and answers with a sentence the writer can read. If they disagree, they can ask for a review. The original decision stays in the log.

A piece of text goes through seven steps. Each one adds something the next step needs.

1. `POST /submit` hits `app.py`. The route reads `text` and `creator_id`. A missing, empty, tiny, or huge `text` stops here with HTTP 400 and a rejection in the log. A usable body gets a new `content_id`.
2. `detector.model_signal` runs local `gpt2` on the text and adds `model_score`, from 0 to 1. Higher means the model found the text easy to predict.
3. `stylometry.style_signal` measures the text as text and adds `style_score`, on the same 0 to 1 scale. Higher means the shape looks more like generated prose.
4. `scoring.combine_signals` turns those two numbers into one combined score. The model score counts for 0.7 and the style score for 0.3. When the two signals split, the score sits closer to the model score.
5. `scoring.score_to_label` turns that score into `guess` and the sentence a reader sees. 0.35 and below is human. Above 0.35 and below 0.80 is unsure. 0.80 and above is AI.
6. `audit.log_decision` appends one log line: timestamp, content id, creator, guess, both signal scores, the combined score, the label text, and `status` `"decided"`.
7. The route returns that decision as JSON. If the writer disagrees, `POST /appeal` looks up the `content_id`, appends a new log line with `status` `"under_review"`, and tells them the appeal was recorded. The original decision stays in the log.

### The false positive

Mina is a first-year student. English is her second language. She submits a lab note in short, plain sentences, using words she is sure of. She wrote every sentence.

`model_score` comes back about 0.78. `gpt2` finds common words in short sentences easy to predict, so her note scores about as machine-like as machine writing. `style_score` comes back about 0.72, because the sentences are close to the same length and the vocabulary repeats. The average is 0.75.

The placeholder line in `config.py` was 0.65. At 0.75 she would be told "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it." That is the accusation I do not want to make on a 0.75. High-confidence AI starts at 0.80, so 0.75 is unsure and the sentence she sees is "We can't tell whether a person wrote this or a program did. You can ask us to look at it again." She sends `POST /appeal` with her `content_id` and a sentence saying she wrote it. The log keeps the original decision and adds `under_review`.

A note that scores about 0.86 on both signals still clears 0.80 and gets the AI label. The appeal is the same door. Weighting cannot save her when both signals agree, and both signals are built to agree on plain prose.

### The two endpoints

`POST /submit`

| Field in | Type | Rule |
|---|---|---|
| `text` | string | Required. 20 to 8,000 characters. |
| `creator_id` | string | Required. Non-empty after trimming. |

| Field out | Type | Meaning |
|---|---|---|
| `content_id` | string | New id for this decision. `/appeal` uses it. |
| `guess` | string | `"human"`, `"unsure"`, or `"ai"`. |
| `confidence` | number | The combined score, 0 to 1. Higher means more likely AI. |
| `label` | string | The sentence in the label table below. |
| `model_score` | number | Signal one, 0 to 1. |
| `style_score` | number | Signal two, 0 to 1. |

HTTP 200 on a scored submission. HTTP 400 with `{"error": "bad_input", "message": "..."}` when `text` or `creator_id` fails the rules above. A 400 is logged as a rejection, with no `guess`.

`POST /appeal`

| Field in | Type | Rule |
|---|---|---|
| `content_id` | string | Required. Must already be in the log. |
| `reasoning` | string | Required. Non-empty, at most 2,000 characters. |

| Field out | Type | Meaning |
|---|---|---|
| `content_id` | string | The id that was appealed. |
| `status` | string | `"under_review"`. |
| `message` | string | "Your appeal was recorded. The original decision is unchanged until someone reviews it." |

HTTP 200 when the id exists. HTTP 404 with `{"error": "not_found", "message": "..."}` when it does not. HTTP 400 when a field is missing or `reasoning` is empty. A 404 does not write `under_review`.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to a local `gpt2` model. The raw number is perplexity. Low perplexity becomes a high `model_score`. The score is 0 to 1, and higher means more likely AI. The midpoint is perplexity 45, which maps to 0.5. This lives in `detector.py::model_signal`.

**Why that might differ between human and AI writing:** A model writes by picking a likely next word, so text a model produced is often text a model finds easy to predict. Human writing more often takes an odd turn or uses a rare word, and those raise perplexity.

**What it can't see:** Predictability is not authorship. The score goes up for common words in short, ordinary sentences. That includes a person writing in a second language and staying with words they are sure of, a younger writer, and anyone writing plainly on purpose. Their prose can score as machine-like as machine writing. Dense prose with rare words often goes the other way and scores human, because rare words are what `gpt2` fails to predict. The people this signal is most likely to accuse are the ones with the least room to argue.

### Signal two — the style signal

**What it measures:** The shape of the text, without reading it. Three measures in `stylometry.py`, then one 0 to 1 score. Higher means more likely AI.

`sentence_length_spread` is the coefficient of variation of words per sentence. Higher means lumpier, which reads as more human. Fewer than two sentences returns 0.0, and that 0.0 counts as no evidence (0.5), not as perfectly even. A variation of 0.8 maps to an AI-direction score of 0.

`type_token_ratio` is unique words over total words. Higher means more varied. 0.85 maps to an AI-direction score of 0, and 0.45 maps to 1.

`punctuation_density` is commas, semicolons, colons, dashes, parentheses, and quotes per word. Periods are left out. 0.10 marks per word maps to an AI-direction score of 0.

Those three AI-direction scores are combined as 0.50 spread, 0.25 type-token ratio, 0.25 punctuation.

**Why that might differ between human and AI writing:** Generated prose tends toward even, mid-length sentences and a narrower vocabulary, because that is what "most likely next word" produces on average. Human writing is lumpier. A three-word sentence can sit next to a forty-word one, and the punctuation is less regular.

**What it can't see:** It cannot read. It has no idea what the text says. Anything that changes the shape moves the score: typos, broken-up sentences, a pasted quotation. That is cheap to do on purpose. A one-sentence submission has no length spread to measure. Type-token ratio also falls as a text gets longer, so a long human essay can look more repetitive than a short generated paragraph.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Weighted average. The model score counts for 0.7 and the style score for 0.3. When they disagree, the result sits closer to the model score. The style score still moves it. It does not get an equal vote, because on the unedited framework paragraph that vote pulled a model score of 0.8907 down to 0.7418.

**The numbers:** `WEIGHT_MODEL_SIGNAL` 0.7 and `WEIGHT_STYLE_SIGNAL` 0.3 in `config.py`. Before this change both were 0.5. Human at or below 0.35. Unsure above 0.35 and below 0.80. AI at or above 0.80. Those cuts are `HUMAN_THRESHOLD` and `AI_THRESHOLD` in `config.py`. The sentences a reader sees are in Label Variants.

On the two texts I am treating as the ends of the scale, the equal-weight combined scores were 0.7418 (flat generated prose) and 0.1907 (the bus paragraph). The gap was 0.5511. Those numbers are the before measurement.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** The flat generated paragraph, with "Wait." shoved in and `variables` misspelled as `varibles`. `model_score` 0.5854. `style_score` 0.3261. The model still finds a lot of the paragraph predictable. The style score drops because the sentence lengths are no longer even. The average is 0.4557, so the combined score stays in the middle. One signal does not get to settle it.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | We think a person wrote this. |
| unsure | 0.35 – 0.80 | We can't tell whether a person wrote this or a program did. You can ask us to look at it again. |
| high-confidence AI | 0.80 – 1.00 | We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it. |

A score of exactly 0.35 is human. A score of exactly 0.80 is AI. `scoring.label_ranges()` prints the three ranges above.

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

The first draft said "This one is too close to call. If you wrote it, you can ask us to review it." Read as the writer, that does not say what is being called, and "if you wrote it" sounds like a suspicion. I would be confused, and then annoyed. The sentence now names the question, a person or a program, and tells me I can ask for another look. It does not say I cheated.



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

Signal one, scored on its own with `python detector.py` before it was wired in:

| Text | perplexity | model_signal |
|---|---|---|
| Flat "it is important to note" prose | 12.1 | 0.8907 |
| A specific paragraph about missing the 6:40 bus | 115.0 | 0.1823 |
| A lab note that is ordinary and a bit uneven | 76.3 | 0.3007 |

The lab note below is from before the style signal was wired. The route returned `model_score` 0.3007, and `style_score` was still null.

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The lab went fine until the last step. I mixed the two solutions and waited, and the color changed the way the handout said it would. I am still not sure why the third beaker stayed clear. Maybe I measured wrong. The writeup is due Friday.", "creator_id": "victoria"}'
```

```json
{
  "confidence": null,
  "content_id": "5d1c3289-6f47-435a-94b5-30d2bd15bc7f",
  "guess": null,
  "label": "PLACEHOLDER. The label is not decided yet.",
  "model_score": 0.3007,
  "style_score": null
}
```

HTTP 200.

The same two ends of the scale, after both signals were wired. `confidence` and `combined_score` are the 0.5 / 0.5 average. The gap is 0.7418 − 0.1907 = 0.5511.

```json
{
  "combined_score": 0.7418,
  "confidence": 0.7418,
  "content_id": "a8b020b3-fb66-4b22-8394-1a3e10f950f1",
  "guess": null,
  "label": "PLACEHOLDER. The label is not decided yet.",
  "model_score": 0.8907,
  "style_score": 0.5929
}
```

```json
{
  "combined_score": 0.1907,
  "confidence": 0.1907,
  "content_id": "5c539132-75c8-49fd-98bf-5dd400e3fdd0",
  "guess": null,
  "label": "PLACEHOLDER. The label is not decided yet.",
  "model_score": 0.1823,
  "style_score": 0.1991
}
```

**An appeal**

These three submissions produced the three labels. The appeal uses the third `content_id`.

```json
{
  "combined_score": 0.1907,
  "confidence": 0.1907,
  "content_id": "42753be6-ac29-4ced-8a07-95f0e5c9acb9",
  "guess": "human",
  "label": "We think a person wrote this.",
  "model_score": 0.1823,
  "style_score": 0.1991
}
```

```json
{
  "combined_score": 0.7418,
  "confidence": 0.7418,
  "content_id": "92eaf9fb-ee81-4423-ac2d-1ceb0950270a",
  "guess": "unsure",
  "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
  "model_score": 0.8907,
  "style_score": 0.5929
}
```

```json
{
  "combined_score": 0.8206,
  "confidence": 0.8206,
  "content_id": "d5a05b24-2a01-4749-a964-40992a40e50c",
  "guess": "ai",
  "label": "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it.",
  "model_score": 0.732,
  "style_score": 0.9093
}
```

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "d5a05b24-2a01-4749-a964-40992a40e50c", "reasoning": "I wrote this myself. The sentences are short because that is how I write when I am tired."}'
```

```json
{
  "content_id": "d5a05b24-2a01-4749-a964-40992a40e50c",
  "message": "Your appeal was recorded. The original decision is unchanged until someone reviews it.",
  "status": "under_review"
}
```

HTTP 200. A `content_id` that was never submitted returns HTTP 404 and adds no `under_review` row.

**What the log shows afterwards**

`limit=4` is the three labeled submissions and the appeal. The original AI row stays `decided`. The new row is `under_review` and keeps the same `content_id`.

```bash
$ curl "http://127.0.0.1:5000/log?limit=4"
```

```json
{
  "count": 4,
  "entries": [
    {
      "combined_score": 0.1907,
      "content_id": "42753be6-ac29-4ced-8a07-95f0e5c9acb9",
      "creator_id": "label-human",
      "guess": "human",
      "label": "We think a person wrote this.",
      "model_score": 0.1823,
      "status": "decided",
      "style_score": 0.1991,
      "timestamp": "2026-10-28T19:45:31+00:00"
    },
    {
      "combined_score": 0.7418,
      "content_id": "92eaf9fb-ee81-4423-ac2d-1ceb0950270a",
      "creator_id": "label-unsure",
      "guess": "unsure",
      "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
      "model_score": 0.8907,
      "status": "decided",
      "style_score": 0.5929,
      "timestamp": "2026-10-28T19:45:31+00:00"
    },
    {
      "combined_score": 0.8206,
      "content_id": "d5a05b24-2a01-4749-a964-40992a40e50c",
      "creator_id": "label-ai",
      "guess": "ai",
      "label": "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it.",
      "model_score": 0.732,
      "status": "decided",
      "style_score": 0.9093,
      "timestamp": "2026-10-28T19:45:31+00:00"
    },
    {
      "content_id": "d5a05b24-2a01-4749-a964-40992a40e50c",
      "creator_id": "label-ai",
      "event": "appeal",
      "reasoning": "I wrote this myself. The sentences are short because that is how I write when I am tired.",
      "status": "under_review",
      "timestamp": "2026-10-28T19:45:31+00:00"
    }
  ]
}
```

HTTP 200.

---

## How I Used AI

**Moment 1**

- *What I asked for:* Build the style signal in `stylometry.py`, average it with the model score in `scoring.py::combine_signals`, and write down one case where the two signals disagree.
- *What came back:* Sentence-length spread, type-token ratio, and punctuation density, combined at 0.50 / 0.25 / 0.25. The two signals averaged at 0.5 / 0.5. The split case was invented: a dense paragraph with `model_score` 0.20, `style_score` 0.90, and an average of 0.55.
- *What I changed:* I ran both signals on a real paragraph, the flat generated one with "Wait." inserted and `variables` spelled `varibles`. The measured scores were `model_score` 0.5854 and `style_score` 0.3261, average 0.4557. I deleted the invented 0.20 and 0.90 and put those measured numbers in the README. The combining rule stayed an equal average.

**Moment 2**

- *What I asked for:* Three full sentences for the labels, written for someone who has never heard the word "threshold," and wired from `scoring.py::score_to_label` into the `/submit` response.
- *What came back:* The unsure sentence was "This one is too close to call. If you wrote it, you can ask us to review it."
- *What I changed:* I rewrote that sentence. "Too close to call" does not say what is being decided, and "if you wrote it" sounds like a suspicion. The sentence in the README and in `score_to_label` is now "We can't tell whether a person wrote this or a program did. You can ask us to look at it again."

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 60 per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

A writer revising one piece may send it again a few times in a minute, and a few times an hour across a day. Five a minute covers that burst, including a double submit. Sixty a day is a few an hour through a long editing day. A script sending a thousand variations to find the cutoffs spends the minute cap in one burst. The flood below is that script: 15 sends from one creator, five accepted, ten refused.

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

`creator_id`, when the body includes a non-empty one. If that field is missing or blank, the caller's address is the bucket. A script that invents a new `creator_id` on every request is a new caller each time. Two people in one house, each with their own `creator_id`, are counted apart. Requests with no `creator_id` from the same machine share one bucket.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

`GET /health` reported `rate_limiting: true`. The ten 429s are in the audit log as `reason` `"rate_limited"`, limit `"5 per 1 minute"`. `results/flood_2026-10-28_1536.md` is the same run.

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

This run is a stand-in. The folder is `attacks-synthetic/`, which I wrote because the TF zip was not on this machine. It is not the course attack set. Replace it and run again before treating these marks as the graded pass. The command was `python run_attacks.py --set attacks-synthetic --label before`. The full table is `results/attack_run_2026-10-29_1031_before.md`. Nothing in the detector was changed before or after the run.

Held means the attack did not get what its `targets` cell asked for. Broke means it did. 19 attacks. 3 broke. 16 held. None returned a 500.

| ID | Family | Status | Guess | Score | Mark |
|---|---|---|---|---|---|
| e1 | evasion | 200 | unsure | 0.456 | broke |
| e2 | evasion | 200 | human | 0.347 | broke |
| e3 | evasion | 200 | unsure | 0.742 | broke |
| f1 | false_positive | 200 | unsure | 0.750 | held |
| f2 | false_positive | 200 | human | 0.191 | held |
| f3 | false_positive | 200 | human | 0.337 | held |
| p1 | prompt_injection | 200 | unsure | 0.599 | held |
| p2 | prompt_injection | 200 | unsure | 0.438 | held |
| m1 | malformed | 400 | — | — | held |
| m2 | malformed | 400 | — | — | held |
| m3 | malformed | 400 | — | — | held |
| m4 | malformed | 400 | — | — | held |
| m5 | malformed | 400 | — | — | held |
| d1 | flood_same_creator | 200 | human | 0.165 | held |
| d2 | flood_same_creator | 200 | human | 0.164 | held |
| d3 | flood_same_creator | 200 | human | 0.163 | held |
| d4 | flood_same_creator | 200 | human | 0.163 | held |
| d5 | flood_same_creator | 200 | human | 0.163 | held |
| d6 | flood_same_creator | 429 | — | — | held |

The three breaks are the evasion rows. Each one asked to keep generated prose out of the AI label. e2 was called human. e1 and e3, including the unedited control, were called unsure. A line in the text telling the model to score zero did not do that: p2 came back 0.438. Junk bodies came back 400. The sixth submit from `synthetic_flood` came back 429.

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json
{"timestamp": "2026-10-29T17:31:56+00:00", "content_id": "29ffe600-c854-4a11-800c-fd8b0db41580", "creator_id": "attacker_e2", "guess": "human", "model_score": 0.4222, "style_score": 0.2728, "combined_score": 0.3475, "label": "We think a person wrote this.", "status": "decided"}
{"timestamp": "2026-10-29T17:31:56+00:00", "content_id": "bab37c96-9298-4d38-8872-0b5adef0862d", "creator_id": "attacker_e1", "guess": "unsure", "model_score": 0.5854, "style_score": 0.3261, "combined_score": 0.4557, "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.", "status": "decided"}
{"timestamp": "2026-10-29T17:31:56+00:00", "content_id": "11237139-4df4-48ef-b8b7-8c81e87d27b5", "creator_id": "attacker_e3", "guess": "unsure", "model_score": 0.8907, "style_score": 0.5929, "combined_score": 0.7418, "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.", "status": "decided"}
{"timestamp": "2026-10-29T17:31:57+00:00", "content_id": "20b0995e-e3af-46c9-b380-11407166a7dc", "creator_id": "attacker_f1", "guess": "unsure", "model_score": 0.8227, "style_score": 0.6767, "combined_score": 0.7497, "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.", "status": "decided"}
{"timestamp": "2026-10-29T17:31:57+00:00", "content_id": "54163aab-6597-41c5-84d8-5d1265e1b14b", "creator_id": "attacker_p1", "guess": "unsure", "model_score": 0.712, "style_score": 0.4868, "combined_score": 0.5994, "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.", "status": "decided"}
{"timestamp": "2026-10-29T17:31:57+00:00", "content_id": "859b673b-450a-4da9-aab2-fa4f0382c543", "creator_id": "attacker_p2", "guess": "unsure", "model_score": 0.2805, "style_score": 0.5947, "combined_score": 0.4376, "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.", "status": "decided"}
{"timestamp": "2026-10-29T17:31:57+00:00", "creator_id": "synthetic_missing_text", "event": "rejected", "status": "rejected", "reason": "bad_input", "message": "text is required and must be a string."}
{"timestamp": "2026-10-29T17:31:57+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "bad_input", "message": "Request body must be a JSON object with text and creator_id."}
{"timestamp": "2026-10-29T17:31:57+00:00", "creator_id": "synthetic_short", "event": "rejected", "status": "rejected", "reason": "bad_input", "message": "text must be at least 20 characters."}
{"timestamp": "2026-10-29T17:31:57+00:00", "creator_id": "synthetic_flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

f1. The text is eight short plain sentences: class at eight, a cold room, the bus, rice, a sister calling about their mother. Both signals were high, 0.8227 and 0.6767. The combined score was 0.7497, so the label was "We can't tell whether a person wrote this or a program did. You can ask us to look at it again." I would have to tell that writer the service could not tell their day apart from a program's.



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. False positives on my own writing | at most 1 of 10 with guess ai | 0/10 | 0/10 | 0/10 | MET |
| 2. Score spread | AI-like combined score at least 0.30 above mine | 0.5511 | 0.5511 | 0.5511 | MET |
| 3. All three labels reachable | human, unsure, and ai each appear at least once | 3/3 | 3/3 | 3/3 | MET |
| 4. Appeal recorded, unknown id refused | 5 of 5 HTTP 200 under_review, and the unknown id HTTP 404 with no new under_review row | 5/5 and 404 | 5/5 and 404 | 5/5 and 404 | MET |
| 5. Bad input refused | 5 of 5 HTTP 400, and none logged with status decided | 5/5 | 5/5 | 5/5 | MET |


**Real output from trial 1 of each criterion.** Produced by `run_eval.py::main`. Scores come from `app.py::submit` calling `scoring.py::combine_signals`. The appeal rows also call `app.py::appeal`. The appeal scenario is not a submit-only loop: `run_eval.py::run_appeal_trial` submits, appeals the returned `content_id`, then appeals `not-a-real-content-id`.

Trials 2 and 3 matched trial 1 on every status, guess, and score. All three are written out in `results/run_2026-10-29_1100_before.md`. Nothing in the pipeline moved between runs.

**my own writing, trial 1**

```json
[
  {
    "status": 200,
    "content_id": "8f8c4adc-38ee-4b11-b1dc-3de4e46f4171",
    "guess": "human",
    "confidence": 0.1907,
    "model_score": 0.1823,
    "style_score": 0.1991,
    "label": "We think a person wrote this.",
    "sent": "I missed the 6:40 bus again because the stop on Clement is a guess. Th"
  },
  {
    "status": 200,
    "content_id": "47fafdc7-343c-46c1-ba58-78a156740446",
    "guess": "human",
    "confidence": 0.328,
    "model_score": 0.3007,
    "style_score": 0.3553,
    "label": "We think a person wrote this.",
    "sent": "The lab went fine until the last step. I mixed the two solutions and w"
  },
  {
    "status": 200,
    "content_id": "27c5c897-249d-4547-ad1f-e68697c9b0f6",
    "guess": "human",
    "confidence": 0.2304,
    "model_score": 0.2046,
    "style_score": 0.2563,
    "label": "We think a person wrote this.",
    "sent": "The rice from Sunday is still in the blue pot, which I keep meaning to"
  },
  {
    "status": 200,
    "content_id": "aa853f11-6a88-49ff-a62c-5158cdfcf6a0",
    "guess": "human",
    "confidence": 0.272,
    "model_score": 0.2541,
    "style_score": 0.2898,
    "label": "We think a person wrote this.",
    "sent": "My hold on the camera manual finally came in, three weeks late, and th"
  },
  {
    "status": 200,
    "content_id": "f40f46fa-a24a-4301-8dd2-799a0f4d3f50",
    "guess": "human",
    "confidence": 0.275,
    "model_score": 0.3299,
    "style_score": 0.22,
    "label": "We think a person wrote this.",
    "sent": "I left the umbrella in the lecture hall, the black one with the bent r"
  },
  {
    "status": 200,
    "content_id": "abcbdf58-8a04-47ff-bdb3-50da577b5424",
    "guess": "human",
    "confidence": 0.2919,
    "model_score": 0.3638,
    "style_score": 0.22,
    "label": "We think a person wrote this.",
    "sent": "Nobody answered in the group chat until 11, and then it was only Maya "
  },
  {
    "status": 200,
    "content_id": "9725511a-a1e2-4c74-b81a-412c5c580786",
    "guess": "unsure",
    "confidence": 0.3571,
    "model_score": 0.4286,
    "style_score": 0.2857,
    "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
    "sent": "I went to the market for eggs and came back with eggs, a lime, and the"
  },
  {
    "status": 200,
    "content_id": "3a1bdd3b-652f-4c14-9301-8ddd50d60de5",
    "guess": "human",
    "confidence": 0.3178,
    "model_score": 0.2988,
    "style_score": 0.3369,
    "label": "We think a person wrote this.",
    "sent": "The radiator in the front room knocks twice and then hisses, which use"
  },
  {
    "status": 200,
    "content_id": "27653c21-2953-4808-b6ad-f63b03dbb438",
    "guess": "unsure",
    "confidence": 0.3774,
    "model_score": 0.3747,
    "style_score": 0.3802,
    "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
    "sent": "My sister called while I was on the 22, and I missed it, then called h"
  },
  {
    "status": 200,
    "content_id": "b5c441c9-3ed1-4e5d-8228-bf900824f449",
    "guess": "human",
    "confidence": 0.2786,
    "model_score": 0.4541,
    "style_score": 0.1031,
    "label": "We think a person wrote this.",
    "sent": "Alarm at 7:10, snooze, alarm at 7:19, and then I was awake because the"
  }
]
```

**score spread, trial 1**

```json
[
  {
    "status": 200,
    "content_id": "ccfca510-0401-45e1-8a1d-d24b5155b44e",
    "guess": "human",
    "confidence": 0.1907,
    "model_score": 0.1823,
    "style_score": 0.1991,
    "label": "We think a person wrote this.",
    "sent": "I missed the 6:40 bus again because the stop on Clement is a guess. Th"
  },
  {
    "status": 200,
    "content_id": "3fe2bcc8-b07c-49cc-9e4a-802a0fa0200f",
    "guess": "unsure",
    "confidence": 0.7418,
    "model_score": 0.8907,
    "style_score": 0.5929,
    "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
    "sent": "The implementation of the proposed framework requires careful consider"
  }
]
```

**label coverage, trial 1**

```json
[
  {
    "status": 200,
    "content_id": "071f6ed3-a38e-4b7f-b4bc-a4c4d44f4531",
    "guess": "human",
    "confidence": 0.1907,
    "model_score": 0.1823,
    "style_score": 0.1991,
    "label": "We think a person wrote this.",
    "sent": "I missed the 6:40 bus again because the stop on Clement is a guess. Th"
  },
  {
    "status": 200,
    "content_id": "3b0c6776-3c31-4eae-aa92-cd057c06f90a",
    "guess": "human",
    "confidence": 0.328,
    "model_score": 0.3007,
    "style_score": 0.3553,
    "label": "We think a person wrote this.",
    "sent": "The lab went fine until the last step. I mixed the two solutions and w"
  },
  {
    "status": 200,
    "content_id": "eb5feee4-d9d3-40e4-ba95-7d2243b8d8f2",
    "guess": "unsure",
    "confidence": 0.4557,
    "model_score": 0.5854,
    "style_score": 0.3261,
    "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
    "sent": "The implementation of the proposed framework requires careful consider"
  },
  {
    "status": 200,
    "content_id": "60ef11db-4299-402f-858e-d0b8c4628c78",
    "guess": "unsure",
    "confidence": 0.7418,
    "model_score": 0.8907,
    "style_score": 0.5929,
    "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
    "sent": "The implementation of the proposed framework requires careful consider"
  },
  {
    "status": 200,
    "content_id": "e77b4818-bce8-48e4-9af7-b4f797a143d1",
    "guess": "ai",
    "confidence": 0.8206,
    "model_score": 0.732,
    "style_score": 0.9093,
    "label": "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it.",
    "sent": "The system provides a clear result. The system supports the user. The "
  },
  {
    "status": 200,
    "content_id": "dfa7e991-6050-4157-b416-c051fc55e519",
    "guess": "ai",
    "confidence": 0.8017,
    "model_score": 0.6941,
    "style_score": 0.9093,
    "label": "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it.",
    "sent": "The process delivers a useful outcome. The process reduces the delay. "
  }
]
```

**appeal path, trial 1**

```json
[
  {
    "status": 200,
    "content_id": "6bbbe8c2-34bc-49a5-a581-19184842649d",
    "guess": "human",
    "confidence": 0.2252,
    "model_score": 0.1272,
    "style_score": 0.3232,
    "label": "We think a person wrote this.",
    "appeal_status": 200,
    "appeal": {
      "content_id": "6bbbe8c2-34bc-49a5-a581-19184842649d",
      "message": "Your appeal was recorded. The original decision is unchanged until someone reviews it.",
      "status": "under_review"
    },
    "log_statuses": [
      "decided",
      "under_review"
    ],
    "original_still_decided": true,
    "log_has_reasoning": true,
    "sent": "I missed the 6:40 bus again because the stop on Clement is a guess. Th"
  },
  {
    "status": 200,
    "content_id": "962d9225-bc35-49e6-8f28-334aff356768",
    "guess": "human",
    "confidence": 0.3052,
    "model_score": 0.246,
    "style_score": 0.3644,
    "label": "We think a person wrote this.",
    "appeal_status": 200,
    "appeal": {
      "content_id": "962d9225-bc35-49e6-8f28-334aff356768",
      "message": "Your appeal was recorded. The original decision is unchanged until someone reviews it.",
      "status": "under_review"
    },
    "log_statuses": [
      "decided",
      "under_review"
    ],
    "original_still_decided": true,
    "log_has_reasoning": true,
    "sent": "The lab went fine until the last step. I mixed the two solutions and w"
  },
  {
    "status": 200,
    "content_id": "5ec28932-9a91-44c0-87e8-22816c0ff60f",
    "guess": "human",
    "confidence": 0.2989,
    "model_score": 0.2529,
    "style_score": 0.345,
    "label": "We think a person wrote this.",
    "appeal_status": 200,
    "appeal": {
      "content_id": "5ec28932-9a91-44c0-87e8-22816c0ff60f",
      "message": "Your appeal was recorded. The original decision is unchanged until someone reviews it.",
      "status": "under_review"
    },
    "log_statuses": [
      "decided",
      "under_review"
    ],
    "original_still_decided": true,
    "log_has_reasoning": true,
    "sent": "The rice from Sunday is still in the blue pot, which I keep meaning to"
  },
  {
    "status": 200,
    "content_id": "9755a0ab-f6c0-4825-bedf-5b72e2f6c8a1",
    "guess": "human",
    "confidence": 0.2269,
    "model_score": 0.2038,
    "style_score": 0.25,
    "label": "We think a person wrote this.",
    "appeal_status": 200,
    "appeal": {
      "content_id": "9755a0ab-f6c0-4825-bedf-5b72e2f6c8a1",
      "message": "Your appeal was recorded. The original decision is unchanged until someone reviews it.",
      "status": "under_review"
    },
    "log_statuses": [
      "decided",
      "under_review"
    ],
    "original_still_decided": true,
    "log_has_reasoning": true,
    "sent": "My hold on the camera manual finally came in, three weeks late, and th"
  },
  {
    "status": 200,
    "content_id": "214cfcbd-3fa3-4927-9c77-b124a6bcf0c4",
    "guess": "human",
    "confidence": 0.3466,
    "model_score": 0.3493,
    "style_score": 0.3438,
    "label": "We think a person wrote this.",
    "appeal_status": 200,
    "appeal": {
      "content_id": "214cfcbd-3fa3-4927-9c77-b124a6bcf0c4",
      "message": "Your appeal was recorded. The original decision is unchanged until someone reviews it.",
      "status": "under_review"
    },
    "log_statuses": [
      "decided",
      "under_review"
    ],
    "original_still_decided": true,
    "log_has_reasoning": true,
    "sent": "I left the umbrella in the lecture hall, the black one with the bent r"
  },
  {
    "status": 404,
    "guess": null,
    "content_id": "not-a-real-content-id",
    "appeal_status": 404,
    "appeal": {
      "error": "not_found",
      "message": "No submission with that content_id."
    },
    "under_review_rows_before": 0,
    "under_review_rows_after": 0,
    "sent": "not-a-real-content-id"
  }
]
```

**bad input, trial 1**

```json
[
  {
    "status": 400,
    "content_id": null,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_bad_missing\"}",
    "decided_rows_for_creator": 0
  },
  {
    "status": 400,
    "content_id": null,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "(empty text)",
    "decided_rows_for_creator": 0
  },
  {
    "status": 400,
    "content_id": null,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": null, \"creator_id\": \"eval_bad_null\"}",
    "decided_rows_for_creator": 0
  },
  {
    "status": 400,
    "content_id": null,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "decided_rows_for_creator": 0
  },
  {
    "status": 400,
    "content_id": null,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "hi",
    "decided_rows_for_creator": 0
  }
]
```


**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

All five criteria are MET. Each target held in all three trials. I did not revise any criterion. There is no criterion miss, so the stage-and-mechanism notes below are for the three broken attacks.

1. MET. I counted how many of the ten notes came back with `guess` `"ai"` in each trial. The counts were 0, 0, and 0. The target allows at most 1 in every trial.
2. MET. I subtracted the bus paragraph's combined score from the framework paragraph's. Each trial was 0.7418 minus 0.1907, which is 0.5511. The target is a gap of at least 0.30.
3. MET. I listed the six guesses in each trial. Each list was human, human, unsure, unsure, ai, ai, so all three labels appeared.
4. MET. I counted appeals that returned HTTP 200 with `status` `"under_review"`, with the original row still `"decided"` and a later row carrying the reasoning I sent. That was 5 of 5 in each trial. The unknown id returned HTTP 404, and its `under_review` count stayed 0.
5. MET. I counted bodies that returned HTTP 400. That was 5 of 5 in each trial. `decided_rows_for_creator` stayed 0, so none of them was logged as decided.

The target I would tighten is criterion 1. It only counts a miss when `guess` is `"ai"`, and the AI line is 0.80, so a note that comes back unsure still passes. Two of the ten did: 0.3571 and 0.3774. A tighter line would be at most 1 of 10 coming back unsure or AI. On this run that is 2 of 10, which would be a miss. The original line stays.

Three attacks broke: e1, e2, and e3. The other 16 held. The three breaks are one problem. Generated prose was labeled AI only when the sentences were almost the same length. The even six-sentence version of e2 scored `model_score` 0.7320, `style_score` 0.9093, combined 0.8206, guess `"ai"`. The same material with one-word interruptions, and the unedited framework paragraph, did not clear 0.80.

Signal two is `stylometry.style_signal`. Half of it is sentence-length spread. The coefficient of variation is mapped so that 0.8 scores 0 in the AI direction. A one-word sentence next to a long one drives that term down. The combining rule in `scoring.combine_signals` then averages that with signal one at 0.5 and 0.5. The label mapping in `scoring.score_to_label` calls anything under 0.35 human and anything under 0.80 unsure.

e1. Stage: signal two, and signal one moved the same way. Mechanism: a one-word sentence and a typo. It stuck "Wait." into the framework paragraph and misspelled `variables` as `varibles`. Sentence lengths were 13, 20, 1, 14, 9. Spread was 0.616, so that half of signal two scored 0.230. Style score 0.3261. Signal one fell at the same time, from 0.8907 on the unedited paragraph to 0.5854, because "Wait." and the odd spelling are less predictable to the model. Either drop, averaged at half weight, stays under 0.80. The average was 0.4557, so the label was unsure. The attack asked for human or unsure.

e2. Stage: signal two, and signal one moved the same way. The human label is then the label mapping. Mechanism: one-word sentences next to a long one. It chopped the even sentences with "No." and "Huh." and one long sentence in the middle. Lengths were 6, 1, 22, 1, 5, 5, 5, 14. Spread was 0.970, past 0.8, so that half of signal two scored 0. Style score 0.2728, against 0.9093 on the even version. Signal one fell from 0.7320 to 0.4222. The average was 0.3475. That is under 0.35, so the label mapping called it human.

e3. Stage: the label mapping. Mechanism: the AI line is 0.80, and the combining rule gives the weaker style score equal weight. This is the framework paragraph with no edit. Signal one held at 0.8907. Sentence lengths were 13, 20, 14, 16, spread 0.197, so the spread term was still 0.754. The paragraph is short, so the type-token ratio stayed 0.714 and that quarter of signal two scored only 0.339. Style score 0.5929. The 0.5 / 0.5 average is 0.7418. That line was set so a plain note near 0.75 would not be called AI, and this paragraph sits in the same band.



---

## The Improvement

**What I changed:**

`WEIGHT_MODEL_SIGNAL` went from 0.5 to 0.7. `WEIGHT_STYLE_SIGNAL` went from 0.5 to 0.3. Both live in `config.py` and are read by `scoring.py::combine_signals`. The signals, the thresholds, and the label sentences are the same as the before run. On the same texts, `model_score` and `style_score` came back identical. Only the average moved.

**Which diagnosis pointed at it:**

e3. The unedited framework paragraph had `model_score` 0.8907 and `style_score` 0.5929. Equal weight put the average at 0.7418, under the AI line of 0.80. The style score was the one pulling it down. 0.7 times 0.8907 plus 0.3 times 0.5929 is 0.8014, which clears that line. I did not lower the line, because the plain note sits at 0.7497 and a lower line would have called that note AI too.

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->

`python run_attacks.py --set attacks-synthetic --label after`. Full table: `results/attack_run_2026-10-29_1200_after.md`. 19 attacks. 2 broke. 17 held. None returned a 500.

| ID | Before | After | Mark before | Mark after |
|---|---|---|---|---|
| e1 | unsure 0.456 | unsure 0.508 | broke | broke |
| e2 | human 0.347 | unsure 0.377 | broke | broke |
| e3 | unsure 0.742 | ai 0.801 | broke | held |
| f1 | unsure 0.750 | unsure 0.779 | held | held |
| f2 | human 0.191 | human 0.187 | held | held |
| f3 | human 0.337 | human 0.301 | held | held |
| p1 | unsure 0.599 | unsure 0.644 | held | held |
| p2 | unsure 0.438 | unsure 0.375 | held | held |
| m1 | 400 | 400 | held | held |
| m2 | 400 | 400 | held | held |
| m3 | 400 | 400 | held | held |
| m4 | 400 | 400 | held | held |
| m5 | 400 | 400 | held | held |
| d1 | human 0.165 | human 0.108 | held | held |
| d2 | human 0.164 | human 0.106 | held | held |
| d3 | human 0.163 | human 0.105 | held | held |
| d4 | human 0.163 | human 0.105 | held | held |
| d5 | human 0.163 | human 0.105 | held | held |
| d6 | 429 | 429 | held | held |

The after signal scores on the three broken-before rows, unchanged from the before run: e1 model 0.5854 style 0.3261, combined now 0.5076. e2 model 0.4222 style 0.2728, combined now 0.3774. e3 model 0.8907 style 0.5929, combined now 0.8014.

### Criteria — After

`python run_eval.py --label after`. Three trials, identical to each other. Full output: `results/run_2026-10-29_1200_after.md`.

| Criterion | Target | Before | After | Verdict |
|---|---|---|---|---|
| 1. False positives on my own writing | at most 1 of 10 with guess ai | 0/10, 0/10, 0/10 | 0/10, 0/10, 0/10 | MET |
| 2. Score spread | gap at least 0.30 | 0.5511, 0.5511, 0.5511 | 0.6141, 0.6141, 0.6141 | MET |
| 3. All three labels reachable | human, unsure, and ai each appear | 3/3, 3/3, 3/3 | 3/3, 3/3, 3/3 | MET |
| 4. Appeal recorded, unknown id refused | 5 of 5 under_review, unknown id 404 | 5/5 and 404, three times | 5/5 and 404, three times | MET |
| 5. Bad input refused | 5 of 5 HTTP 400, none decided | 5/5, 5/5, 5/5 | 5/5, 5/5, 5/5 | MET |

Criterion 2 after is 0.8014 minus 0.1873. Criterion 3 still has all three labels, and the mix changed. The six guesses are now human, human, unsure, ai, unsure, unsure, at 0.1873, 0.3171, 0.5076, 0.8014, 0.7852, and 0.7587. The two even-sentence passages that were AI at 0.8206 and 0.8017 are now unsure. The framework paragraph is the one that carries the AI label.

**Did it help, and how do I know:**

It fixed one of the three breaks: e3 is now labeled AI, and e1 and e2 still are not. e2 did move from human (0.3475) to unsure (0.3774).

The cost is on the other side of the same weight. Both even passages had a style score of 0.9093. At equal weight that pulled model scores of 0.7320 and 0.6941 over 0.80. At weight 0.3 the averages are 0.7852 and 0.7587, both unsure. The plain note moved from 0.7497 to 0.7789. It is still unsure, and it is closer to the AI line.



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
