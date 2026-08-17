import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import appIcon from '../assets/app-icon.png';

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [rollNo, setRollNo] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    setSubmitting(true);
    setError(null);
    const result = await register({ email, fullName, password, rollNo, phone });
    setSubmitting(false);
    if (result) setError(result);
    else setDone(true);
  }

  if (done) {
    return (
      <div className="centered">
        <div className="auth-card">
          <img src={appIcon} alt="" className="app-icon" />
          <p className="title">Account created</p>
          <p className="subtitle">
            Your account is pending admin approval. You can sign in now — face enrollment and
            attendance unlock once approved.
          </p>
          <button className="primary" onClick={() => navigate('/login')}>
            Go to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="centered">
      <div className="auth-card">
        <p className="title">Create account</p>
        <p className="subtitle">Student registration</p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="fullName">Full name</label>
          <input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} required />

          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            inputMode="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label htmlFor="rollNo">Roll number</label>
          <input id="rollNo" value={rollNo} onChange={(e) => setRollNo(e.target.value)} required />

          <label htmlFor="phone">Phone (optional)</label>
          <input id="phone" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />

          <label htmlFor="confirm">Confirm password</label>
          <input
            id="confirm"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />

          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="primary" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create account'}
          </button>
        </form>
        <Link to="/login">
          <button className="link" type="button">
            Already have an account? Sign in
          </button>
        </Link>
      </div>
    </div>
  );
}
