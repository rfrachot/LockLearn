import { gzipSync } from "node:zlib";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const budgetBytes = 500 * 1024;
const bundleUrl = new URL(
  "../../custom_components/locklearn/frontend/locklearn-panel.js",
  import.meta.url,
);
const bundle = await readFile(fileURLToPath(bundleUrl));
const gzipBytes = gzipSync(bundle, { level: 9 }).byteLength;

console.log(`LockLearn initial panel bundle: ${bundle.byteLength} bytes raw / ${gzipBytes} bytes gzip`);
console.log(`Budget: ${budgetBytes} bytes gzip (500 KiB)`);

if (gzipBytes >= budgetBytes) {
  console.error(
    `Bundle budget exceeded by ${gzipBytes - budgetBytes} bytes (gzip)`,
  );
  process.exitCode = 1;
}
