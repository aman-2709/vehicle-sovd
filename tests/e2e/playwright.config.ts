import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration for SOVD Application
 *
 * This configuration enables testing across multiple browsers with automatic
 * screenshot capture on failure and proper timeout settings for WebSocket tests.
 */
export default defineConfig({
  // Test directory configuration
  testDir: './specs',

  // Maximum time one test can run for
  timeout: 60 * 1000,

  // Maximum time for each assertion
  expect: {
    timeout: 10 * 1000,
  },

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure for debugging
    screenshot: 'only-on-failure',

    // Video on failure for debugging
    video: 'retain-on-failure',

    // Maximum time for actions like click, fill, etc.
    actionTimeout: 15 * 1000,

    // Maximum time for navigation
    navigationTimeout: 30 * 1000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 },
      },
    },

    // Optionally add webkit if needed
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Output folder for test artifacts
  outputDir: 'test-results/artifacts',

  // Folder for test screenshots
  snapshotDir: 'test-results/screenshots',

  // Run your local dev server before starting the tests
  // Note: In our setup, services are started via docker-compose in the Makefile
  // so we don't use webServer here
  webServer: undefined,
});
