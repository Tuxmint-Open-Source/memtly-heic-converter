# Changelog

All notable changes to this project are documented here. This project follows semantic-versioned release candidates while the HEIC overlay is validated.

## [0.1.0-rc.1] - pending

### Added

- Reproducible Memtly `1.0.6` overlay image build with exact Community/Core source guards.
- Feature-flagged browser-side HEIC/HEIF still-image conversion to JPEG before Memtly upload.
- Bounded HEIC/HEIF detection, sequential conversion, and fail-closed handling for malformed HEIC-hinted files.
- Licensed public HEIC/HEIF fixtures and browser regression tests.
- Public-safe validation reports for the conversion candidate and unchanged Memtly media lifecycle.
- Release workflow for publishing pre-release images to GitHub Container Registry.
- Public upstream drift monitor for the pinned Memtly refs and watched patch-surface files.
- Real-device Safari validation checklist for iPhone/iPad hardware testing before production-ready claims.
- Read-only pull-request quality gate with reusable exact-upstream patch-apply and public-safety checks.
- Structured public-safe issue/PR intake templates and Contributor Covenant code of conduct.

### Validated

- Memtly Community `1.0.6` at commit `d9b7298866c8cafbd515a6bf5e260e1d0423f262`.
- Memtly Core gitlink `cc8c88d625136f04ae1f1063fc635f74e739bd72`.
- `heic2any` `0.0.4` at commit `3428539e643e112323a5b8a2c77c6402cb1372f6`.
- Browser conversion path, malformed HEIC fail-closed behavior, ordinary media lifecycle, feature-disabled mode, rollback/restore, container recreation without volume deletion, Chromium/Firefox/desktop WebKit conversion regression, and exact published-image digest `sha256:b6f9a70b78c134e01abf64325822c08f84568dde185ce13a7b419bb599b4c6ba`.

### Known limitations

- This is a pre-release candidate, not a production-ready stable release.
- Real iPhone/iPad Safari validation remains outstanding.
- Converted JPEG files do not preserve the original HEIC bitstream.
- EXIF/XMP/GPS metadata and original capture time are not preserved by this browser-conversion slice; runtime browser testing confirms no EXIF/XMP marker in the converted upload, while ICC profile data may be present depending on browser/converter behavior.
