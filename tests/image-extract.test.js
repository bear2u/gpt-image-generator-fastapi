import test from 'node:test';
import assert from 'node:assert/strict';

import { extractImageGeneration } from '../src/codex/extractImageGeneration.js';
import { PNG_BASE64 } from './helpers.js';

test('extractImageGeneration returns the completed image_generation_call', () => {
  const image = extractImageGeneration([
    { type: 'message', role: 'assistant' },
    {
      type: 'image_generation_call',
      id: 'ig-123',
      status: 'generating',
      revised_prompt: 'tiny square',
      result: PNG_BASE64
    }
  ]);

  assert.equal(image.callId, 'ig-123');
  assert.equal(image.revisedPrompt, 'tiny square');
  assert.equal(image.resultBase64, PNG_BASE64);
});



test('extractImageGeneration falls back to partial_image SSE events', () => {
  const image = extractImageGeneration({
    items: [],
    events: [
      {
        event: 'response.image_generation_call.partial_image',
        data: {
          type: 'response.image_generation_call.partial_image',
          item_id: 'ig-partial',
          partial_image_b64: PNG_BASE64,
          revised_prompt: 'tiny square'
        }
      }
    ]
  });

  assert.equal(image.callId, 'ig-partial');
  assert.equal(image.revisedPrompt, 'tiny square');
  assert.equal(image.resultBase64, PNG_BASE64);
});

test('extractImageGeneration prefers output items over partial_image fallback', () => {
  const image = extractImageGeneration({
    items: [
      {
        type: 'image_generation_call',
        id: 'ig-final',
        status: 'generating',
        revised_prompt: 'final square',
        result: 'RklOQUw='
      }
    ],
    events: [
      {
        event: 'response.image_generation_call.partial_image',
        data: {
          type: 'response.image_generation_call.partial_image',
          item_id: 'ig-partial',
          partial_image_b64: PNG_BASE64,
          revised_prompt: 'partial square'
        }
      }
    ]
  });

  assert.equal(image.callId, 'ig-final');
  assert.equal(image.revisedPrompt, 'final square');
  assert.equal(image.resultBase64, 'RklOQUw=');
});

test('extractImageGeneration rejects missing image output', () => {
  assert.throws(() => extractImageGeneration([{ type: 'message', role: 'assistant' }]), /without an image_generation_call/);
});
