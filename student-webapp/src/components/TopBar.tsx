import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import appIcon from '../assets/app-icon.png';

export function TopBar({ title }: { title: string }) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="topbar">
      <div className="brand" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
        <img src={appIcon} alt="" />
        {title}
      </div>
      <button onClick={logout}>Sign out</button>
    </div>
  );
}
