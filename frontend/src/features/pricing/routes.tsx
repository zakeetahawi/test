import React from 'react';
import { RouteObject } from 'react-router-dom';
import { DynamicPricingPage } from './DynamicPricingPage';
import { PricingAnalytics } from './PricingAnalytics';
import { ProtectedRoute } from '../../components/Auth/ProtectedRoute';

export const pricingRoutes: RouteObject[] = [
  {
    path: 'pricing',
    children: [
      {
        path: 'rules',
        element: (
          <ProtectedRoute roles={['admin', 'manager']}>
            <DynamicPricingPage />
          </ProtectedRoute>
        )
      },
      {
        path: 'analytics',
        element: (
          <ProtectedRoute roles={['admin', 'manager']}>
            <PricingAnalytics />
          </ProtectedRoute>
        )
      }
    ]
  }
];