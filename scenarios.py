"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

# Frozen before the three trials. Criterion 1 uses the bus paragraph and the
# lab note already in the README, plus eight more notes in that same specific
# voice, so the count is ten. Criterion 4 sets then_appeal. run_eval.py submits
# each text, appeals the content_id that comes back, then appeals an id that
# was never submitted. The stock runner only posts to /submit, so that path
# was added there.

SCENARIOS = [
    {
        "name": "my own writing",
        "criterion": 1,
        "texts": [
            "I missed the 6:40 bus again because the stop on Clement is a guess. The driver slowed, saw nobody he recognized, and kept going. I stood there with a wet sleeve and the same argument I have with myself every Tuesday: leave ten minutes earlier, or stop pretending 6:40 is a real plan.",
            "The lab went fine until the last step. I mixed the two solutions and waited, and the color changed the way the handout said it would. I am still not sure why the third beaker stayed clear. Maybe I measured wrong. The writeup is due Friday.",
            "The rice from Sunday is still in the blue pot, which I keep meaning to wash and then don't. I ate half of it cold over the sink because the microwave smells like the popcorn somebody burned in February. There is one clean fork. I used a spoon.",
            "My hold on the camera manual finally came in, three weeks late, and the slip says I have until Thursday. The desk person had already started the next person's pile when I got there. I said my name twice. She found it under a book about knots.",
            "I left the umbrella in the lecture hall, the black one with the bent rib, so the walk to the train was just me and a folder over my head. The folder is the draft with the red comments. The comments ran. I can still read most of them.",
            "Nobody answered in the group chat until 11, and then it was only Maya saying she can do the chart if someone else writes the captions. I said I would. I have not started. The chart she sent is a screenshot of a spreadsheet with the columns cut off.",
            "I went to the market for eggs and came back with eggs, a lime, and the wrong milk. The line was out the door because the card reader was down and the cashier was doing cash in her head. A kid in front of me bought one onion. Just one.",
            "The radiator in the front room knocks twice and then hisses, which used to scare me and now just means the heat is coming. I put a towel on the windowsill where the draft comes in. The plant up there is leaning toward the lamp again. I turned the lamp.",
            "My sister called while I was on the 22, and I missed it, then called her back from the stop at Fillmore. She wanted the name of the clinic Mom went to in March. I had it in a note. The note was on the other phone, the one with the cracked corner.",
            "Alarm at 7:10, snooze, alarm at 7:19, and then I was awake because the upstairs neighbor dropped something heavy. Coffee was whatever was left in the pot. I added water. It tasted like the pot. I drank it on the steps while my socks got damp.",
        ],
    },
    {
        "name": "score spread",
        "criterion": 2,
        # First text is the uneven paragraph. Second is the flat generated prose.
        # The gap is the second combined score minus the first.
        "texts": [
            "I missed the 6:40 bus again because the stop on Clement is a guess. The driver slowed, saw nobody he recognized, and kept going. I stood there with a wet sleeve and the same argument I have with myself every Tuesday: leave ten minutes earlier, or stop pretending 6:40 is a real plan.",
            "The implementation of the proposed framework requires careful consideration of several key factors. First, it is important to note that the system must be able to handle a wide variety of different inputs. Additionally, the overall performance of the solution depends on a number of important variables. Furthermore, it is essential to ensure that the approach remains robust across a range of scenarios.",
        ],
    },
    {
        "name": "label coverage",
        "criterion": 3,
        # Two expected human, two expected unsure, two expected AI.
        "texts": [
            "I missed the 6:40 bus again because the stop on Clement is a guess. The driver slowed, saw nobody he recognized, and kept going. I stood there with a wet sleeve and the same argument I have with myself every Tuesday: leave ten minutes earlier, or stop pretending 6:40 is a real plan.",
            "The lab went fine until the last step. I mixed the two solutions and waited, and the color changed the way the handout said it would. I am still not sure why the third beaker stayed clear. Maybe I measured wrong. The writeup is due Friday.",
            "The implementation of the proposed framework requires careful consideration of several key factors. First, it is important to note that the system must be able to handle a wide variety of different inputs. Wait. Additionally, the overall performance of the solution depends on a number of important varibles. I keep typing that wrong and the spellcheck shrugs.",
            "The implementation of the proposed framework requires careful consideration of several key factors. First, it is important to note that the system must be able to handle a wide variety of different inputs. Additionally, the overall performance of the solution depends on a number of important variables. Furthermore, it is essential to ensure that the approach remains robust across a range of scenarios.",
            "The system provides a clear result. The system supports the user. The system handles the input. The system improves the output. The system meets the goal. The system follows the rule.",
            "The process delivers a useful outcome. The process reduces the delay. The process keeps the record. The process checks the result. The process repeats the step. The process reports the status.",
        ],
    },
    {
        "name": "appeal path",
        "criterion": 4,
        "texts": [
            "I missed the 6:40 bus again because the stop on Clement is a guess. The driver slowed, saw nobody he recognized, and kept going.",
            "The lab went fine until the last step. I mixed the two solutions and waited, and the color changed the way the handout said it would.",
            "The rice from Sunday is still in the blue pot, which I keep meaning to wash and then don't. I ate half of it cold over the sink.",
            "My hold on the camera manual finally came in, three weeks late, and the slip says I have until Thursday.",
            "I left the umbrella in the lecture hall, the black one with the bent rib, so the walk to the train was just me and a folder over my head.",
        ],
        "then_appeal": {
            "reasoning": "I wrote this myself. Please read it again.",
            "unknown_id": "not-a-real-content-id",
        },
    },
    {
        "name": "bad input",
        "criterion": 5,
        "bodies": [
            {"creator_id": "eval_bad_missing"},
            {"text": "", "creator_id": "eval_bad_empty"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": "a" * 8001, "creator_id": "eval_bad_huge"},
            {"text": "hi", "creator_id": "eval_bad_short"},
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
