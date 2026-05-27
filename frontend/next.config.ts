import fs from "node:fs";
import type { NextConfig } from "next";

const buildPaths = {
  tailwindPostcss: "/app/node_modules/@tailwindcss/postcss/package.json",
  lightningcssPackage: "/app/node_modules/lightningcss/package.json",
  lightningcssLinuxBinary: "/app/node_modules/lightningcss/node/lightningcss.linux-arm64-musl.node",
  lightningcssDarwinBinary: "/app/node_modules/lightningcss/node/lightningcss.darwin-arm64.node",
  lightningcssLinuxPackage: "/app/node_modules/lightningcss-linux-arm64-musl/package.json",
  lightningcssDarwinPackage: "/app/node_modules/lightningcss-darwin-arm64/package.json",
  nextBuildCache: "/app/.next",
};

// #region agent log
fetch("http://127.0.0.1:7752/ingest/bc9d44cf-fe45-4715-aa75-32f07216a38a",{method:"POST",headers:{"Content-Type":"application/json","X-Debug-Session-Id":"3fe946"},body:JSON.stringify({sessionId:"3fe946",runId:"initial-build-debug",hypothesisId:"H2-H4",location:"frontend/next.config.ts:13",message:"Next build environment snapshot",data:{cwd:process.cwd(),platform:process.platform,arch:process.arch,nodeEnv:process.env.NODE_ENV ?? null,nextPublicApiUrl:process.env.NEXT_PUBLIC_API_URL ?? null,nextBuildCacheExists:fs.existsSync(buildPaths.nextBuildCache)},timestamp:Date.now()})}).catch(()=>{});
// #endregion

// #region agent log
fetch("http://127.0.0.1:7752/ingest/bc9d44cf-fe45-4715-aa75-32f07216a38a",{method:"POST",headers:{"Content-Type":"application/json","X-Debug-Session-Id":"3fe946"},body:JSON.stringify({sessionId:"3fe946",runId:"initial-build-debug",hypothesisId:"H1-H3",location:"frontend/next.config.ts:17",message:"Next build module snapshot",data:{tailwindPostcssExists:fs.existsSync(buildPaths.tailwindPostcss),lightningcssPackageExists:fs.existsSync(buildPaths.lightningcssPackage),lightningcssLinuxBinaryExists:fs.existsSync(buildPaths.lightningcssLinuxBinary),lightningcssDarwinBinaryExists:fs.existsSync(buildPaths.lightningcssDarwinBinary),lightningcssLinuxPackageExists:fs.existsSync(buildPaths.lightningcssLinuxPackage),lightningcssDarwinPackageExists:fs.existsSync(buildPaths.lightningcssDarwinPackage)},timestamp:Date.now()})}).catch(()=>{});
// #endregion

const nextConfig: NextConfig = {};

export default nextConfig;
