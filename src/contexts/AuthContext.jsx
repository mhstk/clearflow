import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const response = await authAPI.me();
          setUser(response.data);
        } catch (err) {
          localStorage.removeItem('auth_token');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    setError(null);
    try {
      const response = await authAPI.login({ email, password });
      const { user, token } = response.data;
      localStorage.setItem('auth_token', token.access_token);
      setUser(user);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed. Please try again.';
      setError(message);
      return { success: false, error: message };
    }
  };

  const signup = async (email, password, name) => {
    setError(null);
    try {
      const response = await authAPI.signup({ email, password, name });
      const { user, token } = response.data;
      localStorage.setItem('auth_token', token.access_token);
      setUser(user);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Signup failed. Please try again.';
      setError(message);
      return { success: false, error: message };
    }
  };

  const loginWithGoogle = async (code) => {
    setError(null);
    try {
      const response = await authAPI.googleAuth({ code });
      const { user, token } = response.data;
      localStorage.setItem('auth_token', token.access_token);
      setUser(user);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Google login failed. Please try again.';
      setError(message);
      return { success: false, error: message };
    }
  };

  const getGoogleAuthUrl = async () => {
    try {
      const response = await authAPI.getGoogleUrl();
      return response.data.url;
    } catch (err) {
      return null;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
    setError(null);
  };

  const clearError = () => setError(null);

  const value = {
    user,
    loading,
    error,
    login,
    signup,
    loginWithGoogle,
    getGoogleAuthUrl,
    logout,
    clearError,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
