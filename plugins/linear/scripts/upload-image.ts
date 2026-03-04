#!/usr/bin/env npx tsx
/**
 * Upload image to Linear and optionally attach to an issue
 *
 * Usage:
 *   npx tsx scripts/upload-image.ts <image-path> [issue-id] [comment-text]
 *
 * Examples:
 *   npx tsx scripts/upload-image.ts ~/Desktop/screenshot.png
 *   npx tsx scripts/upload-image.ts /tmp/diagram.jpg TRE-123
 *   npx tsx scripts/upload-image.ts /tmp/mockup.png TRE-123 "Here's the mockup"
 *
 * Output:
 *   - Prints the asset URL (for embedding in descriptions/comments)
 *   - If issue-id provided, adds the image as a comment on that issue
 */

import { readFileSync, statSync } from 'fs';
import { basename, extname } from 'path';
import { EXIT_CODES } from './lib/exit-codes.js';
import { getLinearClient } from './lib/linear-utils.js';

// Detect content type
const contentTypeMap: Record<string, string> = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf',
};

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: npx tsx scripts/upload-image.ts <image-path> [issue-id] [comment-text]');
    console.error('Example: npx tsx scripts/upload-image.ts ~/Desktop/screenshot.png TRE-123');
    process.exit(EXIT_CODES.INVALID_ARGUMENTS);
  }

  const imagePath = args[0].replace(/^~/, process.env.HOME || '');
  const issueIdentifier = args[1];
  const commentText = args[2] || '';

  const ext = extname(imagePath).toLowerCase();
  const contentType = contentTypeMap[ext] || 'application/octet-stream';

  // Read file
  let fileData: Buffer;
  let fileSize: number;
  try {
    fileData = readFileSync(imagePath);
    fileSize = statSync(imagePath).size;
  } catch (err) {
    console.error(`[ERROR] Cannot read file: ${imagePath}`);
    console.error(err instanceof Error ? err.message : String(err));
    process.exit(EXIT_CODES.INVALID_ARGUMENTS);
  }

  const filename = basename(imagePath);
  console.log(`Uploading: ${filename} (${(fileSize / 1024).toFixed(1)} KB, ${contentType})`);

  let client;
  try {
    client = getLinearClient();
  } catch (err) {
    console.error(err instanceof Error ? err.message : String(err));
    process.exit(EXIT_CODES.MISSING_API_KEY);
  }

  // Step 1: Request upload URL from Linear
  const uploadResult = await client.fileUpload(contentType, filename, fileSize);
  const uploadFile = uploadResult.uploadFile;

  if (!uploadFile) {
    console.error('[ERROR] Failed to get upload URL from Linear');
    process.exit(EXIT_CODES.API_ERROR);
  }

  const { uploadUrl, assetUrl, headers } = uploadFile;

  // Step 2: Upload file to the signed URL
  const uploadHeaders: Record<string, string> = {
    'Content-Type': contentType,
    'Cache-Control': 'public, max-age=31536000',
  };
  for (const h of headers) {
    uploadHeaders[h.key] = h.value;
  }

  const uploadResponse = await fetch(uploadUrl, {
    method: 'PUT',
    headers: uploadHeaders,
    body: new Uint8Array(fileData),
  });

  if (!uploadResponse.ok) {
    console.error(`[ERROR] Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`);
    process.exit(EXIT_CODES.API_ERROR);
  }

  console.log('\n[SUCCESS] Image uploaded!');
  console.log(`  Asset URL: ${assetUrl}`);
  console.log(`  Markdown:  ![${filename}](${assetUrl})`);

  // Step 3: Optionally attach to an issue as a comment
  if (issueIdentifier) {
    console.log(`\nAttaching to issue ${issueIdentifier}...`);

    // Find issue by identifier
    const issueNumber = parseInt(issueIdentifier.replace(/^[A-Z]+-/, ''), 10);
    const teamKey = issueIdentifier.replace(/-\d+$/, '');

    const issues = await client.issues({
      filter: {
        number: { eq: issueNumber },
        team: { key: { eq: teamKey } },
      },
    });

    if (issues.nodes.length === 0) {
      console.error(`[ERROR] Issue ${issueIdentifier} not found`);
      process.exit(EXIT_CODES.RESOURCE_NOT_FOUND);
    }

    const issue = issues.nodes[0];
    const body = commentText
      ? `${commentText}\n\n![${filename}](${assetUrl})`
      : `![${filename}](${assetUrl})`;

    await client.createComment({
      issueId: issue.id,
      body,
    });

    console.log(`[SUCCESS] Image attached to ${issueIdentifier} as a comment`);
    console.log(`  Issue URL: ${issue.url}`);
  }
}

main().catch((err) => {
  console.error('[ERROR]', err instanceof Error ? err.message : String(err));
  process.exit(EXIT_CODES.API_ERROR);
});
