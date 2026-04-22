import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

import { loadCodexSession } from '../src/auth/loadCodexSession.js';
import { validateCodexSession } from '../src/auth/validateSession.js';
import { makeTempDir, writeAuthFixture } from './helpers.js';

test('loadCodexSession reads auth.json and installation_id', async () => {
  const dir = await makeTempDir();
  const fixture = await writeAuthFixture(dir);

  const session = await loadCodexSession({
    authFile: fixture.authPath,
    installationIdFile: fixture.installationIdPath
  });

  assert.equal(session.authMode, 'chatgpt');
  assert.equal(session.accountId, fixture.accountId);
  assert.equal(session.installationId, 'install-123');
  assert.ok(session.accessToken);
});

test('validateCodexSession rejects missing access token', async () => {
  const dir = await makeTempDir();
  const fixture = await writeAuthFixture(dir);
  const auth = JSON.parse(await fs.readFile(fixture.authPath, 'utf8'));
  delete auth.tokens.access_token;
  await fs.writeFile(fixture.authPath, JSON.stringify(auth, null, 2));

  const session = await loadCodexSession({
    authFile: fixture.authPath,
    installationIdFile: fixture.installationIdPath
  });

  assert.throws(() => validateCodexSession(session), /Missing tokens.access_token/);
});

test('validateCodexSession warns when installation_id is missing', async () => {
  const dir = await makeTempDir();
  const fixture = await writeAuthFixture(dir);
  await fs.unlink(fixture.installationIdPath);

  const session = await loadCodexSession({
    authFile: fixture.authPath,
    installationIdFile: fixture.installationIdPath
  });

  const result = validateCodexSession(session);
  assert.equal(result.warnings.length, 1);
  assert.match(result.warnings[0], /installation_id/);
});
