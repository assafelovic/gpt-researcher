import React from 'react';

const LoadingDots = () => {
  return (
    <div className="flex justify-center py-4">
      <div className="animate-pulse flex space-x-2">
        <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
        <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
        <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
      </div>
    </div>
  );
};

export default LoadingDots; 