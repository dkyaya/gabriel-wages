import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const pagesBase = process.env.DASHBOARD_BASE_PATH || "/gabriel-wages/";

export default defineConfig({
  base: pagesBase,
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
