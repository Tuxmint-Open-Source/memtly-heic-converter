# Upstream Memtly drift review

This report is public-safe and contains public upstream Git metadata only.
A drift report is a review prompt, not a compatibility claim.

## Pinned compatibility inputs

- Memtly Community tag: `1.0.6`
- Memtly Community commit: `d9b7298866c8cafbd515a6bf5e260e1d0423f262`
- Memtly Core commit: `cc8c88d625136f04ae1f1063fc635f74e739bd72`

## Observed upstream state

- Community default branch `master`: `3f1f23ea76ce1c22bd603e9433287d64581dc5ae`
- Community latest tag: `1.0.7.6`
- Core default branch `master`: `feadc47f78aab213cdbc792c5a7037cba9024195`

## Drift summary

- `community.observed_default_branch_head` changed from `4ad9d6b7175df87ec6d49ee36e584ee57bacc7ad` to `3f1f23ea76ce1c22bd603e9433287d64581dc5ae`.
- `community.observed_latest_tag` changed from `1.0.6` to `1.0.7.6`.
- `core.observed_default_branch_head` changed from `cc8c88d625136f04ae1f1063fc635f74e739bd72` to `feadc47f78aab213cdbc792c5a7037cba9024195`.

## Review checklist

- [ ] Decide whether upstream changes affect the overlay patch surface.
- [ ] If a new Memtly release is targeted, validate the exact release/artifact before changing compatibility claims.
- [ ] Keep raw runtime evidence and environment-specific validation details out of public artifacts.

## Local validation

```sh
python3 scripts/check-upstream-drift.py --check
```
