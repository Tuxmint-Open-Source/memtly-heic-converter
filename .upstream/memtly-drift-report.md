# Upstream Memtly drift review

This report is public-safe and contains public upstream Git metadata only.
A drift report is a review prompt, not a compatibility claim.

## Pinned compatibility inputs

- Memtly Community tag: `1.0.6`
- Memtly Community commit: `d9b7298866c8cafbd515a6bf5e260e1d0423f262`
- Memtly Core commit: `cc8c88d625136f04ae1f1063fc635f74e739bd72`

## Observed upstream state

- Community default branch `master`: `1630dd19d8f2054a6a3a00185d440d0df3e0347e`
- Community latest tag: `1.0.7.4`
- Core default branch `master`: `ac926e33837ece3c5d5b2cf5b6b80d283fb01e66`

## Drift summary

- `community.observed_default_branch_head` changed from `4ad9d6b7175df87ec6d49ee36e584ee57bacc7ad` to `1630dd19d8f2054a6a3a00185d440d0df3e0347e`.
- `community.observed_latest_tag` changed from `1.0.6` to `1.0.7.4`.
- `core.observed_default_branch_head` changed from `cc8c88d625136f04ae1f1063fc635f74e739bd72` to `ac926e33837ece3c5d5b2cf5b6b80d283fb01e66`.

## Review checklist

- [ ] Decide whether upstream changes affect the overlay patch surface.
- [ ] If a new Memtly release is targeted, validate the exact release/artifact before changing compatibility claims.
- [ ] Keep raw runtime evidence and environment-specific validation details out of public artifacts.

## Local validation

```sh
python3 scripts/check-upstream-drift.py --check
```
