# HEIC/HEIF fixture provenance

No personal guest photographs are required for automated tests. Fixtures must be public, reproducible, minimal, and traceable to a source license.

## Approved candidate sources

| Source | Candidate | Source license | Intended use |
| --- | --- | --- | --- |
| `strukturag/libheif` tag `v1.23.1` | `examples/example.heic` | MIT (`examples/COPYING`) | Valid HEVC-in-HEIF decode and JPEG conversion |
| `strukturag/libheif` tag `v1.23.1` | selected `fuzzing/data/corpus/*.{heic,heif}` | repository license applies; verify per file before vendoring | malformed and edge-case rejection tests |
| `alexcorvi/heic2any` commit `3428539e643e112323a5b8a2c77c6402cb1372f6` | selected `demo/*.heic` | MIT (`LICENSE.md`) | compatibility across several small real-world-style samples |

## Vendoring gate

Before a fixture enters Git:

1. Verify the exact source ref and applicable license.
2. Record source URL, original path, SHA-256, byte size, dimensions, and expected result.
3. Inspect embedded metadata and exclude fixtures with unnecessary personal data.
4. Copy the applicable license/notice into `tests/fixtures/LICENSES/`.
5. Keep the smallest set that covers distinct behavior.
6. Confirm GitHub permits the binary size and normal clones remain reasonable.

Malformed fuzzing corpus files must never be interpreted as successful-photo fixtures.
