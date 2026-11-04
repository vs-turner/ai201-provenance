# Capstone criteria run — before improvement

- Produced by: client timings + `logs/audit.jsonl` (inline eval script)
- Service: `app.py::submit` / `app.py` health; fields written by `audit.log_decision` / `audit.log_rejection`
- 3 trials · 2026-11-03 16:23

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every scored submit writes latency_ms | 10 of 10 with latency_ms > 0 | 10/10 | 10/10 | 10/10 | MET |
| 2. Decided row names input and output fields | 10 of 10 complete field sets | 10/10 | 10/10 | 10/10 | MET |
| 3. Cost per run stays under 3.0 s warm | median of 10 ≤ 3.0 s | 0.0578 s | 0.0568 s | 0.0582 s | MET |
| 4. Refused body leaves timed rejection | 3 of 3 HTTP 400 + rejected + latency_ms > 0 | 3/3 | 3/3 | 3/3 | MET |
| 5. Path B starts from documented command | healthy /health within 15 s | 0.433 s | 0.214 s | 0.213 s | MET |

