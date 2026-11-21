import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { Navbar } from './components/layout/Navbar';
import { CustomerLoginPage } from './pages/CustomerLoginPage';
import { BankingLoginPage } from './pages/BankingLoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { NewPaymentPage } from './pages/NewPaymentPage';
import { PaymentResultPage } from './pages/PaymentResultPage';
import { BudgetsPage } from './pages/BudgetsPage';
import { LearnPage } from './pages/LearnPage';

const AccessDenied: React.FC<{ userRole: string }> = ({ userRole }) => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const isCustomerAttemptingStaff = userRole === 'customer';

  return (
    <div className="min-h-[calc(100vh-80px)] flex items-center justify-center bg-slate-900 px-4 py-12">
      <div className="max-w-md w-full bg-slate-800 border border-rose-500/40 rounded-2xl p-8 text-center shadow-2xl">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-5">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">
          {isCustomerAttemptingStaff ? 'Restricted Bank Operations Area' : 'Customer Banking Area Restricted'}
        </h2>
        <p className="text-xs text-slate-300 mb-6 leading-relaxed">
          {isCustomerAttemptingStaff ? (
            <>
              Access Denied: The <strong>Banking Operations Portal</strong> is strictly restricted to authorized bank officers and compliance managers. Customer accounts cannot enter or inspect internal clearance queues.
            </>
          ) : (
            <>
              Bank operations officers and compliance managers cannot access customer personal banking dashboards to preserve separation of duties.
            </>
          )}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => navigate(userRole === 'customer' ? '/dashboard' : '/review')}
            className="px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold transition"
          >
            {userRole === 'customer' ? '← Return to My Dashboard' : '← Return to Bank Portal'}
          </button>
          <button
            onClick={() => {
              logout();
              navigate(isCustomerAttemptingStaff ? '/login/banking' : '/login/customer');
            }}
            className="px-4 py-2.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-medium transition"
          >
            {isCustomerAttemptingStaff ? 'Sign in to Banking Portal →' : 'Sign in as Customer →'}
          </button>
        </div>
      </div>
    </div>
  );
};

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
    return <AccessDenied userRole={user.role} />;
  }

  return <>{children}</>;
};

function AppContent() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/login" element={<Navigate to="/login/customer" replace />} />
          <Route path="/login/customer" element={<CustomerLoginPage />} />
          <Route path="/login/banking" element={<BankingLoginPage />} />
          <Route path="/login/bank" element={<Navigate to="/login/banking" replace />} />
          <Route path="/login/reviewer" element={<Navigate to="/login/banking" replace />} />
          <Route path="/login/supervisor" element={<Navigate to="/login/banking" replace />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute roles={['customer']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/banking"
            element={
              <ProtectedRoute roles={['reviewer', 'supervisor']}>
                <ReviewQueuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/banking/*"
            element={
              <ProtectedRoute roles={['reviewer', 'supervisor']}>
                <ReviewQueuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute roles={['reviewer', 'supervisor']}>
                <ReviewQueuePage />
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
                <BudgetsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/learn"
            element={
              <ProtectedRoute roles={['customer']}>
                <LearnPage />
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
        <LanguageProvider>
          <AppContent />
        </LanguageProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
