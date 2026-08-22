# Capture-date and metadata decision

Issue #6 asks whether the browser-conversion overlay should preserve capture date, EXIF/XMP, color profile metadata, orientation metadata, or original HEIC assets.

## Decision

For `v0.1.0-rc.1`, metadata copying and original HEIC archival storage are **deferred**.

The current browser-only release stores a JPEG derivative and intentionally does not copy EXIF, XMP, GPS, Live Photo auxiliary data, depth maps, or multi-image HEIF content into that derivative. The measured Chromium/heic2any path may include ICC profile data in the JPEG, but the overlay does not provide a general metadata-preservation feature. This keeps the upload boundary simple and avoids silently copying privacy-sensitive metadata into a public/event-gallery context.

If capture-date fidelity or archival original preservation becomes a product requirement, it should be designed as a later server-side or dual-asset feature with explicit privacy controls, not as an implicit browser-side metadata copy.

## Measurements performed

Fixture corpus:

| Fixture | Source | Measurement result | Decision relevance |
| --- | --- | --- | --- |
| `tests/fixtures/heic/lightning_mini.heif` | `libheif` `v1.20.2` test data | `file` reports ISO media; `ffprobe` cannot decode/display it (`moov atom not found`) | classifier fixture only; not useful for visual metadata/orientation validation |
| `tests/fixtures/heic/heic2any-demo-1.heic` | `heic2any` demo fixture at `3428539e643e112323a5b8a2c77c6402cb1372f6` | `ffprobe` reports HEVC still-image streams at `1440x960` and `240x160`, with `major_brand=mif1` and `compatible_brands=mif1heic`; no date/GPS/EXIF tags are exposed by `ffprobe` | browser conversion fixture; useful for checking derivative JPEG metadata behavior, but not sufficient for orientation/date preservation claims |

Runtime browser measurement:

- The browser upload regression now inspects the converted JPEG chunk before Memtly upload.
- The converted JPEG begins with JPEG magic bytes (`ffd8ff`).
- The converted JPEG upload does not contain APP1 `Exif` / XMP markers in the first 64 KiB scanned by the test.
- The converted JPEG upload may contain an APP2 `ICC_PROFILE` marker; the Chromium/heic2any path measured for the public demo fixture did include one. This is treated as color-management data, not capture-date or GPS preservation.

This confirms the current browser path produces a decodable JPEG derivative without preserving common EXIF/XMP metadata containers in the upload payload. It does not prove color appearance equivalence across engines or devices.

## Memtly behavior impact

Memtly derives `DateTaken` from EXIF/XMP fields when it can inspect them, then falls back to file creation time. The relevant Memtly `1.0.6` upload path sets:

```text
DateTaken = GetExifCreationDateTaken(finalFilePath) ?? GetCreationDatetime(finalFilePath)
```

For a converted browser JPEG with no EXIF/XMP capture date, Memtly cannot recover the original HEIC capture time from the uploaded derivative. Runtime readback against the exact `v0.1.0-rc.1` digest showed both the converted JPEG and ordinary PNG rows had `HasCreatedAt=1` and `DateTakenIsNull=0`; because the converted upload did not carry EXIF/XMP, that `DateTaken` value is a fallback timestamp rather than the original camera capture time.

The overlay preserves the source `File.lastModified` when creating the converted `File`, but this is not a substitute for EXIF `DateTimeOriginal` or a durable camera capture timestamp. It should not be presented as capture-date preservation. Memtly's date-taken sorting/grouping can still operate, but converted HEIC/HEIF images may be sorted/grouped by fallback timing instead of true camera capture time.

## Privacy rationale

Blindly copying metadata is risky because EXIF/XMP may include:

- GPS coordinates
- camera/device identifiers
- timestamps that reveal travel or attendance patterns
- software/edit history
- thumbnails or auxiliary data outside the visible image

For a guest-event upload workflow, the safer default is to avoid copying metadata unless the operator intentionally enables and documents that behavior.

## Rejected for this release candidate

### Browser-side metadata copy

Rejected for `v0.1.0-rc.1` because it would require parsing and reserializing metadata in untrusted browser inputs, deciding field-level privacy policy, testing every orientation/date/color edge case, and proving it does not reintroduce GPS or unexpected private metadata.

### Raw HEIC archival storage

Rejected for `v0.1.0-rc.1` because it would create a dual-asset lifecycle: raw original plus JPEG derivative. That would affect storage, downloads, deletion, duplicate handling, moderation, backups, privacy notices, and operator expectations.

### Server-side conversion as immediate replacement

Deferred. Server-side conversion may be appropriate if exact capture-date preservation, consistent orientation/color behavior, or original archival storage becomes a firm requirement. It should be scoped as a separate design and validation effort.

## Current product statement

For `v0.1.0-rc.1`:

- Converted uploads are JPEG derivatives.
- Raw HEIC/HEIF remains excluded from the server allow-list.
- EXIF/XMP/GPS/capture-date preservation is not supported.
- Original HEIC archival storage is not supported.
- Orientation/date/color preservation is not claimed beyond the measured fixture behavior.
- Real iPhone/iPad Safari validation remains a separate gate.

## Future acceptance criteria if revisited

A future metadata-preservation feature should include:

1. licensed fixtures with known EXIF date, orientation, GPS, XMP, and ICC profiles;
2. explicit allow/deny policy for each copied metadata field;
3. cross-browser evidence for browser-side behavior or exact server-side decoder versions;
4. Memtly sorting/grouping verification for capture date;
5. download/delete/backup behavior for derivative and any original asset;
6. public operator documentation and privacy warnings.
