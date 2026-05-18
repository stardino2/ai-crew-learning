import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));
const reportUrl = new URL("../reports/latest/index.html", import.meta.url);

async function exists(url) {
  try {
    await access(url);
    return true;
  } catch {
    return false;
  }
}

assert.ok(await exists(reportUrl), "reports/latest/index.html must exist");

const report = await readFile(reportUrl, "utf8");

if (!config.maintenance?.enabled) {
  assert.match(
    report,
    /아직 실행된 점검 배너 결과가 없습니다|No active maintenance report/i,
    "baseline report must clearly state that no active maintenance report has been generated"
  );
  console.log("report check passed (no active maintenance scheduled)");
  process.exit(0);
}

const expectedDate = config.maintenance.start.slice(0, 10);
const expectedService = config.maintenance.serviceName;
const requiredText = [
  "Harness passed",
  "lint",
  "unit",
  "config",
  "api contract",
  "ui smoke",
  "docs",
  "design",
  "ops log",
  expectedDate,
  expectedService,
  "before.html",
  "after.html",
  "status-page-before.png",
  "status-page-final.png",
  "maintenance.scheduled"
];

for (const text of requiredText) {
  assert.ok(report.includes(text), `report must include "${text}"`);
}

const requiredFiles = [
  "../reports/latest/harness.log",
  "../reports/latest/snapshots/before.html",
  "../reports/latest/snapshots/after.html",
  "../reports/latest/assets/status-page-before.png",
  "../reports/latest/assets/status-page-final.png"
];

for (const relative of requiredFiles) {
  assert.ok(await exists(new URL(relative, import.meta.url)), `${relative.replace("../", "")} must exist`);
}

const harnessLog = await readFile(new URL("../reports/latest/harness.log", import.meta.url), "utf8");
for (const line of [
  "lint passed",
  "unit tests passed",
  "config check passed",
  "api contract check passed",
  "ui smoke check passed",
  "docs check passed",
  "design contract check passed",
  "ops log check passed"
]) {
  assert.ok(harnessLog.includes(line), `harness.log must include "${line}"`);
}

console.log("report check passed");
