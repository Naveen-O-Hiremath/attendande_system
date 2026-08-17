import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import appIcon from '../assets/app-icon.png';

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <img src={appIcon} alt="" />
          <span>Attendance</span>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/enrollments" className={({ isActive }) => (isActive ? 'active' : '')}>
            Face Enrollments
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12, margin: '0 0 8px' }}>
            {user?.full_name}
          </p>
          <button onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
