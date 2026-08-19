import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TopBar } from '../components/TopBar';
import { AnnouncementFeed } from '../components/AnnouncementFeed';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import type { FaceEnrollment } from '../api/types';

const STATUS_LABEL: Record<string, string> = {
  pending: 'Pending review',
  approved: 'Approved',
  rejected: 'Rejected',
  resubmission_requested: 'Resubmission requested',
};

export function HomePage() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [enrollment, setEnrollment] = useState<FaceEnrollment | null | undefined>(undefined);

  useEffect(() => {
    if (user?.role !== 'student' || !token) return;
    api.get<FaceEnrollment | null>('/face-enrollments/me', token).then(setEnrollment);
  }, [user, token]);

  if (!user) return null;

  return (
    <div className="screen">
      <TopBar title="Attendance" />
      <div className="content">
        <div className="profile-card">
          <div className="avatar">{user.full_name[0]?.toUpperCase() ?? '?'}</div>
          <div>
            <div style={{ fontWeight: 700 }}>{user.full_name}</div>
            <div style={{ color: 'var(--gray-500)', fontSize: 13 }}>{user.email}</div>
            <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
              <span className="badge" style={{ background: 'var(--purple-light)', color: 'var(--purple)' }}>
                {user.role}
              </span>
              <span className={`badge ${user.status}`}>{user.status}</span>
            </div>
          </div>
        </div>

        {user.role === 'student' && (
          <div className="card">
            <h3>Face enrollment</h3>
            {enrollment === undefined ? (
              <p>Loading…</p>
            ) : enrollment === null ? (
              <>
                <p>You haven't submitted a face enrollment yet.</p>
                <button className="primary" onClick={() => navigate('/enroll')}>
                  Start enrollment
                </button>
              </>
            ) : enrollment.status === 'pending' ? (
              <>
                <p>
                  <span className="badge pending">{STATUS_LABEL.pending}</span>
                </p>
                <p>Submitted {new Date(enrollment.created_at).toLocaleString()}. An admin will review it soon.</p>
              </>
            ) : enrollment.status === 'approved' ? (
              <>
                <p>
                  <span className="badge approved">{STATUS_LABEL.approved}</span>
                </p>
                <p>You're all set. Mark attendance any time.</p>
                <button className="primary" onClick={() => navigate('/attendance')}>
                  Mark attendance
                </button>
              </>
            ) : (
              <>
                <p>
                  <span className={`badge ${enrollment.status}`}>{STATUS_LABEL[enrollment.status]}</span>
                </p>
                {enrollment.rejection_reason && <p>"{enrollment.rejection_reason}"</p>}
                <button className="primary" onClick={() => navigate('/enroll')}>
                  Resubmit
                </button>
              </>
            )}
          </div>
        )}

        <AnnouncementFeed />
      </div>
    </div>
  );
}
