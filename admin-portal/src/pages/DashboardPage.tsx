import { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { FaceEnrollment } from '../api/types';

export function DashboardPage() {
  const { token } = useAuth();
  const [counts, setCounts] = useState<{ pending: number; approved: number; rejected: number } | null>(
    null,
  );

  useEffect(() => {
    if (!token) return;
    Promise.all([
      api.get<FaceEnrollment[]>('/face-enrollments?status=pending&limit=200', token),
      api.get<FaceEnrollment[]>('/face-enrollments?status=approved&limit=200', token),
      api.get<FaceEnrollment[]>('/face-enrollments?status=rejected&limit=200', token),
    ]).then(([pending, approved, rejected]) => {
      setCounts({ pending: pending.length, approved: approved.length, rejected: rejected.length });
    });
  }, [token]);

  return (
    <Layout>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Overview of face enrollment activity</p>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="value">{counts?.pending ?? '—'}</div>
          <div className="label">Pending approvals</div>
        </div>
        <div className="stat-card">
          <div className="value">{counts?.approved ?? '—'}</div>
          <div className="label">Approved enrollments</div>
        </div>
        <div className="stat-card">
          <div className="value">{counts?.rejected ?? '—'}</div>
          <div className="label">Rejected submissions</div>
        </div>
      </div>

      {counts && counts.pending > 0 && (
        <div className="card">
          <div className="enrollment-row">
            <div className="enrollment-meta">
              <strong>{counts.pending}</strong> face enrollment{counts.pending === 1 ? '' : 's'} waiting for
              review. Head to <em>Face Enrollments</em> to approve or reject them.
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
