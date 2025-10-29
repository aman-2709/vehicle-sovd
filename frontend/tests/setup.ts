/**
 * Vitest Test Setup
 *
 * Global test configuration and setup for React Testing Library.
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Suppress React Router future flag warnings in tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.error = (...args: unknown[]) => {
  const message = String(args[0]);
  if (
    message.includes('React Router Future Flag Warning') ||
    message.includes('v7_startTransition') ||
    message.includes('v7_relativeSplatPath')
  ) {
    return; // Suppress these specific warnings
  }
  originalConsoleError(...args);
};

console.warn = (...args: unknown[]) => {
  const message = String(args[0]);
  if (
    message.includes('React Router Future Flag Warning') ||
    message.includes('v7_startTransition') ||
    message.includes('v7_relativeSplatPath')
  ) {
    return; // Suppress these specific warnings
  }
  originalConsoleWarn(...args);
};

// Cleanup after each test
afterEach(() => {
  cleanup();
});
