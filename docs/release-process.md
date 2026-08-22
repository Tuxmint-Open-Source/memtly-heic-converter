# Release process

This project publishes reviewed release candidates from immutable Git tags. Release images are built by GitHub Actions from the tagged source and published to GitHub Container Registry.

## Preconditions

Before cutting a pre-release:

1. All release-preparation PRs are merged to `main`.
2. `VERSION` and `CHANGELOG.md` name the intended release candidate.
3. `docs/validation-heic-candidate.md` and `docs/validation-lifecycle.md` record public-safe validation for the exact source line being released.
4. The maintainer has explicitly approved creating the tag and GitHub pre-release.

## Tagging

Create an annotated tag on the reviewed `main` commit:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
version="v$(cat VERSION)"
git tag -a "$version" -m "Memtly HEIC Converter $version"
git push origin "$version"
```

## GitHub pre-release

Create the GitHub pre-release using the matching release notes file:

```bash
gh release create "v$(cat VERSION)" \
  --repo Tuxmint-Open-Source/memtly-heic-converter \
  --title "Memtly HEIC Converter v$(cat VERSION)" \
  --notes-file "docs/release-notes/v$(cat VERSION).md" \
  --prerelease
```

Publishing the GitHub pre-release triggers `.github/workflows/publish-release-image.yml`.

## Image tags

The release workflow publishes only immutable pre-release tags, not `latest`:

```text
ghcr.io/tuxmint-open-source/memtly-heic-converter:<release-tag>
ghcr.io/tuxmint-open-source/memtly-heic-converter:memtly-1.0.6-<release-tag>
```

The release workflow emits SBOM and provenance attestations through Docker Buildx/GitHub attestations. After the workflow completes, update the GitHub release notes with the observed image digest and workflow run URL.

## Compatibility statement

Use this shape for compatibility claims:

```text
memtly-heic-converter <release tag> × Memtly Community 1.0.6 / Core cc8c88d... = validated compatible for the documented pre-release matrix
```

Do not claim compatibility with other Memtly versions until their exact refs are validated.

## Rollback

Rollback is intentionally simple: switch the deployment back to the unmodified Memtly/foundation image and redeploy without deleting Memtly volumes or database data. The unchanged lifecycle validation report records that the rollback path was exercised for this release line.
