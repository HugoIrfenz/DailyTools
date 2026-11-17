# WAV Inspect

Print channels, bits per sample, sample rate, frame count, and duration as JSON. Requires Python 3.9+ with no third-party packages.

```bash
python tools/wav-inspect/wav_inspect.py recording.wav
```

A stereo 16-bit PCM file with 24,000 frames at 48,000 Hz reports two channels and a duration of 0.5 seconds. Format support follows Python's `wave` module. Duration uses the header's frame count, and the tool does not verify the audio payload.
