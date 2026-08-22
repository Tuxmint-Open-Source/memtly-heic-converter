# Public development roadmap

This roadmap is directional and best-effort. It is not a delivery-date commitment. Status claims distinguish planned, implemented, tested, released, and validated work.

## Now

1. Establish a reproducible custom-image overlay against exact Memtly `1.0.6`.
2. Add feature-flagged HEIC/HEIF detection and sequential browser conversion.
3. Add licensed fixture-driven unit and browser tests.

## Next

4. Prove unchanged JPEG, PNG, MP4, and MOV behavior through the existing upload path.
5. Validate review, thumbnails, full view, slideshow, download, duplicate handling, deletion, backup, recreation, and image rollback.
6. Publish a first pre-release with an explicit compatibility result.

## Later / decisions needed

- Determine whether capture-date/EXIF preservation is sufficient.
- Evaluate an integrated server-side conversion mode only if metadata preservation is a firm requirement.
- Decide whether preserving archival HEIC originals is worth a dual-asset lifecycle.
- Add scheduled upstream drift detection for patched files.

## Non-goals for the first release

- Uploading raw HEIC for browsers to display.
- Mutating Memtly's upload volume with a post-upload watcher.
- Preserving Live Photo video components or every HEIF auxiliary image.
- Automatic production deployment.
- Claiming support for unvalidated Memtly releases.

## Public/private boundary

Public issues contain reusable product outcomes and sanitized validation. Environment-specific deployment coordinates, raw logs, credentials, private topology, and operational evidence remain private. Security vulnerabilities should follow [SECURITY.md](SECURITY.md).
