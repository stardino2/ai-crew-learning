import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const config = JSON.parse(await readFile(new URL("../status.config.json", import.meta.url), "utf8"));
const allowedStatuses = new Set(["operational", "maintenance", "degraded", "outage"]);

assert.match(config.generatedAt, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$/);
assert.ok(Array.isArray(config.services), "services must be an array");
assert.ok(config.services.length >= 1, "at least one service is required");

for (const service of config.services) {
  assert.ok(service.id, "service.id is required");
  assert.ok(service.name, "service.name is required");
  assert.ok(allowedStatuses.has(service.status), `${service.name} has an invalid status`);
  assert.equal(typeof service.latencyMs, "number", `${service.name} latencyMs must be a number`);
}

if (config.maintenance?.enabled) {
  assert.ok(config.maintenance.serviceId, "maintenance.serviceId is required");
  assert.ok(config.maintenance.serviceName, "maintenance.serviceName is required");
  assert.ok(config.maintenance.start, "maintenance.start is required");
  assert.ok(config.maintenance.end, "maintenance.end is required");
  assert.ok(config.maintenance.message, "maintenance.message is required");
  assert.ok(new Date(config.maintenance.start) < new Date(config.maintenance.end), "maintenance start must be before end");
  assert.ok(config.services.some((service) => service.id === config.maintenance.serviceId), "maintenance serviceId must match a service");
}

console.log("config check passed");

