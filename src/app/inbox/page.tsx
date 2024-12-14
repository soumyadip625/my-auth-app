'use client';

import { useSession } from "next-auth/react";
import { redirect, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useState } from 'react';
import { FiMail, FiInbox, FiArchive, FiTrash2, FiStar } from 'react-icons/fi';
import EmailList from '@/app/dashboard/components/EmailList';

export default function Inbox() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [selectedFolder, setSelectedFolder] = useState<string>('inbox');

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
              Inbox
            </h1>
            <div className="flex gap-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="px-6 py-3 bg-black/40 rounded-xl
                  flex items-center gap-2 border border-purple-500/20
                  hover:bg-black/60 hover:border-purple-500/40 
                  transition-colors duration-150"
              >
                <FiMail className="text-xl" />
                Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Folders */}
          <div className="col-span-3">
            <div className="bg-black/40 rounded-2xl p-4 border border-purple-500/20 
              hover:bg-black/60 hover:border-purple-500/40 transition-colors duration-150"
            >
              <div className="h-[calc(100vh-12rem)] flex flex-col">
                <h2 className="text-xl font-semibold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                  Folders
                </h2>
                <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                  {[
                    { id: 'inbox', icon: <FiInbox />, label: 'Inbox' },
                    { id: 'starred', icon: <FiStar />, label: 'Starred' },
                    { id: 'archive', icon: <FiArchive />, label: 'Archive' },
                    { id: 'trash', icon: <FiTrash2 />, label: 'Trash' },
                  ].map((folder) => (
                    <motion.div
                      key={folder.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      whileHover={{ scale: 1.02 }}
                      onClick={() => setSelectedFolder(folder.id)}
                      className={`bg-black/40 p-4 rounded-xl border cursor-pointer
                        ${selectedFolder === folder.id 
                          ? 'border-purple-500/40 bg-black/60' 
                          : 'border-purple-500/10 hover:border-purple-500/30 hover:bg-black/50'}
                        transition-colors duration-150`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-black/30 border border-purple-500/20">
                          {folder.icon}
                        </div>
                        <span className="font-medium">{folder.label}</span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column - Email List */}
          <div className="col-span-9">
            <div className="bg-black/40 rounded-2xl p-4 border border-purple-500/20
              hover:bg-black/60 hover:border-purple-500/40 transition-colors duration-150"
            >
              <EmailList folder={selectedFolder} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 