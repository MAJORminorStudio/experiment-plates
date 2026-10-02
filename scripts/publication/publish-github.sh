#!/usr/bin/env bash
# Run only when publication to the selected empty GitHub repository is authorized.
set -euo pipefail
if [[ $# -ne 1 || ! "$1" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo 'Usage: bash scripts/publication/publish-github.sh OWNER/REPO' >&2
  exit 2
fi
plate_repo="$1"
plate_root="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
plate_snapshot="$plate_root/releases/github-ready"
[[ -f "$plate_snapshot/SHA256SUMS" ]] || { echo 'Build the finalized release snapshot first.' >&2; exit 1; }
gh repo view "$plate_repo" --json name >/dev/null
plate_remote="https://github.com/$plate_repo.git"
[[ -z "$(git ls-remote --heads --tags "$plate_remote")" ]] || { echo 'Select an empty repository; the destination already has branches or tags.' >&2; exit 1; }
# This snapshot contains only the allowlisted public release; it is separate from both working checkouts.
if [[ ! -d "$plate_snapshot/.git" ]]; then
  git -C "$plate_snapshot" init --initial-branch=main
  git -C "$plate_snapshot" add .
  git -C "$plate_snapshot" commit -m 'Release PLATE visual 0.1 and Plate 001'
fi
if git -C "$plate_snapshot" remote get-url origin >/dev/null 2>&1; then
  [[ "$(git -C "$plate_snapshot" remote get-url origin)" == "$plate_remote" ]] || { echo 'Snapshot origin does not match the requested repository.' >&2; exit 1; }
else
  git -C "$plate_snapshot" remote add origin "$plate_remote"
fi
git -C "$plate_snapshot" tag -a plate-v0.1.0 -m 'PLATE / Experiment Plates visual 0.1'
git -C "$plate_snapshot" tag -a plate-001-v1.0.0 -m 'Plate 001 / Qwen3-8B Base / 1,680 real trials'
git -C "$plate_snapshot" push origin main refs/tags/plate-v0.1.0 refs/tags/plate-001-v1.0.0
gh release create plate-v0.1.0 "$plate_root/releases/plate-v0.1.0.tar.gz" "$plate_root/releases/plate-v0.1.0.tar.gz.sha256" \
  --repo "$plate_repo" --verify-tag --title 'PLATE / Experiment Plates — visual 0.1' --notes-file "$plate_root/releases/PLATE-v0.1.0.md"
gh release create plate-001-v1.0.0 "$plate_root/releases/plate-001-v1.0.0.tar.gz" "$plate_root/releases/plate-001-v1.0.0.tar.gz.sha256" \
  "$plate_root/releases/plate-001-site-integration.tar.gz" \
  "$plate_root/studies/qwen3-8b-base-20261001/publication/social/plate-001-launch-1600.png" \
  "$plate_root/studies/qwen3-8b-base-20261001/publication/social/plate-001-launch-1600.svg" \
  "$plate_root/studies/qwen3-8b-base-20261001/publication/demo/plate-001-demo.mp4" \
  --repo "$plate_repo" --verify-tag --title 'Plate 001 — Qwen3-8B Base quantization study' --notes-file "$plate_root/releases/Plate-001-v1.0.0.md"
