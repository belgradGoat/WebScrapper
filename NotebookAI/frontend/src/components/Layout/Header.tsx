import React from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../stores/authStore';

const Header: React.FC = () => {
  const { user, logout, userDisplayName } = useAuth();

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="glass border-b border-apple-gray-200 px-6 py-4"
    >
      <div className="flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-r from-apple-blue-500 to-apple-blue-600 rounded-apple-sm flex items-center justify-center">
            <span className="text-white font-bold text-sm">🍎</span>
          </div>
          <div>
            <h1 className="text-title3 font-semibold text-apple-gray-900">
              NotebookAI
            </h1>
            <p className="text-caption1 text-apple-gray-500">
              Multi-Modal AI Analysis
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex-1 max-w-md mx-8">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-apple-gray-400">🔍</span>
            </div>
            <input
              type="text"
              placeholder="Search your data..."
              className="apple-input w-full pl-10 pr-4 py-2 text-subhead"
            />
          </div>
        </div>

        {/* User Menu */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button className="p-2 text-apple-gray-600 hover:text-apple-gray-900 transition-colors">
            <span className="text-lg">🔔</span>
          </button>

          {/* User Profile */}
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-subhead font-medium text-apple-gray-900">
                {userDisplayName}
              </p>
              <p className="text-caption1 text-apple-gray-500">
                {user?.email}
              </p>
            </div>
            
            <div className="relative">
              <button className="w-10 h-10 bg-gradient-to-r from-apple-blue-500 to-apple-blue-600 rounded-full flex items-center justify-center text-white font-medium">
                {userDisplayName.charAt(0).toUpperCase()}
              </button>
            </div>

            {/* Logout Button */}
            <button
              onClick={logout}
              className="text-apple-gray-600 hover:text-red-600 transition-colors p-2"
              title="Logout"
            >
              <span className="text-lg">↗️</span>
            </button>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;