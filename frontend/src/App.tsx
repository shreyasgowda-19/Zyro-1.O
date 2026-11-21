import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { DemoBanner } from './components/common/DemoBanner';
import { Navbar } from './components/layout/Navbar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { NewPaymentPage } from './pages/NewPaymentPage';
import { PaymentResultPage } from './pages/PaymentResultPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode; roles?: string[] }> = ({ children, roles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center space-y-2">
          <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">Loading session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to={user.role === 'customer' ? '/dashboard' : '/review'} replace />;
  }

  return <>{children}</>;
};

function AppContent() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <DemoBanner />
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute roles={['customer']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review/*"
            element={
              <ProtectedRoute roles={['reviewer', 'supervisor']}>
                <ReviewQueuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pay"
            element={
              <ProtectedRoute roles={['customer']}>
                <NewPaymentPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/payments/:id/result"
            element={
              <ProtectedRoute roles={['customer']}>
                <PaymentResultPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute roles={['customer']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/budgets"
            element={
              <ProtectedRoute roles={['customer']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/learn"
            element={
              <ProtectedRoute roles={['customer']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
