#!/usr/bin/env bun
/**
 * WarpGrep Client - Direct API Implementation
 * 
 * A working WarpGrep client that calls Morph's API directly,
 * handling the actual response format from morph-warp-grep-v1.
 * 
 * Usage:
 *   export MORPH_API_KEY="your-key"
 *   bun warpgrep-client.ts "Find authentication logic" /path/to/repo
 * 
 * Or import as a module:
 *   import { warpGrep } from './warpgrep-client';
 *   const result = await warpGrep('query', '/path/to/repo');
 */

import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

// ============================================================================
// Configuration
// ============================================================================

const MORPH_API_URL = 'https://api.morphllm.com/v1/chat/completions';
const MODEL = 'morph-warp-grep-v1';
const MAX_TURNS = 4;
const MAX_TOOL_CALLS_PER_TURN = 8;

// ============================================================================
// Types
// ============================================================================

export interface WarpGrepResult {
  success: boolean;
  contexts?: Array<{ file: string; content: string; lines?: string }>;
  summary?: string;
  error?: string;
  turns?: number;
}

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ToolCall {
  tool: 'grep' | 'read' | 'list_directory' | 'finish';
  args: Record<string, any>;
}

// ============================================================================
// System Prompt (from Morph SDK, slightly modified for actual model behavior)
// ============================================================================

const SYSTEM_PROMPT = `You are a code search agent. Your task is to find all relevant code for a given search_string.

### workflow
You have exactly 4 turns. The 4th turn MUST be a \`finish\` call. Each turn allows up to 8 parallel tool calls.

- Turn 1: Map the territory OR dive deep (based on search_string specificity)
- Turn 2-3: Refine based on findings
- Turn 4: MUST call \`finish\` with all relevant code locations
- You MAY call \`finish\` early if confident—but never before at least 1 search turn.

### tools
Tool calls use nested XML elements.

### \`list_directory\`
Elements:
- \`<path>\` (required): Directory path to list

Example:
<list_directory>
  <path>src/services</path>
</list_directory>

### \`read\`
Elements:
- \`<path>\` (required): File path to read
- \`<lines>\` (optional): Line ranges like "1-50,75-80"

Example:
<read>
  <path>src/main.ts</path>
  <lines>1-50</lines>
</read>

### \`grep\`
Elements:
- \`<pattern>\` (required): Search pattern (regex)
- \`<sub_dir>\` (optional): Subdirectory to search in
- \`<glob>\` (optional): File pattern filter

Example:
<grep>
  <pattern>(authenticate|login)</pattern>
  <sub_dir>src/</sub_dir>
</grep>

### \`finish\`
Submit final answer with code locations using nested \`<file>\` elements.

Example:
<finish>
  <file>
    <path>src/auth.ts</path>
    <lines>1-50</lines>
  </file>
</finish>

<output_format>
1. First, wrap reasoning in \`<tool_call>...</tool_call>\` tags
2. Then output tool calls using XML elements
3. No commentary outside tool_call tags
</output_format>`;

// ============================================================================
// File System Utilities
// ============================================================================

function getRepoStructure(repoRoot: string, maxDepth: number = 3): string {
  const result: string[] = [];
  const seen = new Set<string>();
  
  function walk(dir: string, depth: number, prefix: string = '') {
    if (depth > maxDepth) return;
    if (seen.has(dir)) return;
    seen.add(dir);
    
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true })
        .filter(e => !e.name.startsWith('.') && 
                     !['node_modules', '__pycache__', 'dist', 'build', '.git'].includes(e.name))
        .sort((a, b) => {
          // Directories first
          if (a.isDirectory() && !b.isDirectory()) return -1;
          if (!a.isDirectory() && b.isDirectory()) return 1;
          return a.name.localeCompare(b.name);
        });
      
      for (const entry of entries.slice(0, 20)) { // Limit entries per directory
        const isDir = entry.isDirectory();
        result.push(prefix + entry.name + (isDir ? '/' : ''));
        if (isDir) {
          walk(path.join(dir, entry.name), depth + 1, prefix + '  ');
        }
      }
    } catch (e) {
      // Skip inaccessible directories
    }
  }
  
  result.push(path.basename(repoRoot) + '/');
  walk(repoRoot, 1, '  ');
  return result.slice(0, 100).join('\n'); // Limit total lines
}

// ============================================================================
// Tool Execution
// ============================================================================

function executeGrep(repoRoot: string, pattern: string, subDir?: string, glob?: string): string {
  const searchPath = subDir ? path.join(repoRoot, subDir) : repoRoot;
  
  try {
    let cmd = `rg --line-number --no-heading -C 1`;
    if (glob) {
      cmd += ` --glob "${glob}"`;
    }
    cmd += ` "${pattern}" "${searchPath}" 2>/dev/null | head -150`;
    
    const result = execSync(cmd, { 
      encoding: 'utf-8', 
      maxBuffer: 1024 * 1024,
      timeout: 10000 
    });
    return result.trim() || 'No matches found';
  } catch (e: any) {
    if (e.status === 1) return 'No matches found';
    return `Error: ${e.message}`;
  }
}

function executeRead(repoRoot: string, filePath: string, lines?: string): string {
  const fullPath = path.join(repoRoot, filePath);
  
  try {
    if (!fs.existsSync(fullPath)) {
      return `Error: File not found: ${filePath}`;
    }
    
    const content = fs.readFileSync(fullPath, 'utf-8');
    const allLines = content.split('\n');
    
    if (!lines || lines === '*') {
      // Return entire file with line numbers
      return allLines.map((line, i) => `${i + 1}|${line}`).join('\n');
    }
    
    // Parse line ranges like "1-50,75-80"
    const ranges = lines.split(',').map(r => r.trim());
    const selectedLines: string[] = [];
    
    for (const range of ranges) {
      const [start, end] = range.split('-').map(n => parseInt(n.trim()));
      const s = Math.max(1, start) - 1;
      const e = end ? Math.min(allLines.length, end) : s + 1;
      
      for (let i = s; i < e; i++) {
        selectedLines.push(`${i + 1}|${allLines[i]}`);
      }
    }
    
    return selectedLines.join('\n');
  } catch (e: any) {
    return `Error reading file: ${e.message}`;
  }
}

function executeListDir(repoRoot: string, dirPath: string, pattern?: string): string {
  const fullPath = path.join(repoRoot, dirPath);
  
  try {
    if (!fs.existsSync(fullPath)) {
      return `Error: Directory not found: ${dirPath}`;
    }
    
    const entries = fs.readdirSync(fullPath, { withFileTypes: true })
      .filter(e => !e.name.startsWith('.'))
      .filter(e => !pattern || new RegExp(pattern).test(e.name));
    
    return entries
      .map(e => e.name + (e.isDirectory() ? '/' : ''))
      .sort()
      .join('\n');
  } catch (e: any) {
    return `Error listing directory: ${e.message}`;
  }
}

// ============================================================================
// Response Parser
// ============================================================================

function parseToolCalls(content: string): ToolCall[] {
  const calls: ToolCall[] = [];
  
  // Parse <grep> tags
  const grepRegex = /<grep>([\s\S]*?)<\/grep>/gi;
  let match;
  while ((match = grepRegex.exec(content)) !== null) {
    const inner = match[1];
    const pattern = inner.match(/<pattern>([\s\S]*?)<\/pattern>/i)?.[1]?.trim();
    const subDir = inner.match(/<sub_dir>([\s\S]*?)<\/sub_dir>/i)?.[1]?.trim();
    const glob = inner.match(/<glob>([\s\S]*?)<\/glob>/i)?.[1]?.trim();
    
    if (pattern) {
      calls.push({ tool: 'grep', args: { pattern, sub_dir: subDir, glob } });
    }
  }
  
  // Parse <read> and <read-parallel> tags
  const readRegex = /<read(?:-parallel)?>([\s\S]*?)<\/read(?:-parallel)?>/gi;
  while ((match = readRegex.exec(content)) !== null) {
    const inner = match[1];
    const filePath = inner.match(/<path>([\s\S]*?)<\/path>/i)?.[1]?.trim();
    const lines = inner.match(/<lines>([\s\S]*?)<\/lines>/i)?.[1]?.trim();
    
    if (filePath) {
      calls.push({ tool: 'read', args: { path: filePath, lines } });
    }
  }
  
  // Parse <list_directory> tags
  const listRegex = /<list_directory>([\s\S]*?)<\/list_directory>/gi;
  while ((match = listRegex.exec(content)) !== null) {
    const inner = match[1];
    const dirPath = inner.match(/<path>([\s\S]*?)<\/path>/i)?.[1]?.trim();
    const pattern = inner.match(/<pattern>([\s\S]*?)<\/pattern>/i)?.[1]?.trim();
    
    if (dirPath) {
      calls.push({ tool: 'list_directory', args: { path: dirPath, pattern } });
    }
  }
  
  // Parse <finish> tag
  const finishMatch = content.match(/<finish>([\s\S]*?)<\/finish>/i);
  if (finishMatch) {
    const inner = finishMatch[1];
    const files: Array<{ path: string; lines?: string }> = [];
    
    const fileRegex = /<file>([\s\S]*?)<\/file>/gi;
    while ((match = fileRegex.exec(inner)) !== null) {
      const fileInner = match[1];
      const filePath = fileInner.match(/<path>([\s\S]*?)<\/path>/i)?.[1]?.trim();
      const lines = fileInner.match(/<lines>([\s\S]*?)<\/lines>/i)?.[1]?.trim();
      
      if (filePath) {
        files.push({ path: filePath, lines });
      }
    }
    
    calls.push({ tool: 'finish', args: { files } });
  }
  
  return calls.slice(0, MAX_TOOL_CALLS_PER_TURN);
}

// ============================================================================
// Tool Result Formatting
// ============================================================================

function formatToolResults(repoRoot: string, calls: ToolCall[]): string {
  const results: string[] = [];
  
  for (const call of calls) {
    if (call.tool === 'finish') continue; // Don't execute finish
    
    let output: string;
    
    switch (call.tool) {
      case 'grep':
        output = executeGrep(repoRoot, call.args.pattern, call.args.sub_dir, call.args.glob);
        results.push(`<grep_result pattern="${call.args.pattern}"${call.args.sub_dir ? ` sub_dir="${call.args.sub_dir}"` : ''}>\n${output}\n</grep_result>`);
        break;
        
      case 'read':
        output = executeRead(repoRoot, call.args.path, call.args.lines);
        results.push(`<read_result path="${call.args.path}">\n${output}\n</read_result>`);
        break;
        
      case 'list_directory':
        output = executeListDir(repoRoot, call.args.path, call.args.pattern);
        results.push(`<list_directory_result path="${call.args.path}">\n${output}\n</list_directory_result>`);
        break;
    }
  }
  
  return results.join('\n\n');
}

// ============================================================================
// Main WarpGrep Function
// ============================================================================

export async function warpGrep(
  query: string, 
  repoRoot: string,
  options: { debug?: boolean; apiKey?: string } = {}
): Promise<WarpGrepResult> {
  const apiKey = options.apiKey || process.env.MORPH_API_KEY;
  const debug = options.debug ?? false;
  
  if (!apiKey) {
    return { success: false, error: 'MORPH_API_KEY not set' };
  }
  
  const absoluteRepoRoot = path.resolve(repoRoot);
  
  if (!fs.existsSync(absoluteRepoRoot)) {
    return { success: false, error: `Repository not found: ${absoluteRepoRoot}` };
  }
  
  const repoStructure = getRepoStructure(absoluteRepoRoot);
  
  const messages: Message[] = [
    { role: 'system', content: SYSTEM_PROMPT },
    { 
      role: 'user', 
      content: `<repo_structure>\n${repoStructure}\n</repo_structure>\n\n<search_string>\n${query}\n</search_string>` 
    }
  ];
  
  for (let turn = 1; turn <= MAX_TURNS; turn++) {
    if (debug) console.log(`\n🔄 Turn ${turn}/${MAX_TURNS}`);
    
    // Call Morph API
    const response = await fetch(MORPH_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: MODEL,
        messages,
        temperature: 0,
        max_tokens: 4096
      })
    });
    
    if (!response.ok) {
      const error = await response.text();
      return { success: false, error: `API error (${response.status}): ${error}`, turns: turn };
    }
    
    const data = await response.json();
    const assistantContent = data.choices?.[0]?.message?.content;
    
    if (!assistantContent) {
      return { success: false, error: 'No response from model', turns: turn };
    }
    
    if (debug) {
      console.log('📥 Model response:');
      console.log(assistantContent.slice(0, 500) + (assistantContent.length > 500 ? '...' : ''));
    }
    
    messages.push({ role: 'assistant', content: assistantContent });
    
    // Parse tool calls
    const toolCalls = parseToolCalls(assistantContent);
    
    if (debug) {
      console.log(`📋 Parsed ${toolCalls.length} tool calls:`, toolCalls.map(c => c.tool));
    }
    
    // Check for finish
    const finishCall = toolCalls.find(c => c.tool === 'finish');
    if (finishCall) {
      const contexts: Array<{ file: string; content: string; lines?: string }> = [];
      
      for (const file of finishCall.args.files || []) {
        const content = executeRead(absoluteRepoRoot, file.path, file.lines);
        contexts.push({ 
          file: file.path, 
          content,
          lines: file.lines 
        });
      }
      
      return {
        success: true,
        contexts,
        summary: `Found ${contexts.length} relevant code section(s) in ${turn} turn(s)`,
        turns: turn
      };
    }
    
    // No finish - execute tools and continue
    const otherCalls = toolCalls.filter(c => c.tool !== 'finish');
    
    if (otherCalls.length === 0) {
      if (debug) console.log('⚠️ No tool calls parsed, continuing...');
      // Add a prompt to encourage tool usage
      messages.push({ 
        role: 'user', 
        content: 'Please use the grep, read, or list_directory tools to search the codebase. When ready, use finish to return results.' 
      });
      continue;
    }
    
    const toolResults = formatToolResults(absoluteRepoRoot, otherCalls);
    
    if (debug) {
      console.log('📤 Tool results:');
      console.log(toolResults.slice(0, 500) + (toolResults.length > 500 ? '...' : ''));
    }
    
    messages.push({ role: 'user', content: toolResults });
  }
  
  return { 
    success: false, 
    error: 'Search did not complete within max turns',
    turns: MAX_TURNS 
  };
}

// ============================================================================
// CLI Entry Point
// ============================================================================

async function main() {
  const args = process.argv.slice(2);
  
  // Parse flags
  const debugFlag = args.includes('--debug') || args.includes('-d');
  const filteredArgs = args.filter(a => !a.startsWith('-'));
  
  if (filteredArgs.length < 2) {
    console.log(`
WarpGrep Client - Fast Agentic Code Search

Usage:
  bun warpgrep-client.ts "<search query>" <repo-path> [--debug]

Example:
  export MORPH_API_KEY="your-key"
  bun warpgrep-client.ts "Find authentication logic" ./my-project

Options:
  --debug, -d    Show detailed output for each turn
`);
    process.exit(1);
  }
  
  const [query, repoPath] = filteredArgs;
  
  console.log(`🔍 WarpGrep Search`);
  console.log(`   Query: "${query}"`);
  console.log(`   Repo:  ${path.resolve(repoPath)}`);
  console.log('');
  
  const startTime = Date.now();
  const result = await warpGrep(query, repoPath, { debug: debugFlag });
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  
  if (result.success) {
    console.log(`\n✅ Search completed in ${result.turns} turn(s) (${elapsed}s)\n`);
    console.log(`Found ${result.contexts?.length || 0} relevant code section(s):\n`);
    
    for (const ctx of result.contexts || []) {
      console.log(`📄 ${ctx.file}${ctx.lines ? ` (lines ${ctx.lines})` : ''}`);
      console.log('─'.repeat(60));
      
      // Show first 30 lines or 1500 chars
      const lines = ctx.content.split('\n').slice(0, 30);
      console.log(lines.join('\n'));
      if (ctx.content.split('\n').length > 30) {
        console.log('... (truncated)');
      }
      console.log('');
    }
    
    console.log(`📝 ${result.summary}`);
  } else {
    console.error(`\n❌ Search failed: ${result.error}`);
    if (result.turns) {
      console.error(`   Completed ${result.turns} turn(s) before failing`);
    }
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.main) {
  main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}
