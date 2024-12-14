'use client';

import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { motion } from "framer-motion";
import { useState } from 'react';
import { FiSend, FiMail } from 'react-icons/fi';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Chatbot() {
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ query: input }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        role: 'assistant' as const,
        content: data.response || 'Sorry, I could not process your request.',
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        role: 'assistant' as const,
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-black to-gray-900 text-white">
      <div className="max-w-4xl mx-auto p-8">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
            Email Assistant
          </h1>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => window.location.href = '/dashboard'}
            className="px-4 py-2 bg-black/40 rounded-xl
              flex items-center gap-2 border border-purple-500/20
              hover:bg-black/60 hover:border-purple-500/40 
              transition-colors duration-150"
          >
            <FiMail className="text-xl" />
            Dashboard
          </motion.button>
        </div>

        <div className="bg-black/40 rounded-2xl p-6 border border-purple-500/20">
          <div className="h-[calc(100vh-16rem)] flex flex-col">
            <div className="flex-1 overflow-y-auto mb-4 space-y-4 custom-scrollbar">
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-xl ${
                      message.role === 'user'
                        ? 'bg-purple-500/20 border border-purple-500/20'
                        : 'bg-black/40 border border-purple-500/20'
                    }`}
                  >
                    <p className="text-purple-200/90 whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                </motion.div>
              ))}
              {loading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-black/40 p-4 rounded-xl border border-purple-500/20">
                    <div className="flex gap-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your emails..."
                className="flex-1 bg-black/40 border border-purple-500/20 rounded-xl px-4 py-2
                  focus:outline-none focus:border-purple-500/40 transition-colors"
              />
              <button
                type="submit"
                disabled={loading}
                className="p-2 bg-purple-500/20 rounded-xl border border-purple-500/20
                  hover:bg-purple-500/30 transition-colors disabled:opacity-50"
              >
                <FiSend className="w-6 h-6 text-purple-400" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
} 