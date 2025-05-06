import Image from "next/image";
import { FC, useRef } from "react";
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
  // Only show input if not stopped
  if (isStopped) {
    return null;
  }

  const placeholder = handleSecondary
    ? "Any questions about this report?"
    : "What would you like to research next?";

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resetHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '3em'; // Reset to base height
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        return; // Allow new line on Shift+Enter
      } else {
        e.preventDefault();
        if (!disabled) {
          if (reset) reset();
          handleSubmit(promptValue);
          setPromptValue(''); // Clear prompt value
          resetHeight(); // Reset height after submit
        }
      }
    }
  };

  // Debounced version of the height adjustment function
  const adjustHeight = debounce((target: HTMLTextAreaElement) => {
    target.style.height = 'auto'; // Reset height to auto to allow shrinking
    target.style.height = `${target.scrollHeight}px`; // Adjust height
  }, 100); // Adjust the delay as needed

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target;
    adjustHeight(target); // Use debounced function
    setPromptValue(target.value);
  };

  return (
    <form
      className="mx-auto flex pt-2 pb-2 w-full items-center justify-between rounded-lg border bg-white px-3 shadow-[2px_2px_38px_0px_rgba(0,0,0,0.25),0px_-2px_4px_0px_rgba(0,0,0,0.25)_inset,1px_2px_4px_0px_rgba(0,0,0,0.25)_inset]"
      onSubmit={(e) => {
        e.preventDefault();
        if (reset) reset();
        handleSubmit(promptValue);
        setPromptValue(''); // Clear prompt value
        resetHeight();
      }}
    >

      <textarea
        placeholder={placeholder}
        ref={textareaRef}
        className="focus-visible::outline-0 my-1 w-full pl-5 font-light not-italic leading-[normal] 
        text-[#1B1B16]/30 text-black outline-none focus-visible:ring-0 focus-visible:ring-offset-0 
        sm:text-xl min-h-[3em] resize-none"
        disabled={disabled}
        value={promptValue}
        required
        rows={2}
        onKeyDown={handleKeyDown}
        onChange={handleTextareaChange}
      />
      <button
        disabled={disabled}
        type="submit"
        className="relative flex h-[50px] w-[50px] shrink-0 items-center justify-center rounded-[3px] bg-[linear-gradient(154deg,#1B1B16_23.37%,#565646_91.91%)] disabled:pointer-events-none disabled:opacity-75"
      >
        {disabled && (
          <div className="absolute inset-0 flex items-center justify-center">
            <TypeAnimation />
          </div>
        )}

        <Image
          unoptimized
          src={"/img/arrow-narrow-right.svg"}
          alt="search"
          width={24}
          height={24}
          className={disabled ? "invisible" : ""}
        />
      </button>
    </form>
  );
};

export default InputArea;
