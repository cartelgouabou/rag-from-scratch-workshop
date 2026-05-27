import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

const ENDPOINT = "http://127.0.0.1:7752/ingest/bc9d44cf-fe45-4715-aa75-32f07216a38a";
const SESSION_ID = "18ed2c";

const run = (command, args) => {
  try {
    return execFileSync(command, args, { encoding: "utf8" }).trim();
  } catch (error) {
    return String(error.stdout || error.stderr || error.message || "").trim();
  }
};

const composeYaml = readFileSync(new URL("../compose.yaml", import.meta.url), "utf8");
const dockerfile = readFileSync(new URL("../frontend/Dockerfile", import.meta.url), "utf8");
const packageJson = readFileSync(new URL("../frontend/package.json", import.meta.url), "utf8");

const payloads = [
  {
    sessionId: SESSION_ID,
    runId: "pre-compose-check",
    hypothesisId: "H1-H2",
    location: "scripts/debug-port-3000.mjs:18",
    message: "Host port 3000 occupancy snapshot",
    data: {
      port: 3000,
      lsof3000: run("lsof", ["-nP", "-iTCP:3000", "-sTCP:LISTEN"]),
      lsof3001: run("lsof", ["-nP", "-iTCP:3001", "-sTCP:LISTEN"]),
      dockerPsPorts: run("docker", ["ps", "--format", "{{.Names}}\t{{.Ports}}"]),
    },
    timestamp: Date.now(),
  },
  {
    sessionId: SESSION_ID,
    runId: "pre-compose-check",
    hypothesisId: "H3-H4",
    location: "scripts/debug-port-3000.mjs:30",
    message: "Frontend port configuration snapshot",
    data: {
      composeFrontendPublishes3000: composeYaml.includes('"3000:3000"'),
      composeFrontendPublishes3001: composeYaml.includes('"3001:3000"'),
      composeFrontendSetsPort3000: composeYaml.includes("PORT: 3000"),
      dockerfileExposes3000: dockerfile.includes("EXPOSE 3000"),
      packageStartUses3000: packageJson.includes('next start --hostname 0.0.0.0 --port 3000'),
    },
    timestamp: Date.now(),
  },
];

for (const payload of payloads) {
  // #region agent log
  await fetch(ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Debug-Session-Id": SESSION_ID,
    },
    body: JSON.stringify(payload),
  }).catch(() => {});
  // #endregion
}

console.log("Logged port 3000 preflight snapshot.");
