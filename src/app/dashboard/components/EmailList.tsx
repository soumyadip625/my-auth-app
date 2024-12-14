'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiStar, FiTrash2, FiArchive } from 'react-icons/fi';

interface EmailListProps {
  folder: string;
}

export default function EmailList({ folder }: EmailListProps) {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch emails based on folder
    const fetchEmails = async () => {
      try {
        const response = await fetch(`http://localhost:5001/api/emails/${folder}`);
        const data = await response.json();
        setEmails(data.emails || []);
      } catch (error) {
        console.error('Error fetching emails:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEmails();
  }, [folder]);

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <h2 className="text-xl font-semibold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
        {folder.charAt(0).toUpperCase() + folder.slice(1)}
      </h2>

      <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
        {emails.map((email) => (
          <motion.div
            key={email.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-black/40 p-4 rounded-xl border border-purple-500/10 
              hover:border-purple-500/30 hover:bg-black/50 
              transition-colors duration-150"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="font-medium text-white mb-1">{email.subject}</h3>
                <div className="flex items-center gap-2 text-sm text-purple-300/70">
                  <span>{email.sender}</span>
                  <span>•</span>
                  <span>{new Date(email.date).toLocaleDateString()}</span>
                </div>
                <p className="mt-2 text-sm text-purple-200/60 line-clamp-2">
                  {email.body}
                </p>
              </div>
              <div className="flex gap-2">
                <motion.button whileHover={{ scale: 1.1 }} className="p-2">
                  <FiStar className="text-purple-400" />
                </motion.button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
} 