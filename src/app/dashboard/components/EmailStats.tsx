import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiMail, FiUsers, FiShoppingBag, FiBriefcase, 
  FiBook, FiAlertCircle, FiGlobe, FiStar, FiArchive,
  FiTrendingUp, FiHeart, FiShoppingCart, FiFilm, FiHome, FiFileText, FiHeadphones, FiDollarSign, FiCalendar
} from 'react-icons/fi';

interface EmailStatsProps {
  totalEmails: number;
  categories: { [key: string]: number };
  onCategoryClick: (category: string) => void;
  selectedCategory: string | null;
}

export default function EmailStats({ 
  totalEmails, 
  categories, 
  onCategoryClick,
  selectedCategory 
}: EmailStatsProps) {
  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: JSX.Element } = {
      primary: <FiStar className="text-yellow-400" />,
      social: <FiUsers className="text-blue-400" />,
      promotions: <FiShoppingBag className="text-green-400" />,
      updates: <FiAlertCircle className="text-purple-400" />,
      work: <FiBriefcase className="text-orange-400" />,
      education: <FiBook className="text-pink-400" />,
      forums: <FiGlobe className="text-cyan-400" />,
      other: <FiArchive className="text-gray-400" />,
      health: <FiHeart className="text-red-400" />,
      shopping: <FiShoppingCart className="text-blue-400" />,
      entertainment: <FiFilm className="text-yellow-400" />,
      real_estate: <FiHome className="text-green-400" />,
      legal: <FiFileText className="text-purple-400" />,
      support: <FiHeadphones className="text-orange-400" />,
      subscriptions: <FiDollarSign className="text-pink-400" />,
      events: <FiCalendar className="text-cyan-400" />
    };
    return icons[category.toLowerCase()] || <FiMail className="text-purple-400" />;
  };

  const getLevelInfo = (count: number) => {
    const levels = [
      { min: 0, max: 10, name: "Beginner", color: "text-gray-400" },
      { min: 11, max: 30, name: "Active", color: "text-blue-400" },
      { min: 31, max: 60, name: "Pro", color: "text-purple-400" },
      { min: 61, max: 100, name: "Expert", color: "text-yellow-400" },
      { min: 101, max: Infinity, name: "Master", color: "text-green-400" }
    ];
    return levels.find(level => count >= level.min && count <= level.max) || levels[0];
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
          Email Categories
        </h2>
        <motion.div 
          className="px-3 py-1 bg-purple-500/10 rounded-full border border-purple-500/20"
          whileHover={{ scale: 1.05 }}
        >
          <span className="text-sm text-purple-400">Total: {totalEmails}</span>
        </motion.div>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
        {Object.entries(categories).map(([category, count], index) => {
          const levelInfo = getLevelInfo(count);
          const percentage = Math.round((count / totalEmails) * 100);
          
          return (
            <motion.div
              key={category}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ 
                scale: 1.02,
                transition: { duration: 0.2 }
              }}
              onClick={() => onCategoryClick(category)}
              className={`bg-black/40 p-4 rounded-xl border cursor-pointer
                ${selectedCategory === category 
                  ? 'border-purple-500/40 bg-black/60' 
                  : 'border-purple-500/10 hover:border-purple-500/30 hover:bg-black/50'}
                transition-colors duration-150 relative overflow-hidden group`}
            >
              <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center gap-3">
                  <motion.div
                    whileHover={{ rotate: 15 }}
                    className="p-2 rounded-lg bg-black/30 border border-purple-500/20"
                  >
                    {getCategoryIcon(category)}
                  </motion.div>
                  <div>
                    <span className="text-white font-medium capitalize">{category}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs ${levelInfo.color}`}>
                        {levelInfo.name}
                      </span>
                      <AnimatePresence>
                        {percentage > 20 && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0 }}
                            className="flex items-center gap-1 text-xs text-green-400"
                          >
                            <FiTrendingUp />
                            <span>Active</span>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <motion.div 
                    className="text-purple-400 text-lg font-medium"
                    whileHover={{ scale: 1.1 }}
                  >
                    {count}
                  </motion.div>
                  <div className="text-xs text-purple-300/70">
                    {percentage}%
                  </div>
                </div>
              </div>
              <motion.div
                className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-purple-500/20 to-pink-500/20"
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
              />
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
