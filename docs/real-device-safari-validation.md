# Real-device Safari validation checklist

Automated browser tests and desktop WebKit/Chromium checks are useful, but they are not evidence that real iPhone/iPad Safari upload behavior is ready for production. This checklist defines the minimum public-safe gate before changing the project status from pre-release/controlled testing to production-ready.

## Status

`v0.1.0-rc.1` has **not** completed real-device iPhone/iPad Safari validation.

Do not mark the release production-ready until this checklist is completed with a current iOS/iPadOS device and a maintainer reviews the evidence.

## Test environment requirements

Use the published immutable image, not a locally rebuilt or modified container:

```text
ghcr.io/tuxmint-open-source/memtly-heic-converter@sha256:b6f9a70b78c134e01abf64325822c08f84568dde185ce13a7b419bb599b4c6ba
```

Runtime requirements:

- HEIC conversion explicitly enabled.
- Server allow-list still excludes raw `.heic` and `.heif`.
- Normal JPEG/PNG/MP4/MOV allow-list behavior preserved.
- Rollback target available before testing.
- Test gallery uses non-personal media or purpose-made fixtures only.

Public reports may name browser/device classes and release versions, but must not include private hostnames, IP addresses, credentials, raw logs, personal photos, or guest-identifying metadata.

## Minimum device matrix

| Target | Required before production-ready claim? | Notes |
| --- | --- | --- |
| Current iPhone Safari | Yes | Use a real device, not only browser emulation. |
| Current iPad Safari | Yes | iPadOS can differ in file picker and memory behavior. |
| macOS Safari | Recommended | Useful additional WebKit signal; not a substitute for iPhone/iPad. |
| Android Chrome | Recommended | Confirms non-Apple behavior remains normal. |
| Desktop Chromium/Firefox | Already automated / recommended | Useful regression coverage, not Apple hardware evidence. |

## Test media policy

Use only media that is safe to share internally and safe to summarize publicly.

Recommended fixture set:

1. recent iPhone HEIC still image with no sensitive scene content;
2. HEIC image whose dimensions are clearly asymmetric, to expose orientation or rotation problems;
3. large-but-allowed HEIC image near the configured size/pixel limits;
4. ordinary JPEG;
5. ordinary PNG;
6. ordinary short MP4/MOV;
7. malformed or renamed HEIC-hinted file that must fail closed.

Avoid personal guest photos, location-sensitive images, faces, documents, badges, screens, or other private content. If real-device photos contain EXIF/GPS metadata, keep raw files and raw logs private.

## Browser scenarios

For each real iPhone/iPad target:

1. Open a fresh test gallery in Safari.
2. Confirm the upload control advertises HEIC/HEIF only when conversion is enabled.
3. Upload one valid HEIC still image.
4. Verify the app shows conversion/upload progress without freezing the tab.
5. Verify the stored uploaded file is JPEG, not raw HEIC/HEIF.
6. Verify thumbnail generation succeeds.
7. Verify gallery rendering/full-view rendering succeeds.
8. Verify download/export returns usable media.
9. Verify deletion removes the uploaded media and derived thumbnail(s).
10. Upload a mixed selection: HEIC + JPEG + PNG + MP4/MOV.
11. Verify non-HEIC files are not transformed.
12. Verify malformed HEIC-hinted input fails closed and does not upload raw data.
13. Test feature-disabled mode and confirm `.heic`/`.heif` are not advertised in `accept`.
14. Recreate/restart the container without deleting volumes and verify already uploaded converted media still renders/downloads.
15. Roll back to the foundation image and verify baseline ordinary-media behavior remains available.

## Evidence to record publicly

Public evidence should be sanitized and concise:

- release tag and immutable image digest;
- device class and browser version, without serial numbers or user identifiers;
- feature flag state;
- pass/fail table for the scenarios above;
- confirmation that raw `.heic`/`.heif` was not stored;
- known limitations observed;
- whether compatibility status changed.

## Evidence to keep private

Keep these out of GitHub issues, PRs, release notes, screenshots, and logs:

- private endpoint URLs, IP addresses, hostnames, topology, SSH paths, account names, tokens, passwords, and cookies;
- raw upload/download logs;
- database rows with user-identifying fields;
- original test photos or personal media;
- EXIF/GPS metadata from real photos;
- screenshots containing private gallery URLs or guest names.

## Pass/fail template

```text
Release: v0.1.0-rc.1
Image digest: sha256:b6f9a70b78c134e01abf64325822c08f84568dde185ce13a7b419bb599b4c6ba
Device class: iPhone / iPad
Browser: Safari <version>
Feature flag: enabled
Server allow-list excludes raw HEIC/HEIF: yes/no
Valid HEIC converts to JPEG: pass/fail
Raw HEIC stored: yes/no
Thumbnail: pass/fail
Gallery render: pass/fail
Download: pass/fail
Delete: pass/fail
Mixed ordinary media unchanged: pass/fail
Malformed HEIC fail-closed: pass/fail
Feature-disabled mode: pass/fail
Container recreate persistence: pass/fail
Rollback ordinary-media check: pass/fail
Production-ready claim allowed: no, unless every required gate passes and maintainer approves
```

## Compatibility update rule

Passing this checklist does not automatically validate future Memtly releases. It only supports the exact release/artifact pair tested. Update `docs/compatibility.md` only after the immutable release image digest and the exact upstream Memtly refs are verified.
