import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { publicStatusPayload } from "../src/status.mjs";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));
const payload = publicStatusPayload(config);

assert.equal(typeof payload.generatedAt, "string");
assert.equal(typeof payload.overallStatus, "string");
assert.equal(typeof payload.summary.level, "string");
assert.equal(typeof payload.summary.label, "string");
assert.ok(Array.isArray(payload.services));
assert.equal(typeof payload.maintenance?.enabled, "boolean", "maintenance.enabled must be boolean");

if (payload.maintenance.enabled) {
  const m = payload.maintenance;
  const tsPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$/;
  assert.equal(typeof m.serviceId, "string", "maintenance.serviceId must be a string");
  assert.ok(m.serviceId.length > 0, "maintenance.serviceId must not be empty");
  assert.equal(typeof m.serviceName, "string", "maintenance.serviceName must be a string");
  assert.ok(m.serviceName.length > 0, "maintenance.serviceName must not be empty");
  assert.match(m.start, tsPattern, "maintenance.start must be an ISO8601 timestamp with offset");
  assert.match(m.end, tsPattern, "maintenance.end must be an ISO8601 timestamp with offset");
  assert.ok(new Date(m.start) < new Date(m.end), "maintenance.start must be before maintenance.end");
  assert.equal(typeof m.message, "string", "maintenance.message must be a string");
  assert.ok(m.message.length > 0, "maintenance.message must not be empty");
}

console.log("api contract check passed");
