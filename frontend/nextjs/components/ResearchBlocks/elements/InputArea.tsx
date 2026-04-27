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
      textareaRef.current.style.height = "3em";
    }
  };

  const adjustHeight = debounce((target: HTMLTextAreaElement) => {
    target.style.height = "auto";
    target.style.height = `${target.scrollHeight}px`;
  }, 100);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target;
    adjustHeight(target);
    setPromptValue(target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter") {
      if (e.shiftKey) {
        return;
      } else {
        e.preventDefault();
        if (!disabled) {
          if (reset) reset();
          handleSubmit(promptValue);
          setPromptValue("");
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
      <div
        className={`absolute -inset-0.5 rounded-xl bg-gradient-to-r ${
          hltBranding.enabled
            ? "from-[#155EEF]/30 via-[#1FB2C6]/20 to-[#155EEF]/30"
            : "from-[#0cdbb6]/50 via-[#1fd0f0]/40 to-[#06dbee]/50"
        } opacity-35 blur-sm transition-opacity duration-300 ${isFocused || promptValue ? "opacity-45" : "opacity-20"}`}
      />

      <form
        className="relative z-10 mx-auto flex w-full items-center justify-between overflow-hidden rounded-xl border border-white/10 bg-[#111113]/95 px-3 py-2 shadow-sm backdrop-blur-sm"
        onSubmit={(e) => {
          e.preventDefault();
          if (reset) reset();
          handleSubmit(promptValue);
          setPromptValue("");
          resetHeight();
        }}
      >
        <textarea
          placeholder={placeholder}
          ref={textareaRef}
          className="focus-visible::outline-0 relative z-10 my-0.5 min-h-[2.4em] w-full resize-none bg-transparent pl-2 pr-3 text-base font-light not-italic leading-[normal] text-gray-300 placeholder-gray-400 outline-none focus-visible:ring-0 focus-visible:ring-offset-0 sm:text-lg"
          disabled={disabled}
          value={promptValue}
          required
          rows={1}
          onKeyDown={handleKeyDown}
          onChange={handleTextareaChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
        />

        <button
          disabled={disabled}
          type="submit"
          className="group relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-[#155EEF] transition-all duration-300 before:absolute before:inset-0 before:-z-10 before:rounded-md before:bg-gradient-to-r before:from-blue-300/20 before:to-cyan-300/20 before:opacity-0 before:transition-opacity hover:bg-[#1249C4] before:hover:opacity-100 disabled:opacity-50 disabled:before:opacity-0 disabled:hover:bg-[#155EEF]/75"
        >
          {disabled && (
            <div className="absolute inset-0 flex items-center justify-center">
              <TypeAnimation />
            </div>
          )}

          <div className="relative cursor-pointer overflow-hidden p-2">
            <img
              src={"/img/arrow-narrow-right.svg"}
              alt="search"
              width={20}
              height={20}
              className={`${disabled ? "invisible" : ""} transition-all duration-200 group-hover:scale-105`}
            />
          </div>
        </button>
      </form>
    </div>
  );
};

export default InputArea;
