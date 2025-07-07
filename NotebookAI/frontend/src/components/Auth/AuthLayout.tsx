import React from 'react';
import { motion } from 'framer-motion';

interface AuthLayoutProps {
  children: React.ReactNode;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-apple-gray-50 via-white to-apple-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Apple-style branding */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="w-16 h-16 bg-gradient-to-r from-apple-blue-500 to-apple-blue-600 rounded-apple-lg flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl font-bold">🍎</span>
          </div>
          <h1 className="text-title1 font-semibold text-apple-gray-900 mb-2">
            NotebookAI
          </h1>
          <p className="text-subhead text-apple-gray-600">
            Multi-Modal AI Data Analysis Platform
          </p>
        </motion.div>

        {/* Auth form container with Apple-style glass effect */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="apple-card p-8"
        >
          {children}
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-center mt-8"
        >
          <p className="text-caption1 text-apple-gray-500">
            © 2025 NotebookAI. Designed with 🍎 inspiration.
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default AuthLayout;