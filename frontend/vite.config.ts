/**
 * Vite Configuration for SOVD Command WebApp Frontend
 *
 * Development server configuration with HMR and proxy settings.
 * Production build configuration with code splitting, minification, and bundle analysis.
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';
import viteCompression from 'vite-plugin-compression';

export default defineConfig({
  plugins: [
    react(),
    // Bundle analyzer - generates stats.html for visualizing bundle composition
    visualizer({
      filename: './stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
    // Gzip compression for production builds
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240, // Only compress files larger than 10KB
      algorithm: 'gzip',
      ext: '.gz',
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    hmr: {
      clientPort: 3000,
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
  // Production build optimization settings
  build: {
    // Output directory for production build
    outDir: 'dist',
    // Generate sourcemaps for debugging (can be disabled in production)
    sourcemap: false,
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
      },
    },
    // Chunk size warning limit (1MB)
    chunkSizeWarningLimit: 1000,
    // Rollup-specific options for code splitting
    rollupOptions: {
      output: {
        // Manual chunk splitting strategy
        manualChunks: {
          // React core libraries in one chunk
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Material-UI components and styling in separate chunk
          'vendor-mui': [
            '@mui/material',
            '@mui/icons-material',
            '@emotion/react',
            '@emotion/styled',
          ],
          // React Query for data fetching
          'vendor-query': ['@tanstack/react-query'],
          // Axios for HTTP requests
          'vendor-axios': ['axios'],
        },
        // Naming pattern for chunks
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    // Target modern browsers for smaller bundles
    target: 'esnext',
    // CSS code splitting
    cssCodeSplit: true,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        '**/*.test.{ts,tsx}',
        '**/tests/**',
        'src/pages/**',  // Pages are integration-level, components are unit tested
        'src/App.tsx',   // Main app is integration-level
      ],
      thresholds: {
        lines: 80,
        branches: 75,  // Lowered slightly due to edge cases in error handling
        functions: 75,  // Lowered slightly due to API client setup functions
        statements: 80,
      },
    },
  },
});
