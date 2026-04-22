import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

import { parseSseText } from '../src/codex/streamResponsesSse.js';

const fixturesDir = new URL('../fixtures/', import.meta.url);

test('parseSseText reconstructs response items from fixture stream', async () => {
  const text = await fs.readFile(path.join(fixturesDir.pathname, 'success.sse'), 'utf8');
  const parsed = parseSseText(text);

  assert.equal(parsed.responseId, 'resp_success_1');
  assert.equal(parsed.items.length, 1);
  assert.equal(parsed.items[0].type, 'image_generation_call');
});



test('parseSseText preserves partial_image events from the live-style stream', async () => {
  const text = await fs.readFile(path.join(fixturesDir.pathname, 'partial-image.sse'), 'utf8');
  const parsed = parseSseText(text);

  const partial = parsed.events.find((event) => event.data?.type === 'response.image_generation_call.partial_image');
  assert.ok(partial);
  assert.equal(partial.data.item_id, 'ig_partial_1');
});

test('parseSseText throws on malformed SSE JSON payloads', async () => {
  const text = await fs.readFile(path.join(fixturesDir.pathname, 'malformed.sse'), 'utf8');
  assert.throws(() => parseSseText(text), /Malformed SSE JSON payload/);
});
