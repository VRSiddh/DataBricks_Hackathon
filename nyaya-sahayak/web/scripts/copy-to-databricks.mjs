import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.join(__dirname, "..");
const outDir = path.join(webRoot, "out");
const target = path.join(webRoot, "..", "databricks", "app", "web_static");

if (!fs.existsSync(outDir)) {
  console.error("Missing out/ — run: npm run build");
  process.exit(1);
}

fs.rmSync(target, { recursive: true, force: true });
fs.cpSync(outDir, target, { recursive: true });
console.log("Copied", outDir, "→", target);
