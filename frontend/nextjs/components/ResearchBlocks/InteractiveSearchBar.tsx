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
              ? 'border-teal-400/60 bg-white/95 shadow-lg shadow-teal-500/20'
              : 'border-gray-300/40 bg-white/90 hover:bg-white/95 hover:border-gray-300/60'
            }
            ${disabled ? 'opacity-60 cursor-not-allowed' : ''}
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
            disabled={disabled}
            placeholder="Enter your research question..."
            className="
              flex-1 h-12 px-2 text-gray-800 placeholder-gray-500 bg-transparent border-none outline-none
              text-base font-medium leading-relaxed
              disabled:cursor-not-allowed
            "
          />

          {/* Clear Button */}
          {searchValue && !disabled && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              type="button"
              onClick={handleClear}
              className="flex items-center justify-center w-8 h-8 mr-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </motion.button>
          )}

          {/* Search/Go Button */}
          <motion.button
            type="submit"
            disabled={disabled || !hasChanged}
            className={`
              flex items-center justify-center w-10 h-10 mr-1 rounded-xl transition-all duration-200
              ${hasChanged && !disabled
                ? 'bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white shadow-md hover:shadow-lg transform hover:scale-105'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
            whileTap={hasChanged && !disabled ? { scale: 0.95 } : {}}
          >
            {disabled ? (
              <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            )}
          </motion.button>
        </div>

        {/* Subtle hint text */}
        <div className="flex items-center justify-between mt-2 px-3">
          <span className="text-xs text-gray-400">
            Press Enter or click the arrow to start a new research
          </span>
          {hasChanged && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-teal-500 font-medium"
            >
              Ready to search
            </motion.span>
          )}
        </div>
      </form>
    </motion.div>
  );
};

export default InteractiveSearchBar;
