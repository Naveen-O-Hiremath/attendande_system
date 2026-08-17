import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, ApiError } from '../api/client';
import type { AppUser } from '../api/types';

interface AuthState {
  status: 'unknown' | 'authenticated' | 'unauthenticated';
  user: AppUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<string | null>;
  register: (input: {
    email: string;
    fullName: string;
    password: string;
    rollNo: string;
    phone?: string;
  }) => Promise<string | null>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);
const TOKEN_KEY = 'attendance_student_access_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthState['status']>('unknown');
  const [user, setUser] = useState<AppUser | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));

  const loadMe = useCallback(async (t: string) => {
    const me = await api.get<AppUser>('/auth/me', t);
    setUser(me);
    setStatus('authenticated');
  }, []);

  useEffect(() => {
    if (!token) {
      setStatus('unauthenticated');
      return;
    }
    loadMe(token).catch(() => {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setStatus('unauthenticated');
    });
  }, [token, loadMe]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const tokens = await api.post<{ access_token: string }>('/auth/login', { email, password });
      localStorage.setItem(TOKEN_KEY, tokens.access_token);
      setToken(tokens.access_token);
      await loadMe(tokens.access_token);
      return null;
    } catch (err) {
      return err instanceof ApiError ? err.message : 'Could not reach the server.';
    }
  }, [loadMe]);

  const register = useCallback(
    async (input: { email: string; fullName: string; password: string; rollNo: string; phone?: string }) => {
      try {
        await api.post('/auth/register', {
          email: input.email,
          full_name: input.fullName,
          password: input.password,
          roll_no: input.rollNo,
          ...(input.phone ? { phone: input.phone } : {}),
        });
        return null;
      } catch (err) {
        return err instanceof ApiError ? err.message : 'Could not reach the server.';
      }
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  const refreshUser = useCallback(async () => {
    if (token) await loadMe(token);
  }, [token, loadMe]);

  return (
    <AuthContext.Provider value={{ status, user, token, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
