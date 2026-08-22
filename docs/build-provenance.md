# Build provenance

The foundation image is built directly from public upstream source and does not vendor Memtly history.

## Exact compatibility input

| Input | Exact value |
| --- | --- |
| Memtly Community tag | `1.0.6` |
| Memtly Community commit | `d9b7298866c8cafbd515a6bf5e260e1d0423f262` |
| Memtly Core commit | `cc8c88d625136f04ae1f1063fc635f74e739bd72` |
| Node.js | `22.23.2` |

Container base images are pinned by multi-platform manifest digest in `Dockerfile`. The source stage verifies that:

1. `1.0.6` is an annotated tag;
2. the tag peels to the recorded Community commit;
3. that commit's `Memtly.Core` gitlink equals the recorded Core commit; and
4. the initialized Core checkout equals the same commit.

The build then applies every path in `patches/series` using `git apply --check` before applying it. A changed upstream context therefore fails instead of silently producing a partly patched image. Issue #1 intentionally has an empty patch series and establishes an unmodified control image.

## Build

```bash
./scripts/test-foundation.sh
docker build --pull=false -t memtly-heic-converter:1.0.6-foundation .
```

The source repositories and package feeds are fetched during the build. Exact source commits, lockfiles from upstream, base-image digests, and the emitted OCI labels make inputs reviewable; byte-for-byte image identity across dates is not claimed because external package feeds may change availability and build timestamps may differ.

## Inspect

```bash
docker image inspect memtly-heic-converter:1.0.6-foundation   --format '{{json .Config.Labels}}'
docker run --rm --entrypoint dotnet memtly-heic-converter:1.0.6-foundation   Memtly.Community.dll --version
```

A compatibility claim additionally requires runtime smoke tests. A successful build alone does not establish HEIC support.

## Runtime smoke test

The self-cleaning smoke test logs in through Memtly's CSRF-protected AJAX flow, creates a temporary gallery, uploads a generated ordinary PNG through `UploadFileChunk`, completes the batch, and deletes the gallery. It never prints credentials.

```bash
MEMTLY_SMOKE_BASE_URL=https://memtly.example.com \
MEMTLY_SMOKE_USERNAME=admin \
MEMTLY_SMOKE_PASSWORD='use-a-secret-source' \
  ./scripts/smoke-foundation.py
```

Use only against an isolated validation deployment: the script deliberately exercises create, upload, and delete lifecycle operations.
