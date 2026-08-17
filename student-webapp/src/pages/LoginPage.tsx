import { useState, type FormEvent } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import appIcon from '../assets/app-icon.png';

export function LoginPage() {
  const { status, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === 'authenticated') return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const result = await login(email, password);
    setSubmitting(false);
    if (result) setError(result);
  }

  return (
    <div className="centered">
      <div className="auth-card">
        <img src={appIcon} alt="" className="app-icon" />
        <p className="title">Welcome back</p>
        <p className="subtitle">Sign in to continue</p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            inputMode="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="primary" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <Link to="/register">
          <button className="link" type="button">
            New student? Create an account
          </button>
        </Link>
      </div>
    </div>
  );
}
