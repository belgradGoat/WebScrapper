import React from 'react';
import { motion } from 'framer-motion';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-apple-gray-50 via-white to-apple-blue-50">
      {/* Apple-style grid layout for three panels */}
      <div className="grid grid-cols-apple-3-panel h-screen apple-lg:grid-cols-apple-mobile">
        
        {/* Left Panel - Data Upload Section */}
        <motion.aside
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="glass border-r border-apple-gray-200 overflow-hidden flex flex-col"
        >
          <div className="p-6">
            <h2 className="text-title2 font-semibold text-apple-gray-900 mb-4">
              📁 Data Sources
            </h2>
            <p className="text-subhead text-apple-gray-600 mb-6">
              Upload files, add URLs, or paste text to get started with AI analysis.
            </p>
          </div>
          
          <div className="flex-1 px-6 pb-6 overflow-y-auto">
            {/* Upload component will be rendered here */}
            <div className="apple-card p-6 text-center">
              <div className="w-16 h-16 bg-apple-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⬆️</span>
              </div>
              <h3 className="text-headline font-semibold text-apple-gray-900 mb-2">
                Upload Your Data
              </h3>
              <p className="text-subhead text-apple-gray-600 mb-4">
                Drag & drop files or click to browse
              </p>
              <button className="apple-button apple-button-primary">
                Choose Files
              </button>
            </div>
          </div>
        </motion.aside>

        {/* Middle Panel - AI Chat Interface */}
        <motion.main
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="flex flex-col overflow-hidden"
        >
          <Header />
          
          <div className="flex-1 flex flex-col overflow-hidden">
            {children}
          </div>
        </motion.main>

        {/* Right Panel - Analytics & Settings */}
        <motion.aside
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="glass border-l border-apple-gray-200 overflow-hidden flex flex-col apple-lg:hidden"
        >
          <div className="p-6">
            <h2 className="text-title2 font-semibold text-apple-gray-900 mb-4">
              📊 Analytics
            </h2>
            <p className="text-subhead text-apple-gray-600 mb-6">
              Data insights, settings, and system information.
            </p>
          </div>
          
          <div className="flex-1 px-6 pb-6 overflow-y-auto space-y-6">
            {/* Analytics widgets */}
            <div className="apple-card p-4">
              <h3 className="text-headline font-semibold text-apple-gray-900 mb-3">
                Data Overview
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-subhead text-apple-gray-600">Files</span>
                  <span className="text-subhead font-semibold">0</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-subhead text-apple-gray-600">Queries</span>
                  <span className="text-subhead font-semibold">0</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-subhead text-apple-gray-600">Storage</span>
                  <span className="text-subhead font-semibold">0 MB</span>
                </div>
              </div>
            </div>

            <div className="apple-card p-4">
              <h3 className="text-headline font-semibold text-apple-gray-900 mb-3">
                AI Settings
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-subhead text-apple-gray-600 mb-1">
                    Model
                  </label>
                  <select className="apple-input w-full text-sm">
                    <option>GPT-4</option>
                    <option>GPT-3.5 Turbo</option>
                    <option>Claude</option>
                  </select>
                </div>
                <div>
                  <label className="block text-subhead text-apple-gray-600 mb-1">
                    Temperature
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    defaultValue="0.7"
                    className="w-full"
                  />
                  <div className="flex justify-between text-caption1 text-apple-gray-500 mt-1">
                    <span>Precise</span>
                    <span>Creative</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="apple-card p-4">
              <h3 className="text-headline font-semibold text-apple-gray-900 mb-3">
                System Status
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-subhead text-apple-gray-600">API</span>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-caption1 text-apple-gray-500">Online</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-subhead text-apple-gray-600">Database</span>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-caption1 text-apple-gray-500">Connected</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-subhead text-apple-gray-600">AI Service</span>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-caption1 text-apple-gray-500">Ready</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.aside>
      </div>
    </div>
  );
};

export default Layout;