# Public development roadmap

This roadmap is directional and best-effort. It is not a delivery-date commitment. Status claims distinguish planned, implemented, tested, released, and validated work.

## Now

1. Prepare the first pre-release publication path for `v0.1.0-rc.1`.
2. Review and merge release metadata, release notes, and the GHCR publication workflow.
3. After maintainer approval, create the immutable release tag and GitHub pre-release to publish the image.

## Completed candidate gates

- Reproducible custom-image overlay against exact Memtly `1.0.6`.
- Feature-flagged HEIC/HEIF detection and sequential browser conversion.
- Licensed fixture-driven unit and browser tests.
- Unchanged JPEG, PNG, MP4, and MOV behavior through the existing upload path.
- Review-relevant lifecycle behavior: chunking, duplicates, raw HEIC rejection, download, deletion, feature-disabled behavior, rollback/restore, and container recreation without volume deletion.

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
