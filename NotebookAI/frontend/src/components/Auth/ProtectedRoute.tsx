import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isInitialized } = useAuth();

  // Show loading while checking auth status
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-apple-gray-50 to-apple-blue-50 flex items-center justify-center">
        <div className="apple-card p-8 text-center">
          <div className="w-8 h-8 border-2 border-apple-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-subhead text-apple-gray-600">
            Loading...
          </p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;