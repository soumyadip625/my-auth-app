'use client';

import { useSession } from "next-auth/react";
import { redirect, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Attachments from "./components/Attachments";
import StoredEmails from './components/StoredEmails';
import EmailStats from './components/EmailStats';
import UpcomingBills from './components/UpcomingBills';
import { useState, useEffect } from 'react';
import { FiMail, FiInbox, FiFileText, FiBell, FiDollarSign, FiMessageSquare } from 'react-icons/fi';
import TypingAnimation from './components/TypingAnimation';

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [emailStats, setEmailStats] = useState({ total: 0, categories: {} });
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    fetchEmailStats();
  }, []);

  const fetchEmailStats = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/dashboard-stats');
      const data = await response.json();
      setEmailStats({
        total: data.total_emails,
        categories: data.category_distribution
      });
    } catch (error) {
      console.error('Error fetching email stats:', error);
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 180, 360]
          }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-12 h-12 border-4 border-purple-500 rounded-full border-t-transparent"
        />
      </div>
    );
  }

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-black to-gray-900 text-white">
      <div className="max-w-[1920px] mx-auto p-8">
        {/* Header Section */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
              Welcome back, {session.user?.name}
            </h1>
            <div className="flex gap-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => router.push('/chatbot')}
                className="px-6 py-3 bg-black/40 rounded-xl
                  flex items-center gap-2 border border-purple-500/20
                  hover:bg-black/60 hover:border-purple-500/40 
                  transition-colors duration-150"
              >
                <FiMessageSquare className="text-xl" />
                Email Assistant
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => router.push('/inbox')}
                className="px-6 py-3 bg-black/40 rounded-xl
                  flex items-center gap-2 border border-purple-500/20
                  hover:bg-black/60 hover:border-purple-500/40 
                  transition-colors duration-150"
              >
                <FiInbox className="text-xl" />
                Inbox
              </motion.button>
            </div>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column */}
          <div className="col-span-3">
            <div className="bg-black/40 rounded-2xl p-4 border border-blue-500/20 
              hover:bg-black/60 hover:border-blue-500/40 transition-colors duration-150"
            >
              <EmailStats
                totalEmails={emailStats.total}
                categories={emailStats.categories}
                onCategoryClick={(category) => setSelectedCategory(category)}
                selectedCategory={selectedCategory}
              />
            </div>
          </div>

          {/* Middle Column */}
          <div className="col-span-6">
            <div className="bg-black/40 rounded-2xl p-4 border border-red-500/20
              hover:bg-black/60 hover:border-red-500/40 transition-colors duration-150"
            >
              <StoredEmails 
                title={selectedCategory ? `${selectedCategory} Emails` : "Recent Emails"}
                selectedCategory={selectedCategory}
                onClearFilterAction={async () => setSelectedCategory(null)}
              />
            </div>
          </div>

          {/* Right Column */}
          <div className="col-span-3 space-y-4">
            {/* Bills & Payments */}
            <div className="bg-black/40 rounded-2xl p-4 border border-green-500/20
              hover:bg-black/60 hover:border-green-500/40 transition-colors duration-150"
            >
              <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                <FiDollarSign className="text-green-400" />
                Bills & Payments
              </h3>
              <UpcomingBills />
            </div>

            {/* Recent Attachments */}
            <div className="bg-black/40 rounded-2xl p-4 border border-yellow-500/20
              hover:bg-black/60 hover:border-yellow-500/40 transition-colors duration-150"
            >
              <Attachments />
            </div>

            {/* Important Updates */}
            <div className="bg-black/40 rounded-2xl p-4 border border-pink-500/20
              hover:bg-black/60 hover:border-pink-500/40 transition-colors duration-150"
            >
              <h3 className="text-xl font-semibold mb-3 flex items-center gap-2">
                <FiBell className="text-yellow-400" />
                Important Updates
              </h3>
              <div className="space-y-3">
                <p className="text-gray-300">No new updates</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
