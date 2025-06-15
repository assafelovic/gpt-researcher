import React from 'react';
import { motion } from 'framer-motion';

interface LoadingDotsProps {
  message?: string;
  variant?: 'default' | 'processing' | 'connecting';
}

const LoadingDots: React.FC<LoadingDotsProps> = ({
  message = "Processing...",
  variant = "default"
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case "connecting":
        return {
          dotColor: "bg-yellow-400",
          message: message || "Establishing connection...",
          animation: { scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }
        };
      case "processing":
        return {
          dotColor: "bg-teal-400",
          message: message || "Analyzing information...",
          animation: { y: [0, -8, 0] },
        };
      default:
        return {
          dotColor: "bg-gray-300",
          message: message || "Loading...",
          animation: { scale: [1, 1.2, 1] },
        };
    }
  };

  const { dotColor, message: displayMessage, animation } = getVariantStyles();

  return (
    <div className="flex flex-col items-center justify-center py-6">
      <div className="flex space-x-2 mb-3">
        {[0, 1, 2].map((index) => (
          <motion.div
            key={index}
            className={`w-3 h-3 ${dotColor} rounded-full`}
            animate={animation}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: index * 0.2,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
      <motion.p
        className="text-sm text-gray-400 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {displayMessage}
      </motion.p>
    </div>
  );
};

export default LoadingDots;
