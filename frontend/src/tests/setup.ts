// filepath: d:\CRMsystem\frontend\src\tests\setup.ts
import { expect, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { server } from './mocks/server';

// محاكاة ResizeObserver لـ Chart.js
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock;

// إعداد خادم المحاكاة
beforeAll(() => {
  console.log('🔶 تهيئة خادم MSW');
  server.listen({ onUnhandledRequest: 'error' });
});

// استعادة المعالجات بين الاختبارات
afterEach(() => {
  cleanup(); // تنظيف @testing-library DOM
  server.resetHandlers();
});

// إغلاق الخادم بعد جميع الاختبارات
afterAll(() => {
  console.log('🔶 إغلاق خادم MSW');
  server.close();
});