# Browser HEIC conversion

The overlay can convert selected HEIC/HEIF images to JPEG before Memtly's existing upload pipeline. It is **disabled by default**.

## Enablement

Set:

```dotenv
GALLERY_CLIENT_HEIC_CONVERSION=true
```

Optional limits:

```dotenv
GALLERY_CLIENT_HEIC_MAX_INPUT_MB=25
GALLERY_CLIENT_HEIC_MAX_PIXELS=40000000
GALLERY_CLIENT_HEIC_TIMEOUT_SECONDS=45
```

Keep `GALLERY_ALLOWED_FILE_TYPES` unchanged: raw `.heic` and `.heif` files must remain excluded. The browser replaces recognized HEVC HEIF input with an `image/jpeg` `.jpg` `File` before checksum and chunk calculations.

If an operator supplies a custom Content Security Policy, it must include:

```text
worker-src 'self' blob:
```

The default policy receives that narrow worker allowance. This overlay does not add `unsafe-eval`.

## Detection and failure behavior

- Reads at most the first 64 KiB and parses ISO-BMFF boxes.
- Requires an HEVC HEIF major or compatible brand (`heic`, `heix`, `hevc`, or `hevx`), including the `mif3`/`heic` marker emitted by current `libheif` mini fixtures.
- Does not trust MIME type or filename extension alone; hinted but unclassified HEIC/HEIF is rejected before upload.
- Converts one file at a time.
- Omits failed HEIC files rather than uploading their raw bytes.
- Preserves unaffected files in a mixed selection.
- A newer selection invalidates the older selection before upload.

## Product limits

The JPEG derivative does not preserve the original HEIC bitstream, auxiliary images, Live Photo content, HDR depth, EXIF, XMP, GPS, or capture date. Only the first image returned from a multi-image HEIF container is used. JPEG encoding is lossy.

The pixel bound is checked immediately after decode because this browser decoder does not expose dimensions before decoding. The source-byte bound protects the decoder input, but peak decode memory can still be substantially larger than the source file. Real-device Safari validation remains required before production readiness is claimed.
