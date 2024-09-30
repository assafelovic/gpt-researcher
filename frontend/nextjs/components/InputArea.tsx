import Image from "next/image";
import { FC } from "react";
import TypeAnimation from "./TypeAnimation";

type TInputAreaProps = {
  promptValue: string;
  setPromptValue: React.Dispatch<React.SetStateAction<string>>;
  handleDisplayResult: () => void;
  disabled?: boolean;
  reset?: () => void;
};

const InputArea: FC<TInputAreaProps> = ({
  promptValue,
  setPromptValue,
  handleDisplayResult,
  disabled,
  reset,
}) => {
  return (
    <form
      className="mx-auto flex h-14 w-full max-w-md items-center rounded-full border border-gray-300 bg-gray-100 px-4 shadow-sm"
      onSubmit={(e) => {
        e.preventDefault();
        if (reset) reset();
        handleDisplayResult();
      }}
    >
      <input
        type="text"
        placeholder="What would you like me to research next?"
        className="flex-1 bg-transparent pl-2 text-base text-gray-800 placeholder-gray-500 focus:outline-none"
        disabled={disabled}
        value={promptValue}
        required
        onChange={(e) => setPromptValue(e.target.value)}
      />
      <button
        disabled={disabled}
        type="submit"
        className="relative flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
      >
        {disabled && (
          <div className="absolute inset-0 flex items-center justify-center">
            <TypeAnimation />
          </div>
        )}

        {!disabled && (
          <Image
            src="/img/arrow-narrow-right.svg"
            alt="search"
            width={24}
            height={24}
          />
        )}
      </button>
    </form>
  );
};

export default InputArea;