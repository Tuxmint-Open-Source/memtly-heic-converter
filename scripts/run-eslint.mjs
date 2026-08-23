#!/usr/bin/env node
// Run the lockfile-installed ESLint over every tracked JavaScript module.

import { constants } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { isAbsolute, resolve, sep } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const extensions = new Set(['.js', '.mjs', '.cjs']);

export function trackedJavaScript(repository = root, spawn = spawnSync) {
  const result = spawn(
    'git',
    ['ls-files', '-z', '--', '*.js', '*.mjs', '*.cjs'],
    { cwd: repository, encoding: 'buffer' }
  );
  if (result.status !== 0 || result.error) {
    throw new Error('tracked JavaScript discovery failed', { cause: result.error });
  }
  const paths = result.stdout
    .toString('utf8')
    .split('\0')
    .filter(Boolean)
    .sort();
  if (paths.length === 0) throw new Error('tracked JavaScript inventory is empty');
  for (const path of paths) {
    if (isAbsolute(path) || path.split(/[\\/]/).includes('..')) {
      throw new Error(`unsafe tracked JavaScript path: ${path}`);
    }
    const extension = path.slice(path.lastIndexOf('.'));
    if (!extensions.has(extension)) {
      throw new Error(`unexpected tracked JavaScript extension: ${path}`);
    }
  }
  return paths;
}

export async function validateInventory(paths, repository = root) {
  for (const path of paths) {
    const absolute = resolve(repository, path);
    if (!absolute.startsWith(`${resolve(repository)}${sep}`)) {
      throw new Error(`tracked JavaScript path escaped repository: ${path}`);
    }
    const metadata = await stat(absolute);
    if (!metadata.isFile()) throw new Error(`tracked JavaScript path is not a file: ${path}`);
  }
}

export function runEslint(paths, repository = root, spawn = spawnSync) {
  const binary = resolve(repository, 'node_modules', '.bin', 'eslint');
  const result = spawn(
    binary,
    ['--no-cache', '--format', 'stylish', ...paths],
    { cwd: repository, stdio: 'inherit' }
  );
  if (result.status !== 0 || result.error) {
    throw new Error('ESLint reported findings or failed to execute', { cause: result.error });
  }
}

export async function main() {
  const binary = resolve(root, 'node_modules', '.bin', 'eslint');
  await access(binary, constants.X_OK);
  const paths = trackedJavaScript();
  await validateInventory(paths);
  runEslint(paths);
  console.log(`eslint=passed files=${paths.length}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
