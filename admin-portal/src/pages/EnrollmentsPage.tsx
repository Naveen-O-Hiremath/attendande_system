import { useCallback, useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { AuthImage } from '../components/AuthImage';
import { api, ApiError } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { EnrollmentStatus, FaceEnrollment } from '../api/types';

const FILTERS: { label: string; value: EnrollmentStatus | 'all' }[] = [
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Resubmission requested', value: 'resubmission_requested' },
  { label: 'All', value: 'all' },
];

const STATUS_LABEL: Record<EnrollmentStatus, string> = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  resubmission_requested: 'Resubmission requested',
};

type ModalMode = { enrollmentId: string; action: 'reject' | 'request-resubmission' } | null;

export function EnrollmentsPage() {
  const { token } = useAuth();
  const [filter, setFilter] = useState<EnrollmentStatus | 'all'>('pending');
  const [enrollments, setEnrollments] = useState<FaceEnrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalMode>(null);
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams({ limit: '100' });
    if (filter !== 'all') params.set('status', filter);
    api
      .get<FaceEnrollment[]>(`/face-enrollments?${params.toString()}`, token)
      .then(setEnrollments)
      .finally(() => setLoading(false));
  }, [token, filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleApprove(id: string) {
    if (!token) return;
    setBusyId(id);
    setError(null);
    try {
      await api.post(`/face-enrollments/${id}/approve`, undefined, token);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Approval failed.');
    } finally {
      setBusyId(null);
    }
  }

  async function submitModal() {
    if (!token || !modal) return;
    setBusyId(modal.enrollmentId);
    setError(null);
    try {
      await api.post(`/face-enrollments/${modal.enrollmentId}/${modal.action}`, { reason }, token);
      setModal(null);
      setReason('');
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed.');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Layout>
      <h1 className="page-title">Face Enrollments</h1>
      <p className="page-subtitle">Review submitted face captures before they become trusted for attendance</p>

      <div className="filter-bar">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            className={filter === f.value ? 'active' : ''}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <p className="error-text" style={{ textAlign: 'left' }}>{error}</p>}

      <div className="card">
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : enrollments.length === 0 ? (
          <div className="empty-state">No enrollments in this category.</div>
        ) : (
          enrollments.map((enrollment) => (
            <div className="enrollment-row" key={enrollment.id}>
              <div className="enrollment-images">
                {enrollment.image_urls.map((url) => (
                  <AuthImage key={url} src={url} alt="Face capture" />
                ))}
              </div>
              <div className="enrollment-meta">
                <span className={`badge ${enrollment.status}`}>{STATUS_LABEL[enrollment.status]}</span>
                <div className="id">student: {enrollment.student_id}</div>
                <div className="date">
                  Submitted {new Date(enrollment.created_at).toLocaleString()}
                  {enrollment.rejection_reason ? ` — "${enrollment.rejection_reason}"` : ''}
                </div>
              </div>
              {enrollment.status === 'pending' && (
                <div className="row-actions">
                  <button
                    className="approve"
                    disabled={busyId === enrollment.id}
                    onClick={() => handleApprove(enrollment.id)}
                  >
                    Approve
                  </button>
                  <button
                    className="reject"
                    disabled={busyId === enrollment.id}
                    onClick={() => setModal({ enrollmentId: enrollment.id, action: 'reject' })}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{modal.action === 'reject' ? 'Reject submission' : 'Request resubmission'}</h3>
            <textarea
              placeholder="Reason (shown to the student)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              autoFocus
            />
            <div className="modal-actions">
              <button className="secondary" onClick={() => setModal(null)}>
                Cancel
              </button>
              <button className="primary" style={{ width: 'auto' }} onClick={submitModal} disabled={!reason.trim()}>
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
