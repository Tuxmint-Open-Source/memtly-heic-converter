#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
# shellcheck disable=SC1091
source config/versions.env

test "$MEMTLY_VERSION" = "1.0.6"
test "$MEMTLY_COMMUNITY_TAG" = "$MEMTLY_VERSION"
test "$MEMTLY_COMMUNITY_COMMIT" = "d9b7298866c8cafbd515a6bf5e260e1d0423f262"
test "$MEMTLY_CORE_COMMIT" = "cc8c88d625136f04ae1f1063fc635f74e739bd72"
test "$NODE_VERSION" = "22.23.2"
test "$HEIC_CONVERTER" = "heic2any"
test "$HEIC_CONVERTER_VERSION" = "0.0.4"
test "$HEIC_CONVERTER_COMMIT" = "3428539e643e112323a5b8a2c77c6402cb1372f6"
test "$HEIC_CONVERTER_INTEGRITY" = "sha512-3lLnZiDELfabVH87htnRolZ2iehX9zwpRyGNz22GKXIu0fznlblf0/ftppXKNqS26dqFSeqfIBhAmAj/uSp0cA=="

for value in "$MEMTLY_COMMUNITY_TAG" "$MEMTLY_COMMUNITY_COMMIT" "$MEMTLY_CORE_COMMIT" "$NODE_VERSION"; do
  grep -Fq "$value" Dockerfile
  test "$(grep -Fo "$value" Dockerfile | wc -l)" -ge 1
done

grep -Fq 'git cat-file -t "refs/tags/${MEMTLY_COMMUNITY_TAG}"' Dockerfile
grep -Fq 'git ls-tree HEAD Memtly.Core' Dockerfile
grep -Fq 'git apply --check' Dockerfile
grep -Fq 'test -s /app/publish/wwwroot/_content/Memtly.Core/dist/manifest.json' Dockerfile
grep -Fq "Memtly.Core.wwwroot.dist.manifest.json" Dockerfile
grep -Fq 'io.tuxmint.memtly.heic.available="true"' Dockerfile
grep -Fq 'io.tuxmint.memtly.heic.enabled-by-default="false"' Dockerfile
grep -Fq 'node --test ./Memtly.Core/tests/heic-classifier.test.mjs' Dockerfile
grep -Fq 'heic2any-MIT.txt' Dockerfile

test -f patches/series
grep -Fq '"heic2any": "0.0.4"' patches/0001-client-heic-conversion.patch
grep -Fq "$HEIC_CONVERTER_INTEGRITY" patches/0001-client-heic-conversion.patch
node tests/scripts/verify-fixtures.mjs
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/memtly-heic-pycache" python3 -m py_compile scripts/smoke-foundation.py
while IFS= read -r patch; do
  case "$patch" in ''|'#'*) continue ;; esac
  test -f "patches/$patch"
done < patches/series

printf 'foundation checks passed
'
