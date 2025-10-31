/**
 * SOVD Command WebApp - Main Application Component
 *
 * Root component with React Router route definitions.
 * Implements code splitting with React.lazy() for improved performance.
 */

import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/common/Layout';
import LoadingSpinner from './components/common/LoadingSpinner';
import LoginPage from './pages/LoginPage';

// Code splitting: lazy load page components to reduce initial bundle size
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));
const VehiclesPage = React.lazy(() => import('./pages/VehiclesPage'));
const CommandPage = React.lazy(() => import('./pages/CommandPage'));
const HistoryPage = React.lazy(() => import('./pages/HistoryPage'));
const CommandDetailPage = React.lazy(() => import('./pages/CommandDetailPage'));

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  // Don't render routes until auth state is determined
  if (isLoading) {
    return null;
  }

  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        {/* Root path redirects based on authentication */}
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
          }
        />

        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes with lazy-loaded page components */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/vehicles"
          element={
            <ProtectedRoute>
              <Layout>
                <VehiclesPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/commands"
          element={
            <ProtectedRoute>
              <Layout>
                <CommandPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <Layout>
                <HistoryPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/commands/:commandId"
          element={
            <ProtectedRoute>
              <Layout>
                <CommandDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};

export default App;
