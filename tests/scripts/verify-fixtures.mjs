#!/usr/bin/env node
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const manifestPath = resolve(root, 'tests/fixtures/manifest.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function readBrand(buffer, offset) {
  return String.fromCharCode(...buffer.subarray(offset, offset + 4));
}

function hasIsoBmffFtyp(buffer) {
  if (buffer.length < 16) return false;
  let offset = 0;
  while (offset + 8 <= Math.min(buffer.length, 64 * 1024)) {
    const size = buffer.readUInt32BE(offset);
    const type = readBrand(buffer, offset + 4);
    if (type === 'ftyp') return true;
    if (size < 8) return false;
    offset += size;
  }
  return false;
}

const seen = new Set();
for (const fixture of manifest.fixtures) {
  assert.ok(fixture.name, 'fixture name is required');
  assert.ok(fixture.source?.url, `${fixture.name}: source URL is required`);
  assert.ok(fixture.source?.ref, `${fixture.name}: immutable source ref is required`);
  assert.ok(fixture.source?.path, `${fixture.name}: source path is required`);
  assert.ok(fixture.license?.file, `${fixture.name}: license file is required`);
  assert.ok(fixture.sha256, `${fixture.name}: sha256 is required`);
  assert.ok(fixture.bytes > 0, `${fixture.name}: byte size is required`);
  assert.ok(fixture.dimensions, `${fixture.name}: dimensions field is required, even when not asserted`);
  assert.ok(fixture.metadataInspection, `${fixture.name}: metadata inspection note is required`);
  assert.ok(fixture.purpose, `${fixture.name}: purpose is required`);
  assert.ok(fixture.expected, `${fixture.name}: expected result is required`);

  const path = resolve(root, fixture.path);
  const licensePath = resolve(root, fixture.license.file);
  assert.equal(statSync(path).size, fixture.bytes, `${fixture.name}: size mismatch`);
  assert.equal(sha256(path), fixture.sha256, `${fixture.name}: sha256 mismatch`);
  assert.ok(statSync(licensePath).size > 0, `${fixture.name}: license file is empty`);
  assert.ok(hasIsoBmffFtyp(readFileSync(path)), `${fixture.name}: missing bounded ftyp box`);
  assert.ok(!seen.has(fixture.sha256), `${fixture.name}: duplicate sha256`);
  seen.add(fixture.sha256);
}

for (const fixture of manifest.negativeFixtures ?? []) {
  assert.ok(fixture.name, 'negative fixture name is required');
  assert.ok(fixture.expected, `${fixture.name}: expected result is required`);
  assert.ok(fixture.metadataInspection, `${fixture.name}: metadata inspection note is required`);
}

console.log(`fixture_manifest=passed fixtures=${manifest.fixtures.length} negative=${manifest.negativeFixtures?.length ?? 0}`);
