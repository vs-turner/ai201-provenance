# Capstone criteria run — after preload

- Cold first submit before preload: 5.9905 s
- Cold first submit after preload: 1.1497 s
- Boot until healthy with preload: 4.9174 s

| Criterion | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|
| 1. latency_ms | 10/10 | 10/10 | 10/10 | MET |
| 2. fields | 10/10 | 10/10 | 10/10 | MET |
| 3. median cost | 0.0598 s | 0.0564 s | 0.0562 s | MET |
| 4. bad input | 3/3 | 3/3 | 3/3 | MET |
| 5. Path B start | 5.122 s | 4.311 s | 4.32 s | MET |
