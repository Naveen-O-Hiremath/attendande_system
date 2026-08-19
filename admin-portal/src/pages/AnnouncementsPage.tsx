import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Layout } from '../components/Layout';
import { api, ApiError } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Announcement } from '../api/types';

export function AnnouncementsPage() {
  const { token } = useAuth();
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [posting, setPosting] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    api
      .get<Announcement[]>('/announcements?limit=200', token)
      .then(setAnnouncements)
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handlePost(e: FormEvent) {
    e.preventDefault();
    if (!token || !title.trim() || !body.trim()) return;
    setPosting(true);
    setError(null);
    try {
      await api.post('/announcements', { title: title.trim(), body: body.trim() }, token);
      setTitle('');
      setBody('');
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not post announcement.');
    } finally {
      setPosting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!token) return;
    setBusyId(id);
    setError(null);
    try {
      await api.del(`/announcements/${id}`, token);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not delete announcement.');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Layout>
      <h1 className="page-title">Announcements</h1>
      <p className="page-subtitle">Post updates to every student and see likes/comments come in</p>

      {error && <p className="error-text" style={{ textAlign: 'left' }}>{error}</p>}

      <div className="card" style={{ padding: 20, marginBottom: 24 }}>
        <form onSubmit={handlePost}>
          <label htmlFor="ann-title">Title</label>
          <input id="ann-title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <label htmlFor="ann-body">Message</label>
          <textarea
            id="ann-body"
            className="announcement-textarea"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={3}
            required
          />
          <button
            className="primary"
            type="submit"
            disabled={posting || !title.trim() || !body.trim()}
            style={{ width: 'auto' }}
          >
            {posting ? 'Posting…' : 'Post announcement'}
          </button>
        </form>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : announcements.length === 0 ? (
          <div className="empty-state">No announcements posted yet.</div>
        ) : (
          announcements.map((a) => (
            <div className="enrollment-row" key={a.id} style={{ display: 'block' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ minWidth: 0 }}>
                  <strong>{a.title}</strong>
                  <div className="date">
                    by {a.author_name} · {new Date(a.created_at).toLocaleString()}
                  </div>
                </div>
                <button
                  className="reject"
                  style={{ flexShrink: 0, height: 32 }}
                  disabled={busyId === a.id}
                  onClick={() => handleDelete(a.id)}
                >
                  Delete
                </button>
              </div>
              <p style={{ fontSize: 14, color: 'var(--gray-700)', margin: '10px 0' }}>{a.body}</p>
              <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--gray-500)' }}>
                <span>♥ {a.like_count} like{a.like_count === 1 ? '' : 's'}</span>
                <button
                  className="link-btn"
                  onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}
                >
                  💬 {a.comment_count} comment{a.comment_count === 1 ? '' : 's'}
                </button>
              </div>
              {expandedId === a.id && (
                <div style={{ marginTop: 10, borderTop: '1px solid var(--gray-100)', paddingTop: 10 }}>
                  {a.comments.length === 0 ? (
                    <p style={{ fontSize: 13, color: 'var(--gray-500)', margin: 0 }}>No comments yet.</p>
                  ) : (
                    a.comments.map((c) => (
                      <div key={c.id} style={{ fontSize: 13, marginBottom: 6 }}>
                        <strong style={{ color: 'var(--purple)' }}>{c.author_name}: </strong>
                        {c.body}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </Layout>
  );
}
