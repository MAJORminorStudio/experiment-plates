import { createHash } from 'node:crypto';
export function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object') {
    return '{' + Object.entries(value).sort(([a], [b]) => a.localeCompare(b, 'en')).map(([k, v]) => JSON.stringify(k) + ':' + canonical(v)).join(',') + '}';
  }
  return JSON.stringify(value);
}
export const hash = (value: string | Buffer) => createHash('sha256').update(value).digest('hex');
export const xml = (value: unknown) => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]!));
export const unxml = (value: string) => value.replace(/&(amp|lt|gt|quot|apos);/g, (_, c: string) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" }[c]!));
export const round = (n: number) => Math.round(n * 1000) / 1000;
export const mean = (ns: (number | null)[]) => { const a = ns.filter((v): v is number => v !== null); return a.length ? a.reduce((s, v) => s + v, 0) / a.length : null; };
export const median = (ns: (number | null)[]) => {
  const a = ns.filter((v): v is number => v !== null).sort((a, b) => a - b);
  return a.length ? (a[Math.floor(a.length / 2)] + a[Math.floor((a.length - 1) / 2)]) / 2 : null;
};
