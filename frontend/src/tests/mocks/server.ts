// filepath: d:\CRMsystem\frontend\src\tests\mocks\server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// إنشاء خادم MSW باستخدام المعالجات المعرفة مسبقاً
export const server = setupServer(...handlers);