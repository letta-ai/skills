// Run with: node --test tools/slides/tests/test_image_data_uri.cjs
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { getImageDimensions, imageSizingContain, imageSizingCrop } = require('../assets/pptxgenjs_helpers/image.js');
const { svgToDataUri } = require('../assets/pptxgenjs_helpers/svg.js');

const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><text>café + 50%</text></svg>';
// A complete 2x3 RGB PNG generated with Pillow.
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAIAAAADCAIAAAA2iEnWAAAAFElEQVR4nGOUC6hgYGBgYmBgQFAAEQwA7LuGupgAAAAASUVORK5CYII=', 'base64');

test('reads percent-encoded SVG data URIs through sizing helpers', async () => {
  const source = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  assert.equal(await (await fetch(source)).text(), svg);
  assert.deepEqual(getImageDimensions(source), { width: 320, height: 180, aspectRatio: 16 / 9, type: 'svg' });
  assert.deepEqual(imageSizingContain(source, 0, 0, 16, 9), { x: 0, y: 0, w: 16, h: 9 });
  assert.deepEqual(imageSizingCrop(source, 0, 0, 16, 9).sizing, { type: 'crop', x: 0, y: 0, w: 16, h: 9 });
});

test('reads raw SVG data without interpreting plus signs as spaces', async () => {
  const source = 'data:image/svg+xml,' + svg;
  assert.equal(await (await fetch(source)).text(), svg);
  assert.equal(getImageDimensions(source).aspectRatio, 16 / 9);
});

test('decodes percent-encoded binary image octets', async () => {
  const source = 'data:image/png,' + Array.from(png, byte => '%' + byte.toString(16).padStart(2, '0')).join('');
  assert.deepEqual(Buffer.from(await (await fetch(source)).arrayBuffer()), png);
  assert.deepEqual(getImageDimensions(source), { width: 2, height: 3, aspectRatio: 2 / 3, type: 'png' });
});

test('decodes percent escapes before base64 decoding', async () => {
  const source = 'data:image/png;base64,' + encodeURIComponent(png.toString('base64'));
  assert.deepEqual(Buffer.from(await (await fetch(source)).arrayBuffer()), png);
  assert.equal(getImageDimensions(source).height, 3);
});

test('preserves existing buffer, raw SVG and helper-generated base64 inputs', () => {
  assert.equal(getImageDimensions(png).width, 2);
  assert.equal(getImageDimensions('data:image/png;base64,' + png.toString('base64')).height, 3);
  assert.equal(getImageDimensions(svg).aspectRatio, 16 / 9);
  assert.equal(getImageDimensions(svgToDataUri(svg)).aspectRatio, 16 / 9);
});
