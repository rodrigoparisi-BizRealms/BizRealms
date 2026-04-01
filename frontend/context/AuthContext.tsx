import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  email: string;
  name: string;
  onboarding_completed: boolean;
  avatar_color?: string;
  avatar_icon?: string;
  background?: string;
  dream?: string;
  personality?: any;
  money: number;
  experience_points: number;
  level: number;
  location: string;
  skills: any;
  education: any[];
  certifications: any[];
  work_experience: any[];
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('token');
      const storedUser = await AsyncStorage.getItem('user');
      
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/login`, {
        email,
        password
      });

      const { token: newToken, user: newUser } = response.data;
      
      await AsyncStorage.setItem('token', newToken);
      await AsyncStorage.setItem('user', JSON.stringify(newUser));
      
      setToken(newToken);
      setUser(newUser);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Erro ao fazer login');
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const response = await axios.post(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/register`, {
        email,
        password,
        name
      });

      const { token: newToken, user: newUser } = response.data;
      
      await AsyncStorage.setItem('token', newToken);
      await AsyncStorage.setItem('user', JSON.stringify(newUser));
      
      setToken(newToken);
      setUser(newUser);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Erro ao registrar');
    }
  };

  const logout = async () => {
    await AsyncStorage.removeItem('token');
    await AsyncStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${EXPO_PUBLIC_BACKEND_URL}/api/user/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      const updatedUser = response.data;
      await AsyncStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
    } catch (error) {
      console.error('Error refreshing user:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
