'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface Bill {
  id: string;
  name: string;
  amount: number;
  dueDate: string;
  status: 'paid' | 'pending' | 'overdue';
  category: 'utility' | 'subscription' | 'rent' | 'other';
}

export default function Bills() {
  const [bills, setBills] = useState<Bill[]>([
    {
      id: '1',
      name: 'Electricity Bill',
      amount: 120,
      dueDate: '2024-03-15',
      status: 'pending',
      category: 'utility'
    },
    // Add more sample bills here
  ]);

  useEffect(() => {
    const fetchBills = async () => {
      try {
        const response = await fetch('/api/bills');
        const data = await response.json();
        if (data.bills) {
          setBills(data.bills);
        }
      } catch (error) {
        console.error('Error fetching bills:', error);
      }
    };

    fetchBills();
  }, []);

  const getStatusColor = (status: string) => {
    const colors = {
      paid: 'bg-green-500/20 text-green-400',
      pending: 'bg-yellow-500/20 text-yellow-400',
      overdue: 'bg-red-500/20 text-red-400'
    };
    return colors[status as keyof typeof colors];
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      utility: '⚡',
      subscription: '📱',
      rent: '🏠',
      other: '📝'
    };
    return icons[category as keyof typeof icons];
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Upcoming Bills</h2>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-lg text-sm"
        >
          + Add Bill
        </motion.button>
      </div>

      <div className="space-y-4">
        {bills.map((bill) => {
          const daysUntilDue = Math.ceil(
            (new Date(bill.dueDate).getTime() - new Date().getTime()) / (1000 * 3600 * 24)
          );

          return (
            <motion.div
              key={bill.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800/50 rounded-lg p-4 hover:bg-gray-800/70 transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{getCategoryIcon(bill.category)}</span>
                  <div>
                    <h3 className="font-medium">{bill.name}</h3>
                    <p className="text-sm text-gray-400">
                      Due in {daysUntilDue} days
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold">${bill.amount}</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(bill.status)}`}>
                    {bill.status}
                  </span>
                </div>
              </div>

              <div className="mt-3 w-full bg-gray-700 rounded-full h-1.5">
                <motion.div
                  className="bg-purple-500 h-1.5 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (15 - daysUntilDue) / 15 * 100)}%` }}
                  transition={{ duration: 1 }}
                />
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
} 