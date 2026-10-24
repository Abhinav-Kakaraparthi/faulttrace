# Synthetic image fixtures

These are invented digital instruments, not photographs or real plant data.
`panel-a.png` displays 180 kPa. `panel-b.png` is the same scene with the entire
display, including unit, replaced by solid opaque RGB pixels. The hidden
reading is unrecoverable from panel-b. There are no alpha channels or PNG
metadata fields. A photograph would not establish asset identity or action.

Neutral names, opaque evidence references, and SHA-256 hashes appear in the
runtime manifest. The manifest, filenames, README, generator, and test answers
are never uploaded: only PNG bytes and the common contract prompt are sent.
Expected values occur only in offline generator/test/documentation material;
the probe does not load them. Payload text does not describe either answer.

Reproduce with Python 3.12 and the already available development-only Pillow
12.3.0 (`python tools/generate_image_fixtures.py`). No package is installed
by the probe; inference and standard-library tests do not require Pillow.
Exact regeneration was checked with that version and embedded Pillow fonts.
Changing Pillow may change bytes and requires reviewing/updating the manifest.

The 0..1000 accepted reading range is a synthetic test constraint only,
never an industrial operating limit. Accuracy on these fixtures cannot
establish arbitrary analog-gauge or real-world equipment-reading accuracy.
