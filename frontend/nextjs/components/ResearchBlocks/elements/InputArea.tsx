import Image from "next/image";
import React, { FC, useRef, useState, useEffect } from "react";
import TypeAnimation from "../../TypeAnimation";
import { hltBranding } from "@/lib/hltBranding";

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
        className={`absolute -inset-0.5 rounded-xl bg-gradient-to-r ${
          hltBranding.enabled
            ? "from-[#155EEF]/60 via-[#1FB2C6]/45 to-[#155EEF]/55"
            : "from-[#0cdbb6]/50 via-[#1fd0f0]/40 to-[#06dbee]/50"
        } blur-md opacity-45 transition-opacity duration-300 ${isFocused || promptValue ? 'opacity-55' : 'opacity-35'}`}
      />
      
      {/* Ambient glow effect */}
      <div 
        className="absolute -inset-4 rounded-xl opacity-25"
        style={{
          background: hltBranding.enabled
            ? 'radial-gradient(circle at center, rgba(21, 94, 239, 0.18) 0%, rgba(31, 178, 198, 0.08) 40%, rgba(0, 0, 0, 0) 70%)'
            : 'radial-gradient(circle at center, rgba(12, 219, 182, 0.15) 0%, rgba(6, 219, 238, 0.08) 40%, rgba(0, 0, 0, 0) 70%)',
        }}
      />
    
      <form
        className="relative z-10 mx-auto flex w-full items-center justify-between overflow-hidden rounded-xl border border-white/10 bg-[#111113]/95 px-3 pb-2 pt-2 shadow-md backdrop-blur-sm"
        onSubmit={(e) => {
          e.preventDefault();
          if (reset) reset();
          handleSubmit(promptValue);
          setPromptValue('');
          resetHeight();
        }}
      >
        {/* Inner gradient blur effect */}
        <div className="pointer-events-none absolute -inset-1 animate-pulse bg-gradient-to-r from-blue-400/5 via-cyan-400/5 to-blue-400/5 opacity-25 blur-xl"></div>
        
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
          className="group relative z-10 flex h-[45px] w-[45px] shrink-0 items-center justify-center rounded-md bg-[#155EEF] transition-all duration-300 before:absolute before:inset-0 before:-z-10 before:rounded-md before:bg-gradient-to-r before:from-blue-300/20 before:to-cyan-300/20 before:opacity-0 before:transition-opacity before:hover:opacity-100 hover:bg-[#1249C4] disabled:opacity-50 disabled:hover:bg-[#155EEF]/75 disabled:before:opacity-0"
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
          boxShadow: hltBranding.enabled
            ? '0 0 10px 1px rgba(21, 94, 239, 0.28), 0 0 18px 2px rgba(31, 178, 198, 0.1)'
            : '0 0 8px 1px rgba(12, 219, 182, 0.25), 0 0 16px 2px rgba(6, 219, 238, 0.08)'
        }}
      />
    </div>
  );
};

export default InputArea;
