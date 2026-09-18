import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = await readFile(new URL('./TopNavbar.tsx', import.meta.url), 'utf8');

test('page navigation keeps native href fallbacks', () => {
  assert.match(source, /<Link\s+key=\{item\.href\}\s+href=\{item\.href\}/);

  const childLinks = source.match(/<Link\s+key=\{child\.href\}\s+href=\{child\.href\}/g) ?? [];
  assert.equal(childLinks.length, 2);
});

test('case workspace remains an in-page action', () => {
  assert.match(source, /child\.href === CASE_WORKSPACE_ACTION/);
  assert.match(source, /handleNavigation\(child\.href\)/);
});
