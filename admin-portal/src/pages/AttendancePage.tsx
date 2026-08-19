import { useCallback, useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { api, downloadAuthorized, ApiError } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { AttendanceRecord, SchoolClass } from '../api/types';

export function AttendancePage() {
  const { token } = useAuth();
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [classFilter, setClassFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    const params = new URLSearchParams({ limit: '500' });
    if (classFilter) params.set('school_class_id', classFilter);
    Promise.all([
      api.get<AttendanceRecord[]>(`/attendance?${params.toString()}`, token),
      api.get<SchoolClass[]>('/classes', token),
    ])
      .then(([r, c]) => {
        setRecords(r);
        setClasses(c);
      })
      .finally(() => setLoading(false));
  }, [token, classFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleExport() {
    if (!token) return;
    setExporting(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (classFilter) params.set('school_class_id', classFilter);
      const suffix = params.toString() ? `?${params.toString()}` : '';
      await downloadAuthorized(`/attendance/export${suffix}`, token, 'attendance_export.csv');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Export failed.');
    } finally {
      setExporting(false);
    }
  }

  return (
    <Layout>
      <h1 className="page-title">Attendance</h1>
      <p className="page-subtitle">Every attendance record marked via face match</p>

      {error && <p className="error-text" style={{ textAlign: 'left' }}>{error}</p>}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <select value={classFilter} onChange={(e) => setClassFilter(e.target.value)} style={{ minWidth: 200 }}>
          <option value="">All classes</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
              {c.section ? ` - ${c.section}` : ''}
            </option>
          ))}
        </select>
        <button className="primary" style={{ width: 'auto' }} onClick={handleExport} disabled={exporting}>
          {exporting ? 'Exporting…' : 'Export CSV'}
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : records.length === 0 ? (
          <div className="empty-state">No attendance records yet.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Roll no.</th>
                <th>Class</th>
                <th>Marked at</th>
                <th>Status</th>
                <th>Method</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td>{r.student_name}</td>
                  <td>{r.roll_no}</td>
                  <td>{r.school_class_name}</td>
                  <td>{new Date(r.marked_at).toLocaleString()}</td>
                  <td>
                    <span className={`badge ${r.status === 'present' ? 'approved' : 'rejected'}`}>{r.status}</span>
                  </td>
                  <td>{r.method}</td>
                  <td>{r.match_confidence !== null ? `${(r.match_confidence * 100).toFixed(1)}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}
