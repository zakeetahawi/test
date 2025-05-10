// filepath: d:\CRMsystem\frontend\src\tests\setupIntegrationTests.ts
import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// إعداد محاكاة الخادم قبل الاختبارات
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// إعادة تعيين المعالجات بين الاختبارات
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// إيقاف الخادم بعد الاختبارات
afterAll(() => server.close());

// إسكات تحذيرات React Query
const originalConsoleError = console.error;
console.error = (...args: any[]) => {
  if (
    args[0]?.includes?.('Warning: An update to') ||
    args[0]?.includes?.('[React Query]')
  ) {
    return;
  }
  originalConsoleError(...args);
};

// إعداد Jest mock للmatch media
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// إعداد محاكاة localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// إعداد ترجمة i18next الوهمية
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      changeLanguage: vi.fn()
    }
  })
}));