import test from 'node:test';
import assert from 'node:assert/strict';

import { createProvider } from '../src/providers/createProvider.js';

test('auto provider falls back to codex-cli when private provider fails', async () => {
  const provider = createProvider({
    provider: 'auto',
    generatedImagesDir: '/tmp/missing',
    baseUrl: 'https://chatgpt.com/backend-api/codex',
    authFile: '/tmp/missing-auth.json',
    installationIdFile: '/tmp/missing-installation-id',
    defaultOriginator: 'codex_cli_rs'
  });

  const execImpl = async (_file, args) => {
    if (args[0] === '--version') {
      return { stdout: 'codex-cli 0.122.0\n', stderr: '' };
    }
    if (args[0] === 'login') {
      return { stdout: 'Logged in using ChatGPT\n', stderr: '' };
    }
    throw Object.assign(new Error('missing png'), { code: 'CODEX_CLI_IMAGE_NOT_FOUND' });
  };

  await assert.rejects(
    provider.generateImage({
      prompt: 'red square',
      outputPath: '/tmp/out.png',
      execImpl
    }),
    /missing png|no generated PNG/i
  );
});
