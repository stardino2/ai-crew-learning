import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, extname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { publicStatusPayload } from "./status.mjs";

const rootDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const publicDir = join(rootDir, "public");
const configPath = join(rootDir, "status.config.json");

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8"
};

async function readConfig() {
  return JSON.parse(await readFile(configPath, "utf8"));
}

async function sendFile(response, path) {
  const body = await readFile(path);
  response.writeHead(200, { "content-type": contentTypes[extname(path)] ?? "application/octet-stream" });
  response.end(body);
}

export function createStatusServer() {
  return createServer(async (request, response) => {
    try {
      const url = new URL(request.url ?? "/", "http://localhost");

      if (url.pathname === "/api/status") {
        const payload = publicStatusPayload(await readConfig());
        response.writeHead(200, { "content-type": "application/json; charset=utf-8" });
        response.end(JSON.stringify(payload, null, 2));
        return;
      }

      const asset = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
      await sendFile(response, join(publicDir, asset));
    } catch (error) {
      response.writeHead(error.code === "ENOENT" ? 404 : 500, { "content-type": "text/plain; charset=utf-8" });
      response.end(error.code === "ENOENT" ? "Not found" : "Internal server error");
    }
  });
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const port = Number(process.env.PORT ?? 4173);
  createStatusServer().listen(port, () => {
    console.log(`mini-status-harness listening on http://localhost:${port}`);
  });
}
