'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion'; // Add this import for animations

interface Schedule {
  type: 'meeting' | 'exam' | 'assignment' | 'interview' | 'other';
  scheduled_date: string;
  location?: string;
  meeting_link?: string;
  subject: string;
}

export default function Calendar() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<Schedule['type'] | 'all'>('all');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    async function fetchSchedules() {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:5001/api/schedules', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }

        const validSchedules = (data.schedules || []).map((schedule: any) => ({
          ...schedule,
          type: schedule.type || 'other',
          scheduled_date: schedule.scheduled_date || new Date().toISOString(),
          subject: schedule.subject || 'Untitled Event'
        }));

        setSchedules(validSchedules);
      } catch (error) {
        console.error('Error fetching schedules:', error);
        setError('Failed to load schedules');
      } finally {
        setLoading(false);
      }
    }

    fetchSchedules();
  }, []);

  const getTypeColor = (type: Schedule['type']) => {
    const colors = {
      meeting: 'bg-gradient-to-r from-blue-500 to-blue-600',
      exam: 'bg-gradient-to-r from-red-500 to-red-600',
      assignment: 'bg-gradient-to-r from-green-500 to-green-600',
      interview: 'bg-gradient-to-r from-purple-500 to-purple-600',
      other: 'bg-gradient-to-r from-gray-500 to-gray-600'
    };
    return colors[type];
  };

  const getTypeIcon = (type: Schedule['type']) => {
    const icons = {
      meeting: '👥',
      exam: '📝',
      assignment: '📚',
      interview: '🤝',
      other: '📅'
    };
    return icons[type];
  };

  const toggleSortOrder = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
  };

  const filteredSchedules = schedules
    .filter(schedule => selectedType === 'all' || schedule.type === selectedType)
    .sort((a, b) => {
      const dateA = new Date(a.scheduled_date).getTime();
      const dateB = new Date(b.scheduled_date).getTime();
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    });

  if (loading) {
    return (
      <div>
        <h2 className="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
          Upcoming Events
        </h2>
        <div className="animate-pulse space-y-4">
          <div className="h-20 bg-gray-700/50 rounded-xl" />
          <div className="h-20 bg-gray-700/50 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
          Upcoming Events
        </h2>
        <div className="flex gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleSortOrder}
            className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg text-sm flex items-center gap-2 
              transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20"
          >
            <span>Sort</span>
            <motion.span
              animate={{ rotate: sortOrder === 'asc' ? 0 : 180 }}
              transition={{ duration: 0.3 }}
            >
              ↑
            </motion.span>
          </motion.button>
          <motion.select
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as Schedule['type'] | 'all')}
            className="px-4 py-2 bg-gradient-to-r from-gray-700 to-gray-800 rounded-lg text-sm border border-gray-600
              transition-all duration-300 hover:shadow-lg hover:shadow-gray-500/20 cursor-pointer"
          >
            <option value="all">All Types</option>
            <option value="meeting">Meetings</option>
            <option value="exam">Exams</option>
            <option value="assignment">Assignments</option>
            <option value="interview">Interviews</option>
            <option value="other">Other</option>
          </motion.select>
        </div>
      </div>

      <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto pr-2 custom-scrollbar">
        {filteredSchedules.length > 0 ? (
          filteredSchedules.map((schedule, index) => (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              key={index}
              className="p-4 bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl hover:shadow-lg 
                hover:shadow-purple-500/10 transition-all duration-300 border border-gray-700/50"
            >
              <div className="flex items-center gap-3">
                <span className={`w-2 h-8 rounded-full ${getTypeColor(schedule.type)}`} />
                <div className="flex-1">
                  <span className="text-sm font-medium capitalize flex items-center gap-2">
                    {getTypeIcon(schedule.type)} {schedule.type}
                  </span>
                  <h3 className="font-semibold mt-1">{schedule.subject}</h3>
                  <p className="text-sm text-gray-400">
                    {new Date(schedule.scheduled_date).toLocaleString()}
                  </p>
                  {schedule.location && (
                    <p className="text-sm text-gray-400 mt-1 flex items-center gap-2">
                      <span>📍</span> {schedule.location}
                    </p>
                  )}
                  {schedule.meeting_link && (
                    <motion.a
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      href={schedule.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-purple-400 hover:text-purple-300 mt-2 inline-flex items-center gap-2
                        transition-all duration-300"
                    >
                      <span>🔗</span> Join Meeting
                    </motion.a>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl text-center border border-gray-700/50"
          >
            <p className="text-gray-400">
              {selectedType === 'all' 
                ? 'No upcoming events' 
                : `No ${selectedType} events found`}
            </p>
          </motion.div>
        )}
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #4B5563;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #6B7280;
        }
      `}</style>
    </div>
  );
}