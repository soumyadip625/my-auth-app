import { motion } from 'framer-motion';
import React, { useState, useEffect } from 'react';

interface Event {
  id: string;
  title: string;
  date: string;
  type: string;
  timeSlot?: string;
  link?: string;
  loginId?: string;
  password?: string;
}

export default function UpcomingEvents() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  const getEventIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'exam':
        return '📝';
      case 'meeting':
        return '👥';
      case 'deadline':
        return '⏰';
      default:
        return '📅';
    }
  };

  const formatEventTitle = (event: Event) => {
    if (!event.title) return `${event.type} Event`;
    return event.title.replace(/^re:\s*/i, '').trim();
  };

  const getEventDetails = (event: Event) => {
    switch (event.type.toLowerCase()) {
      case 'exam':
        return (
          <div className="space-y-1">
            {event.timeSlot && (
              <p className="text-sm text-gray-400">
                ⏰ Time: {event.timeSlot}
              </p>
            )}
            {event.loginId && (
              <p className="text-sm text-gray-400">
                👤 Login ID: {event.loginId}
              </p>
            )}
            {event.password && (
              <p className="text-sm text-gray-400">
                🔑 Password: {event.password}
              </p>
            )}
          </div>
        );
      case 'meeting':
        return (
          <div className="space-y-1">
            {event.timeSlot && (
              <p className="text-sm text-gray-400">
                ⏰ Time: {event.timeSlot}
              </p>
            )}
            {event.link && (
              <a
                href={event.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-purple-400 hover:text-purple-300"
              >
                🔗 Join Meeting
              </a>
            )}
          </div>
        );
      default:
        return (
          <div className="space-y-1">
            {event.timeSlot && (
              <p className="text-sm text-gray-400">
                ⏰ Time: {event.timeSlot}
              </p>
            )}
          </div>
        );
    }
  };

  const fetchUpcomingEvents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/schedules', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (!Array.isArray(data)) {
        console.error('Expected array of events, got:', data);
        setEvents([]);
        return;
      }
      
      // Filter and sort events
      const now = new Date();
      const upcomingEvents = data
        .filter((event: Event) => {
          try {
            const eventDate = new Date(event.date);
            return eventDate >= now;
          } catch (e) {
            console.error('Invalid date:', event.date);
            return false;
          }
        })
        .sort((a: Event, b: Event) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
        )
        .slice(0, 5);
      
      setEvents(upcomingEvents);
    } catch (error) {
      console.error('Error fetching events:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUpcomingEvents();
    // Refresh events every 5 minutes
    const interval = setInterval(fetchUpcomingEvents, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-xl">
        <h3 className="text-xl font-bold text-gray-200 mb-6">Loading events...</h3>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 shadow-xl">
        <h3 className="text-xl font-bold text-gray-200 mb-6">Upcoming Events</h3>
        <p className="text-gray-400">No upcoming events found</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800 rounded-xl p-6 shadow-xl"
    >
      <h3 className="text-xl font-bold text-gray-200 mb-6">Upcoming Events</h3>
      <div className="space-y-4">
        {events.map((event, index) => (
          <motion.div
            key={event.id}
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-700/50 rounded-lg p-4"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{getEventIcon(event.type)}</span>
              <div className="flex-1">
                <h4 className="font-medium text-gray-200">{formatEventTitle(event)}</h4>
                <p className="text-sm text-gray-400">
                  {new Date(event.date).toLocaleString('en-US', {
                    dateStyle: 'full',
                    timeStyle: 'short'
                  })}
                </p>
                {getEventDetails(event)}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
} 