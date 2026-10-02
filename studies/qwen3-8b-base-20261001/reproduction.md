# Reproduction

## Verify existing data without inference

```sh
npm ci
npm run build
python3 studies/qwen3-8b-base-20261001/scripts/test_suite.py
node studies/qwen3-8b-base-20261001/scripts/export.mjs --verify
python3 scripts/publication/validate.py
```

For the publication page builder: `npm ci --prefix scripts/publication`, then `python3 scripts/publication/build.py`. To preview, run `python3 -m http.server 4173 --bind 127.0.0.1` from the repository root and open `/studies/qwen3-8b-base-20261001/publication/`.

## Independent inference replication

The following commands run models. They were not run during release preparation. Back up the completed study and use a fresh ledger/workspace for an independent replication. The scripts preserve the historical paths; the original model and runtime files are excluded from the public archive.

## Reproduce on the same Mac

From the repository root (requires the installed llama.cpp 0.4.1 binaries and ggml 0.24.0 recorded in `environment.json`):

```sh
npm ci
npm run build
python3 -m venv studies/qwen3-8b-base-20261001/.venv
studies/qwen3-8b-base-20261001/.venv/bin/pip install -r studies/qwen3-8b-base-20261001/python-requirements.lock.txt
git init studies/qwen3-8b-base-20261001/runtime/llama.cpp
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp remote add origin https://github.com/ggml-org/llama.cpp.git
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp fetch --depth 1 origin b29c606e28a01b1bc8c1351026a0fa6e616bf6c4
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp checkout --detach FETCH_HEAD
studies/qwen3-8b-base-20261001/.venv/bin/hf download Qwen/Qwen3-8B-Base --revision 49e3418fbbbca6ecbdf9608b4d22e5a407081db4 --local-dir studies/qwen3-8b-base-20261001/weights
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/prepare.py
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/run.py --calibrate
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/run.py
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/analyze.py
node studies/qwen3-8b-base-20261001/scripts/export.mjs
node studies/qwen3-8b-base-20261001/scripts/export.mjs --verify
```

Preparation and inference must run serially. The preflight log records one aborted overlapping F16 startup before any scored trials; this was not counted as a model failure. A reference startup can take minutes when loading from external storage. The runner resumes an existing ledger only if the suite and scorer hashes match; for an independent replication, use a fresh study directory/ledger rather than mixing observations. Reproduction commands and server/benchmark arguments are also stored verbatim in the manifests.

