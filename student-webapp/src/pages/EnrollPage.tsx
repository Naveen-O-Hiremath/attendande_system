import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TopBar } from '../components/TopBar';
import { useAuth } from '../auth/AuthContext';
import { api, ApiError } from '../api/client';

const REQUIRED_SHOTS = 2;

export function EnrollPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [shots, setShots] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handleCapture(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setShots((prev) => [...prev, file]);
    setPreviews((prev) => [...prev, URL.createObjectURL(file)]);
    e.target.value = '';
  }

  function removeShot(index: number) {
    setShots((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  }

  async function submit() {
    if (!token || shots.length < REQUIRED_SHOTS) return;
    setSubmitting(true);
    setError(null);
    try {
      const form = new FormData();
      shots.forEach((file) => form.append('files', file, file.name || 'capture.jpg'));
      await api.postForm('/face-enrollments', form, token);
      navigate('/');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Submission failed.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="screen">
      <TopBar title="Face enrollment" />
      <div className="content">
        <p style={{ color: 'var(--gray-500)', fontSize: 13, marginTop: 0 }}>
          Take {REQUIRED_SHOTS} clear photos of your face, one at a time, in good lighting. An admin
          will review them before they become active.
        </p>

        <div className="shot-row">
          {Array.from({ length: Math.max(REQUIRED_SHOTS, shots.length) }).map((_, i) =>
            previews[i] ? (
              <div key={i} style={{ position: 'relative' }}>
                <img src={previews[i]} className="shot-thumb" alt={`Capture ${i + 1}`} />
                <button
                  onClick={() => removeShot(i)}
                  style={{
                    position: 'absolute',
                    top: -6,
                    right: -6,
                    width: 20,
                    height: 20,
                    borderRadius: '50%',
                    border: 'none',
                    background: 'var(--red)',
                    color: 'white',
                    fontSize: 12,
                    cursor: 'pointer',
                    lineHeight: 1,
                  }}
                >
                  ×
                </button>
              </div>
            ) : (
              <div key={i} className="shot-thumb empty" />
            ),
          )}
        </div>

        {error && <p className="error-text">{error}</p>}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="user"
          onChange={handleCapture}
          style={{ display: 'none' }}
        />

        <button className="secondary" onClick={() => fileInputRef.current?.click()} style={{ marginBottom: 12 }}>
          {shots.length === 0 ? 'Take first photo' : 'Take another photo'}
        </button>

        <button
          className="primary"
          disabled={shots.length < REQUIRED_SHOTS || submitting}
          onClick={submit}
        >
          {submitting ? 'Submitting…' : `Submit ${shots.length}/${REQUIRED_SHOTS} photos`}
        </button>
      </div>
    </div>
  );
}
