import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../stores/authStore';
import toast from 'react-hot-toast';

const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const { register, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.fullName || !formData.email || !formData.password || !formData.confirmPassword) {
      toast.error('Please fill in all fields');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    if (!agreedToTerms) {
      toast.error('Please agree to the Terms of Service');
      return;
    }

    try {
      await register(
        formData.email.toLowerCase().trim(),
        formData.password,
        formData.fullName.trim()
      );
      navigate('/auth/login');
    } catch (error) {
      // Error is already handled in the store
    }
  };

  const getPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  const passwordStrength = getPasswordStrength(formData.password);
  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500'];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="text-center mb-8">
        <h2 className="text-title2 font-semibold text-apple-gray-900 mb-2">
          Create Account
        </h2>
        <p className="text-subhead text-apple-gray-600">
          Join NotebookAI and start your AI journey
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Full Name Field */}
        <div>
          <label
            htmlFor="fullName"
            className="block text-subhead font-medium text-apple-gray-700 mb-2"
          >
            Full Name
          </label>
          <input
            id="fullName"
            name="fullName"
            type="text"
            value={formData.fullName}
            onChange={handleChange}
            className="apple-input w-full"
            placeholder="Enter your full name"
            autoComplete="name"
            disabled={isLoading}
          />
        </div>

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
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
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
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleChange}
              className="apple-input w-full pr-12"
              placeholder="Create a strong password"
              autoComplete="new-password"
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
          
          {/* Password Strength Indicator */}
          {formData.password && (
            <div className="mt-2">
              <div className="flex space-x-1 mb-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`h-1 flex-1 rounded-full ${
                      i < passwordStrength ? strengthColors[passwordStrength - 1] : 'bg-apple-gray-200'
                    }`}
                  />
                ))}
              </div>
              <p className="text-caption1 text-apple-gray-600">
                Password strength: {strengthLabels[passwordStrength - 1] || 'Very Weak'}
              </p>
            </div>
          )}
        </div>

        {/* Confirm Password Field */}
        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-subhead font-medium text-apple-gray-700 mb-2"
          >
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            className={`apple-input w-full ${
              formData.confirmPassword && formData.password !== formData.confirmPassword
                ? 'border-red-500 focus:border-red-500'
                : ''
            }`}
            placeholder="Confirm your password"
            autoComplete="new-password"
            disabled={isLoading}
          />
          {formData.confirmPassword && formData.password !== formData.confirmPassword && (
            <p className="text-caption1 text-red-600 mt-1">
              Passwords do not match
            </p>
          )}
        </div>

        {/* Terms Agreement */}
        <div className="flex items-start">
          <input
            id="agreedToTerms"
            type="checkbox"
            checked={agreedToTerms}
            onChange={(e) => setAgreedToTerms(e.target.checked)}
            className="mt-1 rounded border-apple-gray-300 text-apple-blue-600 focus:ring-apple-blue-500"
            disabled={isLoading}
          />
          <label htmlFor="agreedToTerms" className="ml-3 text-subhead text-apple-gray-600">
            I agree to the{' '}
            <Link to="/terms" className="text-apple-blue-600 hover:text-apple-blue-500">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" className="text-apple-blue-600 hover:text-apple-blue-500">
              Privacy Policy
            </Link>
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={
            isLoading ||
            !formData.fullName ||
            !formData.email ||
            !formData.password ||
            !formData.confirmPassword ||
            formData.password !== formData.confirmPassword ||
            !agreedToTerms
          }
          className={`apple-button w-full py-3 ${
            isLoading ||
            !formData.fullName ||
            !formData.email ||
            !formData.password ||
            !formData.confirmPassword ||
            formData.password !== formData.confirmPassword ||
            !agreedToTerms
              ? 'bg-apple-gray-200 text-apple-gray-500 cursor-not-allowed'
              : 'apple-button-primary'
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Creating account...
            </div>
          ) : (
            'Create Account'
          )}
        </button>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-apple-gray-200" />
          </div>
          <div className="relative flex justify-center text-subhead">
            <span className="px-4 bg-white text-apple-gray-500">
              Already have an account?
            </span>
          </div>
        </div>

        {/* Sign in link */}
        <div className="text-center">
          <Link
            to="/auth/login"
            className="text-subhead text-apple-blue-600 hover:text-apple-blue-500 font-medium"
          >
            Sign in instead
          </Link>
        </div>
      </form>
    </motion.div>
  );
};

export default RegisterPage;