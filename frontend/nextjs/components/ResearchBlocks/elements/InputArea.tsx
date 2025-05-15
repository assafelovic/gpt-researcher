import Image from "next/image";
import React, { FC, useRef } from "react";
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
  const placeholder = handleSecondary
    ? "Any questions about this report?"
    : "What would you like me to research next?";

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

  return handleSecondary ? (
    <span></span>
  ) : (
    <form
      className="mx-auto flex pt-2 pb-2 w-full items-center justify-between rounded-lg border bg-white px-3 shadow-[2px_2px_38px_0px_rgba(0,0,0,0.25),0px_-2px_4px_0px_rgba(0,0,0,0.25)_inset,1px_2px_4px_0px_rgba(0,0,0,0.25)_inset]"
      onSubmit={(e) => {
        e.preventDefault();
        if (reset) reset();
        handleSubmit(promptValue);
        setPromptValue('');
        resetHeight();
      }}
    >
      <textarea
        placeholder={placeholder}
        ref={textareaRef}
        className="focus-visible::outline-0 my-1 w-full pl-5 font-light not-italic leading-[normal] 
        text-[#1B1B16]/30 text-black outline-none focus-visible:ring-0 focus-visible:ring-offset-0 
        sm:text-xl min-h-[4em] resize-none"
        disabled={disabled}
        value={promptValue}
        required
        rows={3}
        onKeyDown={handleKeyDown}
        onChange={handleTextareaChange}
      />
      <button
        disabled={disabled}
        type="submit"
        className="relative flex h-[50px] w-[50px] shrink-0 items-center justify-center rounded-[3px] bg-teal-500 hover:bg-gradient-to-br hover:from-[#0cdbb6] hover:via-[#1fd0f0] hover:to-[#06dbee] transition-all duration-300 disabled:opacity-75 disabled:hover:bg-teal-500/75"
      >
        {disabled && (
          <div className="absolute inset-0 flex items-center justify-center">
            <TypeAnimation />
          </div>
        )}

        <div className="relative p-2 cursor-pointer">
          <img
            src={"/img/arrow-narrow-right.svg"}
            alt="search"
            width={24}
            height={24}
            className={`${disabled ? "invisible" : ""} transition-all duration-300 hover:scale-110 hover:brightness-110 hover:filter hover:drop-shadow-[0_0_3px_rgba(255,255,255,0.7)]`}
          />
        </div>
      </button>
    </form>
  );
};

export default InputArea;
