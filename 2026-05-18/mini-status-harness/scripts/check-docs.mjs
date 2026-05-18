import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));

if (!config.maintenance?.enabled) {
  console.log("docs check passed (no active maintenance scheduled)");
  process.exit(0);
}

const notice = await readFile(new URL("../docs/ops-notice.md", import.meta.url), "utf8");
const changelog = await readFile(new URL("../CHANGELOG.md", import.meta.url), "utf8");

const expectedDate = config.maintenance.start.slice(0, 10);
const expectedService = config.maintenance.serviceName;

assert.ok(
  notice.includes(expectedDate),
  `ops notice must include "${expectedDate}" (derived from config maintenance.start)`
);
assert.ok(
  notice.includes(expectedService),
  `ops notice must include "${expectedService}" (derived from config maintenance.serviceName)`
);
assert.ok(
  changelog.includes(expectedDate),
  `changelog must include "${expectedDate}" (derived from config maintenance.start)`
);
assert.ok(
  changelog.includes(expectedService),
  `changelog must include "${expectedService}" (derived from config maintenance.serviceName)`
);

console.log("docs check passed");
