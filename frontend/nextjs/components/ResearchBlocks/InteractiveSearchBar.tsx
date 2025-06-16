import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

interface InteractiveSearchBarProps {
  question: string;
  onNewSearch: (query: string) => void;
}

const InteractiveSearchBar: React.FC<InteractiveSearchBarProps> = ({
  question,
  onNewSearch
}) => {
  const [searchValue, setSearchValue] = useState(question);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Update search value when question prop changes
  useEffect(() => {
    setSearchValue(question);
  }, [question]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      onNewSearch(searchValue.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleClear = () => {
    setSearchValue('');
    inputRef.current?.focus();
  };

  const hasValue = searchValue.trim() !== '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="container w-full mb-6 mt-5"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="flex items-center gap-2">
          <img
            src="/img/message-question-circle.svg"
            alt="search"
            width={20}
            height={20}
            className="w-5 h-5 text-teal-400"
          />
          <span className="text-sm font-medium text-teal-200 uppercase tracking-wide">
            Research Query
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <div
          className={`
            relative flex items-center w-full rounded-2xl border transition-all duration-300 ease-in-out
            ${isFocused
              ? 'border-teal-400/60 bg-gray-900/95 shadow-lg shadow-teal-500/20'
              : 'border-gray-700/40 bg-gray-900/80 hover:bg-gray-900/95 hover:border-gray-600/60'
            }
          `}
        >
          {/* Search Icon */}
          <div className="flex items-center justify-center w-12 h-12 text-gray-400">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Input Field */}
          <input
            ref={inputRef}
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your research question..."
            className="
              flex-1 h-12 px-2 text-white placeholder-gray-400 bg-transparent border-none outline-none
              text-base font-medium leading-relaxed
            "
          />

          {/* Clear Button */}
          {searchValue && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              type="button"
              onClick={handleClear}
              className="flex items-center justify-center w-8 h-8 mr-2 text-gray-400 hover:text-gray-200 rounded-full hover:bg-gray-700/50 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </motion.button>
          )}

          {/* Search/Go Button */}
          <motion.button
            type="submit"
            className={`
              flex items-center justify-center w-10 h-10 mr-1 rounded-xl transition-all duration-200
              ${hasValue
                ? 'bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white shadow-md hover:shadow-lg transform hover:scale-105'
                : 'bg-gray-700/50 text-gray-400 hover:bg-gray-600/50 hover:text-gray-300'
              }
            `}
            whileTap={{ scale: 0.95 }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
};

export default InteractiveSearchBar;
