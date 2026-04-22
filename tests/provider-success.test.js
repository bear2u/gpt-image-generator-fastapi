import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

import { createPrivateCodexProvider } from '../src/providers/privateCodexProvider.js';
import { createFetchResponse, makeTempDir, writeAuthFixture } from './helpers.js';

const fixturesDir = new URL('../fixtures/', import.meta.url);

test('private provider saves PNG from successful SSE response', async () => {
  const dir = await makeTempDir();
  const fixture = await writeAuthFixture(dir);
  const outputPath = path.join(dir, 'out.png');
  const successSse = await fs.readFile(path.join(fixturesDir.pathname, 'success.sse'), 'utf8');

  const provider = createPrivateCodexProvider({
    baseUrl: 'https://chatgpt.com/backend-api/codex',
    authFile: fixture.authPath,
    installationIdFile: fixture.installationIdPath,
    defaultOriginator: 'codex_cli_rs'
  });

  const result = await provider.generateImage({
    prompt: 'make a blue square',
    model: 'gpt-5.4',
    outputPath,
    fetchImpl: async () =>
      createFetchResponse({
        ok: true,
        status: 200,
        body: successSse,
        headers: {
          'content-type': 'text/event-stream',
          'set-cookie': 'secret-cookie=value',
          'x-oai-request-id': 'req-123'
        }
      })
  });

  assert.equal(result.savedPath, outputPath);
  const bytes = await fs.readFile(outputPath);
  assert.ok(bytes.length > 10);
  assert.equal(result.response.status, 200);
});

test('private provider redacts secrets in debug dumps', async () => {
  const dir = await makeTempDir();
  const fixture = await writeAuthFixture(dir);
  const outputPath = path.join(dir, 'debug-image.png');
  const debugDir = path.join(dir, '.debug');
  const successSse = await fs.readFile(path.join(fixturesDir.pathname, 'success.sse'), 'utf8');

  const provider = createPrivateCodexProvider({
    baseUrl: 'https://chatgpt.com/backend-api/codex',
    authFile: fixture.authPath,
    installationIdFile: fixture.installationIdPath,
    defaultOriginator: 'codex_cli_rs'
  });

  await provider.generateImage({
    prompt: 'make a blue square',
    model: 'gpt-5.4',
    outputPath,
    debug: true,
    debugDir,
    fetchImpl: async () =>
      createFetchResponse({
        ok: true,
        status: 200,
        body: successSse,
        headers: {
          'content-type': 'text/event-stream',
          'set-cookie': 'secret-cookie=value',
          'x-oai-request-id': 'req-456'
        }
      })
  });

  const requestDump = await fs.readFile(path.join(debugDir, 'request.json'), 'utf8');
  const responseDump = await fs.readFile(path.join(debugDir, 'response.json'), 'utf8');
  assert.match(requestDump, /Bearer \[REDACTED\]/);
  assert.doesNotMatch(requestDump, /Bearer ey/);
  assert.doesNotMatch(requestDump, new RegExp(fixture.accountId));
  assert.doesNotMatch(requestDump, /install-123/);
  assert.doesNotMatch(requestDump, /session_id":\s*"[0-9a-f-]{36}/i);
  assert.match(requestDump, /REDACTED_ACCOUNT_ID/);
  assert.match(requestDump, /REDACTED_INSTALLATION_ID/);
  assert.match(responseDump, /"format": "sse"/);
  assert.match(responseDump, /"hasResult": true/);
  assert.doesNotMatch(responseDump, /set-cookie/i);
  assert.doesNotMatch(responseDump, /ig_success_1/);
  assert.doesNotMatch(responseDump, /resp_success_1/);
  assert.match(responseDump, /x-oai-request-id/);
});
