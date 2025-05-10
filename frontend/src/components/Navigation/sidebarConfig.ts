// ...existing imports...
import { MonetizationOn, Analytics } from '@mui/icons-material';

export const sidebarItems = [
  // ...existing items...
  {
    title: 'إدارة التسعير',
    items: [
      {
        title: 'قواعد التسعير',
        path: '/pricing/rules',
        icon: MonetizationOn,
        roles: ['admin', 'manager']
      },
      {
        title: 'تحليلات التسعير',
        path: '/pricing/analytics',
        icon: Analytics,
        roles: ['admin', 'manager']
      }
    ]
  },
  // ...existing items...
];