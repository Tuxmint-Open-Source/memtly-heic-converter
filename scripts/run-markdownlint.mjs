#!/usr/bin/env node
// Run lockfile-installed markdownlint-cli2 over every tracked Markdown file.

import { constants } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { isAbsolute, resolve, sep } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));

export function trackedMarkdown(repository = root, spawn = spawnSync) {
  const result = spawn('git', ['ls-files', '-z', '--', '*.md'], {
    cwd: repository,
    encoding: 'buffer'
  });
  if (result.status !== 0 || result.error) {
    throw new Error('tracked Markdown discovery failed', { cause: result.error });
  }
  const paths = result.stdout.toString('utf8').split('\0').filter(Boolean).sort();
  if (paths.length === 0) throw new Error('tracked Markdown inventory is empty');
  for (const path of paths) {
    if (isAbsolute(path) || path.split(/[\\/]/).includes('..')) {
      throw new Error(`unsafe tracked Markdown path: ${path}`);
    }
    if (!path.toLowerCase().endsWith('.md')) {
      throw new Error(`unexpected tracked Markdown extension: ${path}`);
    }
  }
  return paths;
}

export async function validateInventory(paths, repository = root) {
  for (const path of paths) {
    const absolute = resolve(repository, path);
    if (!absolute.startsWith(`${resolve(repository)}${sep}`)) {
      throw new Error(`tracked Markdown path escaped repository: ${path}`);
    }
    const metadata = await stat(absolute);
    if (!metadata.isFile()) throw new Error(`tracked Markdown path is not a file: ${path}`);
  }
}

export function runMarkdownlint(paths, repository = root, spawn = spawnSync) {
  const binary = resolve(repository, 'node_modules', '.bin', 'markdownlint-cli2');
  const config = resolve(repository, '.markdownlint-cli2.jsonc');
  const result = spawn(binary, ['--config', config, ...paths], {
    cwd: repository,
    stdio: 'inherit'
  });
  if (result.status !== 0 || result.error) {
    throw new Error('markdownlint reported findings or failed to execute', {
      cause: result.error
    });
  }
}

export async function main() {
  const binary = resolve(root, 'node_modules', '.bin', 'markdownlint-cli2');
  await access(binary, constants.X_OK);
  const paths = trackedMarkdown();
  await validateInventory(paths);
  runMarkdownlint(paths);
  console.log(`markdownlint=passed files=${paths.length} version=0.23.2`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
