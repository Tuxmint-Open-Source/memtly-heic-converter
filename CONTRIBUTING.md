# Contributing

Please open an issue before substantial implementation work. Keep pull requests focused on one reviewable outcome and include:

- the Memtly tag and exact commit tested;
- converter/dependency refs changed;
- tests added and actual results;
- browser/device distinction (real hardware vs emulation);
- metadata, quality, memory, or compatibility implications;
- confirmation that no private environment data or personal photos are included.

This project is independent from Memtly. Reproduce suspected upstream bugs with an unmodified official image before reporting them upstream.

AI-assisted contributions are accepted when disclosed and human-reviewed. Contributors remain responsible for correctness, licensing, security, and test evidence.

Before opening a pull request, run the commands documented under [Quality gates](README.md#quality-gates). The GitHub Actions quality gate uses read-only repository permissions and does not require private deployment access. Use the structured issue forms and pull-request template; do not replace their public-safety confirmations with raw logs or private deployment evidence.

Dependabot updates are grouped by ecosystem and remain normal reviewable pull requests. GitHub Actions references must stay pinned to immutable full commit SHAs, and coupled Action updates should remain together rather than being merged independently.

CodeQL analyzes repository-owned JavaScript/TypeScript, Python, and GitHub Actions. Treat it as one security signal: it does not scan JavaScript embedded as patch text and does not replace the project quality gate or runtime validation.

ShellCheck analyzes every tracked `.sh` and `.bash` program at style severity through a pinned, checksum-verified release. Keep inline suppressions narrow and include a comment explaining why the literal or construct is intentional.

Follow [SECURITY.md](SECURITY.md) for suspected vulnerabilities. Do not disclose exploit details, sensitive evidence, personal media, or private infrastructure in public issues or pull requests.
