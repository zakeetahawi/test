import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from './theme/ThemeProvider';
import { Layout } from './components/Layout/Layout';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import { useAuth } from './hooks/useAuth';
import ErrorBoundary from './components/error/ErrorBoundary';
import { SnackbarProvider } from './components/core';
import CssBaseline from '@mui/material/CssBaseline';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

// Protected Route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="initial-loading">
        <div style={{ textAlign: 'center' }}>
          <img src="/img/logo.png" alt="شعار النظام" />
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Authentication wrapper for Layout
const ProtectedLayout = () => {
  return (
    <ProtectedRoute>
      <Layout />
    </ProtectedRoute>
  );
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <SnackbarProvider>
            <CssBaseline />
            <Router>
              <ErrorBoundary>
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/dashboard/*" element={<ProtectedLayout />} />
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/404" element={<NotFoundPage />} />
                  <Route path="*" element={<Navigate to="/404" replace />} />
                </Routes>
              </ErrorBoundary>
            </Router>
          </SnackbarProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
