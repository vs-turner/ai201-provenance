"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def _sentence_word_counts(text: str) -> list[int]:
    return [len(words(sentence)) for sentence in sentences(text) if words(sentence)]


def sentence_length_spread(text: str) -> float:
    """
    Coefficient of variation of words per sentence.

    Higher means lumpier sentences, which this signal reads as more human.
    Fewer than two sentences has no spread to measure, so this returns 0.0.
    `style_signal` treats that 0.0 as "no evidence", not as "maximally even".
    """
    lengths = _sentence_word_counts(text)
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    if mean == 0:
        return 0.0
    return statistics.stdev(lengths) / mean


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Higher means a more varied vocabulary, which this signal reads as more
    human. The ratio falls as a text gets longer, so two texts of very
    different lengths are not directly comparable.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    Commas, semicolons, colons, dashes, parentheses, and quotes per word.

    Periods, question marks, and exclamation points are left out. Almost every
    sentence has one, so they do not separate writers. Apostrophes are left
    out too, because they sit inside words like "don't".
    Higher means more of the marks that vary between writers, read here as
    more human.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    marks = re.findall(r"[,;:()\[\]\"“”]|—|–|--", text)
    return len(marks) / len(tokens)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.

    Direction, after flipping onto "higher means more likely AI":
      sentence_length_spread   low CV -> high score. CV 0.8 maps to 0.
      type_token_ratio          high ratio -> low score. 0.85 maps to 0,
                                0.45 maps to 1.
      punctuation_density       low density -> high score. 0.10 marks per
                                word maps to 0.

    One sentence, or no words, contributes 0.5 for the measure that cannot
    be computed. That is "no evidence", not an accusation.

    Weights inside this score: spread 0.50, type-token ratio 0.25,
    punctuation 0.25. Spread gets half because the other two move less on
    a short paragraph.
    """
    def clamp(value: float) -> float:
        return min(max(value, 0.0), 1.0)

    n_sentences = len(_sentence_word_counts(text))
    if n_sentences < 2:
        spread_ai = 0.5
    else:
        # CV 0 is perfectly even. CV 0.8 is a short sentence beside a long one.
        spread_ai = clamp(1.0 - sentence_length_spread(text) / 0.8)

    tokens = words(text)
    if not tokens:
        ttr_ai = 0.5
        punct_ai = 0.5
    else:
        # 0.85 is a varied short paragraph. 0.45 is the same words on repeat.
        ttr_ai = clamp((0.85 - type_token_ratio(text)) / 0.40)
        # 0.10 is about one comma, dash, or semicolon every ten words.
        punct_ai = clamp(1.0 - punctuation_density(text) / 0.10)

    score = 0.50 * spread_ai + 0.25 * ttr_ai + 0.25 * punct_ai
    return round(clamp(score), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
