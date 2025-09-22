import Image from "next/image";
import React, { FC, useRef, useState, useEffect } from "react";
import TypeAnimation from "../../TypeAnimation";

type TInputAreaProps = {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleSubmit: (query: string) => void;
  handleSecondary?: (query: string) => void;
  disabled?: boolean;
  reset?: () => void;
  isStopped?: boolean;
};

// Debounce function to limit the rate at which a function can fire
function debounce(func: Function, wait: number) {
  let timeout: NodeJS.Timeout | undefined;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const InputArea: FC<TInputAreaProps> = ({
  promptValue,
  setPromptValue,
  handleSubmit,
  handleSecondary,
  disabled,
  reset,
  isStopped,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);
  const placeholder = "Enter your topic, question, or area of interest...";

  // Auto-focus the textarea when component mounts
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const resetHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '3em';
    }
  };

  const adjustHeight = debounce((target: HTMLTextAreaElement) => {
    target.style.height = 'auto';
    target.style.height = `${target.scrollHeight}px`;
  }, 100);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target;
    adjustHeight(target);
    setPromptValue(target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        return;
      } else {
        e.preventDefault();
        if (!disabled) {
          if (reset) reset();
          handleSubmit(promptValue);
          setPromptValue('');
          resetHeight();
        }
      }
    }
  };

  if (isStopped) {
    return null;
  }

  return (
    <div className="relative">
      {/* Gradient ring - subtle effect */}
      <div 
        className={`absolute -inset-0.5 rounded-xl bg-gradient-to-r from-[#0cdbb6]/50 via-[#1fd0f0]/40 to-[#06dbee]/50 blur-md opacity-45 transition-opacity duration-300 ${isFocused || promptValue ? 'opacity-55' : 'opacity-35'}`}
      />
      
      {/* Ambient glow effect */}
      <div 
        className="absolute -inset-4 rounded-xl opacity-25"
        style={{
          background: 'radial-gradient(circle at center, rgba(12, 219, 182, 0.15) 0%, rgba(6, 219, 238, 0.08) 40%, rgba(0, 0, 0, 0) 70%)',
        }}
      />
    
      <form
        className="mx-auto flex pt-2 pb-2 w-full items-center justify-between rounded-xl border border-gray-700/50 bg-gray-900/90 backdrop-blur-sm px-3 shadow-md relative overflow-hidden z-10"
        onSubmit={(e) => {
          e.preventDefault();
          if (reset) reset();
          handleSubmit(promptValue);
          setPromptValue('');
          resetHeight();
        }}
      >
        {/* Inner gradient blur effect */}
        <div className="absolute -inset-1 bg-gradient-to-r from-teal-400/4 via-indigo-400/4 to-purple-400/4 blur-xl opacity-25 animate-pulse pointer-events-none"></div>
        
        <textarea
          placeholder={placeholder}
          ref={textareaRef}
          className="focus-visible::outline-0 my-1 w-full pl-2 pr-3 font-light not-italic leading-[normal] 
          text-gray-300 placeholder-gray-400 outline-none focus-visible:ring-0 focus-visible:ring-offset-0 
          text-lg sm:text-xl min-h-[4em] resize-none relative z-10 bg-transparent"
          disabled={disabled}
          value={promptValue}
          required
          rows={3}
          onKeyDown={handleKeyDown}
          onChange={handleTextareaChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />
        
        <button
          disabled={disabled}
          type="submit"
          className="relative flex h-[45px] w-[45px] shrink-0 items-center justify-center rounded-md bg-teal-600 hover:bg-gradient-to-br hover:from-[#0cdbb6] hover:via-[#1fd0f0] hover:to-[#06dbee] transition-all duration-300 disabled:opacity-50 disabled:hover:bg-teal-600/75 z-10 before:absolute before:inset-0 before:rounded-md before:bg-gradient-to-r before:from-teal-300/20 before:to-cyan-300/20 before:opacity-0 before:transition-opacity before:hover:opacity-100 before:-z-10 disabled:before:opacity-0 group"
        >
          {disabled && (
            <div className="absolute inset-0 flex items-center justify-center">
              <TypeAnimation />
            </div>
          )}

          <div className="relative p-2 cursor-pointer overflow-hidden">
            {/* Glow effect on hover */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-white/20 rounded-full blur-md"></div>
            
            <img
              src={"/img/arrow-narrow-right.svg"}
              alt="search"
              width={20}
              height={20}
              className={`${disabled ? "invisible" : ""} transition-all duration-300 group-hover:scale-110 group-hover:brightness-110 group-hover:filter group-hover:drop-shadow-[0_0_3px_rgba(255,255,255,0.7)]`}
            />
          </div>
        </button>
      </form>
      
      {/* Animated glow effect at the bottom */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-[3px] opacity-35 overflow-hidden"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(12, 219, 182, 0.5) 0%, rgba(6, 219, 238, 0.3) 25%, rgba(6, 219, 238, 0.08) 50%, rgba(0, 0, 0, 0) 75%)',
          boxShadow: '0 0 8px 1px rgba(12, 219, 182, 0.25), 0 0 16px 2px rgba(6, 219, 238, 0.08)'
        }}
      />
    </div>
  );
};

export default InputArea;
