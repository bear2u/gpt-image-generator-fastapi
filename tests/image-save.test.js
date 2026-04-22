import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

import { saveImage } from '../src/fs/saveImage.js';
import { PNG_BASE64, makeTempDir } from './helpers.js';

test('saveImage writes decoded PNG bytes to disk', async () => {
  const dir = await makeTempDir();
  const outputPath = path.join(dir, 'image.png');
  const saved = await saveImage({ resultBase64: PNG_BASE64, outputPath });

  assert.equal(saved, outputPath);
  const bytes = await fs.readFile(outputPath);
  assert.ok(bytes.length > 10);
  assert.equal(bytes.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
});

test('saveImage rejects data URLs', async () => {
  const dir = await makeTempDir();
  await assert.rejects(
    saveImage({ resultBase64: 'data:image/png;base64,AAAA', outputPath: path.join(dir, 'bad.png') }),
    /data URL/
  );
});

test('saveImage rejects non-standard base64', async () => {
  const dir = await makeTempDir();
  await assert.rejects(saveImage({ resultBase64: '_-8', outputPath: path.join(dir, 'bad.png') }), /not standard base64/);
});
