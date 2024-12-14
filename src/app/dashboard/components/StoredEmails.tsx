'use client';

import { clearFilterAction } from './actions';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiArrowRight } from 'react-icons/fi';

interface StoredEmail {
  id: string;
  subject: string;
  sender: string;
  date: string;
  body: string;
  category: string;
  processed_at: string;
  summary: string;
  has_attachments: boolean;
  pdf_attachments: Array<{
    filename: string;
    id: string;
  }>;
}

interface EmailModalProps {
  email: StoredEmail;
  onClose: () => void;
}

const cleanSenderName = (sender: string) => {
  // Remove email addresses in brackets
  let name = sender.replace(/<[^>]+>/, '').trim();
  // Remove quotes if present
  name = name.replace(/["']/g, '');
  // If it's just an email address, show only the part before @
  if (name.includes('@')) {
    name = name.split('@')[0];
  }
  return name;
};

const formatEmailBody = (body: string) => {
  // Remove long URLs and replace with cleaner links
  const cleanBody = body.replace(
    /(https?:\/\/[^\s]+)/g, 
    '[View Link]'
  );

  // Split into paragraphs and remove empty lines
  const paragraphs = cleanBody
    .split('\n')
    .filter(line => line.trim())
    .map(line => line.trim());

  return paragraphs;
};

const extractImportantInfo = (email: StoredEmail) => {
  const content = `${email.subject} ${email.body}`.toLowerCase();
  const info: { [key: string]: any } = {};

  // First, clean the body text from HTML tags
  const cleanBody = email.body.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

  // Extract exam/test details
  if (content.includes('exam') || content.includes('test') || content.includes('quiz')) {
    info.type = 'exam';
    
    // Extract time slot
    const timeSlotMatch = cleanBody.match(/slot:\s*([0-9:.]+\s*(?:am|pm)\s*-\s*[0-9:.]+\s*(?:am|pm))/i);
    if (timeSlotMatch) {
      info.timeSlot = timeSlotMatch[1];
    } else {
      // Fallback: try to find time range
      const times = cleanBody.match(/([0-9]{1,2}[:.]?[0-9]{0,2}\s*(?:am|pm))/gi);
      if (times && times.length >= 2) {
        info.timeSlot = `${times[0]} - ${times[1]}`;
      }
    }
    
    // Extract login credentials with improved patterns
    const loginMatch = cleanBody.match(/(?:login|user|id)(?:\s+id)?:\s*([A-Z0-9]+)/i);
    const passMatch = cleanBody.match(/password:\s*([a-zA-Z0-9]+)/i);
    
    if (loginMatch) info.loginId = loginMatch[1].trim();
    if (passMatch) info.password = passMatch[1].trim();
  }

  return info;
};

const EmailModal = ({ email, onClose }: EmailModalProps) => {
  const importantInfo = extractImportantInfo(email);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-bold">{email.subject}</h3>
            <p className="text-sm text-gray-400">{cleanSenderName(email.sender)}</p>
            <p className="text-sm text-gray-400">
              {new Date(email.date).toLocaleString()}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {/* Summary Section */}
          <div className="bg-gray-700/50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-purple-400 mb-2">Summary</h4>
            <p className="text-gray-200">{email.summary}</p>
          </div>

          {/* Important Information Section */}
          {Object.keys(importantInfo).length > 0 && (
            <div className="bg-gray-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-purple-400 mb-2">Important Details</h4>
              <div className="space-y-2">
                {importantInfo.type === 'meeting' && (
                  <>
                    {importantInfo.timeSlot && (
                      <p className="text-gray-200">📅 Time: {importantInfo.timeSlot}</p>
                    )}
                    {importantInfo.link && (
                      <p className="text-purple-400 hover:underline">
                        <a href={importantInfo.link} target="_blank" rel="noopener noreferrer">
                          🔗 Join Meeting
                        </a>
                      </p>
                    )}
                    {importantInfo.agenda && (
                      <p className="text-gray-200">📝 Agenda: {importantInfo.agenda}</p>
                    )}
                  </>
                )}

                {importantInfo.type === 'exam' && (
                  <>
                    {importantInfo.timeSlot && (
                      <p className="text-gray-200">📅 Time Slot: {importantInfo.timeSlot}</p>
                    )}
                    {importantInfo.loginId && (
                      <p className="text-gray-200">👤 Login ID: {importantInfo.loginId}</p>
                    )}
                    {importantInfo.password && (
                      <p className="text-gray-200">🔑 Password: {importantInfo.password}</p>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* Attachments Section */}
          {email.has_attachments && (
            <div className="bg-gray-700/50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-purple-400 mb-2">Attachments</h4>
              <div className="flex flex-wrap gap-2">
                {email.pdf_attachments.map((pdf, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 bg-gray-600 rounded-full text-sm"
                  >
                    📎 {pdf.filename}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

interface StoredEmailsProps {
  title?: string;
  selectedCategory: string | null;
  onClearFilterAction?: () => Promise<void>;
}

export default function StoredEmails({ 
  title = "Stored Emails",
  selectedCategory,
  onClearFilterAction = clearFilterAction
}: StoredEmailsProps) {
  const [emails, setEmails] = useState<StoredEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedEmail, setSelectedEmail] = useState<StoredEmail | null>(null);

  // Function to fetch emails
  async function fetchStoredEmails() {
    try {
      const response = await fetch('http://localhost:5001/api/categorized-emails');
      if (!response.ok) {
        throw new Error('Failed to fetch emails');
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Safely map the emails with proper type checking
      let filteredEmails = data.emails
        .filter((email: any) => 
          email && 
          email.category !== 'spam' && 
          (!selectedCategory || email.category === selectedCategory)
        )
        .map((email: any) => ({
          id: email._id || email.id || '',
          subject: email.subject || '',
          sender: email.sender || '',
          date: email.date || new Date().toISOString(),
          body: email.body || '',
          category: email.category || '',
          processed_at: email.processed_at || '',
          summary: email.summary || 'No summary available',
          has_attachments: email.has_attachments || false,
          pdf_attachments: email.pdf_attachments || []
        }));
      
      setEmails(filteredEmails);
    } catch (error) {
      console.error('Error fetching stored emails:', error);
      setError('Failed to load email summaries');
    } finally {
      setLoading(false);
    }
  }

  // Initial fetch and setup polling
  useEffect(() => {
    // Initial fetch
    fetchStoredEmails();

    // Set up polling every 5 seconds
    const intervalId = setInterval(fetchStoredEmails, 5000);

    // Cleanup interval on unmount
    return () => clearInterval(intervalId);
  }, [selectedCategory]);

  const toggleSort = () => {
    const sorted = [...emails].sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    });
    setEmails(sorted);
    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
  };

  const handleEmailClick = (email: StoredEmail) => {
    setSelectedEmail(email);
    console.log("Selected email:", email);
  };

  if (loading) {
    return <div>Loading stored emails...</div>;
  }

  if (error) {
    return (
      <div>
        <h2 className="text-xl font-bold mb-4">Stored Emails</h2>
        <div className="p-4 bg-red-500/10 text-red-500 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
          {title}
        </h2>
        {selectedCategory && (
          <button
            onClick={onClearFilterAction}
            className="text-sm px-3 py-1 rounded-lg bg-black/40 border border-purple-500/20
              hover:bg-black/60 hover:border-purple-500/40 transition-colors duration-150"
          >
            Clear Filter
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
        {emails.map((email) => (
          <div
            key={email.id}
            className="bg-black/40 p-4 rounded-xl border border-purple-500/10 
              hover:border-purple-500/30 hover:bg-black/50 
              transition-colors duration-150"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="font-medium text-white mb-1">{email.subject}</h3>
                <div className="flex items-center gap-2 text-sm text-purple-300/70">
                  <span>{cleanSenderName(email.sender)}</span>
                  <span>•</span>
                  <span>{new Date(email.date).toLocaleDateString()}</span>
                </div>
                <p className="mt-2 text-sm text-purple-200/60 line-clamp-2">
                  {email.summary}
                </p>
                {email.category && (
                  <span className="inline-block mt-2 text-xs bg-purple-500/10 text-purple-300 px-2 py-1 rounded-full 
                    border border-purple-500/20">
                    {email.category}
                  </span>
                )}
              </div>
              <button
                onClick={() => handleEmailClick(email)}
                className="shrink-0 p-2 rounded-lg bg-black/40 border border-purple-500/20
                  hover:bg-black/60 hover:border-purple-500/40 transition-colors duration-150"
              >
                <FiArrowRight className="w-4 h-4 text-purple-400" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 