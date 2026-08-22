# Upstream drift monitoring

Memtly HEIC Converter depends on exact upstream Memtly Community and Core refs. The overlay intentionally patches a small upload surface, so upstream movement should create a review prompt instead of silently changing compatibility claims.

## What is monitored

The committed baseline in `.upstream/memtly.lock.json` records public upstream facts only:

- pinned Memtly Community tag and commit;
- pinned Memtly Core commit / Community submodule gitlink;
- current observed public upstream default-branch heads and latest Community tag;
- hashes/object IDs for the files that define the overlay patch surface.

The watched files include the browser upload module, file utilities, gallery view, CSP/startup surface, server upload controller, image metadata helper, gallery item model, frontend package manifests, and the Core gitlink.

## How it runs

`.github/workflows/check-upstream-drift.yml` runs weekly and can also be triggered manually. It executes:

```sh
python3 scripts/check-upstream-drift.py --write
```

If the baseline or `.upstream/memtly-drift-report.md` changes, the workflow opens or updates an upstream drift review PR.

## What a drift PR means

A drift PR is a **review prompt**, not a compatibility claim.

Maintainers should read `.upstream/memtly-drift-report.md`, decide whether upstream changes affect the overlay, and perform exact-ref/runtime validation before updating compatibility status or targeting a newer Memtly release.

## Local commands

Check current upstream facts against the committed baseline:

```sh
python3 scripts/check-upstream-drift.py --check
```

Refresh the baseline and report after reviewing public upstream changes:

```sh
python3 scripts/check-upstream-drift.py --write
```

## Public/private boundary

The monitor uses public Git metadata and file hashes only. It must not include private deployment endpoints, infrastructure paths, raw runtime logs, credentials, personal media, or environment-specific validation evidence.
