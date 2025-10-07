import React from 'react';

interface NotFoundContentProps {
  onNewResearch: () => void;
}

export default function NotFoundContent({ onNewResearch }: NotFoundContentProps) {
  return (
    <div className="min-h-[100vh] pt-[70px] flex flex-col items-center justify-center">
      <div className="text-center max-w-md mx-auto">
        <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-gray-800/60 to-gray-700/40 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-100 mb-2">Research Not Found</h2>
        <p className="text-gray-400 mb-6">The research report you&apos;re looking for doesn&apos;t seem to exist or might have been deleted.</p>
        <button 
          onClick={onNewResearch}
          className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-md transition-colors"
        >
          Return to Home
        </button>
      </div>
    </div>
  );
} 