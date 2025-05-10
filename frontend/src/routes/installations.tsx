import React from 'react';
import { RouteObject } from 'react-router-dom';
import { lazy } from 'react';

const InstallationPage = lazy(() => import('../pages/installations/InstallationPage'));

const installationRoutes: RouteObject[] = [
  {
    path: 'installations/:id',
    element: <InstallationPage />,
  }
];

export default installationRoutes;
