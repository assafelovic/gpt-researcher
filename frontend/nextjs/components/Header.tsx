import React from 'react';
import Image from "next/image";

interface HeaderProps {
  loading?: boolean;      // Indicates if research is currently in progress
  isStopped?: boolean;    // Indicates if research was manually stopped
  showResult?: boolean;   // Controls if research results are being displayed
  onStop?: () => void;    // Handler for stopping ongoing research
  onNewResearch?: () => void;  // Handler for starting fresh research
}

const Header = ({ loading, isStopped, showResult, onStop, onNewResearch }: HeaderProps) => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Glass-like background effect */}
      <div className="absolute inset-0 backdrop-blur-md bg-black/30"></div>
      
      {/* Header container */}
      <div className="container relative mx-auto px-4 py-3 md:py-4">
        <div className="flex flex-row items-center justify-between">
          {/* Logo/Home link with subtle hover effect */}
          <a href="/" className="flex items-center transition-transform hover:scale-105 duration-300">
            <img
              src="/img/gptr-logo.png"
              alt="GPT Researcher"
              width={40}
              height={40}
              className="md:h-12 md:w-12"
            />
            <span className="ml-2 font-semibold text-white text-lg hidden sm:inline-block">
              GPT Researcher
            </span>
          </a>
          
          {/* Action buttons container */}
          <div className="flex gap-3 transition-all duration-300 ease-in-out">
            {/* Stop button - shown only during active research */}
            {loading && !isStopped && (
              <button
                onClick={onStop}
                className="flex items-center justify-center px-6 py-2 text-sm font-medium text-white bg-red-500 rounded-full hover:bg-red-600 transform hover:scale-105 transition-all duration-200 shadow-lg whitespace-nowrap"
                aria-label="Stop research"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Stop
              </button>
            )}
            {/* New Research button - shown after stopping or completing research */}
            {(isStopped || !loading) && showResult && (
              <button
                onClick={onNewResearch}
                className="flex items-center justify-center px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-pink-600 rounded-full hover:opacity-90 transform hover:scale-105 transition-all duration-200 shadow-lg whitespace-nowrap"
                aria-label="Start new research"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                New Research
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
