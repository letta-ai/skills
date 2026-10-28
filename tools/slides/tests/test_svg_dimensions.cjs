// Run with: node --test tools/slides/tests/test_svg_dimensions.cjs
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { getImageDimensions, imageSizingContain } = require('../assets/pptxgenjs_helpers/image.js');

const fixtures = [
  ['child dimensions', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200"><rect width="10" height="10"/></svg>', 400, 200],
  ['single quotes', "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='180'></svg>", 320, 180],
  ['comma viewBox', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0,0,320,180"></svg>', 320, 180],
  ['attribute name boundaries', '<svg xmlns="http://www.w3.org/2000/svg" data-width="10" data-height="10" viewBox="0 0 400 200"></svg>', 400, 200],
];

for (const [name, svg, width, height] of fixtures) {
  test(`uses SVG root dimensions: ${name}`, () => {
    assert.deepEqual(getImageDimensions(svg), { width, height, aspectRatio: width / height, type: 'svg' });
    const placement = imageSizingContain(svg, 0, 0, width / 100, height / 100);
    for (const [key, expected] of Object.entries({ x: 0, y: 0, w: width / 100, h: height / 100 })) {
      assert.ok(Math.abs(placement[key] - expected) < 1e-10, `${key}: ${placement[key]} != ${expected}`);
    }
  });
}

test('keeps explicit root dimensions ahead of child attributes and viewBox values', () => {
  assert.deepEqual(getImageDimensions('<svg width="640" height="360" viewBox="0 0 400 200"><rect width="10" height="10"/></svg>'), {
    width: 640, height: 360, aspectRatio: 16 / 9, type: 'svg',
  });
});

test('handles a greater-than character inside a quoted root attribute', () => {
  assert.equal(getImageDimensions('<svg data-label="a > b" width="320" height="180"></svg>').aspectRatio, 16 / 9);
});

test('retains physical units and the existing size fallback', () => {
  assert.deepEqual(getImageDimensions('<svg width="2in" height="1in"></svg>'), {
    width: 192, height: 96, aspectRatio: 2, type: 'svg',
  });
  assert.deepEqual(getImageDimensions('<svg></svg>'), { width: 100, height: 100, aspectRatio: 1, type: 'svg' });
});

