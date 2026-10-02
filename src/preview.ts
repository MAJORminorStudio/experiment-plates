import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, sep, extname } from 'node:path';
const root = resolve('outputs'); const port = Number(process.argv[2] ?? 4173);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid port');
createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? '/', 'http://127.0.0.1'); const path = resolve(root, '.' + decodeURIComponent(url.pathname === '/' ? '/inspector.html' : url.pathname));
    if (!path.startsWith(root + sep)) { response.writeHead(403).end(); return; }
    const content = await readFile(path); response.setHeader('Content-Type', ({ '.html': 'text/html; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.json': 'application/json' } as Record<string, string>)[extname(path)] ?? 'application/octet-stream'); response.end(content);
  } catch { response.writeHead(404).end('Artifact not found'); }
}).listen(port, '127.0.0.1', () => console.log(`Inspector: http://127.0.0.1:${port}`));
