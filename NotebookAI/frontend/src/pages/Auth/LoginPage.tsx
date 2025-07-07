import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../stores/authStore';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      await login(email.toLowerCase().trim(), password);
      navigate('/dashboard');
    } catch (error) {
      // Error is already handled in the store
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="text-center mb-8">
        <h2 className="text-title2 font-semibold text-apple-gray-900 mb-2">
          Welcome Back
        </h2>
        <p className="text-subhead text-apple-gray-600">
          Sign in to continue to NotebookAI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Email Field */}
        <div>
          <label
            htmlFor="email"
            className="block text-subhead font-medium text-apple-gray-700 mb-2"
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="apple-input w-full"
            placeholder="Enter your email"
            autoComplete="email"
            disabled={isLoading}
          />
        </div>

        {/* Password Field */}
        <div>
          <label
            htmlFor="password"
            className="block text-subhead font-medium text-apple-gray-700 mb-2"
          >
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="apple-input w-full pr-12"
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-apple-gray-500 hover:text-apple-gray-700"
              disabled={isLoading}
            >
              <span className="text-lg">
                {showPassword ? '🙈' : '👁️'}
              </span>
            </button>
          </div>
        </div>

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between">
          <label className="flex items-center">
            <input
              type="checkbox"
              className="rounded border-apple-gray-300 text-apple-blue-600 focus:ring-apple-blue-500"
              disabled={isLoading}
            />
            <span className="ml-2 text-subhead text-apple-gray-600">
              Remember me
            </span>
          </label>
          <Link
            to="/auth/forgot-password"
            className="text-subhead text-apple-blue-600 hover:text-apple-blue-500"
          >
            Forgot password?
          </Link>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || !email || !password}
          className={`apple-button w-full py-3 ${
            isLoading || !email || !password
              ? 'bg-apple-gray-200 text-apple-gray-500 cursor-not-allowed'
              : 'apple-button-primary'
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Signing in...
            </div>
          ) : (
            'Sign In'
          )}
        </button>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-apple-gray-200" />
          </div>
          <div className="relative flex justify-center text-subhead">
            <span className="px-4 bg-white text-apple-gray-500">
              New to NotebookAI?
            </span>
          </div>
        </div>

        {/* Sign up link */}
        <div className="text-center">
          <Link
            to="/auth/register"
            className="text-subhead text-apple-blue-600 hover:text-apple-blue-500 font-medium"
          >
            Create your account
          </Link>
        </div>
      </form>

      {/* Demo credentials hint */}
      <div className="mt-8 p-4 bg-apple-blue-50 border border-apple-blue-200 rounded-apple">
        <div className="flex items-start">
          <span className="text-apple-blue-600 mr-2">💡</span>
          <div>
            <p className="text-caption1 text-apple-blue-800 font-medium mb-1">
              Demo Access
            </p>
            <p className="text-caption1 text-apple-blue-700">
              Use any email and password to try the demo (authentication will be simulated)
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default LoginPage;