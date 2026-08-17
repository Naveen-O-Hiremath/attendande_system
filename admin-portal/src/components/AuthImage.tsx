import { useEffect, useState } from 'react';
import { fetchAuthorizedBlobUrl } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export function AuthImage({ src, alt }: { src: string; alt: string }) {
  const { token } = useAuth();
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let objectUrl: string | null = null;
    let cancelled = false;

    fetchAuthorizedBlobUrl(src, token).then((url) => {
      if (cancelled) {
        URL.revokeObjectURL(url);
        return;
      }
      objectUrl = url;
      setBlobUrl(url);
    });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src, token]);

  if (!blobUrl) {
    return <div style={{ width: 56, height: 56, borderRadius: 8, background: '#f1f2f4' }} />;
  }
  return <img src={blobUrl} alt={alt} />;
}
