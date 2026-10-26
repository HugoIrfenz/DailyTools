# Line Sample

Select a deterministic reservoir sample from a line-oriented file. Memory use is proportional to the requested sample count rather than the input size, and selected lines retain source order by default.

Requires Python 3.9 or newer; no third-party packages.

```bash
python tools/line-sample/line_sample.py records.jsonl -n 100 --seed review-1 -o sample.jsonl
cat records.txt | python tools/line-sample/line_sample.py - -n 20
python tools/line-sample/line_sample.py records.txt -n 20 --shuffle
```

Input and output are handled as bytes, so line contents and existing newline bytes are not decoded or normalized. If the requested count exceeds the number of lines, every line is written. The default seed is `0`; identical input, count, seed, and Python runtime produce the same sample. This is statistical sampling with Python's pseudorandom generator, not cryptographic randomness. Input and output cannot be the same path.

Run the tests:

```bash
python -m unittest discover -s tools/line-sample -p 'test_*.py'
```
