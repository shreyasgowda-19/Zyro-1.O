import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password?: string) => Promise<void>;
  logout: () => void;
  switchAccount: (username: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(sessionStorage.getItem('payguard_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.getMe();
        setUser(me);
      } catch (err) {
        console.error('Failed to authenticate token:', err);
        sessionStorage.removeItem('payguard_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [token]);

  const login = async (username: string, password = 'password123') => {
    setLoading(true);
    try {
      const res = await api.login(username, password);
      sessionStorage.setItem('payguard_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem('payguard_token');
    setToken(null);
    setUser(null);
  };

  const switchAccount = async (username: string) => {
    await login(username, 'password123');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, switchAccount }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
