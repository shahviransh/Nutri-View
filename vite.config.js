import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { visualizer } from 'rollup-plugin-visualizer';

// https://vitejs.dev/config/
export default defineConfig(async () => ({
  plugins: [vue(), visualizer({
    filename: 'dist/stats.html',
    template: 'treemap',
    gzipSize: true,
    brotliSize: true,
  })],

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,

  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
  },

  // Add the base and build configuration for Electron/Tauri
  envPrefix: ['VITE_', 'TAURI_ENV_*'],
  // Use relative paths for Tauri, absolute for IIS
  base: "./",  // Ensure assets are loaded relatively
  // // For Electron
  // build: {
  //   outDir: 'dist',  // Output folder for the build
  //   rollupOptions: {
  //     input: 'index.html',
  //   },
  // For Tauri
  build: {
    outDir: "dist",
    // Tauri uses Chromium on Windows and WebKit on macOS and Linux
    target:
      process.env.TAURI_ENV_PLATFORM == 'windows'
        ? 'chrome105'
        : 'safari13',
    // don't minify for debug builds
    minify: process.env.TAURI_ENV_DEBUG ? false : 'esbuild',
    // produce sourcemaps for debug builds
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },
}));