import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

import { runEslint, trackedJavaScript, validateInventory } from '../../scripts/run-eslint.mjs';

async function repository() {
  const root = await mkdtemp(join(tmpdir(), 'memtly-eslint-test-'));
  spawnSync('git', ['init', '--quiet'], { cwd: root, encoding: 'utf8' });
  await mkdir(join(root, 'nested'));
  await writeFile(join(root, 'tracked.mjs'), 'export {};\n');
  await writeFile(join(root, 'nested', 'tracked.cjs'), 'module.exports = {};\n');
  await writeFile(join(root, 'untracked.js'), 'export {};\n');
  await writeFile(join(root, 'other.txt'), 'not JavaScript\n');
  spawnSync('git', ['add', 'tracked.mjs', 'nested/tracked.cjs', 'other.txt'], {
    cwd: root,
    encoding: 'utf8'
  });
  return root;
}

test('tracked inventory excludes untracked and non-JavaScript files', async () => {
  const root = await repository();
  assert.deepEqual(trackedJavaScript(root), ['nested/tracked.cjs', 'tracked.mjs']);
  await validateInventory(trackedJavaScript(root), root);
});

test('empty inventory fails closed', () => {
  const spawn = () => ({ status: 0, stdout: Buffer.from('') });
  assert.throws(() => trackedJavaScript('/tmp/test', spawn), /inventory is empty/);
});

test('discovery failure is propagated', () => {
  const spawn = () => ({ status: 1, stdout: Buffer.from(''), error: new Error('git failed') });
  assert.throws(() => trackedJavaScript('/tmp/test', spawn), /discovery failed/);
});

test('unsafe inventory path is rejected', () => {
  const spawn = () => ({ status: 0, stdout: Buffer.from('../escape.mjs\0') });
  assert.throws(() => trackedJavaScript('/tmp/test', spawn), /unsafe tracked/);
});

test('invocation is cache-free and uses the complete inventory', () => {
  let invocation;
  const spawn = (command, args, options) => {
    invocation = { command, args, options };
    return { status: 0 };
  };
  runEslint(['a.mjs', 'nested/b.cjs'], '/verified/repository', spawn);
  assert.equal(invocation.command, '/verified/repository/node_modules/.bin/eslint');
  assert.deepEqual(invocation.args, [
    '--no-cache',
    '--format',
    'stylish',
    'a.mjs',
    'nested/b.cjs'
  ]);
  assert.equal(invocation.options.cwd, '/verified/repository');
  assert.equal(invocation.options.stdio, 'inherit');
});
