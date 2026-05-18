import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));
const logUrl = new URL("../ops/maintenance-events.ndjson", import.meta.url);

async function readLogLines() {
  try {
    const text = await readFile(logUrl, "utf8");
    return text.split(/\r?\n/).filter(Boolean);
  } catch (error) {
    if (error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

const lines = await readLogLines();

if (!config.maintenance?.enabled) {
  assert.ok(
    lines === null || lines.length === 0,
    "ops log must be absent or empty when no active maintenance is scheduled"
  );
  console.log("ops log check passed (no active maintenance scheduled)");
  process.exit(0);
}

assert.ok(lines?.length, "ops/maintenance-events.ndjson is required when maintenance is enabled");

const events = lines.map((line, index) => {
  try {
    return JSON.parse(line);
  } catch (error) {
    throw new Error(`ops log line ${index + 1} must be valid JSON: ${error.message}`);
  }
});

const expected = config.maintenance;
const event = events.find((candidate) =>
  candidate.type === "maintenance.scheduled" &&
  candidate.serviceId === expected.serviceId &&
  candidate.start === expected.start
);

assert.ok(event, "ops log must include a maintenance.scheduled event derived from status.config.json");
assert.equal(event.serviceName, expected.serviceName, "ops log serviceName must match config maintenance.serviceName");
assert.equal(event.end, expected.end, "ops log end must match config maintenance.end");
assert.equal(event.message, expected.message, "ops log message must match config maintenance.message");
assert.equal(typeof event.createdAt, "string", "ops log createdAt is required");
assert.match(event.createdAt, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$/);
assert.equal(typeof event.source, "string", "ops log source is required");
assert.ok(event.source.length > 0, "ops log source must not be empty");

console.log("ops log check passed");
