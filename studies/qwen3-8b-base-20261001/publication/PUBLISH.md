# Plate 001 — final publication commands

Publication authorized for `MAJORminorStudio/experiment-plates` and the existing MAJOR//MINOR site. The existing website repository is `MAJORminorStudio/major-minor-sites`, site `mm-labs`, canonical origin `https://majorminor.xyz`, Cloudflare Worker `major-minor-mm-labs`.

The article is integrated at `/research/plate-001`, with a research-index entry and sitemap entry. The new 1600×1600 social graphic is the X launch attachment and the article’s Open Graph/Twitter image. The completed hero, contact sheet, tables, inspector and article interactions are retained.

## Deploy the integrated site

From the clean Plate 001 checkout based on origin/main:

```sh
cd /Volumes/Research/major-minor-sites-plate-001-publish
npm run typecheck
npm run site:build -- --site mm-labs
npm run site:deploy -- --site mm-labs
```

The deploy command builds the site and invokes Wrangler using the existing generated manifest. Authentication must be configured for the existing Cloudflare account. The original `/Volumes/Research/major-minor-sites` checkout contains unrelated pending work and is not the deployment source. The isolated checkout includes only Plate 001 additions over the published main branch.

Expected production URL after deployment: `https://majorminor.xyz/research/plate-001`. Root-relative assets live under `/research/plate-001/`. Each public asset is below Cloudflare’s 25 MiB per-file ceiling. The original JSONL ledger and metadata containing machine-local command paths are gzip downloads; decompressed bytes retain the original hashes. The study evidence tarball contains the complete original data and individual plate exports. The site prebuild restores and hash-checks original SVG/inspector assets from compressed build inputs. Served bytes and provenance remain unchanged; no global source-scan rule is altered.

## Apply the site-only bundle to another reviewed checkout

The site integration bundle contains only new route/assets files, a three-file patch for the research index, sitemap and Plate 001 asset prebuild hook, and a source manifest. It omits unrelated pending site work. From a checkout of `major-minor-sites`:

```sh
tar -xzf /Volumes/Research/tools/data-art/releases/plate-001-site-integration.tar.gz
git apply --check plate-001-existing-files.patch
git apply plate-001-existing-files.patch
npm run typecheck
npm run site:build -- --site mm-labs
```

Do not reapply the patch to the isolated checkout, where those additions are already installed. The patch is based on main commit `12569c8`.

## Publish the public study repository and two GitHub releases

The selected public repository is `MAJORminorStudio/experiment-plates`. The initial publication script requires an empty destination so it cannot overwrite another project’s history. It is a one-time initial publishing command.

Initial repository creation (skip if already created):

```sh
export PLATE_REPO='MAJORminorStudio/experiment-plates'
gh repo create "$PLATE_REPO" --public --description 'Experiment Plates visual 0.1 and Plate 001: 1,680 real Qwen3-8B Base trials'
```

Then, from data-art, publish the prepared snapshot and both releases:

```sh
cd /Volumes/Research/tools/data-art
bash scripts/publication/publish-github.sh "$PLATE_REPO"
```

That command initializes only `releases/github-ready`, commits the allowlisted snapshot, pushes `main` and the tags `plate-v0.1.0` and `plate-001-v1.0.0`, and creates public GitHub releases with these exact notes/assets:

- `releases/PLATE-v0.1.0.md`, `releases/plate-v0.1.0.tar.gz` and its SHA256 file.
- `releases/Plate-001-v1.0.0.md`, `releases/plate-001-v1.0.0.tar.gz` and its SHA256 file; the site-only bundle; final social PNG/SVG; completed MP4.

No benchmark, Plate 002, site deployment or social posting occurs in the GitHub publishing script. Live verification and deployment records are retained separately from the pre-publication evidence audit.

## Local revalidation

```sh
cd /Volumes/Research/tools/data-art
node studies/qwen3-8b-base-20261001/scripts/export.mjs --verify
python3 scripts/publication/validate.py
```

For production-build browser checks, serve mm-labs locally on port 4180 with `npm run start --workspace @major-minor/mm-labs -- --hostname 127.0.0.1 --port 4180`, then run `node scripts/publication/production-qa.mjs` from data-art. This checks production-relative article/images, launch metadata, all seven plate selections, inspector compare/download, gzip evidence hashes, 360/390/768 layouts, research-index and sitemap entries.
