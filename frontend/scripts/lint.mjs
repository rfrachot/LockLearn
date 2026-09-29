import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const srcDir = fileURLToPath(new URL("../src", import.meta.url));
const forbidden = [
  [/\bdebugger\b/, "debugger statement"],
  [/\beval\s*\(/, "eval"],
  [/\bnew\s+Function\s*\(/, "dynamic Function constructor"],
  [/\bunsafeHTML\b/, "unsafeHTML renderer"],
  [/\.innerHTML\s*=/, "innerHTML assignment"],
  [/\/\/\s*@ts-ignore\b/, "@ts-ignore suppression"],
];

async function sourceFiles(dir) {
  const files = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await sourceFiles(path)));
    } else if (
      extname(entry.name) === ".ts" &&
      !entry.name.endsWith(".test.ts")
    ) {
      files.push(path);
    }
  }
  return files;
}

let failed = false;
for (const path of await sourceFiles(srcDir)) {
  const source = await readFile(path, "utf8");
  for (const [pattern, label] of forbidden) {
    if (pattern.test(source)) {
      console.error(`${relative(srcDir, path)}: forbidden ${label}`);
      failed = true;
    }
  }
}

if (failed) process.exitCode = 1;
else console.log("Frontend source lint: PASS");
