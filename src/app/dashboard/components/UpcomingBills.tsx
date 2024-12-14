import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiCreditCard, FiCalendar, FiDollarSign } from 'react-icons/fi';

interface Bill {
  id: string;
  title: string;
  amount: number;
  dueDate: string;
  category: string;
  status: 'pending' | 'paid' | 'overdue';
}

export default function UpcomingBills() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const mockBills: Bill[] = [
      {
        id: '1',
        title: 'Electricity Bill',
        amount: 150.00,
        dueDate: '2024-03-25',
        category: 'Utilities',
        status: 'pending'
      },
      {
        id: '2',
        title: 'Internet Service',
        amount: 79.99,
        dueDate: '2024-03-28',
        category: 'Internet',
        status: 'pending'
      }
    ];
    setBills(mockBills);
    setLoading(false);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-500/10 text-green-400 border-green-500/20';
      case 'overdue':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      default:
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
    }
  };

  if (loading) {
    return <div className="text-gray-500">Loading bills...</div>;
  }

  if (bills.length === 0) {
    return <div className="text-gray-500">No upcoming bills</div>;
  }

  return (
    <div className="space-y-4">
      {bills.map((bill) => (
        <motion.div
          key={bill.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-black/80 to-gray-900/80 rounded-xl p-4 space-y-3 border border-gray-800/50 hover:border-gray-700/50 transition-colors"
        >
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <FiCreditCard className="w-4 h-4" />
              </div>
              <h4 className="font-medium text-gray-200">{bill.title}</h4>
            </div>
            <span className={`text-xs font-medium px-2 py-1 rounded-lg border ${getStatusColor(bill.status)}`}>
              {bill.status.toUpperCase()}
            </span>
          </div>
          
          <div className="flex justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-gray-800/50 text-gray-400 border border-gray-700/30">
                <FiCalendar className="w-4 h-4" />
              </div>
              <span className="text-gray-400">
                Due: {new Date(bill.dueDate).toLocaleDateString()}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-green-500/10 text-green-400 border border-green-500/20">
                <FiDollarSign className="w-4 h-4" />
              </div>
              <span className="text-green-400 font-medium">
                ${bill.amount.toFixed(2)}
              </span>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
} 