# HEIC/HEIF fixture provenance

No personal guest photographs are required for automated tests. Fixtures must be public, reproducible, minimal, and traceable to a source license.

## Vendored fixtures

The current fixture corpus is intentionally small. Machine-checkable metadata lives in [`tests/fixtures/manifest.json`](../tests/fixtures/manifest.json), and the fixture integrity gate runs with:

```bash
npm run test:fixtures
# or: node tests/scripts/verify-fixtures.mjs
```

Browser regression tests are defined with Playwright and run with:

```bash
npm install
MEMTLY_BROWSER_BASE_URL=http://127.0.0.1:8080 \
MEMTLY_BROWSER_GALLERY_IDENTIFIER=<temporary-test-gallery-identifier> \
npm run test:browser
```

The browser test is skipped unless the runtime environment variables are present.

| Fixture | Source ref | Source path | License file | SHA-256 | Size | Purpose |
| --- | --- | --- | --- | --- | ---: | --- |
| `tests/fixtures/heic/lightning_mini.heif` | `strukturag/libheif` `v1.20.2` | `tests/data/lightning_mini.heif` | `tests/fixtures/LICENSES/libheif-COPYING.txt` | `47bdf004cf1abb77498917dc5a91f01b18ae1b2985113585595441b57fbf4a84` | 4,726 bytes | Valid compact HEIF classifier coverage, including the `mif3`/`heic` marker pattern. |
| `tests/fixtures/heic/heic2any-demo-1.heic` | `alexcorvi/heic2any` commit `3428539e643e112323a5b8a2c77c6402cb1372f6` | `demo/1.heic` | `tests/fixtures/LICENSES/heic2any-LICENSE.md` | `645877c52c5c656e2004b38f9520e717bbc6670541a56c098b9b7f78de496e8f` | 41,389 bytes | Browser conversion fixture known to decode through the selected converter. |

## Metadata review

The corpus uses small upstream test/demo media rather than personal event photographs. The manifest records the source URL/ref, source path, license, checksum, byte size, inspection note, purpose, and expected result for every committed binary fixture.

The current automated metadata gate verifies that each committed fixture:

1. exists at the manifest path;
2. matches the recorded byte size;
3. matches the recorded SHA-256;
4. has a non-empty referenced license file;
5. contains a bounded ISO-BMFF `ftyp` box.

The project does not currently depend on EXIF/GPS metadata from these fixtures, and the browser-conversion slice does not preserve EXIF/XMP in converted JPEG derivatives.

## Browser tests

The browser test spec lives at [`tests/browser/heic-upload.spec.mjs`](../tests/browser/heic-upload.spec.mjs). It is intentionally environment-driven so private runtime details are never committed.

Required environment variables for runtime browser tests:

```bash
MEMTLY_BROWSER_BASE_URL=http://127.0.0.1:8080 \
MEMTLY_BROWSER_GALLERY_IDENTIFIER=<temporary-test-gallery-identifier> \
npx playwright test tests/browser/heic-upload.spec.mjs
```

Optional:

```bash
MEMTLY_BROWSER_HEIC_FIXTURE=tests/fixtures/heic/heic2any-demo-1.heic
```

The browser spec validates:

- HEIC conversion is enabled in the rendered gallery form;
- `.heic` appears in the upload control accept list;
- a real HEIC fixture is converted before Memtly's upload request;
- the upload request carries a `.jpg` filename, `image/jpeg` MIME type, and JPEG magic bytes;
- a malformed HEIC-hinted file does not send an upload request.

Browser test output must distinguish local Chromium/WebKit/Firefox automation from real iPhone/iPad Safari hardware. Automated browser engines are useful regression gates, but they do not replace the real-device Safari gate.

## Adding fixtures

Before a new fixture enters Git:

1. Verify the exact source ref and applicable license.
2. Record source URL, original path, SHA-256, byte size, dimensions or an explicit reason dimensions are not asserted, and expected result.
3. Inspect embedded metadata and exclude fixtures with unnecessary personal data.
4. Copy the applicable license/notice into `tests/fixtures/LICENSES/`.
5. Keep the smallest set that covers distinct behavior.
6. Confirm normal repository clones remain reasonable.

Malformed fuzzing corpus files must never be interpreted as successful-photo fixtures.
