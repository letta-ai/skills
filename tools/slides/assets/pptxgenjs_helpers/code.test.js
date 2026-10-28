// Run with Prism installed: node --test tools/slides/assets/pptxgenjs_helpers/code.test.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const { buildThemeMap, codeToRuns } = require("./code.js");

test("Okaidia applies grouped token colors to every selector", () => {
  const theme = buildThemeMap();
  for (const token of ["comment", "prolog", "doctype", "cdata"]) {
    assert.equal(theme[token], "8292a2", token);
  }
  assert.equal(theme.number, "ae81ff");
  assert.equal(theme.string, "a6e22e");
  assert.equal(theme.function, "e6db74");
  assert.equal(theme.keyword, "66d9ef");
});

test("JavaScript rich-text runs retain the theme colors and source text", () => {
  const source = 'function greet() { return 42 + "hello"; }';
  const runs = codeToRuns(source, "javascript");
  assert.equal(runs.map(run => run.text).join(""), "1 " + source);
  for (const [text, color] of [["greet", "e6db74"], ["42", "ae81ff"], ['"hello"', "a6e22e"]]) {
    assert.equal(runs.find(run => run.text === text).options.color, color, text);
  }
});

test("global colors ignore scoped selectors and unrelated declarations", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "prism-theme-"));
  try {
    const css = path.join(directory, "theme.css");
    fs.writeFileSync(css, `
      /* .token.number { color: #badbad; } */
      .token.string, .token.number { color: #123456; background-color: #abcdef; }
      .language-css .token.string { color: #ffffff; }
      .token.number { font-weight: bold; }
    `);
    assert.deepEqual(buildThemeMap(css), { string: "123456", number: "123456" });
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
