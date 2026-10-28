"""
Turning two numbers into one, and one number into something a person can read.
← YOU BUILD THIS IN MILESTONES 4 AND 5

Two functions live here, and both are stubs.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0–1 signals into one 0–1 score. ← TODO (Milestone 4)

    Both inputs point the same way: higher means more likely AI. Your output
    should too.

    Args:
        model_score: from `detector.model_signal` — how predictable the text is.
        style_score: from `stylometry.style_signal` — the shape of the text.

    Returns:
        A float from 0.0 (confidently human) to 1.0 (confidently AI).

    ⚠️ **Write the rule down before you code it, and put the numbers in your
    README.** A weighted average is the obvious choice and it is not the only
    one. Things worth thinking about:

      - **What happens when they disagree?** One signal at 0.9 and the other at
        0.1 averages to 0.5 — "unsure". Is that what you want? It might be
        exactly right: two methods disagreeing IS uncertainty. Or you might
        decide one signal is more trustworthy when they split.

      - **Which way do you want to be wrong?** Weighting toward the signal that
        reads more human means fewer false accusations and more AI text
        getting through. There's no weighting that avoids the trade.

      - Milestone 4 asks you to find a case where your two signals split and
        write it down. That case is what this rule exists to handle.

    The weights in config.py are 0.5 and 0.5. A disagreement lands between
    the two scores. See the README section "The combining rule".
    """
    score = (
        config.WEIGHT_MODEL_SIGNAL * float(model_score)
        + config.WEIGHT_STYLE_SIGNAL * float(style_score)
    )
    return round(min(max(score, 0.0), 1.0), 4)


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the sentence a reader actually sees.

    Returns:
        (guess, label_text). `guess` is "ai", "human", or "unsure".
        `label_text` is the full sentence shown to a person.

    At or below HUMAN_THRESHOLD is human. At or above AI_THRESHOLD is AI.
    Everything between them is unsure. A score sitting on 0.35 is human.
    A score sitting on 0.80 is AI.
    """
    if score >= config.AI_THRESHOLD:
        return "ai", "We think a program wrote this. If you wrote it yourself, ask for a review and a person will read it."
    if score <= config.HUMAN_THRESHOLD:
        return "human", "We think a person wrote this."
    return "unsure", "We can't tell whether a person wrote this or a program did. You can ask us to look at it again."


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
