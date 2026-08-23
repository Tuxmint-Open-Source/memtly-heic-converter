import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

import {
  runMarkdownlint,
  trackedMarkdown,
  validateInventory
} from '../../scripts/run-markdownlint.mjs';

async function repository() {
  const root = await mkdtemp(join(tmpdir(), 'memtly-markdownlint-test-'));
  spawnSync('git', ['init', '--quiet'], { cwd: root, encoding: 'utf8' });
  await mkdir(join(root, 'nested'));
  await writeFile(join(root, 'README.md'), '# Tracked\n');
  await writeFile(join(root, 'nested', 'guide.md'), '# Guide\n');
  await writeFile(join(root, 'untracked.md'), '# Untracked\n');
  await writeFile(join(root, 'other.txt'), 'not Markdown\n');
  spawnSync('git', ['add', 'README.md', 'nested/guide.md', 'other.txt'], {
    cwd: root,
    encoding: 'utf8'
  });
  return root;
}

test('tracked inventory excludes untracked and non-Markdown files', async () => {
  const root = await repository();
  assert.deepEqual(trackedMarkdown(root), ['README.md', 'nested/guide.md']);
  await validateInventory(trackedMarkdown(root), root);
});

test('empty inventory fails closed', () => {
  const spawn = () => ({ status: 0, stdout: Buffer.from('') });
  assert.throws(() => trackedMarkdown('/tmp/test', spawn), /inventory is empty/);
});

test('discovery failure is propagated', () => {
  const spawn = () => ({ status: 1, stdout: Buffer.from(''), error: new Error('git failed') });
  assert.throws(() => trackedMarkdown('/tmp/test', spawn), /discovery failed/);
});

test('unsafe inventory path is rejected', () => {
  const spawn = () => ({ status: 0, stdout: Buffer.from('../escape.md\0') });
  assert.throws(() => trackedMarkdown('/tmp/test', spawn), /unsafe tracked/);
});

test('invocation uses the exact config and complete inventory', () => {
  let invocation;
  const spawn = (command, args, options) => {
    invocation = { command, args, options };
    return { status: 0 };
  };
  runMarkdownlint(['README.md', 'nested/guide.md'], '/verified/repository', spawn);
  assert.equal(
    invocation.command,
    '/verified/repository/node_modules/.bin/markdownlint-cli2'
  );
  assert.deepEqual(invocation.args, [
    '--config',
    '/verified/repository/.markdownlint-cli2.jsonc',
    'README.md',
    'nested/guide.md'
  ]);
  assert.equal(invocation.options.cwd, '/verified/repository');
  assert.equal(invocation.options.stdio, 'inherit');
});
