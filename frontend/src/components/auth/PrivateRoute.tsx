import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/auth.service';

export const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  const location = useLocation();
  const user = authService.getCurrentUser();

  if (!user?.access) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};