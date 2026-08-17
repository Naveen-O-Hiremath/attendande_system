import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth();

  if (status === 'unknown') {
    return (
      <div className="centered-page">
        <div className="spinner" />
      </div>
    );
  }
  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
