# Agent guidance

## Purpose

Maintain a minimal, reviewable HEIC/HEIF-to-JPEG upload overlay for Memtly Community without weakening Memtly's existing upload and media lifecycle.

## Hard rules

- Work from exact pinned upstream refs; never silently follow `latest`.
- Keep raw `.heic`/`.heif` excluded from Memtly's server allow-list.
- Never upload raw HEIC after a conversion error.
- Preserve non-HEIC inputs byte-for-byte.
- Do not introduce a post-upload volume watcher.
- Do not commit credentials, environment-specific deployment data, raw logs, backups, or personal photos.
- Do not claim release compatibility before exact-ref runtime validation.
- Use focused branches and pull requests; do not push follow-up work directly to the default branch.

## Workflow

1. Re-read the active issue and newest comments.
2. Add or update a failing regression test.
3. Make the smallest implementation change.
4. Run static, unit, browser, build, and applicable runtime gates.
5. Inspect the complete diff and public-safety markers.
6. Update compatibility status and documentation factually.
