#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$repo_root/config/versions.env"

workdir="$(mktemp -d "${TMPDIR:-/tmp}/memtly-patch-check.XXXXXX")"
cleanup() {
  rm -rf "$workdir"
}
trap cleanup EXIT

community="$workdir/community"
mkdir -p "$community"
git -C "$community" init --quiet
git -C "$community" remote add origin https://github.com/Memtly/Memtly.Community.git
git -C "$community" fetch --quiet --depth 1 origin \
  "refs/tags/${MEMTLY_COMMUNITY_TAG}:refs/tags/${MEMTLY_COMMUNITY_TAG}"

actual_tag_type="$(git -C "$community" cat-file -t "refs/tags/${MEMTLY_COMMUNITY_TAG}")"
actual_community="$(git -C "$community" rev-parse "refs/tags/${MEMTLY_COMMUNITY_TAG}^{commit}")"
test "$actual_tag_type" = tag
test "$actual_community" = "$MEMTLY_COMMUNITY_COMMIT"
git -C "$community" -c advice.detachedHead=false checkout --quiet --detach "$actual_community"

actual_core_pointer="$(git -C "$community" ls-tree HEAD Memtly.Core | awk '{print $3}')"
test "$actual_core_pointer" = "$MEMTLY_CORE_COMMIT"

git -C "$community" submodule update --init --depth 1 Memtly.Core >/dev/null
actual_core_checkout="$(git -C "$community/Memtly.Core" rev-parse HEAD)"
test "$actual_core_checkout" = "$MEMTLY_CORE_COMMIT"

while IFS= read -r patch; do
  case "$patch" in ''|'#'*) continue ;; esac
  patch_path="$repo_root/patches/$patch"
  test -f "$patch_path"
  git -C "$community" apply --check "$patch_path"
  git -C "$community" apply "$patch_path"
done < "$repo_root/patches/series"

git -C "$community" diff --check
printf 'patch_apply=passed community=%s core=%s\n' \
  "$actual_community" "$actual_core_checkout"
