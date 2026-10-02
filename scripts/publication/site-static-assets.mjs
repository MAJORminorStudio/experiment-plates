// Restore byte-identical Plate 001 exports from compact, hash-pinned build inputs.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
const site = fileURLToPath(new URL("../", import.meta.url));
const source = join(site, "plate-001-source-assets");
const manifest = JSON.parse(readFileSync(join(source, "manifest.json"), "utf8"));
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
for (const [name, expected] of Object.entries(manifest.assets)) {
  if (name.startsWith("/") || name.split("/").includes("..")) throw Error("Invalid Plate 001 asset path");
  const bytes = gunzipSync(readFileSync(join(source, name + ".gz")));
  if (hash(bytes) !== expected) throw Error("Plate 001 source hash mismatch: " + name);
  const output = join(site, "public/research/plate-001", name);
  mkdirSync(dirname(output), { recursive: true });
  if (!existsSync(output) || hash(readFileSync(output)) !== expected) writeFileSync(output, bytes);
}
console.log(`Restored ${Object.keys(manifest.assets).length} original Plate 001 SVG/HTML assets; hashes verified.`);
