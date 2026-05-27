import fs from "node:fs";

// #region agent log
fetch("http://127.0.0.1:7752/ingest/bc9d44cf-fe45-4715-aa75-32f07216a38a",{method:"POST",headers:{"Content-Type":"application/json","X-Debug-Session-Id":"3fe946"},body:JSON.stringify({sessionId:"3fe946",runId:"initial-build-debug",hypothesisId:"H1-H3",location:"frontend/postcss.config.mjs:3",message:"PostCSS module snapshot",data:{cwd:process.cwd(),platform:process.platform,arch:process.arch,tailwindPostcssExists:fs.existsSync("/app/node_modules/@tailwindcss/postcss/package.json"),lightningcssPackageExists:fs.existsSync("/app/node_modules/lightningcss/package.json"),lightningcssLinuxBinaryExists:fs.existsSync("/app/node_modules/lightningcss/node/lightningcss.linux-arm64-musl.node"),lightningcssDarwinBinaryExists:fs.existsSync("/app/node_modules/lightningcss/node/lightningcss.darwin-arm64.node"),lightningcssLinuxPackageExists:fs.existsSync("/app/node_modules/lightningcss-linux-arm64-musl/package.json"),lightningcssDarwinPackageExists:fs.existsSync("/app/node_modules/lightningcss-darwin-arm64/package.json")},timestamp:Date.now()})}).catch(()=>{});
// #endregion

const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
