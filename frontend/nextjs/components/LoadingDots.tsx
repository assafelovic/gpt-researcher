import React from 'react';

const LoadingDots = () => {
  return (
    <div className="flex justify-center py-4">
      <div className="flex space-x-3">
        <div className="w-3 h-3 bg-purple-500 rounded-full animate-[bounce_1s_infinite_0ms]"></div>
        <div className="w-3 h-3 bg-pink-500 rounded-full animate-[bounce_1s_infinite_200ms]"></div>
        <div className="w-3 h-3 bg-blue-500 rounded-full animate-[bounce_1s_infinite_400ms]"></div>
        <div className="w-3 h-3 bg-indigo-500 rounded-full animate-[bounce_1s_infinite_600ms]"></div>
      </div>
    </div>
  );
};

export default LoadingDots; 