# Quality gates

A change is not complete until applicable gates pass.

## Repository and supply chain

- Exact upstream Memtly tag resolves to the expected commit.
- Exact Core submodule commit is recorded.
- Overlay patch applies cleanly and fails closed on upstream drift.
- Converter and build dependencies are pinned.
- Licenses and fixture provenance are present.
- No secrets, private infrastructure markers, logs, backups, or personal photos are committed.

## Conversion behavior

- Valid `.heic` and `.heif` inputs become decodable JPEG `File` objects.
- Detection works when MIME is empty or inconsistent.
- Renamed non-HEIC input is rejected as HEIC rather than blindly converted.
- Malformed HEIC fails before network upload.
- Mixed selections continue after a per-file conversion failure according to documented UX.
- Conversion is sequential and respects size/pixel limits.
- JPEG quality, dimensions, orientation, color behavior, and metadata loss are measured or explicitly documented as unclaimed limitations.

## Regression behavior

- JPEG, PNG, MP4, and MOV are not transformed.
- Existing checksum and 10 MB chunk upload behavior remains active.
- Server extension validation remains active.
- Review queue, thumbnails, full view, slideshow, download, duplicate prevention, deletion, backup, recreation, and rollback are exercised.
- Disabling the feature restores baseline behavior.

## Browser matrix

- Current Safari on iPhone/iPad when hardware is available.
- Safari on macOS or an equivalent WebKit gate.
- Current Chrome/Chromium and Firefox desktop.
- Current Android Chrome when hardware is available.

Automated browser emulation is useful but is not represented as real iPhone hardware validation. Use the [real-device Safari validation checklist](docs/real-device-safari-validation.md) before making any production-ready claim.
