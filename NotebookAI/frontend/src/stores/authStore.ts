import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import toast from 'react-hot-toast';

// Types
interface User {
  id: string;
  email: string;
  full_name?: string;
  display_name: string;
  is_active: boolean;
  is_verified: boolean;
  avatar_url?: string;
  bio?: string;
  preferences?: Record<string, any>;
  usage_stats?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

interface AuthState {
  // State
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  isLoading: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  initializeAuth: () => void;
  updateUser: (userData: Partial<User>) => void;
  clearError: () => void;
}

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Apple-inspired API client
class ApiClient {
  private baseURL: string;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }
  
  async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('🍎 API Request failed:', error);
      throw error;
    }
  }
  
  async post<T>(endpoint: string, data?: any, token?: string): Promise<T> {
    return this.request(endpoint, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async get<T>(endpoint: string, token?: string): Promise<T> {
    return this.request(endpoint, {
      method: 'GET',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });
  }
}

const apiClient = new ApiClient(API_BASE_URL);

// Zustand store with Apple-style state management
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isInitialized: false,
      isLoading: false,

      // Login action with Apple-style UX
      login: async (email: string, password: string) => {
        set({ isLoading: true });
        
        try {
          // Create form data for OAuth2 compatibility
          const formData = new FormData();
          formData.append('username', email);
          formData.append('password', password);
          
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            body: formData,
          });
          
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Login failed');
          }
          
          const data = await response.json();
          
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          toast.success(data.user.message || '🍎 Welcome back to NotebookAI!');
        } catch (error: any) {
          set({ isLoading: false });
          toast.error(error.message || 'Login failed. Please try again.');
          throw error;
        }
      },

      // Register action with Apple-style validation
      register: async (email: string, password: string, fullName?: string) => {
        set({ isLoading: true });
        
        try {
          const response = await apiClient.post('/api/v1/auth/register', {
            email,
            password,
            full_name: fullName,
          });
          
          set({ isLoading: false });
          toast.success('🍎 Registration successful! Please check your email to verify your account.');
        } catch (error: any) {
          set({ isLoading: false });
          toast.error(error.message || 'Registration failed. Please try again.');
          throw error;
        }
      },

      // Logout with Apple-style cleanup
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        });
        
        toast.success('🍎 Logged out successfully');
      },

      // Refresh token for seamless authentication
      refreshToken: async () => {
        const { token } = get();
        
        if (!token) {
          throw new Error('No token available');
        }
        
        try {
          const response = await apiClient.post('/api/v1/auth/refresh', {}, token);
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
          });
        } catch (error: any) {
          // Token refresh failed, logout user
          get().logout();
          throw error;
        }
      },

      // Initialize authentication on app start
      initializeAuth: () => {
        const { token } = get();
        
        if (token) {
          // Verify token validity
          apiClient.get('/api/v1/auth/me', token)
            .then((userData) => {
              set({
                user: userData,
                isAuthenticated: true,
                isInitialized: true,
              });
            })
            .catch(() => {
              // Token is invalid, clear auth state
              set({
                user: null,
                token: null,
                isAuthenticated: false,
                isInitialized: true,
              });
            });
        } else {
          set({ isInitialized: true });
        }
      },

      // Update user data
      updateUser: (userData: Partial<User>) => {
        const { user } = get();
        if (user) {
          set({
            user: { ...user, ...userData },
          });
        }
      },

      // Clear any errors (placeholder for future error handling)
      clearError: () => {
        // Future implementation for error state management
      },
    }),
    {
      name: 'notebookai-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Apple-style auth utilities
export const useAuth = () => {
  const store = useAuthStore();
  
  return {
    ...store,
    isLoggedIn: store.isAuthenticated && !!store.user,
    hasToken: !!store.token,
    userDisplayName: store.user?.display_name || store.user?.email?.split('@')[0] || 'User',
    isVerified: store.user?.is_verified || false,
  };
};

// Token utility for API calls
export const getAuthToken = () => useAuthStore.getState().token;

// API client with auto-injected auth token
export const authenticatedApiClient = {
  get: <T>(endpoint: string) => {
    const token = getAuthToken();
    return apiClient.get<T>(endpoint, token);
  },
  
  post: <T>(endpoint: string, data?: any) => {
    const token = getAuthToken();
    return apiClient.post<T>(endpoint, data, token);
  },
};