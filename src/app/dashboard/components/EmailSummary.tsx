'use client';

import { useEffect, useState } from 'react';

export default function EmailSummary() {
  const [summaries, setSummaries] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchEmails() {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:5001/api/emails', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const data = await response.json();
        setSummaries(data.summaries);
      } catch (err) {
        console.error('Failed to fetch emails:', err);
        setError('Failed to load email summaries. Please make sure the server is running.');
      } finally {
        setLoading(false);
      }
    }

    fetchEmails();
  }, []);

  if (loading) {
    return (
      <div>
        <h2 className="text-xl font-bold mb-4">Email Summaries</h2>
        <div className="animate-pulse space-y-4">
          <div className="h-20 bg-gray-700/50 rounded" />
          <div className="h-20 bg-gray-700/50 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="text-xl font-bold mb-4">Email Summaries</h2>
        <div className="p-4 bg-red-500/10 text-red-500 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Email Summaries</h2>
      <div className="space-y-4">
        {summaries.length > 0 ? (
          summaries.map((summary, index) => (
            <div key={index} className="p-3 bg-gray-700 rounded">
              <p className="text-sm text-gray-300">{summary}</p>
            </div>
          ))
        ) : (
          <div className="p-3 bg-gray-700 rounded">
            <p className="text-sm text-gray-300">No new emails today</p>
          </div>
        )}
      </div>
    </div>
  );
} 