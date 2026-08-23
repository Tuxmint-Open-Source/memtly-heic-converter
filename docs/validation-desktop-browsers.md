# Desktop cross-browser conversion validation

This report records automated desktop browser-engine coverage for the HEIC conversion regression. It does **not** replace real iPhone/iPad Safari hardware validation.

## Artifact under test

- Overlay release: `v0.1.0-rc.1`
- Memtly Community: `1.0.6`
- Published image: `ghcr.io/tuxmint-open-source/memtly-heic-converter@sha256:b6f9a70b78c134e01abf64325822c08f84568dde185ce13a7b419bb599b4c6ba`
- Client HEIC conversion: enabled for this validation
- Server raw HEIC/HEIF allow-list: unchanged (raw HEIC/HEIF excluded)

## Automated matrix

| Playwright project | Engine | Result | Notes |
| --- | --- | --- | --- |
| `chromium` | Chromium | Passed | Exact published image, fresh temporary gallery. |
| `firefox` | Firefox | Passed | Exact published image, fresh temporary gallery. |
| `webkit` | Desktop WebKit | Passed | Exact published image in the pinned Playwright `1.62.1` environment; not real Safari/iOS. |

Each passing engine exercises the same assertions:

- a licensed real HEIC fixture is converted before upload;
- the upload uses a `.jpg` filename, `image/jpeg`, and JPEG magic bytes;
- an ordinary PNG remains PNG;
- no raw `.heic`/`.heif` upload is observed;
- malformed HEIC-hinted input fails closed;
- Memtly's upload-completion request is observed;
- converted JPEG metadata marker behavior remains measured.

## Fresh-session determinism

The test establishes Memtly's culture cookie before first navigation and explicitly chooses the anonymous guest path when the optional identity dialog appears. This avoids treating first-visit language reloads or guest-identification UI as converter failures while preserving the real guest upload flow.

Desktop WebKit ran through a loopback origin inside the pinned Playwright container. Memtly's existing uploader calls `crypto.randomUUID()`, which browsers expose only in secure contexts; loopback is treated as trustworthy and matches the HTTPS/localhost requirement. A first diagnostic run against a non-trustworthy container hostname correctly failed before upload because `crypto.randomUUID` was unavailable.

During test development, Firefox exposed a first-visit race: Memtly's language initialization reloaded the page while Webpack was loading the converter chunk. The aborted request was visible as `NS_BINDING_ABORTED`; after deterministic culture/identity setup, Firefox passed the unchanged conversion assertions.

## Non-claims

- Desktop Playwright WebKit is not Safari on real Apple hardware.
- This report does not measure iPhone/iPad memory pressure, Photos picker behavior, mobile tab termination, or device-specific orientation/color rendering.
- Production readiness remains blocked on the [real-device Safari validation checklist](real-device-safari-validation.md).
