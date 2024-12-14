'use client';

import { useEffect, useState } from 'react';
import { FiDownload } from 'react-icons/fi';

interface PDFAttachment {
  filename: string;
  id: string;
  email_id: number;
  upload_date: string;
  type: string;
  size: string;
}

export default function Attachments() {
  const [attachments, setAttachments] = useState<PDFAttachment[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAttachments = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/attachments');
      const data = await response.json();
      setAttachments(data.attachments || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttachments();
  }, []);

  const handleDownload = async (attachment: PDFAttachment) => {
    try {
      const response = await fetch(`http://localhost:5001/api/attachment/${attachment.id}`);
      if (!response.ok) {
        throw new Error('Failed to download attachment');
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Convert base64 to blob
      const content = atob(data.content);
      const bytes = new Uint8Array(content.length);
      for (let i = 0; i < content.length; i++) {
        bytes[i] = content.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = attachment.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading attachment:', error);
      alert('Failed to download attachment');
    }
  };

  if (loading) {
    return (
      <div>
        <h2 className="text-xl font-bold mb-4">Attachments</h2>
        <div className="animate-pulse space-y-2">
          <div className="h-10 bg-gray-700/50 rounded" />
          <div className="h-10 bg-gray-700/50 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-24rem)] flex flex-col">
      <h2 className="text-xl font-semibold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
        Recent Attachments
      </h2>

      <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
        {attachments.map((attachment) => (
          <div
            key={attachment.id}
            className="bg-black/40 p-4 rounded-xl border border-purple-500/10 
              hover:border-purple-500/30 hover:bg-black/50 
              transition-colors duration-150"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="font-medium text-white mb-1">{attachment.filename}</h3>
                <div className="flex items-center gap-2 text-sm text-purple-300/70">
                  <span>{attachment.type}</span>
                  <span>•</span>
                  <span>{attachment.size}</span>
                </div>
              </div>
              <button
                onClick={() => handleDownload(attachment)}
                className="shrink-0 p-2 rounded-lg bg-black/40 border border-purple-500/20
                  hover:bg-black/60 hover:border-purple-500/40 transition-colors duration-150"
              >
                <FiDownload className="w-4 h-4 text-purple-400" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 