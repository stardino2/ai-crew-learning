import assert from "node:assert/strict";
import { test } from "node:test";
import { publicStatusPayload, summarizeStatus } from "../../src/status.mjs";

test("summarizeStatus prioritizes active maintenance", () => {
  const summary = summarizeStatus({
    overallStatus: "operational",
    services: [{ id: "api", name: "API", status: "operational", latencyMs: 10 }],
    maintenance: {
      enabled: true,
      serviceName: "API Gateway"
    }
  });

  assert.equal(summary.level, "maintenance");
  assert.equal(summary.affected, "API Gateway");
});

test("publicStatusPayload exposes the contract fields", () => {
  const payload = publicStatusPayload({
    generatedAt: "2026-05-15T09:00:00+09:00",
    overallStatus: "operational",
    services: [],
    maintenance: { enabled: false }
  });

  assert.deepEqual(Object.keys(payload), [
    "generatedAt",
    "overallStatus",
    "summary",
    "services",
    "maintenance"
  ]);
});

