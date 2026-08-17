import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, ApiError } from '../api/client';
import type { AppUser } from '../api/types';

interface AuthState {
  status: 'unknown' | 'authenticated' | 'unauthenticated';
  user: AppUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<string | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = 'attendance_admin_access_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthState['status']>('unknown');
  const [user, setUser] = useState<AppUser | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));

  useEffect(() => {
    if (!token) {
      setStatus('unauthenticated');
      return;
    }
    api
      .get<AppUser>('/auth/me', token)
      .then((me) => {
        if (me.role !== 'admin' && me.role !== 'super_admin') {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
          setStatus('unauthenticated');
          return;
        }
        setUser(me);
        setStatus('authenticated');
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setStatus('unauthenticated');
      });
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const tokens = await api.post<{ access_token: string }>('/auth/login', { email, password });
      const me = await api.get<AppUser>('/auth/me', tokens.access_token);
      if (me.role !== 'admin' && me.role !== 'super_admin') {
        return 'This account does not have admin access.';
      }
      localStorage.setItem(TOKEN_KEY, tokens.access_token);
      setToken(tokens.access_token);
      setUser(me);
      setStatus('authenticated');
      return null;
    } catch (err) {
      return err instanceof ApiError ? err.message : 'Could not reach the server.';
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  return (
    <AuthContext.Provider value={{ status, user, token, login, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
