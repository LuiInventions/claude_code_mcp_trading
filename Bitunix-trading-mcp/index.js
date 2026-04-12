const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const scriptDir = __dirname;
const mainPy = path.join(scriptDir, "main.py");

// Load .env if it exists in the script directory
try {
  const envPath = path.join(scriptDir, ".env");
  if (fs.existsSync(envPath)) {
    const envConfig = fs.readFileSync(envPath, "utf8");
    envConfig.split("\n").forEach((line) => {
      const parts = line.split("=");
      if (parts.length === 2) {
        process.env[parts[0].trim()] = parts[1].trim();
      }
    });
  }
} catch (err) {
  process.stderr.write(`Warning: Could not load .env file: ${err.message}\n`);
}

// Find python executable
const pythonCandidates = [
  "python3",
  "python",
  "py",
];

let pythonExe = "python";
for (const candidate of pythonCandidates) {
  try {
    // We check if the command exists by trying to run it
    const { execSync } = require("child_process");
    execSync(`${candidate} --version`, { stdio: "ignore" });
    pythonExe = candidate;
    break;
  } catch {}
}

process.stderr.write(`Python: ${pythonExe}\n`);
process.stderr.write(`Script: ${mainPy}\n`);

const child = spawn(pythonExe, [mainPy], {
  cwd: scriptDir,
  env: {
    ...process.env,
  },
  stdio: ["pipe", "pipe", "pipe"],
});

process.stderr.write(`Python PID: ${child.pid}\n`);

child.stdout.on("data", (data) => {
  process.stdout.write(data);
});

process.stdin.on("data", (data) => {
  child.stdin.write(data);
});

child.stderr.on("data", (data) => {
  process.stderr.write(data);
});

child.on("close", (code) => {
  process.exit(code ?? 0);
});

process.on("exit", () => {
  child.kill();
});
