import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { Announcement } from '../api/types';

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function AnnouncementCard({ announcement, onChange }: { announcement: Announcement; onChange: () => void }) {
  const { token } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [busy, setBusy] = useState(false);

  async function handleLike() {
    if (!token || busy) return;
    setBusy(true);
    try {
      await api.post(`/announcements/${announcement.id}/like`, undefined, token);
      onChange();
    } catch {
      // Best-effort — a failed like toggle isn't worth interrupting the feed with an error banner.
    } finally {
      setBusy(false);
    }
  }

  async function handleComment() {
    if (!token || !commentText.trim() || busy) return;
    setBusy(true);
    try {
      await api.post(`/announcements/${announcement.id}/comments`, { body: commentText.trim() }, token);
      setCommentText('');
      onChange();
    } catch {
      // Best-effort — same as above.
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="announcement-card">
      <div className="announcement-header">
        <span className="announcement-author">{announcement.author_name}</span>
        <span className="announcement-time">{timeAgo(announcement.created_at)}</span>
      </div>
      <h4 className="announcement-title">{announcement.title}</h4>
      <p className="announcement-body">{announcement.body}</p>

      <div className="announcement-actions">
        <button
          className={`like-btn ${announcement.liked_by_me ? 'liked' : ''}`}
          onClick={handleLike}
          disabled={busy}
        >
          {announcement.liked_by_me ? '♥' : '♡'} {announcement.like_count}
        </button>
        <button className="comment-btn" onClick={() => setExpanded((v) => !v)}>
          💬 {announcement.comment_count}
        </button>
      </div>

      {expanded && (
        <div className="announcement-comments">
          {announcement.comments.length === 0 ? (
            <p className="no-comments">No comments yet.</p>
          ) : (
            announcement.comments.map((c) => (
              <div className="comment-row" key={c.id}>
                <span className="comment-author">{c.author_name}</span>
                <span className="comment-body">{c.body}</span>
              </div>
            ))
          )}
          <div className="comment-input-row">
            <input
              placeholder="Write a comment…"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleComment()}
            />
            <button onClick={handleComment} disabled={busy || !commentText.trim()}>
              Post
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function AnnouncementFeed() {
  const { token } = useAuth();
  const [announcements, setAnnouncements] = useState<Announcement[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    api
      .get<Announcement[]>('/announcements?limit=50', token)
      .then(setAnnouncements)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load announcements.'));
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="announcement-feed">
      <h3 className="feed-heading">Announcements</h3>
      {error && <p className="error-text">{error}</p>}
      {announcements === null ? (
        <p style={{ color: 'var(--gray-500)', fontSize: 13 }}>Loading…</p>
      ) : announcements.length === 0 ? (
        <div className="card">
          <p style={{ margin: 0 }}>No announcements yet.</p>
        </div>
      ) : (
        announcements.map((a) => <AnnouncementCard key={a.id} announcement={a} onChange={load} />)
      )}
    </div>
  );
}
