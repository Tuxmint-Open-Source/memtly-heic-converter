# Memtly HEIC Converter

[![Quality gate](https://github.com/Tuxmint-Open-Source/memtly-heic-converter/actions/workflows/quality-gate.yml/badge.svg?branch=main)](https://github.com/Tuxmint-Open-Source/memtly-heic-converter/actions/workflows/quality-gate.yml)

A feature-flagged build overlay for converting HEIC/HEIF still images to JPEG **in the guest's browser before upload** to [Memtly Community](https://github.com/Memtly/Memtly.Community).

> [!IMPORTANT]
> This independent community project is not affiliated with, endorsed by, or supported by Memtly or its maintainers. Do not report extension-specific problems to the Memtly project unless they are reproduced with an unmodified upstream image.

## Status

**Feature-flagged browser conversion pre-release. Not ready for production.**

The first compatibility target is:

| Extension line | Memtly Community | Upstream commit | Status |
| --- | --- | --- | --- |
| `v0.1.0-rc.1` | `1.0.6` | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` | validated compatible pre-release |
| `main` | `1.0.6` | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` | validated candidate source line |

Follow the [public roadmap](ROADMAP.md), [compatibility matrix](docs/compatibility.md), and pinned roadmap issue for current work.

## Quality gates

Pull requests and `main` pushes run the read-only [quality gate](.github/workflows/quality-gate.yml). The App-bound `Project quality gate` check is required for `main`, and pull-request branches must be current with `main`. Run the same core checks locally with:

```bash
npm ci
./scripts/test-foundation.sh
npm run test:browser
npm audit
./scripts/check-public-safety.py
./scripts/check-community-files.py
./scripts/check-security-policy.py
./scripts/check-codeql-workflow.py
python3 tests/scripts/test-run-shellcheck.py
./scripts/check-shellcheck-workflow.py
python3 scripts/run-shellcheck.py
python3 tests/scripts/test-run-actionlint.py
./scripts/check-actionlint-workflow.py
python3 scripts/run-actionlint.py
python3 tests/scripts/test-run-hadolint.py
./scripts/check-hadolint-workflow.py
python3 scripts/run-hadolint.py
python3 tests/scripts/test-run-ruff.py
./scripts/check-ruff-workflow.py
python3 scripts/run-ruff.py
./scripts/check-dependabot-config.py
./scripts/check-workflow-actions.py
python3 scripts/check-upstream-drift.py --check
./scripts/check-patch-apply.sh
```

Without runtime variables, the browser suite enumerates all configured projects and skips the live upload case. Exact-image browser evidence is recorded separately in the validation reports.

The separate [Code scanning workflow](.github/workflows/codeql.yml) analyzes repository-owned JavaScript/TypeScript, Python, and GitHub Actions with CodeQL on pull requests, `main`, manual dispatches, and a weekly schedule. It does not parse JavaScript embedded inside the upstream overlay patch as JavaScript source, so CodeQL complements rather than replaces fixture, browser, patch-apply, and exact-artifact validation.

The [ShellCheck workflow](.github/workflows/shellcheck.yml) scans every tracked `.sh` and `.bash` program at style severity. Its runner pins ShellCheck `0.11.0`, verifies the official Linux x86_64 release artifact before extraction, and derives the scan inventory from Git. It does not treat shell snippets embedded in documentation, Dockerfiles, patch text, or private deployment helpers as repository-owned shell programs.

The [actionlint workflow](.github/workflows/actionlint.yml) validates the semantic structure, expressions, contexts, matrices, events, and permissions of every tracked GitHub Actions workflow. Its runner pins actionlint `1.7.12`, verifies the official Linux x86_64 release artifact before extraction, and derives the workflow inventory from Git.

The [hadolint workflow](.github/workflows/hadolint.yml) scans every tracked Dockerfile with hadolint `2.15.1` after verifying the official Linux x86_64 binary. The sole configured exception is informational rule `DL3059`: separate test, restore, build, publish, and artifact-verification layers are intentional cache and review boundaries.

The [Ruff workflow](.github/workflows/ruff.yml) scans every tracked Python program with Ruff `0.16.4` after checksum-verifying the official Linux x86_64 archive. Its explicit `E4,E7,E9,F,I,EXE,B,UP` rule set covers core syntax/correctness, imports, executable contracts, Bugbear checks, and Python upgrades without imposing repository-wide formatting or broad subprocess-policy suppressions.

## Foundation image

Issue #1 established the merged Memtly `1.0.6` control image. The build verifies the annotated Community tag, Community commit, Core gitlink, and checked-out Core commit, then applies the committed patch series with drift checks.

```bash
./scripts/test-foundation.sh
docker build --pull=false -t memtly-heic-converter:1.0.6-heic-candidate .
```

See [build provenance](docs/build-provenance.md), [browser conversion](docs/browser-conversion.md), [fixture provenance](docs/fixture-provenance.md), [compatibility](docs/compatibility.md), [metadata decision](docs/metadata-decision.md), [desktop cross-browser validation](docs/validation-desktop-browsers.md), [real-device Safari validation](docs/real-device-safari-validation.md), [upstream drift monitoring](docs/upstream-drift.md), the public-safe [candidate validation report](docs/validation-heic-candidate.md), and the [unchanged lifecycle validation report](docs/validation-lifecycle.md). Conversion remains disabled at runtime unless explicitly enabled.

## Intended behavior

```text
HEIC/HEIF selected
  → detect from a bounded ISO-BMFF content scan
  → convert sequentially to JPEG in-browser
  → hand the new .jpg File to Memtly's existing upload path
  → Memtly retains its checksum, chunking, validation, review,
    thumbnail, gallery, download, deletion, and backup behavior
```

Non-HEIC files must pass through unchanged. Raw `.heic` and `.heif` remain excluded from the server allow-list. If conversion fails, the file must not upload.

## Why an overlay instead of a fork?

The project aims to build from an exact upstream Memtly ref and apply a small, reviewable patch. This keeps upstream provenance visible, makes drift detectable, and avoids maintaining an unrelated copy of the full application history.

## Safety and limitations

- The JPEG is a derivative, not an archival HEIC original.
- HEIF sequences, Live Photo auxiliaries, depth maps, and other auxiliary images may not be retained.
- EXIF/XMP/GPS metadata and original capture time are not preserved by the `v0.1.0-rc.1` browser-conversion path.
- Browser conversion can be memory-intensive on mobile devices, so conversion will be sequential and bounded.
- HEVC/HEIC codec patents may matter in some jurisdictions. Open-source licensing is not a patent opinion.

See [docs/architecture.md](docs/architecture.md), [QA.md](QA.md), and the clone-visible [security policy](SECURITY.md). Suspected vulnerabilities must use GitHub private vulnerability reporting rather than public issues or pull requests.

## Licensing and transparency

Project code and patches are licensed under GPL-3.0. Bundled dependencies and test fixtures retain their own licenses and notices.

Development is AI-assisted by [`hermes-archham`](https://github.com/hermes-archham) under human maintainer review. Trust should come from reviewable source, pinned provenance, tests, and published validation—not from authorship claims.
