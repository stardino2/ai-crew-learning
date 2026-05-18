import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));

if (!config.maintenance?.enabled) {
  console.log("design contract check passed (no active maintenance scheduled)");
  process.exit(0);
}

const design = await readFile(new URL("../../design.md", import.meta.url), "utf8");
const css = await readFile(new URL("../public/styles.css", import.meta.url), "utf8");

assert.match(design, /\{colors\.primary\}/, "design.md must define the primary color token");
assert.match(design, /No decorative gradients/i, "design.md must document the no-gradient rule");

const requiredTokens = [
  "--primary",
  "--canvas",
  "--parchment",
  "--ink",
  "--hairline",
  "--radius-sm",
  "--radius-lg",
  "--pill"
];

for (const token of requiredTokens) {
  assert.match(css, new RegExp(token.replaceAll("-", "\\-")), `styles.css must define or use ${token} from design.md`);
}

function cssBlock(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`${escaped}\\s*\\{(?<body>[^}]+)\\}`, "m"));
  assert.ok(match?.groups?.body, `${selector} style block is required when maintenance is enabled`);
  return match.groups.body;
}

const bannerCss = [
  cssBlock(".maintenance-banner"),
  cssBlock(".banner-label"),
  cssBlock(".banner-window")
].join("\n");

assert.match(bannerCss, /var\(--/, "maintenance banner styles must use design tokens via CSS variables");
assert.doesNotMatch(bannerCss, /#[0-9a-f]{3,8}\b/i, "maintenance banner styles must not introduce raw hex colors");

const forbiddenPatterns = [
  [/linear-gradient|radial-gradient/i, "decorative gradients are not allowed by design.md"],
  [/text-shadow\s*:/i, "text shadows are not allowed by design.md"],
  [/box-shadow\s*:/i, "UI shadows are not allowed on banner/card/text surfaces"],
  [/font-weight\s*:\s*500\b/i, "font-weight 500 is deliberately absent from design.md"]
];

for (const [pattern, message] of forbiddenPatterns) {
  assert.doesNotMatch(css, pattern, message);
}

console.log("design contract check passed");
