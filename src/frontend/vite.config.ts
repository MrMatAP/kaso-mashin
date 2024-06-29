/// <reference types="vitest"/>

// Plugins
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";
import { quasar, transformAssetUrls } from "@quasar/vite-plugin";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls },
    }),
    quasar({
      sassVariables: "src/quasar-variables.sass",
    }),
  ],
  define: { "process.env": {} },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
    extensions: [".js", ".json", ".jsx", ".mjs", ".ts", ".tsx", ".vue"],
  },
  test: {
    globals: true,
    environment: "happy-dom",
    coverage: {
      provider: "istanbul",
      include: ["src"],
      reporter: [
        ["lcov", { file: "frontend.lcov", projectRoot: "./src" }],
        ["json", { file: "frontend.json" }],
        ["text"],
      ],
      reportsDirectory: "../../build/frontend/",
      clean: true,
    },
    reporters: ["default", "junit"],
    outputFile: {
      junit: "../../build/frontend/junit.xml",
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api/notifications": {
        target: "ws://localhost:8000",
        ws: true,
      },
      "/api": "http://localhost:8000",
    },
  },
});
