#!/usr/bin/env bun
/**
 * WarpGrep Test Script
 * 
 * Tests the Morph WarpGrep SDK with various queries.
 * 
 * Usage:
 *   export MORPH_API_KEY="your-key"
 *   bun scripts/test-warpgrep.ts /path/to/repo
 * 
 * Example:
 *   bun scripts/test-warpgrep.ts ../../../  # test on skills repo itself
 *   bun scripts/test-warpgrep.ts /path/to/letta-code
 */

import { MorphClient } from '@morphllm/morphsdk';

const REPO = process.argv[2] || '.';

if (!process.env.MORPH_API_KEY) {
  console.error('❌ MORPH_API_KEY not set');
  console.error('   Run: export MORPH_API_KEY="your-key"');
  process.exit(1);
}

const morph = new MorphClient({ apiKey: process.env.MORPH_API_KEY });

const tests = [
  'Find the main entry point',
  'Find authentication logic',
  'Find where configuration is handled',
  'Find error handling patterns',
];

console.log('======================================================================');
console.log('MORPH WARPGREP TEST');
console.log('======================================================================');
console.log(`Repo: ${REPO}`);
console.log(`SDK: @morphllm/morphsdk`);
console.log('======================================================================\n');

console.log('| Query                              | Result | Time   | Files |');
console.log('|------------------------------------|--------|--------|-------|');

let passed = 0;
let failed = 0;

for (const query of tests) {
  const start = Date.now();
  
  try {
    const result = await morph.warpGrep.execute({
      query,
      repoRoot: REPO
    });
    
    const time = ((Date.now() - start) / 1000).toFixed(1) + 's';
    const files = result.contexts?.length || 0;
    const status = result.success ? '✅' : '❌';
    
    if (result.success) passed++; else failed++;
    
    console.log(`| ${query.padEnd(34)} | ${status}     | ${time.padEnd(6)} | ${String(files).padEnd(5)} |`);
    
  } catch (err: any) {
    const time = ((Date.now() - start) / 1000).toFixed(1) + 's';
    failed++;
    console.log(`| ${query.padEnd(34)} | ❌     | ${time.padEnd(6)} | ERR   |`);
  }
}

console.log('\n======================================================================');
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log('======================================================================');

if (failed > 0) process.exit(1);
