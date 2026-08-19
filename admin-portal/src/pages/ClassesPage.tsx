import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Layout } from '../components/Layout';
import { api, ApiError } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { SchoolClass, StudentSummary } from '../api/types';

export function ClassesPage() {
  const { token } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyStudentId, setBusyStudentId] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [section, setSection] = useState('');
  const [year, setYear] = useState('');
  const [creating, setCreating] = useState(false);

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    Promise.all([
      api.get<SchoolClass[]>('/classes', token),
      api.get<StudentSummary[]>('/users/students', token),
    ])
      .then(([c, s]) => {
        setClasses(c);
        setStudents(s);
      })
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!token || !name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await api.post(
        '/classes',
        { name: name.trim(), section: section.trim() || undefined, year: year.trim() || undefined },
        token,
      );
      setName('');
      setSection('');
      setYear('');
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create class.');
    } finally {
      setCreating(false);
    }
  }

  async function handleAssign(studentId: string, schoolClassId: string) {
    if (!token) return;
    setBusyStudentId(studentId);
    setError(null);
    try {
      await api.patch(
        `/users/${studentId}/class`,
        { school_class_id: schoolClassId || null },
        token,
      );
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update class assignment.');
    } finally {
      setBusyStudentId(null);
    }
  }

  return (
    <Layout>
      <h1 className="page-title">Classes</h1>
      <p className="page-subtitle">Create classes and assign students so attendance can be recorded</p>

      {error && <p className="error-text" style={{ textAlign: 'left' }}>{error}</p>}

      <div className="card" style={{ padding: 20, marginBottom: 24 }}>
        <form onSubmit={handleCreate} className="inline-form">
          <input
            placeholder="Class name (e.g. Grade 10)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <input placeholder="Section (optional)" value={section} onChange={(e) => setSection(e.target.value)} />
          <input placeholder="Year (optional)" value={year} onChange={(e) => setYear(e.target.value)} />
          <button className="primary" type="submit" disabled={creating || !name.trim()} style={{ width: 'auto' }}>
            {creating ? 'Adding…' : 'Add class'}
          </button>
        </form>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : classes.length === 0 ? (
          <div className="empty-state">No classes yet — add one above.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Section</th>
                <th>Year</th>
                <th>Students</th>
              </tr>
            </thead>
            <tbody>
              {classes.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td>{c.section ?? '—'}</td>
                  <td>{c.year ?? '—'}</td>
                  <td>{c.student_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <h1 className="page-title" style={{ fontSize: 18 }}>Students</h1>
      <div className="card">
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : students.length === 0 ? (
          <div className="empty-state">No student accounts yet.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Roll no.</th>
                <th>Enrollment</th>
                <th>Class</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td>
                    {s.full_name}
                    <div className="id">{s.email}</div>
                  </td>
                  <td>{s.roll_no}</td>
                  <td>
                    <span className={`badge ${s.enrollment_status}`}>{s.enrollment_status}</span>
                  </td>
                  <td>
                    <select
                      value={s.school_class_id ?? ''}
                      disabled={busyStudentId === s.id}
                      onChange={(e) => handleAssign(s.id, e.target.value)}
                    >
                      <option value="">Unassigned</option>
                      {classes.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                          {c.section ? ` - ${c.section}` : ''}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}
