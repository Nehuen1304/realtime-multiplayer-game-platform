import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect functionality with all the matchers from jest-dom
expect.extend(matchers);

// Run a cleanup function after each test case
afterEach(() => {
  cleanup();
});