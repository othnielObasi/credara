'use client';

import { useEffect, useState } from 'react';

export default function AuthCallback() {
  const [message, setMessage] = useState('Signing you in...');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauthError = params.get('error');
    if (oauthError) {
      setMessage(oauthError);
      return;
    }

    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const token = hash.get('token');
    const role = hash.get('role');
    if (!token) {
      setMessage('Sign-in failed - no token received from Auth0.');
      return;
    }
    localStorage.setItem('credara.authToken', token);
    if (role) localStorage.setItem('credara.role', role);
    window.location.replace('/workspace');
  }, []);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'sans-serif', padding: 24, textAlign: 'center' }}>
      <div>
        <p>{message}</p>
        {message !== 'Signing you in...' && (
          <p style={{ marginTop: 16 }}>
            <a href="/workspace">Back to workspace</a>
          </p>
        )}
      </div>
    </div>
  );
}
