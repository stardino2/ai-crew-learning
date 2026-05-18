import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));
const html = await readFile(new URL("../public/index.html", import.meta.url), "utf8");
const js = await readFile(new URL("../public/app.js", import.meta.url), "utf8");
const css = await readFile(new URL("../public/styles.css", import.meta.url), "utf8");

assert.match(html, /id="service-grid"/, "service grid must exist");
assert.match(js, /fetch\("\/api\/status"\)/, "UI must fetch /api/status");

if (config.maintenance?.enabled) {
  const bannerIndex = html.indexOf('id="maintenance-banner"');
  const gridIndex = html.indexOf('id="service-grid"');

  assert.match(
    html,
    /id="maintenance-banner"/,
    'config schedules maintenance, but public/index.html is missing id="maintenance-banner"'
  );
  assert.ok(
    bannerIndex > -1 && gridIndex > -1 && bannerIndex < gridIndex,
    'maintenance banner must appear before id="service-grid" so it is visible before service cards'
  );
  assert.match(
    js,
    /renderMaintenance/,
    "config schedules maintenance, but public/app.js is missing a renderMaintenance handler"
  );
  assert.match(
    css,
    /\.maintenance-banner/,
    "config schedules maintenance, but public/styles.css is missing .maintenance-banner styles"
  );
}

console.log("ui smoke check passed");
