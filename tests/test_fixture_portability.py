"""Canonical bytes are portable; historical fixture pixels remain unchanged."""
import hashlib
import json
from pathlib import Path
import struct
from io import BytesIO
import random
import tempfile
import unittest
import zlib

from PIL import Image
from tools.generate_image_fixtures import generate
from tools.canonical_png import encode

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
    def test_canonical_encoder_roundtrips_varied_rgb_content(self):
        generator = random.Random(812)
        for width, height in ((1, 1), (257, 91), (480, 300)):
            with self.subTest(size=(width, height)):
                pixels = bytes(generator.randrange(256) for _ in range(width * height * 3))
                frame = Image.frombytes('RGB', (width, height), pixels)
                encoded = encode(frame)
                self.assertEqual(encoded, encode(frame))
                with Image.open(BytesIO(encoded)) as decoded:
                    self.assertEqual(decoded.tobytes(), pixels)

    def test_historical_originals_preserved_and_canonical_pixels_identical(self):
        legacy = FIXTURES / 'legacy'
        manifest = json.loads((legacy / 'manifest.json').read_text())
        self.assertEqual(manifest['panel-a']['sha256'], '865db39953a926433d00de7be42eedc07f5795940bc07d78dc5c44d90dd16da6')
        self.assertEqual(manifest['panel-b']['sha256'], '0b787644c7315751357ed5e4bee087810d37d1ed1f976a264cd15505bad4547a')
        for name in ('panel-a', 'panel-b'):
            original, canonical = legacy / (name + '.png'), FIXTURES / (name + '.png')
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), manifest[name]['sha256'])
            with Image.open(original) as expected, Image.open(canonical) as actual:
                self.assertEqual(actual.mode, expected.mode)
                self.assertEqual(actual.size, expected.size)
                self.assertEqual(actual.tobytes(), expected.tobytes())

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
