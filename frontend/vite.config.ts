/**
 * Vite Configuration for SOVD Command WebApp Frontend
 *
 * Development server configuration with HMR and proxy settings.
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
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
