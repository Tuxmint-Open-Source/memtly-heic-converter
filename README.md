# Memtly HEIC Converter

A feature-flagged build overlay for converting HEIC/HEIF still images to JPEG **in the guest's browser before upload** to [Memtly Community](https://github.com/Memtly/Memtly.Community).

> [!IMPORTANT]
> This independent community project is not affiliated with, endorsed by, or supported by Memtly or its maintainers. Do not report extension-specific problems to the Memtly project unless they are reproduced with an unmodified upstream image.

## Status

**Feature-flagged browser conversion pre-release. Not ready for production.**

The first compatibility target is:

| Extension line | Memtly Community | Upstream commit | Status |
| --- | --- | --- | --- |
| `v0.1.0-rc.1` | `1.0.6` | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` | validated compatible pre-release |
| `main` | `1.0.6` | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` | validated candidate source line |

Follow the [public roadmap](ROADMAP.md), [compatibility matrix](docs/compatibility.md), and pinned roadmap issue for current work.

## Foundation image

Issue #1 established the merged Memtly `1.0.6` control image. The build verifies the annotated Community tag, Community commit, Core gitlink, and checked-out Core commit, then applies the committed patch series with drift checks.

```bash
./scripts/test-foundation.sh
docker build --pull=false -t memtly-heic-converter:1.0.6-heic-candidate .
```

See [build provenance](docs/build-provenance.md), [browser conversion](docs/browser-conversion.md), [fixture provenance](docs/fixture-provenance.md), [compatibility](docs/compatibility.md), [metadata decision](docs/metadata-decision.md), the public-safe [candidate validation report](docs/validation-heic-candidate.md), and the [unchanged lifecycle validation report](docs/validation-lifecycle.md). Conversion remains disabled at runtime unless explicitly enabled.

## Intended behavior

```text
HEIC/HEIF selected
  → detect from a bounded ISO-BMFF content scan
  → convert sequentially to JPEG in-browser
  → hand the new .jpg File to Memtly's existing upload path
  → Memtly retains its checksum, chunking, validation, review,
    thumbnail, gallery, download, deletion, and backup behavior
```

Non-HEIC files must pass through unchanged. Raw `.heic` and `.heif` remain excluded from the server allow-list. If conversion fails, the file must not upload.

## Why an overlay instead of a fork?

The project aims to build from an exact upstream Memtly ref and apply a small, reviewable patch. This keeps upstream provenance visible, makes drift detectable, and avoids maintaining an unrelated copy of the full application history.

## Safety and limitations

- The JPEG is a derivative, not an archival HEIC original.
- HEIF sequences, Live Photo auxiliaries, depth maps, and other auxiliary images may not be retained.
- EXIF/XMP/GPS metadata and original capture time are not preserved by the `v0.1.0-rc.1` browser-conversion path.
- Browser conversion can be memory-intensive on mobile devices, so conversion will be sequential and bounded.
- HEVC/HEIC codec patents may matter in some jurisdictions. Open-source licensing is not a patent opinion.

See [docs/architecture.md](docs/architecture.md), [QA.md](QA.md), and [SECURITY.md](SECURITY.md).

## Licensing and transparency

Project code and patches are licensed under GPL-3.0. Bundled dependencies and test fixtures retain their own licenses and notices.

Development is AI-assisted by [`hermes-archham`](https://github.com/hermes-archham) under human maintainer review. Trust should come from reviewable source, pinned provenance, tests, and published validation—not from authorship claims.
