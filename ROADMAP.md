# Public development roadmap

This roadmap is directional and best-effort. It is not a delivery-date commitment. Status claims distinguish planned, implemented, tested, released, and validated work.

## Now

1. Use `v0.1.0-rc.1` as the first validated pre-release for controlled testing.
2. Collect real-device Safari/iPhone/iPad validation using the documented checklist before any production-ready claim.
3. Keep the scheduled upstream drift monitor healthy and review any generated drift PRs before changing compatibility claims.

## Completed candidate gates

- Reproducible custom-image overlay against exact Memtly `1.0.6`.
- Feature-flagged HEIC/HEIF detection and sequential browser conversion.
- Licensed fixture-driven unit and browser tests.
- Unchanged JPEG, PNG, MP4, and MOV behavior through the existing upload path.
- Review-relevant lifecycle behavior: chunking, duplicates, raw HEIC rejection, download, deletion, feature-disabled behavior, rollback/restore, and container recreation without volume deletion.
- First validated pre-release image published to GHCR and validated by immutable digest.
- Capture-date/EXIF preservation decision recorded: metadata copying and original HEIC archival storage are deferred for the browser-conversion release candidate.
- Scheduled upstream drift detection added for pinned Memtly refs and watched patch-surface files.
- Automated conversion regression passes in Chromium, Firefox, and desktop WebKit against the exact published image digest.
- Read-only pull-request CI enforces foundation, fixture, browser-contract, dependency-audit, upstream-baseline, patch-apply, whitespace, and public-safety checks.
- Structured issue/PR intake and a Contributor Covenant code of conduct provide public-safe community reporting paths.
- Weekly grouped Dependabot maintenance covers the repository's npm and GitHub Actions dependency surfaces.
- Clone-visible security policy defines pre-release support, private intake, vulnerability scope, safe evidence, and coordinated disclosure.
- CodeQL scans repository-owned JavaScript/TypeScript, Python, and GitHub Actions; patch-text and runtime media behavior remain covered by the dedicated project gates.
- Checksum-verified ShellCheck `0.11.0` scans the complete tracked shell-program inventory at style severity.
- Checksum-verified actionlint `1.7.12` semantically validates the complete tracked GitHub Actions workflow inventory.
- Checksum-verified hadolint `2.15.1` validates the complete tracked Dockerfile inventory; the measured directory-switch and pipefail findings are remediated.
- Checksum-verified Ruff `0.16.4` validates the complete tracked Python inventory with an explicit low-noise core rule set.
- Lockfile-verified ESLint `10.9.0` validates the complete tracked JavaScript module inventory with explicit Node/browser contexts.

## Later / decisions needed

- Revisit capture-date/EXIF preservation only if it becomes a product requirement with explicit privacy controls and licensed fixtures.
- Evaluate an integrated server-side conversion mode only if metadata preservation is a firm requirement.
- Decide whether preserving archival HEIC originals is worth a dual-asset lifecycle.

## Non-goals for the first release

- Uploading raw HEIC for browsers to display.
- Mutating Memtly's upload volume with a post-upload watcher.
- Preserving Live Photo video components or every HEIF auxiliary image.
- Automatic production deployment.
- Claiming support for unvalidated Memtly releases.

## Public/private boundary

Public issues contain reusable product outcomes and sanitized validation. Environment-specific deployment coordinates, raw logs, credentials, private topology, and operational evidence remain private. Security vulnerabilities should follow [SECURITY.md](SECURITY.md).
