import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { CircularProgress, Box } from '@mui/material';
import PrivateRoute from '@components/core/PrivateRoute';

// تحميل الصفحات باستخدام التحميل الكسول
const Login = lazy(() => import('@pages/Login'));
const Dashboard = lazy(() => import('@pages/Dashboard'));
const Customers = lazy(() => import('@pages/Customers'));
const Inventory = lazy(() => import('@pages/Inventory'));
const Orders = lazy(() => import('@pages/Orders'));
const Factory = lazy(() => import('@pages/Factory'));
const Inspections = lazy(() => import('@pages/Inspections'));
const Installations = lazy(() => import('@pages/Installations'));
const Reports = lazy(() => import('@pages/Reports'));
const Settings = lazy(() => import('@pages/Settings'));

// مكون التحميل
const LoadingScreen = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
    <CircularProgress />
  </Box>
);

const AppRoutes = () => {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        {/* صفحة تسجيل الدخول - غير محمية */}
        <Route path="/login" element={<Login />} />

        {/* المسارات المحمية */}
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/customers/*"
          element={
            <PrivateRoute>
              <Customers />
            </PrivateRoute>
          }
        />
        <Route
          path="/inventory/*"
          element={
            <PrivateRoute>
              <Inventory />
            </PrivateRoute>
          }
        />
        <Route
          path="/orders/*"
          element={
            <PrivateRoute>
              <Orders />
            </PrivateRoute>
          }
        />
        <Route
          path="/factory/*"
          element={
            <PrivateRoute>
              <Factory />
            </PrivateRoute>
          }
        />
        <Route
          path="/inspections/*"
          element={
            <PrivateRoute>
              <Inspections />
            </PrivateRoute>
          }
        />
        <Route
          path="/installations/*"
          element={
            <PrivateRoute>
              <Installations />
            </PrivateRoute>
          }
        />
        <Route
          path="/reports/*"
          element={
            <PrivateRoute>
              <Reports />
            </PrivateRoute>
          }
        />
        <Route
          path="/settings/*"
          element={
            <PrivateRoute>
              <Settings />
            </PrivateRoute>
          }
        />

        {/* إعادة التوجيه للمسارات غير الموجودة */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;