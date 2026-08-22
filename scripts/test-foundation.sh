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

for value in "$MEMTLY_COMMUNITY_TAG" "$MEMTLY_COMMUNITY_COMMIT" "$MEMTLY_CORE_COMMIT" "$NODE_VERSION"; do
  grep -Fq "$value" Dockerfile
  test "$(grep -Fo "$value" Dockerfile | wc -l)" -ge 1
done

grep -Fq 'git cat-file -t "refs/tags/${MEMTLY_COMMUNITY_TAG}"' Dockerfile
grep -Fq 'git ls-tree HEAD Memtly.Core' Dockerfile
grep -Fq 'git apply --check' Dockerfile
grep -Fq 'io.tuxmint.memtly.heic.enabled="false"' Dockerfile

test -f patches/series
while IFS= read -r patch; do
  case "$patch" in ''|'#'*) continue ;; esac
  test -f "patches/$patch"
done < patches/series

printf 'foundation checks passed
'
