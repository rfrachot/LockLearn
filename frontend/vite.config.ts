import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: fileURLToPath(new URL("./src/locklearn-panel.ts", import.meta.url)),
      formats: ["es"],
      fileName: () => "locklearn-panel.js",
    },
    outDir: fileURLToPath(new URL("../custom_components/locklearn/frontend", import.meta.url)),
    emptyOutDir: false,
  },
});
