# Validation report: HEIC browser-conversion candidate

This report records public-safe validation for the feature-flagged HEIC/HEIF browser-conversion candidate in this repository.

## Target

| Component | Version / ref |
| --- | --- |
| Memtly Community | `1.0.6` |
| Memtly Community commit | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` |
| Memtly Core gitlink | `cc8c88d625136f04ae1f1063fc635f74e739bd72` |
| Overlay branch | `feat/heic-browser-conversion` |
| Converter | `heic2any` `0.0.4` |
| Converter source commit | `3428539e643e112323a5b8a2c77c6402cb1372f6` |

The candidate image was built as an immutable local test image with HEIC conversion available but disabled by default. Runtime validation enabled the feature explicitly.

## What passed

| Scenario | Result |
| --- | --- |
| Exact upstream patch applies to a clean Memtly `1.0.6` checkout | Passed |
| Static foundation checks | Passed |
| Public-safety marker scan | Passed |
| Production frontend build | Passed |
| Production npm audit for runtime dependencies | Passed: zero reported vulnerabilities |
| HEIC classifier tests | Passed |
| Candidate container health and HTTP render | Passed |
| Existing ordinary PNG upload lifecycle | Passed |
| Browser-side HEIC conversion before upload | Passed |
| Converted upload stored as JPEG, not HEIC | Passed |
| Thumbnail files generated for converted upload | Passed |
| Gallery download contains JPEG and no raw HEIC | Passed |
| Temporary gallery deletion removes uploaded media | Passed |
| Malformed HEIC-hinted file does not send an upload request | Passed |

## Browser conversion evidence

A real browser test selected a licensed HEIC fixture through the gallery upload control. The intercepted upload request showed that the file entering Memtly's chunk endpoint had been converted before upload:

- filename ended in `.jpg`;
- MIME type was `image/jpeg`;
- bytes started with JPEG magic `ff d8 ff`;
- original raw HEIC bytes were not uploaded.

The server-side storage check found:

- one uploaded JPEG file;
- zero raw `.heic` or `.heif` files;
- generated thumbnails for the converted item.

A gallery download check returned a ZIP containing JPEG media and no raw HEIC/HEIF entries.

## Failure behavior

A malformed file with a HEIC filename/MIME hint was selected in the browser. The client rejected it before upload, and no Memtly upload request was sent for that file.

This is the intended fail-closed behavior: a conversion failure must not fall back to uploading raw HEIC/HEIF.

## Existing upload behavior

A self-cleaning ordinary PNG smoke test passed against the candidate runtime:

- administrator login;
- temporary gallery creation/readback;
- PNG chunk upload;
- upload batch completion;
- gallery cleanup.

This confirms that the existing Memtly upload path still works for normal supported media in the candidate runtime.

## What this validates

This validation supports the issue #2 claim that the candidate can convert selected HEIC/HEIF still images to JPEG in the browser before Memtly's existing checksum/chunk upload path, while preserving the server-side HEIC/HEIF exclusion.

## What this does not claim

- This is not a production-ready release claim.
- Real iPhone/iPad Safari validation has not yet been performed.
- EXIF/XMP, original HEIC bitstreams, Live Photo auxiliaries, depth maps, and multi-image HEIF content are not preserved by this browser-conversion slice.
- The JPEG derivative is the stored/downloaded media artifact for this candidate path.
- Browser memory behavior on real mobile devices still requires hardware validation.
