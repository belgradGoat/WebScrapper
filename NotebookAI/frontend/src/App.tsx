import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

// Components
import Layout from './components/Layout/Layout';
import AuthLayout from './components/Auth/AuthLayout';
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import DashboardPage from './pages/Dashboard/DashboardPage';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Hooks and stores
import { useAuthStore } from './stores/authStore';

// Apple-inspired loading spinner
const LoadingSpinner = () => (
  <div className="min-h-screen bg-gradient-to-br from-apple-gray-50 to-apple-blue-50 flex items-center justify-center">
    <motion.div
      className="w-8 h-8 border-2 border-apple-blue-500 border-t-transparent rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
    />
  </div>
);

// Apple-inspired error boundary
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('🍎 NotebookAI Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-apple-gray-50 to-apple-blue-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="apple-card max-w-md w-full p-8 text-center"
          >
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">⚠️</span>
            </div>
            <h2 className="text-title2 font-semibold text-apple-gray-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-body text-apple-gray-600 mb-6">
              We're sorry, but something unexpected happened. Please refresh the page and try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="apple-button apple-button-primary w-full"
            >
              Refresh Page
            </button>
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Create React Query client with Apple-style configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        // Apple-style smart retry logic
        if (error?.response?.status === 401) return false;
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Apple-inspired toast configuration
const toastOptions = {
  duration: 4000,
  position: 'top-center' as const,
  style: {
    background: 'rgba(255, 255, 255, 0.8)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '14px',
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
    color: '#1c1917',
    fontSize: '17px',
    fontFamily: '-apple-system, BlinkMacSystemFont, SF Pro Display, sans-serif',
  },
  success: {
    iconTheme: {
      primary: '#10B981',
      secondary: '#FFFFFF',
    },
  },
  error: {
    iconTheme: {
      primary: '#EF4444',
      secondary: '#FFFFFF',
    },
  },
};

function App() {
  const { isInitialized, isAuthenticated, initializeAuth } = useAuthStore();

  // Initialize authentication on app start
  React.useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Show loading spinner while initializing
  if (!isInitialized) {
    return <LoadingSpinner />;
  }

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className="App font-apple antialiased">
            {/* Apple-style gradient background */}
            <div className="fixed inset-0 bg-gradient-to-br from-apple-gray-50 via-white to-apple-blue-50 -z-10" />
            
            <AnimatePresence mode="wait">
              <Routes>
                {/* Authentication Routes */}
                <Route
                  path="/auth/*"
                  element={
                    isAuthenticated ? (
                      <Navigate to="/dashboard" replace />
                    ) : (
                      <AuthLayout>
                        <Routes>
                          <Route path="login" element={<LoginPage />} />
                          <Route path="register" element={<RegisterPage />} />
                          <Route path="*" element={<Navigate to="login" replace />} />
                        </Routes>
                      </AuthLayout>
                    )
                  }
                />

                {/* Protected Dashboard Routes */}
                <Route
                  path="/dashboard/*"
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <Routes>
                          <Route index element={<DashboardPage />} />
                          {/* Add more dashboard routes here as needed */}
                        </Routes>
                      </Layout>
                    </ProtectedRoute>
                  }
                />

                {/* Root redirect */}
                <Route
                  path="/"
                  element={
                    <Navigate
                      to={isAuthenticated ? "/dashboard" : "/auth/login"}
                      replace
                    />
                  }
                />

                {/* Catch all route */}
                <Route
                  path="*"
                  element={
                    <div className="min-h-screen bg-gradient-to-br from-apple-gray-50 to-apple-blue-50 flex items-center justify-center p-4">
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="apple-card max-w-md w-full p-8 text-center"
                      >
                        <div className="w-16 h-16 bg-apple-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                          <span className="text-2xl">🔍</span>
                        </div>
                        <h2 className="text-title2 font-semibold text-apple-gray-900 mb-2">
                          Page Not Found
                        </h2>
                        <p className="text-body text-apple-gray-600 mb-6">
                          The page you're looking for doesn't exist or has been moved.
                        </p>
                        <button
                          onClick={() => window.history.back()}
                          className="apple-button apple-button-primary w-full"
                        >
                          Go Back
                        </button>
                      </motion.div>
                    </div>
                  }
                />
              </Routes>
            </AnimatePresence>

            {/* Apple-style toast notifications */}
            <Toaster
              position="top-center"
              reverseOrder={false}
              gutter={8}
              containerClassName=""
              containerStyle={{}}
              toastOptions={toastOptions}
            />
          </div>
        </Router>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;