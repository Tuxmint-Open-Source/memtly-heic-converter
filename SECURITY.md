# Security policy

## Supported versions

This project has no stable production release yet.

| Version or ref | Security support posture |
| --- | --- |
| `v0.1.0-rc.1` | Current validated pre-release; security reports are accepted, but it remains a controlled-testing artifact rather than a production-ready release. |
| `main` | Development source; reports are accepted when reproduced at an exact commit. Compatibility and validation claims may lag behind the branch. |
| Older commits, local rebuilds, modified images, and unpublished artifacts | Not supported as release artifacts. Reports may still be useful when they identify a vulnerability in current project code. |
| Unmodified upstream Memtly | Outside this project's ownership; reproduce against the official upstream project and follow its reporting policy. |

Security support does not expand the compatibility claim beyond the exact Memtly and converter refs documented in the repository's compatibility matrix.

## Report a vulnerability privately

Do not open a public issue, pull request, discussion, or comment for a suspected vulnerability.

Use [GitHub private vulnerability reporting](https://github.com/Tuxmint-Open-Source/memtly-heic-converter/security/advisories/new). If that route is unavailable, contact a repository maintainer privately through a contact method published on their GitHub profile. Send only the minimum evidence needed to reproduce and assess the issue.

A useful private report includes:

- the exact project release, image digest, or full commit tested;
- the exact Memtly Community/Core refs when relevant;
- the affected browser/device class, clearly distinguishing real hardware from emulation;
- a concise impact statement and sanitized reproduction steps;
- whether the behavior also reproduces with an unmodified official Memtly image;
- a minimal purpose-made fixture when one is necessary and safe to share;
- any known workaround or rollback that does not expose private operations.

Do not send credentials, tokens, cookies, private keys, private endpoint or topology details, database contents, backups, raw application/configuration archives, personal photos, guest-identifying data, or unnecessary EXIF/GPS metadata. Redact private evidence before sharing it, even through a private report.

## Vulnerabilities in scope

Examples include:

- malicious HEIC/HEIF input causing code execution, cross-site scripting, persistent script content, browser compromise, or an uncontrolled denial of service;
- bypass of fail-closed conversion that permits raw HEIC/HEIF or another disallowed type to reach Memtly's upload path;
- validation, filename, MIME, checksum, chunking, or metadata confusion that crosses the intended browser-to-server trust boundary;
- exposure of guest media, gallery data, credentials, sensitive metadata, or private configuration caused by this overlay;
- unsafe generated JPEG content or file handling that creates a downstream security impact;
- container, build, release, registry, provenance, attestation, or dependency-integrity weaknesses specific to this project;
- GitHub Actions or automation behavior that permits untrusted code to gain write credentials, publish artifacts, modify protected refs, or bypass immutable dependency pins;
- resource-bound bypasses that create a practical browser or service denial of service outside the documented limits.

## Not a private security report

Use the structured public issue forms for:

- ordinary conversion failures with public-safe fixtures;
- browser compatibility questions without a security impact;
- feature requests, metadata-preservation requests, or quality differences;
- documentation corrections;
- expected pre-release limitations;
- operational support where the report can be fully sanitized;
- upstream Memtly behavior reproduced independently of this overlay.

When uncertain, choose private reporting first. Maintainers can move a non-sensitive report to a public issue after reviewing it.

## Coordinated disclosure

Maintainers will acknowledge a private report when possible, assess whether the issue belongs to this project or upstream, and coordinate remediation and disclosure based on impact and available evidence. Please avoid public disclosure until maintainers have had a reasonable opportunity to investigate and publish a fix or mitigation.

A fix is not considered released merely because it exists on `main`. Release-specific claims require an immutable tag/artifact and the validation status documented for that exact artifact.

## Security controls and limitations

The repository uses private vulnerability reporting, dependency alerts/security updates, secret scanning with push protection, immutable GitHub Action pins, a required read-only quality gate, explicit CodeQL scanning for repository-owned JavaScript/TypeScript, Python, and GitHub Actions, checksum-verified ShellCheck scanning for tracked shell programs, public-safety checks, exact upstream source guards, and published image provenance/attestation.

These controls reduce risk but are not a guarantee. In particular:

- `v0.1.0-rc.1` is still not production-ready;
- real iPhone/iPad Safari validation remains outstanding;
- browser conversion processes untrusted media and can be resource-intensive;
- open-source licensing does not resolve every codec patent question;
- project security support does not imply support or affiliation from Memtly.
