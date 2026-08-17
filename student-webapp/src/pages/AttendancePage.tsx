import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { TopBar } from '../components/TopBar';
import { useAuth } from '../auth/AuthContext';
import { api, ApiError } from '../api/client';
import type { FaceMatchResult } from '../api/types';

export function AttendancePage() {
  const { token } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<FaceMatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function handleCapture(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  }

  async function submit() {
    if (!token || !file) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append('file', file, file.name || 'capture.jpg');
      const res = await api.postForm<FaceMatchResult>('/face-enrollments/match', form, token);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not check attendance.');
    } finally {
      setSubmitting(false);
    }
  }

  const resultClass = result ? (result.matched ? 'success' : result.needs_review ? 'review' : 'fail') : '';

  return (
    <div className="screen">
      <TopBar title="Mark attendance" />
      <div className="content">
        <Link to="/" className="back-link">
          ← Back
        </Link>

        <div className="capture-preview">
          {preview ? (
            <img src={preview} alt="Capture" />
          ) : (
            <div className="placeholder">Take a live photo to mark your attendance</div>
          )}
        </div>

        {result && (
          <div className={`result-box ${resultClass}`}>
            <strong>{result.matched ? 'Attendance marked' : result.needs_review ? 'Needs review' : 'Not recognized'}</strong>
            <p style={{ margin: '6px 0 0', fontSize: 13 }}>{result.message}</p>
            <p style={{ margin: '4px 0 0', fontSize: 12, opacity: 0.8 }}>
              similarity: {(result.similarity * 100).toFixed(1)}%
            </p>
          </div>
        )}

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
          {preview ? 'Retake photo' : 'Open camera'}
        </button>

        <button className="primary" disabled={!file || submitting} onClick={submit}>
          {submitting ? 'Checking…' : 'Mark attendance'}
        </button>
      </div>
    </div>
  );
}
