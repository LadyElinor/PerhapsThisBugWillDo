import fs from 'node:fs';
import path from 'node:path';

function resolveFromCwd(p) {
  if (!p) return p;
  if (path.isAbsolute(p)) return p;
  return path.resolve(process.cwd(), p);
}

export function writeReceipt({ runId, receiptDir, receiptObj }) {
  const dir = resolveFromCwd(receiptDir ?? './outputs/receipts');
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `${runId}.json`);
  fs.writeFileSync(p, JSON.stringify(receiptObj, null, 2), 'utf8');
  return p;
}
