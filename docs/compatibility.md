# Compatibility

Compatibility is stated as a pair: **Memtly HEIC Converter release × upstream Memtly source refs**.

A build from `main` is not a release compatibility claim. A release is only marked validated after its immutable tag and published image digest pass the documented validation matrix.

## Matrix

| Overlay release | Memtly Community | Community commit | Core commit | Image | Status |
| --- | --- | --- | --- | --- | --- |
| `v0.1.0-rc.1` | `1.0.6` | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` | `cc8c88d625136f04ae1f1063fc635f74e739bd72` | Pending GHCR publication | Pending exact-tag publication |
| `main` | `1.0.6` | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` | `cc8c88d625136f04ae1f1063fc635f74e739bd72` | Build locally | Candidate source line |

## Validation evidence

The current release-candidate source line is backed by public-safe reports:

- [build provenance](build-provenance.md)
- [browser conversion validation](validation-heic-candidate.md)
- [fixture provenance](fixture-provenance.md)
- [unchanged media lifecycle validation](validation-lifecycle.md)

## Unsupported / unknown

- Memtly versions other than `1.0.6` are unvalidated.
- Real iPhone/iPad Safari hardware validation is not complete.
- Original HEIC preservation, EXIF/XMP preservation, Live Photo auxiliaries, depth maps, and multi-image HEIF content are not supported by this browser-conversion release candidate.
- `latest` image tags are intentionally not published for pre-releases.
