# SRT Shift

Shift numbered SRT cues by a signed millisecond offset. Requires Python 3.9+ with no third-party packages.

```bash
printf '1\n00:00:01,000 --> 00:00:02,000\nHello\n' > subtitles.srt
python tools/srt-shift/srt_shift.py subtitles.srt --ms 500 > shifted.srt
```

The example shifts the cue to `00:00:01,500 --> 00:00:02,500`. Input must be UTF-8, optionally with a BOM. Output uses LF and one blank line between cues. The entire file is read into memory. Negative resulting timestamps and reversed intervals are rejected. Use a different output filename from the input.
