/**
 * Lighthouse CI Configuration
 *
 * Defines performance budgets and assertions for automated performance testing.
 * Runs on every commit via GitHub Actions to ensure performance standards are met.
 */

module.exports = {
  ci: {
    collect: {
      // Directory containing the production build
      staticDistDir: './frontend/dist',
      // Number of runs to average (more runs = more reliable results)
      numberOfRuns: 3,
      // URLs to test
      url: ['http://localhost/'],
    },
    assert: {
      // Use Lighthouse recommended preset as baseline
      preset: 'lighthouse:recommended',
      // Custom performance assertions
      assertions: {
        // Performance category score must be >= 90
        'categories:performance': ['error', { minScore: 0.9 }],
        // First Contentful Paint must be <= 1.5 seconds (1500ms)
        'first-contentful-paint': ['error', { maxNumericValue: 1500 }],
        // Time to Interactive must be <= 3 seconds (3000ms)
        'interactive': ['error', { maxNumericValue: 3000 }],
        // Largest Contentful Paint should be <= 2.5 seconds
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        // Total Blocking Time should be minimal (<200ms)
        'total-blocking-time': ['warn', { maxNumericValue: 200 }],
        // Cumulative Layout Shift should be minimal (<0.1)
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        // Speed Index should be <= 3.4 seconds
        'speed-index': ['warn', { maxNumericValue: 3400 }],
        // Resource budgets
        'resource-summary:script:size': ['warn', { maxNumericValue: 500000 }], // 500KB main chunk
        'resource-summary:total:size': ['warn', { maxNumericValue: 2000000 }], // 2MB total
        // Best practices
        'uses-text-compression': 'error',
        'uses-responsive-images': 'warn',
        'offscreen-images': 'warn',
        'render-blocking-resources': 'warn',
      },
    },
    upload: {
      // Store results as GitHub Action artifacts (no external server needed)
      target: 'temporary-public-storage',
    },
  },
};
