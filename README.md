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

A piece of text goes through seven steps. Each one adds something the next step needs.

1. `POST /submit` hits `app.py`. The route reads `text` and `creator_id`. A missing, empty, tiny, or huge `text` stops here with HTTP 400 and a rejection in the log. A usable body gets a new `content_id`.
2. `detector.model_signal` runs local `gpt2` on the text and adds `model_score`, from 0 to 1. Higher means the model found the text easy to predict.
3. `stylometry.style_signal` measures the text as text and adds `style_score`, on the same 0 to 1 scale. Higher means the shape looks more like generated prose.
4. `scoring.combine_signals` turns those two numbers into one combined score. A 0.5 / 0.5 average. When the two signals split, the score sits in the middle.
5. `scoring.score_to_label` turns that score into `guess` and the sentence a reader sees. 0.35 and below is human. Above 0.35 and below 0.80 is unsure. 0.80 and above is AI.
6. `audit.log_decision` appends one log line: timestamp, content id, creator, guess, both signal scores, the combined score, the label text, and `status` `"decided"`.
7. The route returns that decision as JSON. If the writer disagrees, `POST /appeal` looks up the `content_id`, appends a new log line with `status` `"under_review"`, and tells them the appeal was recorded. The original decision stays in the log.

### The false positive

Mina is a first-year student. English is her second language. She submits a lab note in short, plain sentences, using words she is sure of. She wrote every sentence.

`model_score` comes back about 0.78. `gpt2` finds common words in short sentences easy to predict, so her note scores about as machine-like as machine writing. `style_score` comes back about 0.72, because the sentences are close to the same length and the vocabulary repeats. The average is 0.75.

The placeholder line in `config.py` is 0.65. At 0.75 she would be told "This looks like model-written text." That is the accusation I do not want to make on a 0.75. I am moving high-confidence AI to 0.80, so 0.75 is unsure and the sentence she sees is "This one is too close to call. If you wrote it, you can ask us to review it." She sends `POST /appeal` with her `content_id` and a sentence saying she wrote it. The log keeps the original decision and adds `under_review`.

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

**What it measures:** The shape of the text, without reading it. Three measures in `stylometry.py`: how much sentence length varies (`sentence_length_spread`), how much of the vocabulary repeats (`type_token_ratio`), and how much punctuation there is relative to length (`punctuation_density`). `style_signal` flips the ones that point at human writing and scales them onto one 0 to 1 score. Higher means more likely AI.

**Why that might differ between human and AI writing:** Generated prose tends toward even, mid-length sentences and a narrower vocabulary, because that is what "most likely next word" produces on average. Human writing is lumpier. A three-word sentence can sit next to a forty-word one, and the punctuation is less regular.

**What it can't see:** It cannot read. It has no idea what the text says. Anything that changes the shape moves the score: typos, broken-up sentences, a pasted quotation. That is cheap to do on purpose. A one-sentence submission has no length spread to measure. Type-token ratio also falls as a text gets longer, so a long human essay can look more repetitive than a short generated paragraph.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:** Average the two scores with equal weight. When they disagree, the result sits between them, which is the unsure band. Neither signal gets to overrule the other. Each one is blind where the other can still see something: the model signal misses plain human prose, and the style signal misses meaning and can be shoved around by typos.

**The numbers:** `WEIGHT_MODEL_SIGNAL` 0.5, `WEIGHT_STYLE_SIGNAL` 0.5. Human at or below 0.35. Unsure above 0.35 and below 0.80. AI at or above 0.80. These replace the 0.65 placeholder. I have not changed `config.py` yet. Milestone 5 is where the thresholds get coded.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:** A dense paragraph with rare words and very even sentences. `model_score` 0.20, because the rare words surprise `gpt2`. `style_score` 0.90, because the sentence lengths barely move. The average is 0.55, so `guess` is `"unsure"`. The model signal wanted "human" and the style signal wanted "AI". The rule keeps that split in the middle. It does not let the style score alone accuse the writer, and it does not let the model score alone clear them.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | This looks like a person wrote it. |
| unsure | 0.35 – 0.80 | This one is too close to call. If you wrote it, you can ask us to review it. |
| high-confidence AI | 0.80 – 1.00 | This looks like model-written text. If that is wrong, send an appeal and a person will look at it. |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

Mina may have written every word and still land here, because plain sentences score high on both signals. "Too close to call" says the system did not decide she cheated. The second sentence tells her the appeal exists, which is the only thing she can do about it.



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

The lab note is the submission below. The route returned the same `model_score`, 0.3007. `guess`, `confidence`, `label`, and `style_score` are still placeholders. The second signal is not wired in yet.

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

**An appeal**

`POST /appeal` is still the starter response. Milestone 5 builds it. The `content_id` below is from an earlier submission of the same lab note.

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "2132c72a-6b5d-4a16-af72-005f8831abf8", "reasoning": "I wrote this myself."}'
```

```json
{
  "error": "not_implemented",
  "message": "POST /appeal isn't built yet \u2014 see the TODO in app.py.",
  "you_sent": {
    "content_id": "2132c72a-6b5d-4a16-af72-005f8831abf8",
    "reasoning": "I wrote this myself."
  }
}
```

HTTP 501.

**What the log shows afterwards**

The middle row is an empty `text` I sent on purpose. It came back HTTP 400 and was logged as `rejected`, not as a decision. The first row is an earlier run of the same lab note, from before the placeholder label lost its dash.

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json
{
  "count": 3,
  "entries": [
    {
      "combined_score": null,
      "content_id": "2132c72a-6b5d-4a16-af72-005f8831abf8",
      "creator_id": "victoria",
      "guess": null,
      "label": "PLACEHOLDER \u2014 the label is not decided yet.",
      "model_score": 0.3007,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-10-28T19:29:47+00:00"
    },
    {
      "creator_id": "victoria",
      "event": "rejected",
      "message": "text must be at least 20 characters.",
      "reason": "bad_input",
      "status": "rejected",
      "timestamp": "2026-10-28T19:29:47+00:00"
    },
    {
      "combined_score": null,
      "content_id": "5d1c3289-6f47-435a-94b5-30d2bd15bc7f",
      "creator_id": "victoria",
      "guess": null,
      "label": "PLACEHOLDER. The label is not decided yet.",
      "model_score": 0.3007,
      "status": "decided",
      "style_score": null,
      "timestamp": "2026-10-28T19:30:22+00:00"
    }
  ]
}
```

HTTP 200.

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



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
