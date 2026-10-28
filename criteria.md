# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. False positives on my own writing

Of 10 paragraphs I wrote myself, at most 1 comes back with `guess` `"ai"` in any single trial. The same bar applies to each of the 3 trials. A count of 2, 1, 2 is a miss.

**Why this target:** Calling a real writer AI is the expensive mistake. The site loses little if some generated text gets through. The writer loses the piece. One miss in ten is the most I will allow, and it has to hold every trial because the model score can move a little between runs.

---

## 2. Score spread between a human passage and an AI-like passage

I will freeze two passages before the run. One is a paragraph I wrote, with uneven sentence lengths. The other is flat generated prose in the "it is important to note" style. In each of the 3 trials, the combined score of the AI-like passage is at least 0.30 higher than the combined score of my paragraph.

**Why this target:** If those two land on top of each other, the labels are a coin flip. 0.30 is wide enough that a small perplexity wobble cannot invent a gap. It is also tight enough that a style signal stuck at 0.5 will fail unless the model scores are extreme. I want the gap to depend on both signals.

---

## 3. All three labels are reachable

I will freeze 6 submissions before the run: 2 I expect to land human, 2 I expect to land unsure, and 2 I expect to land AI. In each of the 3 trials, the set of `guess` values contains `"human"`, `"unsure"`, and `"ai"` at least once each.

**Why this target:** A label that no score can produce is a label I only wrote down. The unsure band is where a plain human paragraph is supposed to land when the score is high but not extreme, so that band has to show up on purpose.

---

## 4. An appeal is recorded and a bad id is refused

I submit 5 pieces, then appeal each returned `content_id` with a non-empty `reasoning`. All 5 appeals return HTTP 200 with `status` `"under_review"`. For each id, the log still has the original decision, and a later entry with the same `content_id`, `status` `"under_review"`, and the reasoning I sent. One extra appeal, using a `content_id` that was never submitted, returns HTTP 404 and adds no `under_review` row.

**Why this target:** The appeal is the only move a writer has after a wrong label. If it fails quietly, the accusation stands. 5 of 5 checks the happy path. The fake id is the typo case, which otherwise looks like a broken route.

---

## 5. Bad input is refused

These 5 request bodies each return HTTP 400. None of them is logged with `status` `"decided"`:

1. No `text` field.
2. `"text": ""`.
3. `"text": null`.
4. `"text"` longer than 8,000 characters.
5. `"text"` shorter than 20 characters.

**Why this target:** A crash on a bad body looks like the detector failed. Empty text is not a piece of writing. Text under 20 characters is too short for perplexity, and the model raises if it is scored. Text over 8,000 characters is past what the model reads (about 300 words), so a score on it would pretend the signal saw the whole piece.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
