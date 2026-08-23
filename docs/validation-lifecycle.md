# Validation report: unchanged Memtly media lifecycle

This report records public-safe validation that the HEIC browser-conversion overlay does not bypass or replace Memtly's ordinary media lifecycle.

## Target

| Component | Version / ref |
| --- | --- |
| Memtly Community | `1.0.6` |
| Memtly Community commit | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` |
| Memtly Core gitlink | `cc8c88d625136f04ae1f1063fc635f74e739bd72` |
| Prior validation PRs | #8, #9, #10 |

The candidate runtime used the same overlay image family established by the previous validation reports. HEIC conversion was enabled for candidate checks, while the server-side allow-list remained `.jpg,.jpeg,.png,.mp4,.mov`.

## What passed

| Scenario | Foundation/control | Candidate with HEIC enabled | Candidate with HEIC disabled | Rollback image |
| --- | --- | --- | --- | --- |
| Application health and HTTP render | Passed | Passed | Passed | Passed |
| Authenticated administrator login | Passed | Passed | Passed | Passed |
| Temporary clean gallery creation/readback | Passed | Passed | Passed | Passed |
| Ordinary JPEG upload | Passed | Passed | Passed | Passed |
| Ordinary PNG upload | Passed | Passed | Passed | Passed |
| Ordinary MP4 upload | Passed | Passed | Passed | Passed |
| Ordinary MOV upload | Passed | Passed | Passed | Passed |
| Multi-chunk ordinary upload over Memtly's 10 MB chunk size | Passed | Passed | Passed | Passed |
| 150 generated ordinary PNG uploads in one batch | Passed | Passed | Not part of disabled-mode smoke | Not part of rollback smoke |
| Batch completion after ordinary uploads | Passed | Passed | Passed | Passed |
| Duplicate checksum rejection | Passed | Passed | Passed | Passed |
| Raw `.heic` server-side rejection | Passed | Passed | Passed | Passed |
| Gallery page render with ordinary media entries | Passed | Passed | Passed | Passed |
| Gallery ZIP download | Passed | Passed | Passed | Passed |
| Download contains ordinary JPEG/PNG/MP4/MOV entries | Passed | Passed | Passed | Passed |
| Download contains no raw HEIC/HEIF entries | Passed | Passed | Passed | Passed |
| Temporary gallery deletion and cleanup | Passed | Passed | Passed | Passed |
| Gallery data survives container recreation without deleting volumes | Not separately run | Passed | Not separately run | Not separately run |
| Browser HEIC path reaches the same post-selection upload pipeline as JPEG | Not applicable | Passed in #9/#10 validation | Disabled by design | Not applicable |

## Validation scripts

The reusable lifecycle smoke is [`scripts/smoke-lifecycle.py`](../scripts/smoke-lifecycle.py). It is environment-driven and does not commit credentials, private endpoints, or generated validation state.

Required environment variables:

```bash
MEMTLY_SMOKE_BASE_URL=http://127.0.0.1:8080 \
MEMTLY_SMOKE_USERNAME=admin \
MEMTLY_SMOKE_PASSWORD=<redacted> \
python3 scripts/smoke-lifecycle.py
```

Optional:

```bash
MEMTLY_SMOKE_MEDIA_FIXTURE_DIR=/path/to/generated-fixtures
MEMTLY_SMOKE_STRESS_IMAGES=150
MEMTLY_SMOKE_KEEP_GALLERY=true
MEMTLY_SMOKE_STATE_FILE=/tmp/memtly-lifecycle-state.json
MEMTLY_SMOKE_NEW_GALLERY_SECRET_KEY=<caller-generated temporary value>
```

When `MEMTLY_SMOKE_MEDIA_FIXTURE_DIR` is omitted, the script generates ordinary JPEG/PNG/MP4/MOV fixtures locally. If the target host lacks a video encoder, generate the fixtures on a build host and pass the directory through `MEMTLY_SMOKE_MEDIA_FIXTURE_DIR`.

The keep/state-file mode is for validation jobs that intentionally keep a temporary gallery across a container recreation and then validate and remove the same gallery in a second script invocation. The owner-only runtime state contains only the temporary gallery ID and identifier; the gallery access secret is not persisted. For a protected gallery, the orchestrator must hold a generated value outside the state file: pass it as `MEMTLY_SMOKE_NEW_GALLERY_SECRET_KEY` to the first invocation and `MEMTLY_SMOKE_EXISTING_GALLERY_SECRET_KEY` to the resumed invocation. The state file must not be committed.

## What this validates

- The overlay still relies on Memtly's existing upload endpoints, checksum behavior, duplicate detection, gallery listing, thumbnail/media processing, download ZIP path, and gallery deletion cleanup.
- The server keeps rejecting raw HEIC/HEIF input even when browser conversion is enabled.
- Ordinary media formats continue through the expected Memtly lifecycle without being converted by the HEIC overlay.
- The candidate can run with HEIC conversion disabled, at which point the rendered gallery input omits explicit `.heic`/`.heif` support.
- Rollback to the conversion-free foundation image succeeds against the same candidate runtime data shape and can be restored back to the candidate image afterward.
- A temporary gallery with ordinary media remains renderable and downloadable after recreating the application container without deleting persistent volumes.

## What this does not claim

- This is not a production-ready release claim.
- The test uses generated ordinary media fixtures and public HEIC fixtures, not personal event photos.
- Automated browser checks do not replace real iPhone/iPad Safari validation.
- The container-recreation persistence check is not a substitute for a full operator disaster-recovery exercise with private backups.
