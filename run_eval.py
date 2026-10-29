#!/usr/bin/env python3
"""
Run your five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

The attack set tests what staff thought to test. This tests what *you* thought
to test, and the two rarely overlap much. Both count.

Fill in `scenarios.py` first — that's where you say what each criterion needs
run against it. A criterion about false positives needs your own writing. One
about label coverage needs inputs across the score range.

!! Three trials, and **your first signal runs a model, so identical input can
score differently twice.** That's exactly why repeats matter here.

This does the sending and the recording. It does not decide whether a trial
passed — that depends on the criterion you wrote, so the Verdict column comes
back blank.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help — which is a miserable first thing to hit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def bodies_for(scenario):
    """
    The request bodies one scenario sends.

    A "texts" scenario gets a creator_id made up for it. A "bodies" scenario is
    sent exactly as written, which is how a bad-input criterion says things a
    string can't — no `text` field, a null, something enormous.
    """
    if scenario.get("bodies"):
        return list(scenario["bodies"])
    return [
        {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
        for i, text in enumerate(scenario["texts"], 1)
    ]


def describe(body):
    """A short, readable note of what was sent — for the report."""
    if set(body) == {"text", "creator_id"} and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


def log_entries(url, timeout):
    """The audit log, oldest first. Appeal and bad-input checks read it back."""
    import requests
    response = requests.get(f"{url}/log", timeout=timeout)
    payload = response.json() if response.content else {}
    return payload.get("entries", [])


def post_json(url, path, body, timeout):
    """POST one JSON body and return status plus the parsed payload."""
    import requests
    response = requests.post(f"{url}{path}", json=body, timeout=timeout)
    try:
        payload = response.json() if response.content else {}
    except ValueError as exc:
        payload = {"error": f"{type(exc).__name__}: {exc}"}
    return response.status_code, payload


def run_appeal_trial(scenario, url, timeout):
    """
    Submit each text, appeal the content_id that comes back, then appeal an
    id that was never submitted.

    Criterion 4 needs all of that. A submit-only loop cannot see whether the
    original decision stayed in the log.
    """
    step = scenario["then_appeal"]
    reasoning = step["reasoning"]
    unknown_id = step["unknown_id"]
    results = []
    for i, text in enumerate(scenario["texts"], 1):
        body = {"text": text, "creator_id": f"eval_appeal_{i}"}
        status, payload = post_json(url, "/submit", body, timeout)
        content_id = payload.get("content_id")
        appeal_status, appeal_payload = post_json(
            url, "/appeal",
            {"content_id": content_id, "reasoning": reasoning},
            timeout,
        )
        entries = [entry for entry in log_entries(url, timeout)
                   if entry.get("content_id") == content_id]
        results.append({
            "status": status,
            "content_id": content_id,
            "guess": payload.get("guess"),
            "confidence": payload.get("confidence"),
            "model_score": payload.get("model_score"),
            "style_score": payload.get("style_score"),
            "label": payload.get("label"),
            "appeal_status": appeal_status,
            "appeal": appeal_payload,
            "log_statuses": [entry.get("status") for entry in entries],
            "original_still_decided": any(entry.get("status") == "decided" for entry in entries),
            "log_has_reasoning": any(
                entry.get("status") == "under_review" and entry.get("reasoning") == reasoning
                for entry in entries
            ),
            "sent": describe(body),
        })

    before = sum(
        1 for entry in log_entries(url, timeout)
        if entry.get("content_id") == unknown_id and entry.get("status") == "under_review"
    )
    appeal_status, appeal_payload = post_json(
        url, "/appeal",
        {"content_id": unknown_id, "reasoning": reasoning},
        timeout,
    )
    after = sum(
        1 for entry in log_entries(url, timeout)
        if entry.get("content_id") == unknown_id and entry.get("status") == "under_review"
    )
    results.append({
        "status": appeal_status,
        "guess": None,
        "content_id": unknown_id,
        "appeal_status": appeal_status,
        "appeal": appeal_payload,
        "under_review_rows_before": before,
        "under_review_rows_after": after,
        "sent": unknown_id,
    })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    rows = []
    for scenario in scenarios.SCENARIOS:
        print(f"\n{scenario['name']}  (criterion {scenario.get('criterion') or '—'})")

        trials = []
        for trial in range(1, args.trials + 1):
            if scenario.get("then_appeal"):
                try:
                    results = run_appeal_trial(scenario, args.url, args.timeout)
                except Exception as exc:  # noqa: BLE001
                    results = [{"status": None, "error": f"{type(exc).__name__}: {exc}"}]
            else:
                results = []
                for body in bodies_for(scenario):
                    preview = describe(body)
                    try:
                        response = requests.post(f"{args.url}/submit", json=body,
                                                 timeout=args.timeout)
                        payload = response.json() if response.content else {}
                        row = {
                            "status": response.status_code,
                            "content_id": payload.get("content_id"),
                            "guess": payload.get("guess"),
                            "confidence": payload.get("confidence"),
                            "model_score": payload.get("model_score"),
                            "style_score": payload.get("style_score"),
                            "label": payload.get("label"),
                            "sent": preview,
                        }
                        if scenario.get("bodies"):
                            creator = body.get("creator_id", "unknown")
                            if not isinstance(creator, str) or not creator.strip():
                                creator = "unknown"
                            decided = sum(
                                1 for entry in log_entries(args.url, args.timeout)
                                if entry.get("creator_id") == creator
                                and entry.get("status") == "decided"
                            )
                            row["decided_rows_for_creator"] = decided
                        results.append(row)
                    except Exception as exc:  # noqa: BLE001
                        results.append({"status": None, "error": f"{type(exc).__name__}: {exc}",
                                        "sent": preview})

            trials.append(results)
            bits = []
            for row in results:
                guess = row.get("guess") or "—"
                if row.get("appeal_status") is not None:
                    bits.append(f"{guess}/{row.get('appeal_status')}")
                else:
                    bits.append(f"{row.get('status')}:{guess}")
            print(f"  trial {trial}: {', '.join(bits)}")

        rows.append({"scenario": scenario, "trials": trials})

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Fill in Target from `criteria.md`, and Run and Verdict from the output",
        "underneath. Whether a trial passed depends on the criterion you wrote.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = f"{number}. {scenario['name']}" if number else scenario["name"]
        lines.append(f"| {name} |  | {' | '.join([' '] * n)} |  |")

    lines += ["", "---", "", "## What actually came back", "",
              "Real output. Paste the relevant parts into your README — the rubric",
              "asks for the actual JSON, not a description of it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, results in enumerate(row["trials"], 1):
            lines += [f"**Trial {trial_number}**", "", "```json",
                      json.dumps(results, indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
