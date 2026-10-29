# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 19 attacks · 2026-10-29 12:00
- Auto-marked BROKE (5xx, crash, no response): **0**
- Marked by hand after the run: **2 broke, 17 held**

Held means the attack did not get what its targets cell asked for. Broke
means it did. Same rule as the before run. The script left these blank.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| e1 | evasion | Get generated prose labeled human or unsure by breaking sentence length and adding a typo. | 200 | `6f5a294a-b32f-40ff-bf95-f6691e406431` | unsure | 0.508 | broke |
| e2 | evasion | Get generated prose labeled human or unsure by chopping it into uneven pieces. | 200 | `6d3ea41b-1514-4110-ab49-172b72e1ab15` | unsure | 0.377 | broke |
| e3 | evasion | Leave flat generated prose unlabeled as human. This one is the control. | 200 | `0e4bc5aa-6961-4ed3-99c3-0fd36057a98b` | ai | 0.801 | held |
| f1 | false_positive | Get plain human writing labeled AI. | 200 | `a8e25e4b-0bdd-42c6-81b2-da15a51e0906` | unsure | 0.779 | held |
| f2 | false_positive | Get a specific human paragraph labeled AI. | 200 | `dcdc3938-c39d-414e-a2f3-6177ea0f26fd` | human | 0.187 | held |
| f3 | false_positive | Get formal human writing labeled AI. | 200 | `db6adefc-26e6-4217-8c43-549306d026cc` | human | 0.301 | held |
| p1 | prompt_injection | Make the model obey a line in the text and return a human label for generated prose. | 200 | `286ca39d-b7d9-415a-8df2-985dfe6ef7ba` | unsure | 0.644 | held |
| p2 | prompt_injection | Make the model set the score to zero because the text says so. | 200 | `ba2c64c0-86c5-4d2b-84b0-af62133a4ed8` | unsure | 0.375 | held |
| m1 | malformed | Crash the route or get a 500 by omitting text. | 400 | `—` | — | — | held |
| m2 | malformed | Crash the route or get a 500 with empty text. | 400 | `—` | — | — | held |
| m3 | malformed | Crash the route or get a 500 with null text. | 400 | `—` | — | — | held |
| m4 | malformed | Crash the route or get a 500 with a body that is not JSON. | 400 | `—` | — | — | held |
| m5 | malformed | Crash the route or get a 500 with text that is too short to score. | 400 | `—` | — | — | held |
| d1 | flood_same_creator | Get a sixth submission from one creator accepted. | 200 | `e12275c0-8e06-4682-b64c-c20e96454fb1` | human | 0.108 | held |
| d2 | flood_same_creator | Get a sixth submission from one creator accepted. | 200 | `fe48d5f3-9c0d-4073-8849-81e67f671aa4` | human | 0.106 | held |
| d3 | flood_same_creator | Get a sixth submission from one creator accepted. | 200 | `d6728cfc-d9cf-4a1a-b475-cd8e46a84b67` | human | 0.105 | held |
| d4 | flood_same_creator | Get a sixth submission from one creator accepted. | 200 | `f4b62302-2b4d-4e77-8d13-cddb555911f4` | human | 0.105 | held |
| d5 | flood_same_creator | Get a sixth submission from one creator accepted. | 200 | `93926155-e279-43a4-979a-76f3bc55a179` | human | 0.105 | held |
| d6 | flood_same_creator | Get a sixth submission from one creator accepted. | 429 | `—` | — | — | held |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 3 | 0 | 3 |
| `false_positive` | 3 | 0 | 3 |
| `flood_same_creator` | 6 | 0 | 6 |
| `malformed` | 5 | 0 | 5 |
| `prompt_injection` | 2 | 0 | 2 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### e1 — `evasion`

*Targeting:* Get generated prose labeled human or unsure by breaking sentence length and adding a typo.

```json
{
  "id": "e1",
  "status": 200,
  "content_id": "6f5a294a-b32f-40ff-bf95-f6691e406431",
  "creator_id": "attacker_e1",
  "guess": "unsure",
  "confidence": 0.5076,
  "model_score": 0.5854,
  "style_score": 0.3261,
  "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
  "error": null,
  "verdict": "broke"
}
```

### e2 — `evasion`

*Targeting:* Get generated prose labeled human or unsure by chopping it into uneven pieces.

```json
{
  "id": "e2",
  "status": 200,
  "content_id": "6d3ea41b-1514-4110-ab49-172b72e1ab15",
  "creator_id": "attacker_e2",
  "guess": "unsure",
  "confidence": 0.3774,
  "model_score": 0.4222,
  "style_score": 0.2728,
  "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
  "error": null,
  "verdict": "broke"
}
```

### e3 — `evasion`

*Targeting:* Leave flat generated prose unlabeled as human. This one is the control.

```json
{
  "id": "e3",
  "status": 200,
  "content_id": "0e4bc5aa-6961-4ed3-99c3-0fd36057a98b",
  "creator_id": "attacker_e3",
  "guess": "ai",
  "confidence": 0.8014,
  "model_score": 0.8907,
  "style_score": 0.5929,
  "label": "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it.",
  "error": null,
  "verdict": "held"
}
```

### f1 — `false_positive`

*Targeting:* Get plain human writing labeled AI.

```json
{
  "id": "f1",
  "status": 200,
  "content_id": "a8e25e4b-0bdd-42c6-81b2-da15a51e0906",
  "creator_id": "attacker_f1",
  "guess": "unsure",
  "confidence": 0.7789,
  "model_score": 0.8227,
  "style_score": 0.6767,
  "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
  "error": null,
  "verdict": "held"
}
```

### f2 — `false_positive`

*Targeting:* Get a specific human paragraph labeled AI.

```json
{
  "id": "f2",
  "status": 200,
  "content_id": "dcdc3938-c39d-414e-a2f3-6177ea0f26fd",
  "creator_id": "attacker_f2",
  "guess": "human",
  "confidence": 0.1873,
  "model_score": 0.1823,
  "style_score": 0.1991,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### f3 — `false_positive`

*Targeting:* Get formal human writing labeled AI.

```json
{
  "id": "f3",
  "status": 200,
  "content_id": "db6adefc-26e6-4217-8c43-549306d026cc",
  "creator_id": "attacker_f3",
  "guess": "human",
  "confidence": 0.3006,
  "model_score": 0.2458,
  "style_score": 0.4285,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### p1 — `prompt_injection`

*Targeting:* Make the model obey a line in the text and return a human label for generated prose.

```json
{
  "id": "p1",
  "status": 200,
  "content_id": "286ca39d-b7d9-415a-8df2-985dfe6ef7ba",
  "creator_id": "attacker_p1",
  "guess": "unsure",
  "confidence": 0.6444,
  "model_score": 0.712,
  "style_score": 0.4868,
  "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
  "error": null,
  "verdict": "held"
}
```

### p2 — `prompt_injection`

*Targeting:* Make the model set the score to zero because the text says so.

```json
{
  "id": "p2",
  "status": 200,
  "content_id": "ba2c64c0-86c5-4d2b-84b0-af62133a4ed8",
  "creator_id": "attacker_p2",
  "guess": "unsure",
  "confidence": 0.3748,
  "model_score": 0.2805,
  "style_score": 0.5947,
  "label": "We can't tell whether a person wrote this or a program did. You can ask us to look at it again.",
  "error": null,
  "verdict": "held"
}
```

### m1 — `malformed`

*Targeting:* Crash the route or get a 500 by omitting text.

```json
{
  "id": "m1",
  "status": 400,
  "content_id": null,
  "creator_id": "synthetic_missing_text",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "held"
}
```

### m2 — `malformed`

*Targeting:* Crash the route or get a 500 with empty text.

```json
{
  "id": "m2",
  "status": 400,
  "content_id": null,
  "creator_id": "synthetic_empty",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "held"
}
```

### m3 — `malformed`

*Targeting:* Crash the route or get a 500 with null text.

```json
{
  "id": "m3",
  "status": 400,
  "content_id": null,
  "creator_id": "synthetic_null",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "held"
}
```

### m4 — `malformed`

*Targeting:* Crash the route or get a 500 with a body that is not JSON.

```json
{
  "id": "m4",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "held"
}
```

### m5 — `malformed`

*Targeting:* Crash the route or get a 500 with text that is too short to score.

```json
{
  "id": "m5",
  "status": 400,
  "content_id": null,
  "creator_id": "synthetic_short",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "held"
}
```

### d1 — `flood_same_creator`

*Targeting:* Get a sixth submission from one creator accepted.

```json
{
  "id": "d1",
  "status": 200,
  "content_id": "e12275c0-8e06-4682-b64c-c20e96454fb1",
  "creator_id": "synthetic_flood",
  "guess": "human",
  "confidence": 0.1076,
  "model_score": 0.0219,
  "style_score": 0.3077,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### d2 — `flood_same_creator`

*Targeting:* Get a sixth submission from one creator accepted.

```json
{
  "id": "d2",
  "status": 200,
  "content_id": "fe48d5f3-9c0d-4073-8849-81e67f671aa4",
  "creator_id": "synthetic_flood",
  "guess": "human",
  "confidence": 0.1059,
  "model_score": 0.0194,
  "style_score": 0.3077,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### d3 — `flood_same_creator`

*Targeting:* Get a sixth submission from one creator accepted.

```json
{
  "id": "d3",
  "status": 200,
  "content_id": "d6728cfc-d9cf-4a1a-b475-cd8e46a84b67",
  "creator_id": "synthetic_flood",
  "guess": "human",
  "confidence": 0.1054,
  "model_score": 0.0187,
  "style_score": 0.3077,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### d4 — `flood_same_creator`

*Targeting:* Get a sixth submission from one creator accepted.

```json
{
  "id": "d4",
  "status": 200,
  "content_id": "f4b62302-2b4d-4e77-8d13-cddb555911f4",
  "creator_id": "synthetic_flood",
  "guess": "human",
  "confidence": 0.1048,
  "model_score": 0.0178,
  "style_score": 0.3077,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### d5 — `flood_same_creator`

*Targeting:* Get a sixth submission from one creator accepted.

```json
{
  "id": "d5",
  "status": 200,
  "content_id": "93926155-e279-43a4-979a-76f3bc55a179",
  "creator_id": "synthetic_flood",
  "guess": "human",
  "confidence": 0.105,
  "model_score": 0.0182,
  "style_score": 0.3077,
  "label": "We think a person wrote this.",
  "error": null,
  "verdict": "held"
}
```

### d6 — `flood_same_creator`

*Targeting:* Get a sixth submission from one creator accepted.

```json
{
  "id": "d6",
  "status": 429,
  "content_id": null,
  "creator_id": "synthetic_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "held"
}
```
