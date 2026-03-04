#!/usr/bin/env npx tsx
/**
 * Extract inline images from a Claude Code session JSONL file
 *
 * Images shared inline in Claude Code are not saved to disk automatically —
 * they live as base64 in the session JSONL. This script extracts them.
 *
 * Usage:
 *   npx tsx scripts/extract-image.ts <path-to-session.jsonl> [output-dir]
 *
 * Examples:
 *   npx tsx scripts/extract-image.ts ~/.claude/projects/.../session.jsonl
 *   npx tsx scripts/extract-image.ts ~/.claude/projects/.../session.jsonl /tmp
 *
 * Find the current session JSONL path with:
 *   ls -t ~/.claude/projects/<project-path>/*.jsonl | head -1
 *
 * Output:
 *   Saves images to <output-dir>/shared-image-0.png, shared-image-1.png, etc.
 *   Defaults to /tmp if no output directory is specified.
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { EXIT_CODES } from './lib/exit-codes.js';

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: npx tsx scripts/extract-image.ts <path-to-session.jsonl> [output-dir]');
  console.error('');
  console.error('Find the current session JSONL:');
  console.error('  ls -t ~/.claude/projects/<project-path>/*.jsonl | head -1');
  process.exit(EXIT_CODES.INVALID_ARGUMENTS);
}

const sessionPath = args[0].replace(/^~/, process.env.HOME || '');
const outputDir = args[1] || '/tmp';

let lines: string[];
try {
  lines = readFileSync(sessionPath, 'utf8').trim().split('\n');
} catch (err) {
  console.error(`[ERROR] Cannot read file: ${sessionPath}`);
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(EXIT_CODES.INVALID_ARGUMENTS);
}

let count = 0;
for (const line of lines) {
  const obj = JSON.parse(line);
  const msg = obj.message;
  if (!msg) continue;
  for (const c of msg.content || []) {
    if (c.type === 'image' && c.source?.type === 'base64') {
      const ext = (c.source.media_type || 'image/png').split('/')[1];
      const outPath = join(outputDir, `shared-image-${count}.${ext}`);
      writeFileSync(outPath, Buffer.from(c.source.data, 'base64'));
      console.log(`Saved ${outPath}`);
      count++;
    }
  }
}

if (count === 0) {
  console.log('No inline images found in session.');
} else {
  console.log(`\nExtracted ${count} image(s).`);
}
