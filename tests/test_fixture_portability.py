"""Diagnostic parity checks; existing strict PNG byte equality remains unchanged."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from PIL import Image
from tools.generate_image_fixtures import generate

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures/image-evidence'


def idat(path):
    raw, offset, compressed = path.read_bytes(), 8, bytearray()
    while offset < len(raw):
        length = struct.unpack('>I', raw[offset:offset + 4])[0]
        if raw[offset + 4:offset + 8] == b'IDAT':
            compressed.extend(raw[offset + 8:offset + 8 + length])
        offset += length + 12
    return zlib.decompress(compressed)


class FixturePortabilityTests(unittest.TestCase):
    def test_raster_and_png_filters_match_independently_of_compression(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)
            generate(destination)
            for name in ('panel-a.png', 'panel-b.png'):
                with self.subTest(name=name):
                    with Image.open(destination / name) as actual, Image.open(FIXTURES / name) as expected:
                        self.assertEqual(actual.mode, 'RGB')
                        self.assertEqual(actual.size, (480, 300))
                        self.assertEqual(actual.tobytes(), expected.tobytes())
                    self.assertEqual(idat(destination / name), idat(FIXTURES / name))
            expected = json.loads((FIXTURES / 'manifest.json').read_text())
            actual = json.loads((destination / 'manifest.json').read_text())
            self.assertEqual({k: v['evidence_ref'] for k, v in actual.items()},
                             {'panel-a': 'image-001', 'panel-b': 'image-002'})
            self.assertEqual(set(actual), set(expected))
