import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import wave


SCRIPT = Path(__file__).with_name("wav_inspect.py")


class WavInspectTests(unittest.TestCase):
    def run_cli(self, path):
        return subprocess.run([sys.executable, SCRIPT, path], capture_output=True)

    def write_pcm(self, path, frames):
        with wave.open(str(path), "wb") as audio:
            audio.setparams((2, 2, 48000, 0, "NONE", "not compressed"))
            audio.writeframes(b"\x00" * (4 * frames))

    def test_stereo_metadata_and_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stereo.wav"
            self.write_pcm(path, 24000)
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "channels": 2, "bits_per_sample": 16, "sample_rate_hz": 48000,
            "frames": 24000, "duration_seconds": 0.5,
        })

    def test_zero_frame_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.wav"
            self.write_pcm(path, 0)
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["duration_seconds"], 0)

    def test_invalid_headers_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.wav"
            self.write_pcm(path, 1)
            pcm = path.read_bytes()
            for content in (b"", pcm[:20], pcm[:20] + struct.pack("<H", 3) + pcm[22:],
                            pcm[:24] + b"\x00" * 4 + pcm[28:]):
                with self.subTest(content=content):
                    path.write_bytes(content)
                    result = self.run_cli(path)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, b"")
                    self.assertIn(b"wav-inspect:", result.stderr)
            path.unlink()
            self.assertEqual(self.run_cli(path).returncode, 1)
