#!/usr/bin/env bash
# Publish missing releases from the existing canonical checkout and published tags.
set -euo pipefail
if [[ $# -ne 1 || ! "$1" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo 'Usage: bash scripts/publication/publish-github.sh OWNER/REPO' >&2
  exit 2
fi
plate_repo="$1"
plate_root="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
plate_remote="https://github.com/$plate_repo.git"
[[ "$(git -C "$plate_root" rev-parse --show-toplevel)" == "$plate_root" ]] || { echo 'Run from the canonical Git checkout.' >&2; exit 1; }
[[ "$(git -C "$plate_root" remote get-url origin)" == "$plate_remote" ]] || { echo 'Origin does not match the requested repository.' >&2; exit 1; }
gh repo view "$plate_repo" --json name >/dev/null
# Preserve the existing annotated tags and uploaded release assets.
for plate_tag in plate-v0.1.0 plate-001-v1.0.0; do
  plate_local_commit="$(git -C "$plate_root" rev-parse "$plate_tag^{commit}")"
  plate_remote_commit="$(git ls-remote "$plate_remote" "refs/tags/$plate_tag^{}" | cut -f1)"
  [[ "$plate_local_commit" == "$plate_remote_commit" ]] || { echo "Published tag differs or is missing: $plate_tag" >&2; exit 1; }
done
if gh release view plate-v0.1.0 --repo "$plate_repo" >/dev/null 2>&1; then
  echo 'plate-v0.1.0 is already published; preserved.'
else
  gh release create plate-v0.1.0 "$plate_root/releases/plate-v0.1.0.tar.gz" "$plate_root/releases/plate-v0.1.0.tar.gz.sha256" \
    --repo "$plate_repo" --verify-tag --title 'PLATE / Experiment Plates — visual 0.1' --notes-file "$plate_root/releases/PLATE-v0.1.0.md"
fi
if gh release view plate-001-v1.0.0 --repo "$plate_repo" >/dev/null 2>&1; then
  echo 'plate-001-v1.0.0 is already published; preserved.'
else
  gh release create plate-001-v1.0.0 "$plate_root/releases/plate-001-v1.0.0.tar.gz" "$plate_root/releases/plate-001-v1.0.0.tar.gz.sha256" \
    "$plate_root/releases/plate-001-site-integration.tar.gz" \
    "$plate_root/studies/qwen3-8b-base-20261001/publication/social/plate-001-launch-1600.png" \
    "$plate_root/studies/qwen3-8b-base-20261001/publication/social/plate-001-launch-1600.svg" \
    "$plate_root/studies/qwen3-8b-base-20261001/publication/demo/plate-001-demo.mp4" \
    --repo "$plate_repo" --verify-tag --title 'Plate 001 — Qwen3-8B Base quantization study' --notes-file "$plate_root/releases/Plate-001-v1.0.0.md"
fi
